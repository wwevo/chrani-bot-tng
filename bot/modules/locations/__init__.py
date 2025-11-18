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
            "run_observer_interval": 3,
            "run_observer_interval_idle": 10
        })

        setattr(self, "required_modules", [
            'module_dom',
            'module_dom_management',
            'module_game_environment',
            'module_players',
            'module_telnet',
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
    def get_location_volume(location_dict):
        """
        Calculate the 3D volume coordinates for a box-shaped location.

        Handles different map quadrants (SW, SE, NE, NW) with appropriate
        coordinate adjustments for the game's coordinate system.

        Args:
            location_dict: Dictionary containing shape, dimensions, and coordinates

        Returns:
            Dictionary with pos_x, pos_y, pos_z, pos_x2, pos_y2, pos_z2
            or None if not a box shape
        """
        shape = location_dict.get("shape", None)
        if shape != "box":
            return None

        dimensions = location_dict.get("dimensions", None)
        coords = location_dict.get("coordinates", None)

        # Convert coordinates to integers
        x = int(float(coords["x"]))
        y = int(float(coords["y"]))
        z = int(float(coords["z"]))

        width = float(dimensions["width"])
        height = float(dimensions["height"])
        length = float(dimensions["length"])

        # Determine quadrant and calculate adjustments
        is_west = x < 0  # West quadrants (SW, NW)
        is_south = z < 0  # South quadrants (SW, SE)

        # Base coordinates
        pos_x = x - 1 if is_west else x
        pos_z = z - 1

        # Z2 adjustment depends on quadrant
        z2_offset = -2 if is_south else -1

        return {
            "pos_x": pos_x,
            "pos_y": y,
            "pos_z": pos_z,
            "pos_x2": int(x - width),
            "pos_y2": int(y + height - 1),
            "pos_z2": int(z + length + z2_offset)
        }

    @staticmethod
    def _is_inside_sphere(player_pos, center, radius):
        """Check if position is inside a 3D sphere."""
        distance = math.sqrt(
            (player_pos['x'] - center['x']) ** 2 +
            (player_pos['y'] - center['y']) ** 2 +
            (player_pos['z'] - center['z']) ** 2
        )
        return distance <= radius

    @staticmethod
    def _is_inside_circle(player_pos, center, radius):
        """Check if position is inside a 2D circle (ignores Y axis)."""
        distance = math.sqrt(
            (player_pos['x'] - center['x']) ** 2 +
            (player_pos['z'] - center['z']) ** 2
        )
        return distance <= radius

    @staticmethod
    def _is_inside_box(player_pos, corner, dimensions):
        """Check if position is inside a 3D box."""
        return all([
            player_pos['x'] - dimensions['width'] <= corner['x'] <= player_pos['x'] + dimensions['width'],
            player_pos['y'] - dimensions['height'] <= corner['y'] <= player_pos['y'] + dimensions['height'],
            player_pos['z'] - dimensions['length'] <= corner['z'] <= player_pos['z'] + dimensions['length']
        ])

    @staticmethod
    def _is_inside_rectangle(player_pos, corner, dimensions):
        """Check if position is inside a 2D rectangle (ignores Y axis)."""
        return all([
            player_pos['x'] - dimensions['width'] <= corner['x'] <= player_pos['x'] + dimensions['width'],
            player_pos['z'] - dimensions['length'] <= corner['z'] <= player_pos['z'] + dimensions['length']
        ])

    @staticmethod
    def position_is_inside_boundary(position_dict=None, boundary_dict=None):
        """
        Check if a position is inside a boundary shape.

        Supports multiple shape types: spherical, circle, box, rectangular.

        Args:
            position_dict: Dictionary with 'pos' containing x, y, z coordinates
            boundary_dict: Dictionary with 'shape', 'dimensions', 'coordinates'

        Returns:
            bool: True if position is inside boundary, False otherwise
        """
        if not all([position_dict, boundary_dict]):
            return False

        shape = boundary_dict.get("shape")
        dimensions = boundary_dict.get("dimensions")
        coordinates = boundary_dict.get("coordinates")

        if not all([shape, dimensions, coordinates]):
            return False

        # Extract player position
        player_pos = {
            'x': float(position_dict.get("pos", {}).get("x", 0)),
            'y': float(position_dict.get("pos", {}).get("y", 0)),
            'z': float(position_dict.get("pos", {}).get("z", 0))
        }

        # Extract boundary center/corner coordinates
        boundary_coords = {
            'x': float(coordinates.get("x", 0)),
            'y': float(coordinates.get("y", 0)),
            'z': float(coordinates.get("z", 0))
        }

        # Check shape type and delegate to appropriate helper
        if shape == "spherical":
            radius = float(dimensions.get("radius", 0))
            return Locations._is_inside_sphere(player_pos, boundary_coords, radius)

        elif shape == "circle":
            radius = float(dimensions.get("radius", 0))
            return Locations._is_inside_circle(player_pos, boundary_coords, radius)

        elif shape == "box":
            dims = {
                'width': float(dimensions.get("width", 0)),
                'height': float(dimensions.get("height", 0)),
                'length': float(dimensions.get("length", 0))
            }
            return Locations._is_inside_box(player_pos, boundary_coords, dims)

        elif shape == "rectangular":
            dims = {
                'width': float(dimensions.get("width", 0)),
                'length': float(dimensions.get("length", 0))
            }
            return Locations._is_inside_rectangle(player_pos, boundary_coords, dims)

        return False

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Locations().get_module_identifier()] = Locations()
