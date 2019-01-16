from modules import started_modules_dict


def dispatch_socket_event(target_module, event_data, dispatchers_steamid):
    module_identifer = "module_{}".format(target_module)
    print("{} tries sending {} to module {}...".format(dispatchers_steamid, event_data, target_module))
    try:
        started_modules_dict[module_identifer].on_socket_event(event_data, dispatchers_steamid)
    except KeyError as error:
        print("{} attempt to send data to module {} failed: module not found!".format(dispatchers_steamid, target_module))
