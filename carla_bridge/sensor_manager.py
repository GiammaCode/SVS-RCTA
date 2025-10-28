from symtable import Class

import carla
import config

class SensorManager:
    """
    manages creation and configuration about sensors
    """
    def __init__(self, world, actor_list):
        self.world = world
        self.actor_list = actor_list
        self.blueprint_library = world.get_blueprint_library()

    def setup_rcta_cameras(self, parent_vehicle):
        """
        creates and fittings 3 cameras for the system RCTA

        :param parent_vehicle: vehicle actor to attach cameras
        :return: tupla of 3 sensors (rear_cam, left_cam, right_cam)
        """
