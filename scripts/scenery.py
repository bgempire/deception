import bge
from bge.types import *


def door(cont):
    # type: (SCA_PythonController) -> None
    
    DEBUG = 1
    DOOR_SPEED = 0.6
    ANIMS = {
        "Open1": (0, 20, bge.logic.KX_ACTION_MODE_PLAY),
        "Close1": (20, 0, bge.logic.KX_ACTION_MODE_PLAY),
        "Open2": (30, 50, bge.logic.KX_ACTION_MODE_PLAY),
        "Close2": (50, 30, bge.logic.KX_ACTION_MODE_PLAY),
    }
    DEFAULT_PROPS = {
        "Opened": False,
        "Use": False,
        "Direction": 1,
    }
    
    own = cont.owner
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            
            for prop in DEFAULT_PROPS.keys():
                own[prop] = DEFAULT_PROPS[prop]
                if DEBUG: own.addDebugProperty(prop)
            
        animName = "Open" if not own["Opened"] else "Close"
        curAnim = ANIMS[animName + str(own["Direction"])]
        
        if own.isPlayingAction():
            own["Use"] = False
        
        if own["Use"]:
            own["Opened"] = not own["Opened"]
            own.playAction("Door", curAnim[0], curAnim[1], play_mode=curAnim[2], speed=DOOR_SPEED)