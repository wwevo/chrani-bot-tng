"""
Reactive Dictionary with Callbacks

A dictionary implementation that triggers callbacks when values are modified.
Similar to React's state management but for Python dictionaries.

Features:
- Monitors nested dictionary changes (insert, update, delete, append)
- Path-based callback registration with wildcard support
- Thread-safe callback execution
- Efficient path matching using pre-compiled patterns
"""

from typing import Dict, List, Any, Optional, Callable, Tuple
from collections.abc import Mapping
from collections import deque
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from functools import reduce
import operator
import re

from bot import loaded_modules_dict
from bot.constants import CALLBACK_THREAD_POOL_SIZE


class CallbackDict(dict):
    """
    A dictionary that triggers registered callbacks when its values change.

    Callbacks can be registered for specific paths (e.g., "players/76561198012345678/name")
    or with wildcards (e.g., "players/%steamid%/name").
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Structure: {depth: {path_pattern: [callback_info, ...]}}
        self._callbacks: Dict[int, Dict[str, List[Dict]]] = {}
        # Compiled regex patterns for fast matching: {path_pattern: compiled_regex}
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        # Thread pool for callback execution (reuse threads instead of creating new ones)
        self._executor = ThreadPoolExecutor(max_workers=CALLBACK_THREAD_POOL_SIZE, thread_name_prefix="callback")

    # ==================== Path Utilities ====================

    @staticmethod
    def _split_path(path: str) -> List[str]:
        """Split a path string into components."""
        return path.split("/") if path else []

    @staticmethod
    def _join_path(components: List[str]) -> str:
        """Join path components into a string."""
        return "/".join(components)

    @staticmethod
    def _get_nested_value(data: dict, keys: List[str]) -> Any:
        """Get a value from a nested dictionary using a list of keys."""
        if not keys:
            return data
        return reduce(operator.getitem, keys, data)

    def _calculate_depth(self, d: Any) -> int:
        """Calculate the maximum depth of a nested dictionary."""
        if not isinstance(d, dict) or not d:
            return 0
        return 1 + max((self._calculate_depth(v) for v in d.values()), default=0)

    # ==================== Pattern Matching ====================

    def _compile_pattern(self, path_pattern: str) -> re.Pattern:
        """
        Compile a path pattern into a regex for efficient matching.

        Wildcards like %steamid% become regex capture groups.
        Example: "players/%steamid%/name" -> r"^players/([^/]+)/name$"
        """
        if path_pattern in self._compiled_patterns:
            return self._compiled_patterns[path_pattern]

        # Escape special regex characters except our wildcard markers
        escaped = re.escape(path_pattern)
        # Convert %wildcard% to regex capture group
        regex_pattern = re.sub(r'%[^%]+%', r'([^/]+)', escaped)
        # Anchor the pattern
        regex_pattern = f"^{regex_pattern}$"

        compiled = re.compile(regex_pattern)
        self._compiled_patterns[path_pattern] = compiled
        return compiled

    def _match_path(self, path: str, depth: int) -> List[str]:
        """
        Find all registered callback patterns that match the given path.

        Returns list of matching pattern strings.
        """
        if depth not in self._callbacks:
            return []

        matching_patterns = []
        for pattern in self._callbacks[depth].keys():
            compiled_pattern = self._compile_pattern(pattern)
            if compiled_pattern.match(path):
                matching_patterns.append(pattern)

        return matching_patterns

    # ==================== Callback Management ====================

    def register_callback(
        self,
        module: Any,
        path_pattern: str,
        callback: Callable
    ) -> None:
        """
        Register a callback for a specific path pattern.

        Args:
            module: The module that owns this callback
            path_pattern: Path to monitor (e.g., "players/%steamid%/name")
            callback: Function to call when path changes
        """
        depth = path_pattern.count('/')

        # Initialize depth level if needed
        if depth not in self._callbacks:
            self._callbacks[depth] = {}

        # Initialize pattern list if needed
        if path_pattern not in self._callbacks[depth]:
            self._callbacks[depth][path_pattern] = []

        # Add callback info
        self._callbacks[depth][path_pattern].append({
            "callback": callback,
            "module": module
        })

    def _collect_callbacks(
        self,
        path: str,
        method: str,
        updated_values: Any,
        original_values: Any,
        dispatchers_steamid: Optional[str],
        min_depth: int = 0,
        max_depth: Optional[int] = None
    ) -> List[Dict]:
        """
        Collect all callbacks that should be triggered for a path change.

        Returns list of callback packages ready for execution.
        """
        depth = path.count('/')

        # DEBUG: Log callback collection attempt
        if "selected_by" in path:
            print(f"[DEBUG CALLBACKDICT] Checking path: {path}")
            print(f"[DEBUG CALLBACKDICT] Path depth: {depth}, min_depth: {min_depth}, max_depth: {max_depth}")
            print(f"[DEBUG CALLBACKDICT] Registered depths: {list(self._callbacks.keys())}")
            if depth in self._callbacks:
                print(f"[DEBUG CALLBACKDICT] Patterns at depth {depth}: {list(self._callbacks[depth].keys())}")

        # Check depth constraints
        if max_depth is not None and depth > max_depth:
            if "selected_by" in path:
                print(f"[DEBUG CALLBACKDICT] REJECTED: depth {depth} > max_depth {max_depth}")
            return []
        if depth < min_depth:
            if "selected_by" in path:
                print(f"[DEBUG CALLBACKDICT] REJECTED: depth {depth} < min_depth {min_depth}")
            return []

        # Find matching patterns
        matching_patterns = self._match_path(path, depth)
        if not matching_patterns:
            if "selected_by" in path:
                print(f"[DEBUG CALLBACKDICT] REJECTED: No matching patterns found")
            return []

        if "selected_by" in path:
            print(f"[DEBUG CALLBACKDICT] MATCHED patterns: {matching_patterns}")

        # Build callback packages
        packages = []
        for pattern in matching_patterns:
            for callback_info in self._callbacks[depth][pattern]:
                packages.append({
                    "target": callback_info["callback"],
                    "args": (callback_info["module"],),
                    "kwargs": {
                        "updated_values_dict": updated_values,
                        "original_values_dict": original_values,
                        "dispatchers_steamid": dispatchers_steamid,
                        "method": method,
                        "matched_path": pattern
                    }
                })

        return packages

    def _execute_callbacks(self, callback_packages: List[Dict]) -> None:
        """Execute a list of callback packages in separate threads."""
        for package in callback_packages:
            self._executor.submit(
                package["target"],
                *package["args"],
                **package["kwargs"]
            )

    # ==================== Dictionary Operations ====================

    def upsert(
        self,
        updates: Dict,
        dispatchers_steamid: Optional[str] = None,
        min_callback_level: int = 0,
        max_callback_level: Optional[int] = None
    ) -> None:
        """
        Update or insert values into the dictionary.

        This is the main method for modifying the dictionary. It handles nested
        updates intelligently and triggers appropriate callbacks.

        Args:
            updates: Dictionary of values to upsert
            dispatchers_steamid: ID of the user who triggered this change
            min_callback_level: Minimum depth level for callbacks
            max_callback_level: Maximum depth level for callbacks
        """
        if not isinstance(updates, Mapping) or not updates:
            return

        # Make a snapshot of current state before any changes
        original_state = deepcopy(dict(self))

        # Determine max depth if not specified
        if max_callback_level is None:
            max_callback_level = self._calculate_depth(updates)

        # Collect all callbacks that will be triggered
        all_callbacks = []

        # Process updates recursively
        self._upsert_recursive(
            current_dict=self,
            updates=updates,
            original_state=original_state,
            path_components=[],
            callbacks_accumulator=all_callbacks,
            dispatchers_steamid=dispatchers_steamid,
            min_depth=min_callback_level,
            max_depth=max_callback_level
        )

        # Execute all collected callbacks
        self._execute_callbacks(all_callbacks)

    def _upsert_recursive(
        self,
        current_dict: dict,
        updates: Dict,
        original_state: Dict,
        path_components: List[str],
        callbacks_accumulator: List[Dict],
        dispatchers_steamid: Optional[str],
        min_depth: int,
        max_depth: int
    ) -> None:
        """Recursive helper for upsert operation."""
        current_depth = len(path_components)

        for key, new_value in updates.items():
            # Build the full path for this key
            full_path_components = path_components + [key]
            full_path = self._join_path(full_path_components)

            # Determine the operation type
            key_exists = key in current_dict
            old_value = current_dict.get(key)

            if key_exists:
                # Update case
                if isinstance(old_value, dict) and isinstance(new_value, dict):
                    # Both are dicts - recurse deeper
                    method = "update"
                    self._upsert_recursive(
                        current_dict=current_dict[key],
                        updates=new_value,
                        original_state=original_state.get(key, {}),
                        path_components=full_path_components,
                        callbacks_accumulator=callbacks_accumulator,
                        dispatchers_steamid=dispatchers_steamid,
                        min_depth=min_depth,
                        max_depth=max_depth
                    )
                elif old_value == new_value:
                    # Value unchanged - skip callbacks
                    method = "unchanged"
                else:
                    # Value changed - update it
                    method = "update"
                    current_dict[key] = new_value
            else:
                # Insert case
                method = "insert"
                current_dict[key] = new_value

                # If inserted value is a dict, recurse through it
                if isinstance(new_value, dict):
                    self._upsert_recursive(
                        current_dict=current_dict[key],
                        updates=new_value,
                        original_state={},
                        path_components=full_path_components,
                        callbacks_accumulator=callbacks_accumulator,
                        dispatchers_steamid=dispatchers_steamid,
                        min_depth=min_depth,
                        max_depth=max_depth
                    )

            # Collect callbacks for this change (skip if unchanged)
            if method != "unchanged":
                callbacks = self._collect_callbacks(
                    path=full_path,
                    method=method,
                    updated_values=updates,
                    original_values=original_state,
                    dispatchers_steamid=dispatchers_steamid,
                    min_depth=min_depth,
                    max_depth=max_depth
                )
                callbacks_accumulator.extend(callbacks)

    def append(
        self,
        updates: Dict,
        dispatchers_steamid: Optional[str] = None,
        maxlen: Optional[int] = None,
        min_callback_level: int = 0,
        max_callback_level: Optional[int] = None
    ) -> None:
        """
        Append values to list entries in the dictionary.

        If the target key doesn't exist, creates a new list.
        If maxlen is specified, creates a deque with that maxlen.

        Args:
            updates: Dictionary mapping paths to values to append
            dispatchers_steamid: ID of user who triggered this
            maxlen: Maximum length for created lists (uses deque)
            min_callback_level: Minimum depth for callbacks
            max_callback_level: Maximum depth for callbacks
        """
        if not isinstance(updates, Mapping) or not updates:
            return

        original_state = deepcopy(dict(self))

        if max_callback_level is None:
            max_callback_level = self._calculate_depth(updates)

        all_callbacks = []

        self._append_recursive(
            current_dict=self,
            updates=updates,
            original_state=original_state,
            path_components=[],
            callbacks_accumulator=all_callbacks,
            dispatchers_steamid=dispatchers_steamid,
            maxlen=maxlen,
            min_depth=min_callback_level,
            max_depth=max_callback_level
        )

        self._execute_callbacks(all_callbacks)

    def _append_recursive(
        self,
        current_dict: dict,
        updates: Dict,
        original_state: Dict,
        path_components: List[str],
        callbacks_accumulator: List[Dict],
        dispatchers_steamid: Optional[str],
        maxlen: Optional[int],
        min_depth: int,
        max_depth: int
    ) -> None:
        """Recursive helper for append operation."""
        current_depth = len(path_components)

        for key, value in updates.items():
            full_path_components = path_components + [key]
            full_path = self._join_path(full_path_components)

            # Collect callbacks before making changes
            callbacks = self._collect_callbacks(
                path=full_path,
                method="append",
                updated_values=updates,
                original_values=original_state,
                dispatchers_steamid=dispatchers_steamid,
                min_depth=min_depth,
                max_depth=max_depth
            )
            callbacks_accumulator.extend(callbacks)

            # Perform the append operation
            if key in current_dict:
                try:
                    current_dict[key].append(value)
                except AttributeError:
                    # Not a list/deque, can't append
                    pass
            else:
                # Create new list or deque
                if maxlen is not None:
                    current_dict[key] = deque(maxlen=maxlen)
                else:
                    current_dict[key] = []
                current_dict[key].append(value)

            # If we found callbacks, don't recurse deeper (callback is at this level)
            if callbacks:
                return

            # Otherwise, recurse if both are dicts
            old_value = current_dict.get(key)
            if isinstance(value, Mapping) and isinstance(old_value, Mapping):
                self._append_recursive(
                    current_dict=old_value,
                    updates=value,
                    original_state=original_state.get(key, {}),
                    path_components=full_path_components,
                    callbacks_accumulator=callbacks_accumulator,
                    dispatchers_steamid=dispatchers_steamid,
                    maxlen=maxlen,
                    min_depth=min_depth,
                    max_depth=max_depth
                )

    def remove_key_by_path(
        self,
        key_path: List[str],
        dispatchers_steamid: Optional[str] = None
    ) -> None:
        """
        Remove a key from the dictionary by its path.

        Args:
            key_path: List of keys representing the path (e.g., ['players', '12345', 'name'])
            dispatchers_steamid: ID of user who triggered this
        """
        if not key_path:
            return

        # Get module's delete root to determine how much of the path to use
        try:
            module = loaded_modules_dict[key_path[0]]
            delete_root = getattr(module, 'dom_element_select_root', [])
            keys_to_ignore = len(delete_root) - 1 if delete_root else 0
        except (KeyError, AttributeError):
            keys_to_ignore = 0

        # Build the path for callback matching
        if keys_to_ignore >= 1:
            path_for_callbacks = self._join_path(key_path[:-keys_to_ignore])
        else:
            path_for_callbacks = self._join_path(key_path)

        # Collect callbacks
        callbacks = self._collect_callbacks(
            path=path_for_callbacks,
            method="remove",
            updated_values=key_path,
            original_values={},
            dispatchers_steamid=dispatchers_steamid,
            min_depth=len(key_path),
            max_depth=len(key_path)
        )

        # Perform the deletion
        try:
            parent = self._get_nested_value(self, key_path[:-1])
            del parent[key_path[-1]]
        except (KeyError, TypeError, IndexError):
            # Key doesn't exist or path is invalid
            pass

        # Execute callbacks
        self._execute_callbacks(callbacks)

    def __del__(self):
        """Cleanup: shutdown the thread pool when the object is destroyed."""
        try:
            self._executor.shutdown(wait=False)
        except:
            pass
