from collections import Mapping, deque
from threading import Thread
from copy import deepcopy


class CallbackDict(dict, object):

    registered_callbacks = dict

    def __init__(self, *args, **kwargs):
        self.registered_callbacks = {}
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

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

        return "/".join(current_path)

    def get_matching_callback_path(self, path):
        exploded_path = path.split("/")
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

    def remove(self, *args, **kwargs):
        updated_values_dict = args[0]
        working_copy_dict = kwargs.get("dict_to_update", self)
        original_values_dict = kwargs.get("original_values_dict", {})
        if len(original_values_dict) <= 0:
            original_values_dict = deepcopy(dict(working_copy_dict))

        path = kwargs.get("path", [])
        dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
        layer = kwargs.get("layer", 0)
        max_callback_level = kwargs.get("max_callback_level", self.dict_depth(updated_values_dict))
        min_callback_level = kwargs.get("min_callback_level", 0)
        callbacks = kwargs.get("callbacks", None)
        maxlen = kwargs.get("maxlen", None)

        if layer == 0 and callbacks is None:
            callbacks = []

        path = path[0:layer]

        """" recursion happens in this section """
        for k, v in updated_values_dict.items():
            full_path = self.construct_full_path(path, k, layer)
            if max_callback_level >= layer >= min_callback_level:
                matching_callback_path = self.get_matching_callback_path(full_path)
            else:
                matching_callback_path = None

            if matching_callback_path is not None:
                for working_path in matching_callback_path:
                    for callback in self.registered_callbacks[layer][working_path]:
                        callbacks.append(
                            self.get_callback_package(
                                updated_values=updated_values_dict,
                                original_values_dict=original_values_dict,
                                dispatchers_steamid=dispatchers_steamid,
                                callback=callback,
                                method="remove",
                                matched_path=working_path
                            ))

            if isinstance(v, Mapping) and isinstance(working_copy_dict[k], Mapping):
                self.remove(
                    v,
                    dict_to_update=working_copy_dict[k],
                    original_values_dict=original_values_dict[k],
                    path=path,
                    layer=layer + 1,
                    callbacks=callbacks,
                    maxlen=maxlen,
                    dispatchers_steamid=dispatchers_steamid,
                    max_callback_level=max_callback_level,
                    min_callback_level=min_callback_level
                )
            else:
                try:
                    del working_copy_dict[k][v]
                except KeyError:
                    pass
                except TypeError:
                    try:
                        working_copy_dict[k].remove(v)
                    except ValueError:
                        pass

        if layer != 0:
            return

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
            full_path = self.construct_full_path(path, k, layer)
            if max_callback_level >= layer >= min_callback_level:
                matching_callback_path = self.get_matching_callback_path(full_path)
            else:
                matching_callback_path = None

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
        if isinstance(updated_values_dict, Mapping) and len(updated_values_dict) < 1:
            # early exit: nothing to update!
            return

        working_copy_dict = kwargs.get("dict_to_update", self)
        original_values_dict = kwargs.get("original_values_dict", {})

        if len(original_values_dict) <= 0:
            original_values_dict = deepcopy(dict(working_copy_dict))

        overwrite = kwargs.get("overwrite", False)
        path = kwargs.get("path", [])
        dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
        max_callback_level = kwargs.get("max_callback_level", self.dict_depth(updated_values_dict))
        min_callback_level = kwargs.get("min_callback_level", 0)
        layer = kwargs.get("layer", 0)
        callbacks = kwargs.get("callbacks", None)

        if layer == 0 and callbacks is None:
            callbacks = []

        path = path[0:layer]

        """" recursion happens in this section """
        for k, v in updated_values_dict.items():
            full_path = self.construct_full_path(path, k, layer)
            if max_callback_level >= layer >= min_callback_level:
                matching_callback_path = self.get_matching_callback_path(full_path)
            else:
                matching_callback_path = None

            working_paths_list = None
            if matching_callback_path is not None:
                working_paths_list = matching_callback_path

            if not overwrite:
                d_v = working_copy_dict.get(k, None)
                if isinstance(v, Mapping) and d_v is None:
                    # doesn't exist in working copy
                    d_v = working_copy_dict[k] = v
                if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                    try:
                        self.upsert(
                            v, dict_to_update=d_v, original_values_dict=original_values_dict[k], path=path,
                            layer=layer + 1, callbacks=callbacks, overwrite=overwrite,
                            dispatchers_steamid=dispatchers_steamid, max_callback_level=max_callback_level,
                            min_callback_level=min_callback_level
                            )
                    except KeyError:
                        self.upsert(
                            v, dict_to_update=d_v, original_values_dict=original_values_dict, path=path,
                            layer=layer + 1, callbacks=callbacks, overwrite=overwrite,
                            dispatchers_steamid=dispatchers_steamid, max_callback_level=max_callback_level,
                            min_callback_level=min_callback_level
                        )
                else:
                    working_copy_dict[k] = v
            else:
                working_copy_dict[k] = v

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
                                    method="upsert",
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
