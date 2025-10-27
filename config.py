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
    carla.Location(x = 184.5, y=-5.5, z = 0.5),
    carla.Rotation(yaw=180)  #ready to reverse direction (retromarcia)
)

BLOCKING_VEHICLE_TRANSFORMS = [
    carla.Transform(
        carla.Location(x=-184.5, y=-3.0, z=0.5),
        carla.Rotation(yaw=180)
    ),
    carla.Transform(
        carla.Location(x=-184.5, y=-8.0, z=0.5),
        carla.Rotation(yaw=180)
    ),
     carla.Transform(
        carla.Location(x=-184.5, y=-10.5, z=0.5),
        carla.Rotation(yaw=180)
    )
]

TARGET_VEHICLE_MODEL = 'vehicle.coca_cola.truck'
#spawn sulla strada principale (x ~ -175), ma a y=20 (fuori dalla vista iniziale)
TARGET_SPAWN_TRANSFORM = carla.Transform(
    carla.Location(x=-175.0, y=20.0, z=0.5),
)
# Si muove a 8 m/s (circa 29 km/h) lungo l'asse Y negativo.
TARGET_VELOCITY = carla.Vector3D(x=0, y=-8.0, z=0)




