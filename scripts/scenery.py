import bge
from bge.types import *


def door(cont):
    # type: (SCA_PythonController) -> None
    """ Generic behavior of any door. """
    
    from .bgf import playSound
    import aud
    
    DEBUG = 0
    DOOR_SPEED = 0.6
    ANIMS = {
        "Open1": (0, 20, bge.logic.KX_ACTION_MODE_PLAY),
        "Close1": (20, 0, bge.logic.KX_ACTION_MODE_PLAY),
        "Open2": (30, 50, bge.logic.KX_ACTION_MODE_PLAY),
        "Close2": (50, 30, bge.logic.KX_ACTION_MODE_PLAY),
    }
    DEFAULT_PROPS = {
        "Use": False,
        "Opened": False,
        "Locked": False,
        "Key": "",
        "Direction": 1,
        "Sound": None,
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
            
            # Play close sound
            if not own["Opened"]:
                frame = own.getActionFrame()
                
                if (0 <= frame <= 4 or 30 <= frame <= 34) \
                and (not own["Sound"] or own["Sound"].status == aud.AUD_STATUS_INVALID):
                    own["Sound"] = playSound("Door" + own["Type"] + "Close", own)
        
        if own["Use"]:
            
            # Play open sound
            if not own["Opened"]:
                own["Sound"] = playSound("Door" + own["Type"] + "Open", own)
                
            own["Opened"] = not own["Opened"]
            own.playAction("Door", curAnim[0], curAnim[1], play_mode=curAnim[2], speed=DOOR_SPEED)


def container(cont):
    # type: (SCA_PythonController) -> None
    """ Generic behavior for any item container such as drawers, wardrobes, boxes, etc. """
    
    from .map.spawner import getCurrentMap
    
    DEBUG = 1
    DEFAULT_PROPS = {
        "Use": False,
        "Item": "",
        "Taken": False,
    }
    
    own = cont.owner
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            
            for prop in DEFAULT_PROPS.keys():
                own[prop] = DEFAULT_PROPS[prop]
                if DEBUG: own.addDebugProperty(prop)
                
        curMap = getCurrentMap(cont)
        
        if curMap:
            pass

