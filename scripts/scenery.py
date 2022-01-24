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
                
            __getEventFromMap(cont, DEBUG)
            
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
    """ Generic behavior for any item container such as drawers, closets, boxes, etc. """
    
    DEBUG = 0
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
                
            __getEventFromMap(cont, DEBUG)
            
        pass


def __getEventFromMap(cont, debug=False):
    # type: (SCA_PythonController, bool) -> None
    """ Get event from map at current object coordinates. """
    
    from .bgf import getUpmostParent
    from .map.spawner import getCurrentMap
    
    own = cont.owner
    curMap = getCurrentMap(cont)  
    parent = getUpmostParent(own)
    
    eventsLayer = own.scene.get("EventsLayer") # type: dict[tuple[int], dict[str, object]]
    
    if not eventsLayer:
        
        for layer in curMap.keys():
            if "event" in layer.lower():
                own.scene["EventsLayer"] = eventsLayer = curMap[layer]
                break
                
    if curMap and eventsLayer and "Position" in parent:
        curPos = parent["Position"]
        
        if eventsLayer.get(curPos):
            event = eventsLayer[curPos] # type: dict[str, object]
            
            for prop in event.get("Properties", {}).keys():
                own[prop] = event["Properties"][prop]
                if debug: own.addDebugProperty(prop)
                

