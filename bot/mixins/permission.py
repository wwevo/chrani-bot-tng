class Permission(object):
    available_permissions_dict = dict

    def __init__(self):
        self.available_permissions_dict = {}

    def register_permission(self, identifier, permission_dict):
        self.available_permissions_dict[identifier] = permission_dict

    def has_permission(self, category, identifier, dispatchers_steamid):
        print("user '{}' is allowed to execute '{}/{}".format(
            dispatchers_steamid, category, identifier
        ))
        return True
