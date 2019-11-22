from bot import loaded_modules_dict
from collections import Mapping, deque
from threading import Thread
from copy import deepcopy
from functools import reduce
import operator


class CallbackDict(dict, object):

    registered_callbacks = dict

    def __init__(self, *args, **kwargs):
        self.registered_callbacks = {}
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    @staticmethod
    def get_from_dict(data_dict, map_list):
        return reduce(operator.getitem, map_list[:-1], data_dict)

    @staticmethod
    def get_callback_package(
            updated_values=dict,
            original_values_dict=dict,
            dispatchers_steamid=None,
            callback=None,
            method=None,
            matched_path=None
    ):
        try:
            callback_kwargs = {
                "updated_values_dict": updated_values,
                "original_values_dict": original_values_dict,
                "dispatchers_steamid": dispatchers_steamid,
                "method": method,
                "matched_path": matched_path
            }

            return {
                "target": callback["callback"],
                "args": [callback["module"]],
                "kwargs": callback_kwargs
            }
        except TypeError as error:
            print(error)

    @staticmethod
    def construct_full_path(current_path, new_key, current_layer):
        try:
            current_path[current_layer] = new_key
        except IndexError:
            current_path.append(new_key)

        try:
            current_path_string = "/".join(current_path)
        except TypeError:
            current_path_string = None

        return current_path_string

    def get_matching_callback_path(self, path, **kwargs):
        exploded_path = path.split("/")
        max_callback_level = kwargs.get("max_callback_level")
        min_callback_level = kwargs.get("min_callback_level")
        layer = kwargs.get("layer")
        if not (max_callback_level >= layer >= min_callback_level):
            return None

        matching_callbacks = []
        try:
            for callback in self.registered_callbacks[len(exploded_path) - 1]:
                exploded_callback = callback.split("/")
                """ if they have the same length or given path is bigger, then it's a candidate """
                if len(exploded_callback) == len(exploded_path):
                    """ let's compare the individual elements """
                    its_a_match = False
                    for element in range(len(exploded_callback)):
                        if exploded_callback[element] == exploded_path[element]:
                            its_a_match = True
                        elif exploded_callback[element].startswith("%") and exploded_callback[element].endswith("%"):
                            its_a_match = True
                        else:
                            its_a_match = False
                            break

                    if its_a_match is True:
                        # callback matches all required fields after testing for each spot/wildcard
                        matching_callbacks.append(callback)
        except KeyError:
            # no callbacks with that level available!
            pass

        if len(matching_callbacks) >= 1:
            return matching_callbacks
        else:
            return None

    def dict_depth(self, d):
        if isinstance(d, dict):
            return 1 + (max(map(self.dict_depth, d.values())) if d else 0)
        return 0

    def remove_key_by_path(self, *args, **kwargs):
        key_to_remove = args[0]
        dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
        target_module_delete_root = loaded_modules_dict[key_to_remove[0]].dom_element_select_root
        keys_to_ignore = len(target_module_delete_root) - 1
        if keys_to_ignore >= 1:
            path_to_delete = "/".join(key_to_remove[:-(keys_to_ignore)])
        else:
            path_to_delete = "/".join(key_to_remove)

        matching_callback_path = self.get_matching_callback_path(
            path_to_delete,
            min_callback_level=len(key_to_remove),
            max_callback_level=len(key_to_remove),
            layer=len(key_to_remove)
        )

        callbacks = []
        if matching_callback_path is not None:
            for working_path in matching_callback_path:
                for callback in self.registered_callbacks[len(key_to_remove) - (1 + keys_to_ignore)][working_path]:
                    callbacks.append(
                        self.get_callback_package(
                            updated_values=key_to_remove,
                            original_values_dict={},
                            dispatchers_steamid=dispatchers_steamid,
                            callback=callback,
                            method="remove",
                            matched_path=working_path
                        )
                    )

        try:
            # print(target_module_delete_root, "remove:", key_to_remove[-1])
            del self.get_from_dict(self, key_to_remove)[key_to_remove[-1]]
            # del working_copy_dict[k]
        except KeyError:
            pass
        except TypeError:
            pass

        """ we've reached the end of all recursions """
        for callback in callbacks:
            Thread(
                target=callback["target"],
                args=callback["args"],
                kwargs=callback["kwargs"]
            ).start()

    def append(self, *args, **kwargs):
        updated_values_dict = args[0]
        working_copy_dict = kwargs.get("dict_to_update", self)
        original_values_dict = kwargs.get("original_values_dict", {})
        if len(original_values_dict) <= 0:
            original_values_dict = deepcopy(dict(working_copy_dict))

        path = kwargs.get("path", [])
        max_callback_level = kwargs.get("max_callback_level", self.dict_depth(updated_values_dict))
        min_callback_level = kwargs.get("min_callback_level", 0)
        dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
        layer = kwargs.get("layer", 0)
        callbacks = kwargs.get("callbacks", None)
        maxlen = kwargs.get("maxlen", None)

        if layer == 0 and callbacks is None:
            callbacks = []

        path = path[0:layer]

        """" recursion happens in this section """
        for k, v in updated_values_dict.items():
            matching_callback_path = self.get_matching_callback_path(
                self.construct_full_path(path, k, layer),
                min_callback_level=min_callback_level,
                max_callback_level=max_callback_level,
                layer=layer
            )

            if matching_callback_path is not None:
                for working_path in matching_callback_path:
                    for callback in self.registered_callbacks[layer][working_path]:
                        callbacks.append(
                            self.get_callback_package(
                                updated_values=updated_values_dict,
                                original_values_dict=original_values_dict,
                                dispatchers_steamid=dispatchers_steamid,
                                callback=callback,
                                method="append",
                                matched_path=working_path
                            ))

                try:
                    working_copy_dict[k].append(v)

                except KeyError:
                    if maxlen is not None:
                        working_copy_dict[k] = deque(maxlen=maxlen)
                    else:
                        working_copy_dict[k] = []

                    working_copy_dict[k].append(v)
                except AttributeError:
                    pass

                return

            d_v = working_copy_dict.get(k)
            if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                self.append(
                    v,
                    dict_to_update=d_v,
                    original_values_dict=original_values_dict[k],
                    path=path,
                    layer=layer + 1,
                    callbacks=callbacks,
                    maxlen=maxlen,
                    dispatchers_steamid=dispatchers_steamid,
                    max_callback_level=max_callback_level,
                    min_callback_level=min_callback_level
                )

        if layer != 0:
            return

        """ we've reached the end of all recursions """
        for callback in callbacks:
            Thread(
                target=callback["target"],
                args=callback["args"],
                kwargs=callback["kwargs"]
            ).start()

    def upsert(self, *args, **kwargs):
        updated_values_dict = args[0]
        dict_to_update = kwargs.get("dict_to_update", self)
        if isinstance(updated_values_dict, Mapping) and len(updated_values_dict) < 1:
            # early exit: nothing to update!
            return

        path = kwargs.get("path", [])
        layer = len(path)

        original_values_dict = kwargs.get("original_values_dict", {})
        if layer == 0 and len(original_values_dict) == 0:
            original_values_dict = deepcopy(dict(dict_to_update))

        dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
        max_callback_level = kwargs.get("max_callback_level", self.dict_depth(updated_values_dict))
        min_callback_level = kwargs.get("min_callback_level", 0)
        callbacks = kwargs.get("callbacks", None)

        if layer == 0 and callbacks is None:
            callbacks = []

        path = path[0:layer]

        """" recursion happens in this section """
        for key_to_update, value_to_update in updated_values_dict.items():
            working_paths_list = self.get_matching_callback_path(
                self.construct_full_path(path, key_to_update, layer),
                min_callback_level=min_callback_level,
                max_callback_level=max_callback_level,
                layer=layer
            )

            if key_to_update in dict_to_update:
                method = "update"
                # the key exists in the current dom
                if isinstance(dict_to_update[key_to_update], (list, dict)) and isinstance(updated_values_dict[key_to_update], (list, dict)):
                    # both the updated values and the original ones are Mappings. Let's dive in
                    if isinstance(updated_values_dict.get(key_to_update, None), dict):
                        self.upsert(
                            updated_values_dict[key_to_update], dict_to_update=dict_to_update[key_to_update],
                            original_values_dict=original_values_dict.get(key_to_update, {}),
                            path=path, callbacks=callbacks, dispatchers_steamid=dispatchers_steamid,
                            max_callback_level=max_callback_level, min_callback_level=min_callback_level
                        )
                    elif isinstance(updated_values_dict.get(key_to_update, None), list):
                        # if the value is a list, we simply replace the entire list. We will not go
                        # through list items in this dict
                        dict_to_update[key_to_update] = updated_values_dict.get(key_to_update)

                elif all([
                    not isinstance(dict_to_update[key_to_update], (list, dict)),
                    not isinstance(updated_values_dict[key_to_update], (list, dict))
                ]):
                    # both keys are Values, we'll update and continue the loop
                    if dict_to_update[key_to_update] != updated_values_dict[key_to_update]:
                        dict_to_update[key_to_update] = updated_values_dict[key_to_update]
            else:
                # the key is not in our current dom
                method = "insert"
                original_values_dict = {}
                dict_to_update[key_to_update] = updated_values_dict[key_to_update]
                if isinstance(updated_values_dict[key_to_update], dict):
                    # it's a mapping, it's not present in the current dom. Copy it over and go through it
                    self.upsert(
                        updated_values_dict[key_to_update], dict_to_update=dict_to_update[key_to_update],
                        original_values_dict=original_values_dict,
                        path=path, callbacks=callbacks, dispatchers_steamid=dispatchers_steamid,
                        max_callback_level=max_callback_level, min_callback_level=min_callback_level
                    )

            if working_paths_list is not None:
                try:
                    for working_path in working_paths_list:
                        for callback in self.registered_callbacks[layer][working_path]:
                            callbacks.append(
                                self.get_callback_package(
                                    updated_values=updated_values_dict,
                                    original_values_dict=original_values_dict,
                                    dispatchers_steamid=dispatchers_steamid,
                                    callback=callback,
                                    method=method,
                                    matched_path=working_path
                                )
                            )

                except KeyError:
                    pass

        if layer != 0:
            return

        """ we've reached the end of all recursions """
        for callback in callbacks:
            try:
                Thread(
                    target=callback["target"],
                    args=callback["args"],
                    kwargs=callback["kwargs"]
                ).start()
            except TypeError as error:
                print(error)

    def register_callback(self, module, dict_to_monitor, callback):
        callback_depth = dict_to_monitor.count('/')
        depth_already_exists = self.registered_callbacks.get(callback_depth, False)
        if not depth_already_exists:
            self.registered_callbacks[callback_depth] = {}
        try:
            self.registered_callbacks[callback_depth][dict_to_monitor].append({
                "callback": callback,
                "module": module
            })
        except KeyError as error:
            self.registered_callbacks[callback_depth][dict_to_monitor] = [{
                "callback": callback,
                "module": module
            }]
