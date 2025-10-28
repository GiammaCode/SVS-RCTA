import carla

"""
Configuration constants for the CARLA simulation.
"""

#Server connection
HOST = 'localhost'
PORT = 2000
TIMEOUT = 10

#Scenarios
MAP_NAME = 'Town05'

EGO_VEHICLE_MODEL = 'vehicle.audi.tt'
BLOCKING_VEHICLE_MODELS = [
    'vehicle.toyota.prius',
    'vehicle.nissan.patrol',
    'vehicle.ford.mustang',
    'vehicle.chevrolet.impala'
]

EGO_SPAWN_TRANSFORM = carla.Transform(
    carla.Location(x=-30.0, y=-30, z=0.5),
    carla.Rotation(yaw=0)  #ready to reverse direction (retromarcia)
)

BLOCKING_VEHICLE_TRANSFORMS = [
    carla.Transform(
        carla.Location(x=-30.0, y=-27.0, z=0.5),
        carla.Rotation(yaw=0)
    ),
    carla.Transform(
        carla.Location(x=-30.0, y=-32.8, z=0.5),
        carla.Rotation(yaw=0)
    ),
     carla.Transform(
        carla.Location(x=-30.0, y=-35.5, z=0.5),
        carla.Rotation(yaw=0)
    )
]

# Emergency Braking System (EBS) settings
TTC_THRESHOLD = 2 #seconds
STABLE_DETECTION_THRESHOLD = 3 #number of consecutive "true"

#RADAR value
RADAR_RANGE = 50.0 #meters
RADAR_HORIZONTAL_FOV = 45 #degrees
RADAR_VERTICAL_FOV = 30 #degrees
RADAR_POINTS_PER_SECOND = 1500



