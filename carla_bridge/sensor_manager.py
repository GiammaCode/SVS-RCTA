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
        camera_bp = self.blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', str(config.CAMERA_IMAGE_WIDTH))
        camera_bp.set_attribute('image_size_y', str(config.CAMERA_IMAGE_HEIGHT))
        camera_bp.set_attribute('fov', config.CAMERA_FOV)

        spawned_sensor={}
        transforms = {
            'rear':config.REAR_CAMERA_TRANSFORM,
            'left': config.RCTA_LEFT_CAMERA_TRANSFORM,
            'right': config.RCTA_RIGHT_CAMERA_TRANSFORM
        }

        for name, transform in transforms.items():
            camera_sensor = self.world.try_spawn_actor(
                camera_bp,
                transform,
                attach_to = parent_vehicle
            )

            if camera_sensor:
                self.actor_list.append(camera_sensor)
                spawned_sensor[name] = camera_sensor
                print(f"RCTA camera {name} spawned with successfully")
            else:
                print(f"Error, spawn camera {name} failed")
                spawned_sensor[name] = None

        return(
            spawned_sensor.get('rear'),
            spawned_sensor.get('left'),
            spawned_sensor.get('right'),
        )


