import bge
from bge.types import *
from .bgf import config, isKeyboardPressed
from mathutils import Vector


DEBUG = 1
MOVE_SPEED_FACTOR = 0.035
MOVE_RUN_MULTIPLIER = 2.2
DEFAULT_PROPS = {
    "Run": False,
    "MoveH": 0,
    "MoveV": 0,
}


def main(cont):
    # type: (SCA_PythonController) -> None
    
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            init(cont)
            
        inputManager(cont)
        mouseLook(cont)
        move(cont)


def init(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    own.scene.active_camera = own.childrenRecursive.get("PlayerCamera")
    
    for key in DEFAULT_PROPS.keys():
        own[key] = DEFAULT_PROPS[key]
        if DEBUG: own.addDebugProperty(key, True)


def inputManager(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    isUp = isKeyboardPressed(config["KeyUp"])
    isDown = isKeyboardPressed(config["KeyDown"])
    isLeft = isKeyboardPressed(config["KeyLeft"])
    isRight = isKeyboardPressed(config["KeyRight"])
    isRun = isKeyboardPressed(config["KeyRun"])
    
    own["Run"] = bool(isRun)
    
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


def mouseLook(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    mouseX = cont.actuators["MouseX"] # type: KX_MouseActuator
    mouseY = cont.actuators["MouseY"] # type: KX_MouseActuator
    
    mouseX.sensitivity = [config["MouseSensitivity"], 0]
    mouseY.sensitivity = [0, config["MouseSensitivity"]]
    
    for sen in (mouseX, mouseY):
        cont.activate(sen)


def move(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    runFactor = MOVE_RUN_MULTIPLIER if own["Run"] else 1.0
    moveVector = Vector([-own["MoveH"], -own["MoveV"], 0]).normalized() * MOVE_SPEED_FACTOR * runFactor
    own.applyMovement(moveVector, True)