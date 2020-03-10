from bot.module import Module
from bot import loaded_modules_dict
from time import time
import math


class Locations(Module):
    dom_element_root = list
    dom_element_select_root = list
    default_max_locations = int
    standard_location_shape = str

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "dom_element_root": ["%dom_element_identifier%"],
            "dom_element_select_root": ["%dom_element_identifier%", "selected_by"],
            "default_max_locations": 3,
            "standard_location_shape": "rectangular",
            "run_observer_interval": 5,
            "run_observer_interval_idle": 10
        })

        setattr(self, "required_modules", [
            'module_dom',
            'module_dom_management',
            'module_game_environment',
            'module_players',
            'module_webserver'
        ])

        self.next_cycle = 0
        self.all_available_actions_dict = {}
        self.all_available_widgets_dict = {}
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_locations"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)

        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )
        self.run_observer_interval_idle = self.options.get(
            "run_observer_interval_idle", self.default_options.get("run_observer_interval_idle", None)
        )
        self.dom_element_root = self.options.get(
            "dom_element_root", self.default_options.get("dom_element_root", None)
        )
        self.dom_element_select_root = self.options.get(
            "dom_element_select_root", self.default_options.get("dom_element_select_root", None)
        )
        self.default_max_locations = self.options.get(
            "default_max_locations", self.default_options.get("default_max_locations", None)
        )
        self.standard_location_shape = self.options.get(
            "standard_location_shape", self.default_options.get("standard_location_shape", None)
        )
    # endregion

    def start(self):
        """ all modules have been loaded and initialized by now. we can bend the rules here."""
        Module.start(self)
    # endregion

    def get_elements_by_type(self, location_type: str, var=None):
        if var is None:
            active_dataset = self.dom.data.get("module_game_environment", {}).get("active_dataset", None)
            var = (
                self.dom.data
                .get("module_locations", {})
                .get("elements", {})
                .get(active_dataset, {})
            )
        if hasattr(var, 'items'):
            for k, v in var.items():
                if k == "type":
                    if location_type in v:
                        yield var
                if isinstance(v, dict):
                    for result in self.get_elements_by_type(location_type, v):
                        yield result
                elif isinstance(v, list):
                    for d in v:
                        for result in self.get_elements_by_type(location_type, d):
                            yield result

    @staticmethod
    def position_is_inside_boundary(position_dict=None, boundary_dict=None):
        position_is_inside_boundary = False

        shape = boundary_dict.get("shape", None)
        dimensions = boundary_dict.get("dimensions", None)
        if all([
            shape is not None,
            dimensions is not None,
            position_dict is not None,
            boundary_dict is not None
        ]):
            player_pos_x = float(position_dict.get("pos", {}).get("x", None))
            player_pos_y = float(position_dict.get("pos", {}).get("y", None))
            player_pos_z = float(position_dict.get("pos", {}).get("z", None))

            """ round areas have to be treated differently from rectangular ones """
            if shape in ["spherical", "circle"]:
                location_radius = float(dimensions.get("radius", 0))

                cx = float(boundary_dict.get("coordinates", {}).get("x", 0))
                cy = float(boundary_dict.get("coordinates", {}).get("y", 0))
                cz = float(boundary_dict.get("coordinates", {}).get("z", 0))

                if shape == "spherical":  # (3D)
                    distance_to_location_center = math.sqrt(
                        (player_pos_x - cx) ** 2 + (player_pos_y - cy) ** 2 + (player_pos_z - cz) ** 2
                    )
                    position_is_inside_boundary = distance_to_location_center <= location_radius
                elif shape == "circle":  # (2D)
                    distance_to_location_center = math.sqrt(
                        (player_pos_x - cx) ** 2 + (player_pos_z - cz) ** 2
                    )
                    position_is_inside_boundary = distance_to_location_center <= location_radius

            elif shape in ["box", "rectangular"]:
                location_width = float(dimensions.get("width", 0))
                location_height = float(dimensions.get("height", 0))
                location_length = float(dimensions.get("length", 0))

                south_east_x = float(boundary_dict.get("coordinates", {}).get("x", 0))
                south_east_y = float(boundary_dict.get("coordinates", {}).get("y", 0))
                south_east_z = float(boundary_dict.get("coordinates", {}).get("z", 0))

                if shape == "box":  # (3D)
                    position_is_inside_boundary = all([
                        player_pos_x - location_width <= south_east_x <= player_pos_x + location_width,
                        player_pos_y - location_height <= south_east_y <= player_pos_y + location_height,
                        player_pos_z - location_length <= south_east_z <= player_pos_z + location_length
                    ])
                elif shape == "rectangular":  # (2D)
                    position_is_inside_boundary = all([
                        player_pos_x - location_width <= south_east_x <= player_pos_x + location_width,
                        player_pos_z - location_length <= south_east_z <= player_pos_z + location_length
                    ])

        return position_is_inside_boundary

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Locations().get_module_identifier()] = Locations()
