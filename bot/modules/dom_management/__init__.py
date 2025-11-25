from bot.module import Module
from bot import loaded_modules_dict


class DomManagement(Module):
    # region Standard module stuff
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

    def setup(self, options=dict):
        Module.setup(self, options)
    # endregion

    # region Tools and workers
    @staticmethod
    def sanitize_for_html_id(value):
        """
        Sanitize a string for use in HTML IDs.
        Replaces spaces with underscores and converts to lowercase.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string safe for HTML IDs
        """
        return str(value).replace(" ", "_").lower()

    def occurrences_of_key_in_nested_mapping(self, key, value):
        for k, v in value.items():
            if k == key:
                yield v
            elif isinstance(v, dict):
                for result in self.occurrences_of_key_in_nested_mapping(key, v):
                    yield result

    def get_dict_element_by_path(self, d, l):
        if len(l) == 1:
            return d.get(l[0], [])
        return self.get_dict_element_by_path(d.get(l[0], {}), l[1:])
    # endregion

    # region Template functions
    @staticmethod
    def get_selection_dom_element(*args, **kwargs):
        module = args[0]
        return module.template_render_hook(
            module,
            template=module.dom_management.templates.get_template('control_select_link.html'),
            dom_element_select_root=kwargs.get("dom_element_select_root"),
            target_module=kwargs.get("target_module"),
            dom_element_entry_selected=kwargs.get("dom_element_entry_selected"),
            dom_element=kwargs.get("dom_element"),
            dom_action_inactive=kwargs.get("dom_action_inactive"),
            dom_action_active=kwargs.get("dom_action_active")
        )

    @staticmethod
    def get_select_all_checkbox_dom_element(*args, **kwargs):
        module = args[0]
        return module.template_render_hook(
            module,
            template=module.dom_management.templates.get_template('control_select_link.html'),
            dom_element_select_root=kwargs.get("dom_element_select_root"),
            target_module=kwargs.get("target_module"),
            dom_element_entry_selected=kwargs.get("all_elements_selected"),
            dom_element=kwargs.get("dom_element"),
            dom_action_inactive=kwargs.get("dom_action_inactive"),
            dom_action_active=kwargs.get("dom_action_active"),
            event_action=kwargs.get("event_action", "select_all"),
            label_active=kwargs.get("label_active", "&#9745; all"),
            label_inactive=kwargs.get("label_inactive", "&#9744; all")
        )

    @staticmethod
    def get_delete_button_dom_element(*args, **kwargs):
        module = args[0]
        return module.template_render_hook(
            module,
            template=module.dom_management.templates.get_template('control_action_delete_button.html'),
            count=kwargs.get("count"),
            target_module=kwargs.get("target_module"),
            dom_element_root=kwargs.get("dom_element_root"),
            dom_element_select_root=kwargs.get("dom_element_select_root"),
            dom_action=kwargs.get("dom_action"),
            delete_selected_entries_active=kwargs.get("count") >= 1,
            dom_element_id=kwargs.get("dom_element_id"),
            confirmed=kwargs.get("confirmed", "False")
        )

    @staticmethod
    def get_delete_confirm_modal(*args, **kwargs):
        module = args[0]
        return module.template_render_hook(
            module,
            template=module.dom_management.templates.get_template('modal_confirm_delete.html'),
            count=kwargs.get("count"),
            target_module=kwargs.get("target_module"),
            dom_element_root=kwargs.get("dom_element_root"),
            dom_element_select_root=kwargs.get("dom_element_select_root"),
            dom_action=kwargs.get("dom_action"),
            delete_selected_entries_active=kwargs.get("count") >= 1,
            dom_element_id=kwargs.get("dom_element_id"),
            confirmed=kwargs.get("confirmed", "False")
        )

    @staticmethod
    def update_selection_status(*args, **kwargs):
        module = args[0]
        updated_values_dict = kwargs.get("updated_values_dict", None)
        target_module = kwargs.get("target_module", None)
        dom_element_root = kwargs.get("dom_element_root", [])
        dom_action_active = kwargs.get("dom_action_active", None)
        dom_action_inactive = kwargs.get("dom_action_inactive", None)
        dom_element_select_root = kwargs.get("dom_element_select_root", ["selected_by"])
        dom_element_id = kwargs.get("dom_element_id", None)

        # Use unsanitized dataset_original for DOM lookups (if available)
        dom_element_origin = updated_values_dict.get("dataset_original", updated_values_dict.get("dataset"))
        dom_element_owner = updated_values_dict["owner"]

        dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

        # getting the base root for all elements. it's always this path if the module wants to use these built
        # in functions
        dom_element = (
            module.dom.data
            .get(target_module.get_module_identifier(), {})
            .get("elements", {})
            .get(dom_element_origin, {})
            .get(dom_element_owner, {})
        )

        # get the individual element path, as provided by the module
        for sub_dict in dom_element_root:
            dom_element = dom_element.get(sub_dict)

        dom_element_is_selected_by = dom_element.get("selected_by", [])
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
            payload=control_select_link,
            data_type="element_content",
            clients=[dispatchers_steamid],
            method="update",
            target_element=dom_element_id
        )

    def update_delete_button_status(self, *args, **kwargs):
        module = args[0]

        target_module = kwargs.get("target_module", None)
        dom_action = kwargs.get("dom_action", None)
        dom_element_id = kwargs.get("dom_element_id", None)

        template_action_delete_button = module.dom_management.templates.get_template('control_action_delete_button.html')

        all_available_elements = (
            module.dom.data
            .get(target_module.get_module_identifier(), {})
            .get("elements", {})
        )

        for clientid in module.webserver.connected_clients.keys():
            all_selected_elements = 0
            for dom_element_is_selected_by in self.occurrences_of_key_in_nested_mapping(
                    "selected_by",
                    all_available_elements
            ):
                if clientid in dom_element_is_selected_by:
                    all_selected_elements += 1

            data_to_emit = module.template_render_hook(
                module,
                template=template_action_delete_button,
                dom_action=dom_action,
                dom_element_root=kwargs.get("dom_element_root", []),
                dom_element_select_root=kwargs.get("dom_element_select_root", []),
                target_module=target_module.get_module_identifier(),
                count=all_selected_elements,
                delete_selected_entries_active=all_selected_elements >= 1,
                dom_element_id=dom_element_id["id"],
                confirmed=kwargs.get("confirmed", "False")
            )

            module.webserver.send_data_to_client_hook(
                module,
                payload=data_to_emit,
                data_type="element_content",
                clients=[clientid],
                method="replace",
                target_element=dom_element_id
            )

    # endregion


loaded_modules_dict[DomManagement().get_module_identifier()] = DomManagement()
