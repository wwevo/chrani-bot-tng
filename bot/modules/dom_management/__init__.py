from bot.module import Module
from bot import loaded_modules_dict


class DomManagement(Module):

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })

        setattr(self, "required_modules", [
            "module_dom",
            "module_webserver"
        ])

        self.run_observer_interval = 5
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_dom_management"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
    # endregion

    def get_selection_dom_element(self, *args, **kwargs):
        module = args[0]
        return module.template_render_hook(
            module,
            module.dom_management.templates.get_template('control_select_link.html'),
            dom_element_select_root=kwargs.get("dom_element_select_root"),
            target_module=kwargs.get("target_module"),
            dom_element_entry_selected=kwargs.get("dom_element_entry_selected"),
            dom_element=kwargs.get("dom_element"),
            dom_action_inactive=kwargs.get("dom_action_inactive"),
            dom_action_active=kwargs.get("dom_action_active")
        )

    def get_delete_button_dom_element(self, *args, **kwargs):
        module = args[0]
        return module.template_render_hook(
            module,
            module.dom_management.templates.get_template('control_action_delete_button.html'),
            count=kwargs.get("count"),
            target_module=kwargs.get("target_module"),
            dom_action=kwargs.get("dom_action"),
            delete_selected_entries_active=True if kwargs.get("count") >= 1 else False,
            dom_element_id=kwargs.get("dom_element_id")
        )

    @staticmethod
    def update_selection_status(*args, **kwargs):
        module = args[0]
        updated_values_dict = kwargs.get("updated_values_dict", None)
        target_module = kwargs.get("target_module", None)
        dom_element_root = kwargs.get("dom_element_root", None)
        dom_action_active = kwargs.get("dom_action_active", None)
        dom_action_inactive = kwargs.get("dom_action_inactive", None)
        dom_element_select_root = kwargs.get("dom_element_select_root", None)
        dom_element_id = kwargs.get("dom_element_id", None)

        dom_element_origin = updated_values_dict["origin"]
        dom_element_owner = updated_values_dict["owner"]

        dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

        dom_element = (
            module.dom.data
            .get(target_module.get_module_identifier(), {})
            .get("elements", {})
            .get(dom_element_origin, {})
            .get(dom_element_owner, {})
        )

        for sub_dict in dom_element_root:
            dom_element = dom_element.get(sub_dict)

        dom_element_is_selected_by = (
            module.dom.data
            .get("module_dom", {})
            .get(target_module.get_module_identifier(), {})
            .get(dom_element_origin, {})
            .get(dom_element_owner, {})
        )

        for sub_dict in dom_element_select_root:
            dom_element_is_selected_by = dom_element_is_selected_by.get(sub_dict)

        dom_element_entry_selected = False
        if dispatchers_steamid in dom_element_is_selected_by:
            dom_element_entry_selected = True

        control_select_link = module.dom_management.get_selection_dom_element(
            module,
            target_module=target_module.get_module_identifier(),
            dom_element_select_root=dom_element_select_root,
            dom_element=dom_element,
            dom_element_entry_selected=dom_element_entry_selected,
            dom_action_inactive=dom_action_inactive,
            dom_action_active=dom_action_active
        )

        module.webserver.send_data_to_client_hook(
            module,
            event_data=control_select_link,
            data_type="element_content",
            clients=[dispatchers_steamid],
            method="update",
            target_element=dom_element_id
        )

    def occurrences_of_key_in_nested_mapping(self, key, value):
        for k, v in value.items():
            if k == key:
                yield v
            elif isinstance(v, dict):
                for result in self.occurrences_of_key_in_nested_mapping(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in self.occurrences_of_key_in_nested_mapping(key, d):
                        yield result

    def update_delete_button_status(self, *args, **kwargs):
        module = args[0]
        updated_values_dict = kwargs.get("updated_values_dict", None)
        target_module = kwargs.get("target_module", None)
        dom_action = kwargs.get("dom_action", None)

        dom_element_origin = updated_values_dict["origin"]
        dom_element_id = kwargs.get("dom_element_id", None)

        template_action_delete_button = module.dom_management.templates.get_template('control_action_delete_button.html')

        all_available_elements = (
            module.dom.data
            .get("module_dom", {})
            .get(target_module.get_module_identifier(), {})
            .get(dom_element_origin, {})
        )

        for clientid in module.webserver.connected_clients.keys():
            all_selected_elements = 0
            for dom_element_is_selected_by in self.occurrences_of_key_in_nested_mapping("selected_by", all_available_elements):
                if clientid in dom_element_is_selected_by:
                    all_selected_elements += 1

            data_to_emit = module.template_render_hook(
                module,
                template_action_delete_button,
                dom_action=dom_action,
                target_module=target_module.get_module_identifier(),
                count=all_selected_elements,
                delete_selected_entries_active=True if all_selected_elements >= 1 else False,
                dom_element_id=dom_element_id["id"]
            )

            module.webserver.send_data_to_client_hook(
                module,
                event_data=data_to_emit,
                data_type="element_content",
                clients=[clientid],
                method="replace",
                target_element=dom_element_id
            )

    def get_dict_element_by_path(self, d, l):
        if len(l) == 1:
            return d.get(l[0], [])
        return self.get_dict_element_by_path(d.get(l[0], {}), l[1:])


loaded_modules_dict[DomManagement().get_module_identifier()] = DomManagement()
