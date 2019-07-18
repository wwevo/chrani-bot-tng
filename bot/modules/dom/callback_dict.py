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
    def get_callback_package(updated_values=dict, old_values=dict, original_values_dict=dict, dispatchers_steamid=None, callback=None):
        try:
            callback_kwargs = {
                "updated_values_dict": updated_values,
                "old_values_dict": old_values,
                "original_values_dict": original_values_dict,
                "dispatchers_steamid": dispatchers_steamid
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
        any_steamid = re.search(r"(?P<steamid>\d{17})", new_key, re.MULTILINE)
        if any_steamid:
            """ substitute any steam id with a placeholder for matching """
            try:
                current_path[current_layer] = "%steamid%"
            except IndexError:
                current_path.append("%steamid%")
        else:
            try:
                current_path[current_layer] = new_key
            except IndexError:
                current_path.append(new_key)

        return "/".join(current_path)

    def append(self, *args, **kwargs):
        updated_values_dict = args[0]
        working_copy_dict = kwargs.get("dict_to_update", self)
        original_values_dict = kwargs.get("original_values_dict", {})
        if len(original_values_dict) <= 0:
            original_values_dict = deepcopy(dict(working_copy_dict))

        path = kwargs.get("path", [])
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

            if len(self.registered_callbacks) >= 1 and full_path in self.registered_callbacks.keys():
                for callback in self.registered_callbacks[full_path]:
                    callbacks.append(
                        self.get_callback_package(
                            updated_values=updated_values_dict,
                            old_values=working_copy_dict,
                            original_values_dict=original_values_dict,
                            dispatchers_steamid=dispatchers_steamid,
                            callback=callback
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
                self.append(v, dict_to_update=d_v, original_values_dict=original_values_dict[k], path=path,
                            layer=layer + 1, callbacks=callbacks, maxlen=maxlen)

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
        layer = kwargs.get("layer", 0)
        callbacks = kwargs.get("callbacks", None)

        if layer == 0 and callbacks is None:
            callbacks = []

        path = path[0:layer]

        """" recursion happens in this section """
        for k, v in updated_values_dict.items():
            full_path = self.construct_full_path(path, k, layer)

            forced_overwrite = False
            working_path = None
            if len(self.registered_callbacks) >= 1 and full_path in self.registered_callbacks.keys():
                if overwrite is True:
                    forced_overwrite = True
                    working_copy_dict[k] = v

                working_path = full_path

            if not forced_overwrite:
                d_v = working_copy_dict.get(k)
                if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                    self.upsert(v, dict_to_update=d_v, original_values_dict=original_values_dict[k], path=path,
                                layer=layer + 1, callbacks=callbacks, overwrite=overwrite,
                                dispatchers_steamid=dispatchers_steamid)
                else:
                    working_copy_dict[k] = v
                    if isinstance(v, Mapping) and len(v) >= 1:
                        working_path = "{}/{}".format(full_path, next(iter(v)))

            if working_path is not None:
                try:
                    for callback in self.registered_callbacks[working_path]:
                        callbacks.append(
                            self.get_callback_package(
                                updated_values=updated_values_dict,
                                old_values=working_copy_dict,
                                original_values_dict=original_values_dict,
                                dispatchers_steamid=dispatchers_steamid,
                                callback=callback
                            ))

                except KeyError:
                    print("no callback found")

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
