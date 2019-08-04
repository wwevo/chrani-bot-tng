from collections import Mapping, deque
from threading import Thread
import re
from copy import deepcopy


class CallbackDict(dict, object):

    registered_callbacks = dict

    def __init__(self, *args, **kw):
        self.registered_callbacks = {}
        super().__init__(*args, **kw)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    @staticmethod
    def get_callback_package(
            updated_values=dict,
            original_values_dict=dict,
            dispatchers_steamid=None,
            callback=None,
            method=None
    ):
        try:
            callback_kwargs = {
                "updated_values_dict": updated_values,
                "original_values_dict": original_values_dict,
                "dispatchers_steamid": dispatchers_steamid,
                "method": method
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
        for callback in self.registered_callbacks:
            exploded_callback = callback.split("/")
            """ if they have the same length or given path is bigger, then it's a candidate """
            if len(exploded_callback) <= len(exploded_path):
                """ let's compare the individual elements """
                its_a_match = False
                for element in range(len(exploded_callback)):
                    # no sense in checking anything larger than the callback itself
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
        depth = kwargs.get("depth", self.dict_depth(updated_values_dict))
        callbacks = kwargs.get("callbacks", None)
        maxlen = kwargs.get("maxlen", None)

        if layer == 0 and callbacks is None:
            callbacks = []

        path = path[0:layer]

        """" recursion happens in this section """
        for k, v in updated_values_dict.items():
            full_path = self.construct_full_path(path, k, layer)
            matching_callback_path = self.get_matching_callback_path(full_path)

            if len(self.registered_callbacks) >= 1 and matching_callback_path is not None:
                for working_path in matching_callback_path:
                    for callback in self.registered_callbacks[working_path]:
                        if depth == len(full_path.split("/")):
                            callbacks.append(
                                self.get_callback_package(
                                    updated_values=updated_values_dict,
                                    original_values_dict=original_values_dict,
                                    dispatchers_steamid=dispatchers_steamid,
                                    callback=callback,
                                    method="remove"
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
                    depth=depth
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
        depth = kwargs.get("depth", self.dict_depth(updated_values_dict))
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
            matching_callback_path = self.get_matching_callback_path(full_path)

            if len(self.registered_callbacks) >= 1 and matching_callback_path is not None:
                for working_path in matching_callback_path:
                    for callback in self.registered_callbacks[working_path]:
                        if depth == len(full_path.split("/")):
                            callbacks.append(
                                self.get_callback_package(
                                    updated_values=updated_values_dict,
                                    original_values_dict=original_values_dict,
                                    dispatchers_steamid=dispatchers_steamid,
                                    callback=callback,
                                    method="append"
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
                    depth=depth
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
        depth = kwargs.get("depth", self.dict_depth(updated_values_dict))
        layer = kwargs.get("layer", 0)
        callbacks = kwargs.get("callbacks", None)

        if layer == 0 and callbacks is None:
            callbacks = []

        path = path[0:layer]

        """" recursion happens in this section """
        for k, v in updated_values_dict.items():
            full_path = self.construct_full_path(path, k, layer)

            forced_overwrite = False
            working_paths_list = None
            matching_callback_path = self.get_matching_callback_path(full_path)

            if len(self.registered_callbacks) >= 1 and matching_callback_path is not None:
                if overwrite is True:
                    forced_overwrite = True
                    working_copy_dict[k] = v

                working_paths_list = matching_callback_path

            if not forced_overwrite:
                d_v = working_copy_dict.get(k)
                if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                    self.upsert(v, dict_to_update=d_v, original_values_dict=original_values_dict[k], path=path,
                                layer=layer + 1, callbacks=callbacks, overwrite=overwrite,
                                dispatchers_steamid=dispatchers_steamid, depth=depth)
                else:
                    working_copy_dict[k] = v
                    if isinstance(v, Mapping) and len(v) >= 1:
                        next_value = next(iter(v))
                        if working_paths_list is not None:
                            for i in range(len(working_paths_list)):
                                working_paths_list[i] = "{}/{}".format(working_paths_list[i], next_value)

            if working_paths_list is not None:
                try:
                    for working_path in working_paths_list:
                        for callback in self.registered_callbacks[working_path]:
                            if depth == len(working_path.split("/")):
                                callbacks.append(
                                    self.get_callback_package(
                                        updated_values=updated_values_dict,
                                        original_values_dict=original_values_dict,
                                        dispatchers_steamid=dispatchers_steamid,
                                        callback=callback,
                                        method="upsert"
                                    ))

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
        try:
            self.registered_callbacks[dict_to_monitor].append({
                "callback": callback,
                "module": module
            })
        except KeyError as error:
            self.registered_callbacks[dict_to_monitor] = [{
                "callback": callback,
                "module": module
            }]
