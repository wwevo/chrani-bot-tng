# Command Queue Redesign - Priority & Rate Limiting

## Current Problem
- Commands are executed only in 3-second telnet cycles
- No priority system: `lp` and `teleportplayer` treated equally
- Teleport commands delayed up to 3 seconds waiting for next cycle
- No rate limiting beyond "max 6 commands per cycle"

## Proposed Solution

### 1. Priority Queue System

Three priority levels:
- **HIGH**: System-critical commands that need immediate execution
  - `teleportplayer` - security critical (lobby enforcement)
  - Player authentication commands
  - Server state queries when needed

- **NORMAL**: Regular monitoring commands
  - `lp` (list players) - runs every 3s anyway
  - `gettime`
  - Other periodic polling

- **LOW**: Non-critical commands
  - Manual admin commands
  - Statistics gathering
  - Batch operations

### 2. Implementation Approach

```python
class PriorityCommandQueue:
    def __init__(self):
        self.queues = {
            'high': deque(),
            'normal': deque(),
            'low': deque()
        }
        self.rate_limits = {
            'high': (10, 1.0),    # max 10 commands per 1 second
            'normal': (6, 1.0),   # max 6 commands per 1 second
            'low': (3, 1.0)       # max 3 commands per 1 second
        }
        self.last_sent = {
            'high': [],
            'normal': [],
            'low': []
        }

    def add_command(self, command, priority='normal'):
        """Add command with priority check."""
        # Detect priority from command content if not specified
        if priority == 'auto':
            priority = self._detect_priority(command)

        queue = self.queues[priority]
        if command not in queue:
            queue.appendleft(command)
            return True
        return False

    def _detect_priority(self, command):
        """Auto-detect command priority."""
        high_priority_commands = ['teleportplayer', 'kick', 'ban']
        if any(cmd in command for cmd in high_priority_commands):
            return 'high'

        low_priority_commands = ['listplayerslanded', 'listthreads']
        if any(cmd in command for cmd in low_priority_commands):
            return 'low'

        return 'normal'

    def get_next_batch(self, max_total=6):
        """Get next batch respecting priorities and rate limits."""
        current_time = time()
        batch = []

        # Try high priority first (up to 50% of batch)
        batch.extend(self._get_from_queue('high', current_time, max_total // 2))

        # Fill rest with normal priority
        remaining = max_total - len(batch)
        batch.extend(self._get_from_queue('normal', current_time, remaining))

        # Low priority only if nothing else
        if not batch:
            batch.extend(self._get_from_queue('low', current_time, max_total))

        return batch

    def _get_from_queue(self, priority, current_time, max_count):
        """Get commands from specific priority queue with rate limiting."""
        max_rate, time_window = self.rate_limits[priority]

        # Clean old timestamps
        cutoff = current_time - time_window
        self.last_sent[priority] = [t for t in self.last_sent[priority] if t > cutoff]

        # Check rate limit
        available_slots = max_rate - len(self.last_sent[priority])
        count = min(max_count, available_slots)

        commands = []
        queue = self.queues[priority]
        for _ in range(count):
            try:
                cmd = queue.popleft()
                commands.append(cmd)
                self.last_sent[priority].append(current_time)
            except IndexError:
                break

        return commands
```

### 3. Integration Changes

**Current:**
```python
# In run() loop - every 3 seconds
if server_is_online:
    self.execute_telnet_command_queue(self.max_command_queue_execution)
```

**Proposed:**
```python
# In run() loop - every 3 seconds OR on-demand trigger
if server_is_online:
    batch = self.command_queue.get_next_batch(max_total=6)
    for command in batch:
        self.tn.write(f"{command}\r\n".encode('ascii'))
```

**Key change:** Add trigger mechanism for high-priority commands
```python
def add_telnet_command_to_queue(self, command, priority='normal'):
    """Add command and trigger immediate execution for high priority."""
    added = self.command_queue.add_command(command, priority)

    if added and priority == 'high':
        # Don't wait for next cycle - execute immediately
        # (But still respect rate limits!)
        self._execute_high_priority_batch()

    return added

def _execute_high_priority_batch(self):
    """Execute high-priority commands immediately (rate-limited)."""
    if not self.server_is_online:
        return

    batch = self.command_queue.get_next_batch(max_total=3)  # Smaller batch
    for command in batch:
        try:
            self.tn.write(f"{command}\r\n".encode('ascii'))
        except Exception as e:
            logger.error("high_priority_command_failed", command=command, error=str(e))
```

### 4. Usage Changes

**Priority Definition in Meta:**

Priorities are defined in action/trigger metadata, not hardcoded:

```python
# In teleport_player.py
action_meta = {
    "description": "teleports a player",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "command_priority": "high",  # ← Priority defined here!
    "enabled": True
}
```

**Telnet Module Integration:**

The telnet module automatically extracts priority from the calling context:

```python
# Option 1: Explicit priority from action_meta
def add_telnet_command_to_queue(self, command, action_meta=None, priority='normal'):
    """Add command with priority from action metadata or explicit value."""
    if action_meta and 'command_priority' in action_meta:
        priority = action_meta['command_priority']

    return self.command_queue.add_command(command, priority)

# Usage in action:
module.telnet.add_telnet_command_to_queue(command, action_meta=action_meta)
```

```python
# Option 2: Helper method that bundles command + meta
def queue_action_command(self, command, action_meta):
    """Queue a command with priority from action metadata."""
    priority = action_meta.get('command_priority', 'normal')
    return self.add_telnet_command_to_queue(command, priority=priority)

# Usage in action:
module.telnet.queue_action_command(command, action_meta)
```

**Examples:**

```python
# High priority: teleport_player.py
action_meta = {
    "command_priority": "high",
    # ...
}

# Normal priority: get_players.py
action_meta = {
    "command_priority": "normal",  # or omit (defaults to normal)
    # ...
}

# Low priority: list_threads.py
action_meta = {
    "command_priority": "low",
    # ...
}
```

### 5. Benefits

1. **Reduced Latency**: High-priority commands execute immediately
   - Teleports: ~0-500ms instead of 0-3000ms

2. **Better Resource Management**: Rate limiting prevents telnet overload
   - Per-priority limits prevent one priority starving others

3. **Fair Scheduling**: Normal operations (lp polling) don't block critical actions

4. **Flexible**: Easy to add new priority tiers or adjust limits

### 6. Migration Path

1. Add `PriorityCommandQueue` class to telnet module
2. Replace `deque` with `PriorityCommandQueue` in telnet.__init__
3. Update `add_telnet_command_to_queue` signature (backward compatible)
4. Update critical action calls to use `priority='high'`
5. Test rate limits don't cause command drops

### 7. Potential Issues

- **Starvation**: Low-priority commands might never execute
  - Solution: Aging mechanism (bump priority after X seconds)

- **Telnet overload**: Too many immediate executions
  - Solution: Rate limits per priority tier

- **Complexity**: More code to maintain
  - Solution: Well-tested, clear abstraction

### 8. Testing Strategy

1. Profile command latency before/after
2. Stress test with 10+ simultaneous teleports
3. Verify low-priority commands still execute
4. Check rate limits work under load

## Expected Performance Impact

**Before:**
- Teleport delay: 0-6000ms (avg ~3000ms)
- Reason: Waiting for cycle + command execution

**After:**
- Teleport delay: 0-500ms (avg ~250ms)
- Reason: Immediate execution + rate limit buffer

**CPU Impact:** Minimal - same number of commands, just better scheduled

## Future Enhancements (Post 1.0)

### Web Interface for Priority Management

Allow admins to adjust command priorities via webinterface:

**Features:**
- View all actions/commands with current priorities
- Adjust priority (high/normal/low) per action
- Adjust rate limits per priority tier
- Monitor command queue stats in real-time
- History of priority changes (audit log)

**UI Mockup:**
```
┌─────────────────────────────────────────────────────┐
│ Command Priority Management                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│ Action               Current    New      [Save]     │
│ ─────────────────────────────────────────────────   │
│ teleportplayer       HIGH       [▼]                 │
│ getplayers           NORMAL     [▼]                 │
│ kick                 HIGH       [▼]                 │
│ listthreads          LOW        [▼]                 │
│                                                      │
│ Rate Limits:                                        │
│ ─────────────────────────────────────────────────   │
│ High:   [10] commands per [1.0] seconds            │
│ Normal: [ 6] commands per [1.0] seconds            │
│ Low:    [ 3] commands per [1.0] seconds            │
│                                                      │
│ Queue Stats (last 60s):                             │
│ ─────────────────────────────────────────────────   │
│ High:   245 commands, avg wait: 23ms                │
│ Normal: 180 commands, avg wait: 156ms               │
│ Low:    12 commands, avg wait: 2.3s                 │
└─────────────────────────────────────────────────────┘
```

**Implementation:**
- Store priority overrides in database
- Merge with default action_meta values
- Reload on-the-fly without restart
- Validate rate limits to prevent telnet overload

**Benefits:**
- Fine-tune performance without code changes
- Adapt to server load dynamically
- Debug priority issues quickly
