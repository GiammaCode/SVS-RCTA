import carla

"""
Configuration constants for the CARLA simulation.
"""

#Server connection
HOST = 'localhost'
PORT = 2000
TIMEOUT = 10

#Scenarios setting
MAP_NAME = 'Town05'

#EGO vehicle
EGO_VEHICLE_MODEL = 'vehicle.audi.tt'
EGO_SPAWN_TRANSFORM = carla.Transform(
    carla.Location(x=-30.0, y=-30, z=0.5),
    carla.Rotation(yaw=0)  #ready to reverse direction (retromarcia)
)

#blocking vehicles
BLOCKING_VEHICLE_MODELS = [
    'vehicle.toyota.prius',
    'vehicle.nissan.patrol',
    'vehicle.ford.mustang',
    'vehicle.chevrolet.impala'
]
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


#target vehicle
TARGET_VEHICLE_MODEL = 'vehicle.mercedes.sprinter'
TARGET_SPAWN_TRANSFORM = carla.Transform(
    carla.Location(x=-35.0, y=-40.0, z=0.5),
    carla.Rotation(yaw=90)
)
#2 m/s (circa 7 km/h)
TARGET_VELOCITY = carla.Vector3D(x=0, y=2.0, z=0)




