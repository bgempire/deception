import bge
from bge.types import *


def door(cont):
    # type: (SCA_PythonController) -> None
    """ Generic behavior of any door. """
    
    from .bgf import state, playSound
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
        "Direction": 1,
        "Key": "",
        "Locked": False,
        "Opened": False,
        "Sound": None,
        "Use": False,
    }
    
    own = cont.owner
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    getAnimName = lambda obj: ("Open" if not obj["Opened"] else "Close") + str(obj["Direction"])
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            
            for prop in DEFAULT_PROPS.keys():
                
                own[prop] = DEFAULT_PROPS[prop]
                if DEBUG: own.addDebugProperty(prop)
                
            __getEventFromMap(cont, DEBUG)
            
            # Start opened according to state
            if own["Opened"]:
                animName = getAnimName(own)
                curAnim = ANIMS[animName]
                own.playAction("Door", curAnim[0], curAnim[0], play_mode=curAnim[2], speed=DOOR_SPEED)
            
        animName = getAnimName(own)
        curAnim = ANIMS[animName]
        
        if own.isPlayingAction():
            own["Use"] = False
            
            # Play close sound
            if not own["Opened"]:
                frame = own.getActionFrame()
                
                if (0 <= frame <= 4 or 30 <= frame <= 34) \
                and (not own["Sound"] or own["Sound"].status == aud.AUD_STATUS_INVALID):
                    own["Sound"] = playSound("Door" + own["Type"] + "Close", own)
        
        inventory = state["Player"]["Inventory"] # type: list[str]
        canUnlock = own["Locked"] and own["Key"] in inventory
        
        if own["Use"]:
            own["Use"] = False
            
            if not own["Locked"] or canUnlock:
                
                # Unlock door and remove key from inventory
                if canUnlock:
                    own["Locked"] = False
                    inventory.remove(own["Key"])
                    own["Sound"] = playSound("DoorUnlocked1", own.parent)
                
                else:
                    # Play open sound
                    if not own["Opened"]:
                        own["Sound"] = playSound("Door" + own["Type"] + "Open", own.parent)
                        
                    own["Opened"] = not own["Opened"]
                    own.playAction("Door", curAnim[0], curAnim[1], play_mode=curAnim[2], speed=DOOR_SPEED)
                    
                    # Add door to state
                    __addToState(cont, props=["Locked", "Opened", "Direction"])
                
            else:
                own["Sound"] = playSound("DoorLocked1", own.parent)


def container(cont):
    # type: (SCA_PythonController) -> None
    """ Generic behavior for any item container such as drawers, closets, boxes, etc. """
    
    from .bgf import state, database, playSound
    
    DEBUG = 0
    DEFAULT_PROPS = {
        "Item": "",
        "Taken": False,
        "Use": False,
    }
    
    own = cont.owner
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            
            for prop in DEFAULT_PROPS.keys():
                own[prop] = DEFAULT_PROPS[prop]
                if DEBUG: own.addDebugProperty(prop)
                
            __getEventFromMap(cont, DEBUG)
            
        if own["Use"]:
            own["Use"] = False
            
            if own["Item"] and not own["Taken"]:
                items = database["Items"] # type: dict[str, dict[str, object]]
                sound = items.get(own["Item"], {}).get("Sound", 1)
                
                own["Sound"] = playSound("ItemPickup" + str(sound), own.parent)
                
                # Add item to player's inventory
                state["Player"]["Inventory"].append(own["Item"])
                own["Taken"] = True
                
                # Add container to state
                __addToState(cont, props=["Taken", "Item"])


def __getEventFromMap(cont, debug=False):
    # type: (SCA_PythonController, bool) -> None
    """ Get event from map at current object coordinates. """
    
    from .bgf import state, getUpmostParent
    from .map.spawner import getCurrentMap
    
    own = cont.owner
    curMap = getCurrentMap(cont)  
    parent = getUpmostParent(own)
    
    eventsLayer = own.scene.get("EventsLayer") # type: dict[tuple[int], dict[str, object]]
    eventsState = state["Events"] # type: dict[tuple[int], dict[str, object]]
    
    if not eventsLayer:
        
        for layer in curMap.keys():
            if "event" in layer.lower():
                own.scene["EventsLayer"] = eventsLayer = curMap[layer]
                break
                
    if curMap and eventsLayer:
        curPos = parent["Position"]
        
        if eventsLayer.get(curPos):
            event = eventsLayer[curPos] # type: dict[str, object]
            
            for prop in event.get("Properties", {}).keys():
                own[prop] = event["Properties"][prop]
                if debug: own.addDebugProperty(prop)
        
        if eventsState.get(curPos):
            event = eventsState[curPos] # type: dict[str, object]
            
            for prop in event.keys():
                own[prop] = event[prop]
                if debug: own.addDebugProperty(prop)


def __addToState(cont, props=[]):
    # type: (SCA_PythonController, list[str]) -> None
    """ Add object properties to state. """
    
    from .bgf import state, getUpmostParent
    
    own = cont.owner
    parent = getUpmostParent(own)
    PROP_VALID_TYPES = (int, float, tuple, list, bool, str)
    
    event = {}
    
    for prop in own.getPropertyNames():
        
        if (not props or prop in props) and type(own[prop]) in PROP_VALID_TYPES:
            event[prop] = own[prop]
    
    state["Events"][parent["Position"]] = event

