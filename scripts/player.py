""" This module is responsible for the player logic, from movement to scenery interactions. """

import bge
from bge.types import *
from .bgf import config, isKeyPressed
from mathutils import Vector


DEBUG = 0
MOVE_SPEED_FACTOR = 2.0
MOVE_RUN_MULTIPLIER = 2.2
FLASHLIGHT_MOVE_SMOOTH = 15.0
FLASHLIGHT_MAX_ENERGY = 5.0
FLASHLIGHT_BATTERY_DRAIN = 0.0000 # Default: 0.0001
USE_DISTANCE = 2.0 # meters
DEFAULT_PROPS = {
    "Run": False,
    "MoveH": 0,
    "MoveV": 0,
    "FlashlightOn": True,
    "FlashlightBattery": 1.0,
}


def main(cont):
    # type: (SCA_PythonController) -> None
    
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            __init(cont)
            
        __inputManager(cont)
        __mouseLook(cont)
        __move(cont)
        __flashlight(cont)


def __flashlight(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    _flashlight = own.childrenRecursive.get("Flashlight") # type: KX_LightObject
    
    if _flashlight:
        _flashlight.timeOffset = FLASHLIGHT_MOVE_SMOOTH
        
        if own["FlashlightOn"]:
            
            if own["FlashlightBattery"] > 0:
                own["FlashlightBattery"] -= FLASHLIGHT_BATTERY_DRAIN
                
            if own["FlashlightBattery"] < 0:
                own["FlashlightBattery"] = 0.0
                
            _flashlight.energy = FLASHLIGHT_MAX_ENERGY * own["FlashlightBattery"]
                
        else:
            _flashlight.energy = 0.0


def __init(cont):
    # type: (SCA_PythonController) -> None
    own = cont.owner
    own.scene.active_camera = own.childrenRecursive.get("PlayerCamera")
    own.scene["Player"] = own
    
    global DEBUG
    DEBUG = own.groupObject.get("Debug") if own.groupObject else DEBUG
    
    for key in DEFAULT_PROPS.keys():
        own[key] = DEFAULT_PROPS[key]
        if DEBUG: own.addDebugProperty(key, True)


def __inputManager(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    isUp = isKeyPressed(config["KeyUp"])
    isDown = isKeyPressed(config["KeyDown"])
    isLeft = isKeyPressed(config["KeyLeft"])
    isRight = isKeyPressed(config["KeyRight"])
    isRun = isKeyPressed(config["KeyRun"])
    isFlashlight = isKeyPressed(config["KeyFlashlight"], status=1)
    isUse = isKeyPressed(config["KeyUse"], status=1)
    
    own["Run"] = bool(isRun)
    
    # Turn flashlight on or off
    if isFlashlight:
        own["FlashlightOn"] = not own["FlashlightOn"]
        
    # Use aimed object
    if isUse:
        __use(cont)
    
    # Vertical movement
    if isUp and not isDown:
        own["MoveV"] = 1
    
    elif not isUp and isDown:
        own["MoveV"] = -1
        
    else:
        own["MoveV"] = 0
    
    # Horizontal movement
    if isRight and not isLeft:
        own["MoveH"] = 1
    
    elif not isRight and isLeft:
        own["MoveH"] = -1
        
    else:
        own["MoveH"] = 0


def __mouseLook(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    mouseX = cont.actuators["MouseX"] # type: KX_MouseActuator
    mouseY = cont.actuators["MouseY"] # type: KX_MouseActuator
    
    mouseX.sensitivity = [config["MouseSensitivity"], 0]
    mouseY.sensitivity = [0, config["MouseSensitivity"]]
    
    for sen in (mouseX, mouseY):
        cont.activate(sen)


def __move(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    runFactor = MOVE_RUN_MULTIPLIER if own["Run"] else 1.0
    moveVector = Vector([-own["MoveH"], -own["MoveV"], 0]).normalized() * MOVE_SPEED_FACTOR * runFactor
    
    onGround = own.rayCast(own.worldPosition + Vector([0, 0, -1]), own, 1)
    
    if not onGround[0]:
        moveVector.z = own.localLinearVelocity.z
        
    own.localLinearVelocity = moveVector


def __use(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    camera = own.scene.active_camera
    
    hitObject = camera.getScreenRay(0.5, 0.5, USE_DISTANCE)
    
    if hitObject:
        
        if "Door" in hitObject:
            vect = (hitObject.parent.localPosition - own.localPosition) * hitObject.parent.localOrientation # type: Vector
            hitObject["Use"] = True
            
            if not hitObject["Opened"]:
                hitObject["Direction"] = 1 if vect.y >= 0 else 2

