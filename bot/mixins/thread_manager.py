"""
Thread management mixin providing centralized thread tracking, monitoring, and timeout enforcement.
"""
from threading import Thread, Lock, current_thread
from time import time
import traceback
import sys


class ThreadManager:
    """
    Centralized thread registry and management.

    Provides:
    - Thread tracking with metadata
    - Timeout enforcement with automatic killing
    - Debug logging for timeout diagnosis
    - Thread statistics and monitoring
    """

    # Class-level registry (shared across all modules)
    _thread_registry = {}
    _registry_lock = Lock()

    def spawn_tracked(self, name, target, *args, timeout=None, **kwargs):
        """
        Spawn a tracked thread with optional timeout enforcement.

        Args:
            name: Human-readable thread name (e.g., "action_lp")
            target: Function to execute in thread
            *args: Positional arguments for target
            timeout: Maximum execution time in seconds (None = no timeout)
            **kwargs: Keyword arguments for target

        Returns:
            Thread object
        """
        thread_context = {
            'name': name,
            'started_at': time(),
            'timeout': timeout,
            'spawned_by': self.get_module_identifier() if hasattr(self, 'get_module_identifier') else 'unknown',
            'status': 'running',
            'target_name': f"{target.__module__}.{target.__name__}" if hasattr(target, '__name__') else str(target),
            'args': str(args)[:200],  # Truncate for safety
            'debug_data': None  # Will be set by target if needed
        }

        def wrapped_target():
            thread_id = current_thread().ident
            try:
                result = target(*args, **kwargs)
                ThreadManager._mark_thread_completed(thread_id)
                return result
            except Exception as e:
                ThreadManager._mark_thread_failed(thread_id, e)
                print(f"[ThreadManager] Thread {name} failed with exception: {e}")
                traceback.print_exc()

        thread = Thread(target=wrapped_target, name=name, daemon=True)
        thread.start()

        thread_context['thread_obj'] = thread

        with ThreadManager._registry_lock:
            ThreadManager._thread_registry[thread.ident] = thread_context

        return thread

    @staticmethod
    def _mark_thread_completed(thread_id):
        """Mark thread as completed successfully."""
        with ThreadManager._registry_lock:
            if thread_id in ThreadManager._thread_registry:
                ThreadManager._thread_registry[thread_id]['status'] = 'completed'
                ThreadManager._thread_registry[thread_id]['completed_at'] = time()

    @staticmethod
    def _mark_thread_failed(thread_id, exception):
        """Mark thread as failed with exception."""
        with ThreadManager._registry_lock:
            if thread_id in ThreadManager._thread_registry:
                ThreadManager._thread_registry[thread_id]['status'] = 'failed'
                ThreadManager._thread_registry[thread_id]['failed_at'] = time()
                ThreadManager._thread_registry[thread_id]['exception'] = str(exception)

    def set_thread_debug_data(self, debug_data):
        """
        Set debug data for current thread (called from within the thread).

        Args:
            debug_data: Dict with debug info (e.g., {'waiting_for': 'telnet response', 'buffer': '...'})
        """
        thread_id = current_thread().ident
        with ThreadManager._registry_lock:
            if thread_id in ThreadManager._thread_registry:
                ThreadManager._thread_registry[thread_id]['debug_data'] = debug_data

    @classmethod
    def check_thread_timeouts(cls):
        """
        Check all tracked threads for timeouts and kill if necessary.
        Should be called periodically from a main loop.

        Returns:
            List of killed thread IDs
        """
        current_time = time()
        killed_threads = []
        threads_to_remove = []

        with cls._registry_lock:
            for thread_id, context in list(cls._thread_registry.items()):
                # Clean up old completed/failed threads (after 60 seconds)
                if context['status'] in ('completed', 'failed'):
                    completion_time = context.get('completed_at') or context.get('failed_at', 0)
                    if current_time - completion_time > 60:
                        threads_to_remove.append(thread_id)
                        continue

                # Check timeout for running threads
                if context['status'] == 'running' and context['timeout'] is not None:
                    runtime = current_time - context['started_at']
                    if runtime > context['timeout']:
                        # Kill thread
                        cls._kill_thread(thread_id, context, runtime)
                        killed_threads.append(thread_id)
                        threads_to_remove.append(thread_id)

            # Remove cleaned threads
            for thread_id in threads_to_remove:
                del cls._thread_registry[thread_id]

        return killed_threads

    @classmethod
    def _kill_thread(cls, thread_id, context, runtime):
        """
        Kill a thread that exceeded timeout with detailed debug logging.

        Args:
            thread_id: Thread identifier
            context: Thread metadata dict
            runtime: Actual runtime in seconds
        """
        print("=" * 80)
        print(f"[ThreadManager] THREAD TIMEOUT - KILLING THREAD")
        print("=" * 80)
        print(f"Thread Name:     {context['name']}")
        print(f"Thread ID:       {thread_id}")
        print(f"Spawned By:      {context['spawned_by']}")
        print(f"Target:          {context['target_name']}")
        print(f"Started At:      {time() - context['started_at']:.2f}s ago")
        print(f"Timeout:         {context['timeout']}s")
        print(f"Actual Runtime:  {runtime:.2f}s")
        print(f"Exceeded By:     {runtime - context['timeout']:.2f}s")
        print("-" * 80)
        print(f"Arguments:       {context['args']}")

        if context['debug_data']:
            print("-" * 80)
            print("Debug Data:")
            for key, value in context['debug_data'].items():
                # Truncate long values
                value_str = str(value)
                if len(value_str) > 500:
                    value_str = value_str[:500] + f"... (truncated, total length: {len(value_str)})"
                print(f"  {key}: {value_str}")

        print("-" * 80)
        print("Stack Trace:")
        thread_obj = context.get('thread_obj')
        if thread_obj and thread_obj.is_alive():
            # Try to get stack trace (Python 3.x)
            try:
                frame = sys._current_frames().get(thread_id)
                if frame:
                    traceback.print_stack(frame)
                else:
                    print("  (Stack trace not available)")
            except Exception as e:
                print(f"  (Could not retrieve stack trace: {e})")
        else:
            print("  (Thread already dead)")

        print("=" * 80)

        # Note: Python doesn't support forceful thread termination
        # The thread will continue running but is marked as timed out
        # Consider this a "soft kill" - mainly for monitoring/alerting
        context['status'] = 'timeout_killed'
        context['killed_at'] = time()

    @classmethod
    def get_all_threads(cls):
        """Get snapshot of all tracked threads."""
        with cls._registry_lock:
            return {
                tid: {
                    'name': ctx['name'],
                    'spawned_by': ctx['spawned_by'],
                    'status': ctx['status'],
                    'started_at': ctx['started_at'],
                    'runtime': time() - ctx['started_at'] if ctx['status'] == 'running' else None,
                    'timeout': ctx['timeout']
                }
                for tid, ctx in cls._thread_registry.items()
            }

    @classmethod
    def get_thread_count(cls):
        """Get current number of tracked threads."""
        with cls._registry_lock:
            return len(cls._thread_registry)

    @classmethod
    def get_thread_stats(cls):
        """Get thread statistics."""
        with cls._registry_lock:
            stats = {
                'total': len(cls._thread_registry),
                'running': 0,
                'completed': 0,
                'failed': 0,
                'timeout_killed': 0,
                'by_spawner': {},
                'oldest_thread': None,
                'oldest_age': 0
            }

            current_time = time()
            for context in cls._thread_registry.values():
                stats[context['status']] += 1

                spawner = context['spawned_by']
                stats['by_spawner'][spawner] = stats['by_spawner'].get(spawner, 0) + 1

                if context['status'] == 'running':
                    age = current_time - context['started_at']
                    if age > stats['oldest_age']:
                        stats['oldest_age'] = age
                        stats['oldest_thread'] = context['name']

            return stats
