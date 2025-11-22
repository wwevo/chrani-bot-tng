# Performance Analysis: Player Update Lag

## Problem Statement

Player position updates are polled every 3 seconds via the `lp` command, but actions triggered by position changes (teleports, `player_moved` callbacks) can take 10+ seconds to execute.

## Architecture Overview

### Update Flow Chain

```
1. players.run() [every 3s]
   └─> trigger_action_hook("getplayers")

2. getplayers action
   ├─> Send "lp" command to telnet
   ├─> Wait for response
   ├─> Parse player data
   └─> DOM.upsert(player_data)

3. DOM.upsert()
   ├─> deepcopy(entire_dom)  ← CRITICAL BOTTLENECK #1
   ├─> Recursively process updates
   ├─> Collect matching callbacks
   └─> Submit callbacks to ThreadPool

4. ThreadPoolExecutor (max 10 workers)
   ├─> Execute callbacks in parallel
   └─> Wait if pool is full  ← CRITICAL BOTTLENECK #2

5. player_moved callback
   ├─> Check if player authenticated
   ├─> Check if position changed
   ├─> Check if inside lobby
   └─> trigger_action_hook("teleport_to_coordinates")
```

## Identified Bottlenecks

### 1. **DOM Deepcopy (CRITICAL)**

**Location:** `bot/modules/dom/callback_dict.py:248`

```python
original_state = deepcopy(dict(self))  # Copies ENTIRE DOM every upsert!
```

**Impact:**
- Executes on EVERY `upsert()` call
- Copies the entire DOM tree (all modules, all players, all data)
- With 5+ players online, this could be 10-50MB of data
- Estimated time: **10-100ms per upsert** depending on DOM size

**Why it's needed:**
- Provides "before" state to callbacks for comparison
- Currently used by very few callbacks

**Potential fix:**
- Only copy affected subtrees, not entire DOM
- Use shallow copy + selective deep copy
- Implement copy-on-write semantics

### 2. **Thread Pool Size**

**Location:** `bot/constants.py:54`

```python
CALLBACK_THREAD_POOL_SIZE = 10  # Only 10 concurrent callbacks!
```

**Impact:**
- If more than 10 callbacks triggered simultaneously, they queue
- Each player update can trigger multiple callbacks:
  - `player_moved` (permissions module)
  - `send_player_update_to_map` (players module)
  - Other position-based triggers
- With 5 players, that's potentially 10-15 callbacks per update cycle
- **Callbacks wait in queue if pool is saturated**

**Potential fix:**
- Increase pool size to 20-50
- Implement priority queue (teleport-related callbacks first)
- Use dedicated pools for different callback types

### 3. **Callback Execution Time**

**Location:** `bot/modules/permissions/triggers/player_moved.py`

**Each callback:**
- Checks authentication status
- Checks if position changed
- Iterates through all lobbies
- Performs boundary calculations
- May trigger additional actions

**Estimated time:** 1-5ms per callback under normal load

### 4. **Synchronous Telnet Commands**

Some actions may block waiting for telnet responses, preventing other work.

## Profiling Instrumentation

### What's Being Measured

The new profiling system tracks:

| Metric | What It Measures |
|--------|-----------------|
| `dom_upsert_total` | Total time for DOM upsert operation |
| `dom_deepcopy` | Time spent copying entire DOM |
| `dom_collect_callbacks` | Time finding and collecting callbacks |
| `dom_submit_callbacks` | Time submitting callbacks to thread pool |
| `player_moved_callback` | Time executing player_moved callback |

### How To Use

1. **In-game command** (admin only):
   ```
   /profiling
   ```
   Shows top 10 slowest operations with avg/p95/max times

2. **Check server logs:**
   All detailed profiling data is logged automatically

3. **Programmatic access:**
   ```python
   from bot.profiler import profiler

   stats = profiler.get_stats("dom_upsert_total")
   # Returns: {count, total, avg, min, max, median, p95}
   ```

### Reading the Results

Example output:
```
dom_deepcopy: avg=45.2ms p95=78.3ms max=120.5ms (1234 calls)
```

- **avg**: Average time - indicates typical performance
- **p95**: 95th percentile - shows worst-case scenarios (excluding outliers)
- **max**: Maximum time ever recorded
- **calls**: How many times this was measured

**What to look for:**
- `dom_deepcopy` > 50ms → DOM is getting too large
- `dom_submit_callbacks` > 10ms → Thread pool likely saturated
- `player_moved_callback` > 5ms → Callback logic is slow

## Expected Improvements

### Quick Wins (Low effort, high impact)

1. **Increase thread pool size**
   - Change `CALLBACK_THREAD_POOL_SIZE` from 10 to 30
   - **Expected improvement:** 30-50% reduction in lag
   - **Risk:** Low (threads are cheap in Python with gevent)

2. **Add callback metrics**
   - Instrument all frequently-used callbacks
   - Identify which callbacks are actually slow
   - **Expected improvement:** Better visibility for future optimization

### Medium Effort

3. **Optimize DOM deepcopy**
   - Only copy subtree being modified
   - **Expected improvement:** 50-80% reduction in upsert time
   - **Risk:** Medium (requires careful refactoring)

4. **Cache lobby lookups in player_moved**
   - Lobby list rarely changes, don't look up every time
   - **Expected improvement:** 10-20% faster callbacks
   - **Risk:** Low

### High Effort (Future work)

5. **Implement copy-on-write DOM**
   - Only copy when actually needed by callbacks
   - **Expected improvement:** 80-95% reduction in upsert overhead
   - **Risk:** High (major architectural change)

6. **Separate thread pools by priority**
   - Critical callbacks (teleports) in fast pool
   - Non-critical callbacks in slow pool
   - **Expected improvement:** More predictable latency
   - **Risk:** Medium

## How to Diagnose Your Issue

1. **Start the bot with profiling enabled** (it's on by default)

2. **Let it run for 5-10 minutes** with players online

3. **Run `/profiling` in-game** to see stats

4. **Look for these patterns:**

   **Pattern A: DOM Deepcopy is the killer**
   ```
   dom_deepcopy: avg=80ms p95=150ms
   dom_upsert_total: avg=95ms p95=170ms
   ```
   → The deepcopy is taking 80-90% of upsert time
   → **Fix:** Optimize deepcopy (see "Medium Effort" above)

   **Pattern B: Thread pool saturation**
   ```
   dom_submit_callbacks: avg=25ms p95=200ms
   ```
   → High variance suggests threads are queuing
   → **Fix:** Increase CALLBACK_THREAD_POOL_SIZE

   **Pattern C: Slow callbacks**
   ```
   player_moved_callback: avg=15ms p95=50ms
   ```
   → The callback itself is slow
   → **Fix:** Optimize callback logic

5. **Check server logs** for detailed breakdown

## Next Steps

1. ✅ Profiling instrumentation added
2. ⏳ Run with real workload, collect metrics
3. ⏳ Identify primary bottleneck from data
4. ⏳ Implement quick wins (thread pool size)
5. ⏳ Implement medium-effort optimizations based on data
6. ⏳ Re-measure and validate improvements

## Files Modified

- `bot/profiler.py` - New profiling system
- `bot/modules/dom/callback_dict.py` - Instrumented DOM operations
- `bot/modules/permissions/triggers/player_moved.py` - Instrumented callback
- `bot/modules/players/commands/show_profiling_stats.py` - In-game stats display
- `PERFORMANCE_ANALYSIS.md` - This document
