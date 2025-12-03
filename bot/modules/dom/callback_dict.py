from typing import List, Optional, Callable
from copy import deepcopy

class CallbackDict(dict):
    def __init__(self, *args, **kwargs):
        self.registered_callbacks = []
        super().__init__(*args, **kwargs)

    def register_callback(self, module, callback_path: str, callback: Callable):
        callback_dict = {
            "module": module,
            "callback_path": callback_path,
            "callback": callback
        }
        self.registered_callbacks.append(callback_dict)

    def _deep_compare(self, data1, data2, path="") -> bool:
        if type(data1) != type(data2):
            return False

        if isinstance(data1, dict):
            for key in data2.keys():
                if key not in data1:
                    return False

                new_path = f"{path}/{key}" if path else key
                if not self._deep_compare(data1[key], data2[key], new_path):
                    return False

            return True

        elif isinstance(data1, list):
            if len(data1) != len(data2):
                return False

            for i in range(len(data1)):
                if not self._deep_compare(data1[i], data2[i], f"{path}[{i}]"):
                    return False

            return True

        else:
            if data1 != data2:
                return False
            return True

    def _has_actual_changes(self, current_data: dict, new_data: dict) -> bool:
        for key, new_value in new_data.items():
            if key not in current_data:
                return True

            current_value = current_data[key]

            if not self._deep_compare(current_value, new_value, key):
                return True

        return False

    @staticmethod
    def _check_if_pattern_matches(pattern_path: str, actual_data: dict, current_dict_state: dict) -> bool:
        _pattern_parts = pattern_path.split('/')

        def recurse(data, _pattern_parts, current_state, level=0):
            if level >= len(_pattern_parts):
                return True

            pattern = _pattern_parts[level]

            if not isinstance(data, dict):
                return False

            for key in data.keys():
                matches_this_level = False

                if pattern.startswith('*') and pattern.endswith('*'):
                    if level == len(_pattern_parts) - 1:
                        if isinstance(current_state, dict):
                            if key not in current_state:
                                matches_this_level = True
                        else:
                            matches_this_level = True

                elif pattern.startswith('%') and pattern.endswith('%'):
                    matches_this_level = True

                else:
                    if pattern == key:
                        matches_this_level = True

                if matches_this_level:
                    next_state = current_state.get(key) if isinstance(current_state, dict) else None

                    if recurse(data[key], _pattern_parts, next_state, level + 1):
                        return True

            return False

        return recurse(actual_data, _pattern_parts, current_dict_state)

    def _deep_merge(self, target: dict, source: dict):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = deepcopy(value)

    @staticmethod
    def _extract_relevant_data(full_data: dict, pattern_path: str, change_data: dict) -> dict:
        _pattern_parts = pattern_path.split('/')

        def recurse(data, change, pattern_parts, level=0):
            if level >= len(pattern_parts):
                return deepcopy(data)

            if not isinstance(data, dict) or not isinstance(change, dict):
                return {}

            pattern = pattern_parts[level]
            result = {}

            for key in change.keys():
                if key not in data:
                    continue

                matches = False

                if pattern.startswith('*') and pattern.endswith('*'):
                    matches = True
                elif pattern.startswith('%') and pattern.endswith('%'):
                    matches = True
                else:
                    if pattern == key:
                        matches = True

                if matches:
                    sub_result = recurse(data[key], change[key], pattern_parts, level + 1)
                    if sub_result or level == len(pattern_parts) - 1:
                        result[key] = sub_result if sub_result else deepcopy(data[key])

            return result

        return recurse(full_data, change_data, _pattern_parts)

    def upsert(self, dict_to_upsert: dict, dispatchers_steamid: Optional[str] = None):
        original_state = deepcopy(dict(self))
        simulated_state = deepcopy(dict(self))
        self._deep_merge(simulated_state, dict_to_upsert)
        if self._deep_compare(original_state, simulated_state):
            return

        matching_callbacks = []
        for callback in self.registered_callbacks:
            if self._check_if_pattern_matches(
                    callback["callback_path"],
                    dict_to_upsert,
                    self
            ):
                matching_callbacks.append(callback)

        self._deep_merge(self, dict_to_upsert)

        for callback in matching_callbacks:
            try:
                relevant_original = self._extract_relevant_data(original_state, callback["callback_path"], dict_to_upsert)
                relevant_updated = self._extract_relevant_data(simulated_state, callback["callback_path"], dict_to_upsert)

                callback_kwargs = {
                    "method": "upsert",
                    "matched_path": callback["callback_path"],
                    "original_data": relevant_original,
                    "updated_data": relevant_updated
                }

                callback["module"].spawn_tracked(
                    f"callback_{callback['callback_path'].replace('/', '_')}",
                    callback["callback"],
                    callback["module"], callback_kwargs,
                    dispatchers_id=dispatchers_steamid,
                    timeout=10  # Callbacks should complete within 10 seconds
                )
            except Exception as e:
                print(f"[ERROR] Callback {callback['callback_path']} failed: {e}")


    def delete(self, key_path: List[str], dispatchers_steamid: Optional[str] = None):
        original_state = deepcopy(dict(self))
        current = self
        for key in key_path[:-1]:
            if key not in current:
                return
            current = current[key]

        last_key = key_path[-1]
        if last_key not in current:
            return

        simulated_state = deepcopy(dict(self))
        simulated_current = simulated_state
        for key in key_path[:-1]:
            simulated_current = simulated_current[key]

        deleted_value = simulated_current[last_key]
        del simulated_current[last_key]

        if self._deep_compare(original_state, simulated_state):
            return

        matching_callbacks = []
        for callback in self.registered_callbacks:
            pattern_parts = callback["callback_path"].split('/')

            if len(pattern_parts) != len(key_path):
                continue

            matches = True
            for i, pattern in enumerate(pattern_parts):
                if pattern.startswith('*') and pattern.endswith('*'):
                    if i == len(pattern_parts) - 1:
                        continue
                    else:
                        matches = False
                        break
                elif pattern.startswith('%') and pattern.endswith('%'):
                    continue
                else:
                    if pattern != key_path[i]:
                        matches = False
                        break

            if matches:
                matching_callbacks.append(callback)

        del current[last_key]
        for callback in matching_callbacks:
            try:
                change_data_for_extract = {}
                current_level = change_data_for_extract
                for i, key in enumerate(key_path):
                    if i == len(key_path) - 1:
                        current_level[key] = deleted_value
                    else:
                        current_level[key] = {}
                        current_level = current_level[key]

                relevant_original = self._extract_relevant_data(original_state, callback["callback_path"], change_data_for_extract)
                relevant_updated = self._extract_relevant_data(simulated_state, callback["callback_path"], change_data_for_extract)

                callback_kwargs = {
                    "method": "delete",
                    "matched_path": callback["callback_path"],
                    "original_data": relevant_original,
                    "updated_data": relevant_updated,
                    "dispatchers_steamid": dispatchers_steamid,
                }

                callback["module"].spawn_tracked(
                    f"callback_{callback['callback_path'].replace('/', '_')}",
                    callback["callback"],
                    callback["module"],
                    timeout=10,  # Callbacks should complete within 10 seconds
                    **callback_kwargs
                )
            except Exception as e:
                print(f"[ERROR] Callback {callback['callback_path']} failed: {e}")

    def append(self, value_to_append: dict, dispatchers_steamid: Optional[str] = None, maxlen: Optional[int] = None):
        original_state = deepcopy(dict(self))
        simulated_state = deepcopy(dict(self))

        def find_and_append(data, target_data):
            for key, value in target_data.items():
                if key not in data:
                    data[key] = {}

                if isinstance(value, dict):
                    find_and_append(data[key], value)
                else:
                    if not isinstance(data[key], list):
                        data[key] = []

                    data[key].append(value)

                    if maxlen and len(data[key]) > maxlen:
                        data[key] = data[key][-maxlen:]

        matching_callbacks = []
        for callback in self.registered_callbacks:
            if self._check_if_pattern_matches(
                    callback["callback_path"],
                    value_to_append,
                    self
            ):
                matching_callbacks.append(callback)

        find_and_append(self, value_to_append)

        for callback in matching_callbacks:
            try:
                relevant_original = self._extract_relevant_data(original_state, callback["callback_path"], value_to_append)
                relevant_updated = self._extract_relevant_data(simulated_state, callback["callback_path"], value_to_append)

                callback_kwargs = {
                    "method": "append",
                    "matched_path": callback["callback_path"],
                    "original_data": relevant_original,
                    "updated_data": relevant_updated,
                    "dispatchers_steamid": dispatchers_steamid,
                }

                callback["module"].spawn_tracked(
                    f"callback_{callback['callback_path'].replace('/', '_')}",
                    callback["callback"],
                    callback["module"],
                    timeout=10,  # Callbacks should complete within 10 seconds
                    **callback_kwargs
                )
            except Exception as e:
                print(f"[ERROR] Callback {callback['callback_path']} failed: {e}")
