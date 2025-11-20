from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def send_location_update_to_map(*args, **kwargs):
    """Send location updates to map view via socket.io"""
    module = args[0]
    method = kwargs.get("method", None)
    updated_values_dict = kwargs.get("updated_values_dict", None)

    if updated_values_dict is None:
        return

    # Check which clients are viewing the map
    for clientid in module.webserver.connected_clients.keys():
        current_view = module.get_current_view(clientid)
        if current_view != "map":
            continue

        if method in ["upsert", "update", "edit"]:
            # Send location update for each changed location
            active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

            # updated_values_dict structure at callback depth 4:
            # {location_identifier: {location_data}}
            # location_data includes "owner" field

            for identifier, location_dict in updated_values_dict.items():
                if not isinstance(location_dict, dict):
                    continue

                # Get owner directly from location_dict
                owner_steamid = location_dict.get("owner")
                if owner_steamid is None:
                    continue

                location_id = f"{active_dataset}_{owner_steamid}_{identifier}"

                # Get full location data from DOM if fields are missing in updated_values_dict
                # (e.g., when only is_enabled is updated)
                full_location_dict = (
                    module.dom.data
                    .get("module_locations", {})
                    .get("elements", {})
                    .get(active_dataset, {})
                    .get(owner_steamid, {})
                    .get(identifier, {})
                )

                coordinates = location_dict.get("coordinates")
                if coordinates is None:
                    coordinates = full_location_dict.get("coordinates", {})

                dimensions = location_dict.get("dimensions")
                if dimensions is None:
                    dimensions = full_location_dict.get("dimensions", {})

                location_data = {
                    "name": location_dict.get("name", full_location_dict.get("name", "Unknown")),
                    "identifier": identifier,
                    "owner": owner_steamid,
                    "shape": location_dict.get("shape", full_location_dict.get("shape", "circle")),
                    "coordinates": {
                        "x": float(coordinates.get("x", 0)),
                        "y": float(coordinates.get("y", 0)),
                        "z": float(coordinates.get("z", 0))
                    },
                    "dimensions": dimensions,
                    "teleport_entry": location_dict.get("teleport_entry", full_location_dict.get("teleport_entry", {})),
                    "type": location_dict.get("type", full_location_dict.get("type", [])),
                    "is_enabled": location_dict.get("is_enabled", full_location_dict.get("is_enabled", False))
                }

                module.webserver.send_data_to_client_hook(
                    module,
                    payload={
                        "location_id": location_id,
                        "location": location_data
                    },
                    data_type="location_update",
                    clients=[clientid]
                )

        elif method in ["remove"]:
            # Send location removal
            location_origin = updated_values_dict[2]
            owner_steamid = updated_values_dict[3]
            location_identifier = updated_values_dict[-1]
            location_id = f"{location_origin}_{owner_steamid}_{location_identifier}"

            module.webserver.send_data_to_client_hook(
                module,
                payload={
                    "location_id": location_id
                },
                data_type="location_remove",
                clients=[clientid]
            )


trigger_meta = {
    "description": "sends location updates to webmap clients",
    "main_function": send_location_update_to_map,
    "handlers": {
        "module_locations/elements/%map_identifier%/%owner_steamid%/%element_identifier%":
            send_location_update_to_map,
    }
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
