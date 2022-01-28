import bge
from bge.types import *


def door(cont):
    # type: (SCA_PythonController) -> None
    """ Generic behavior of any door. """
    
    from ..bgf import state, playSound
    from .shared import getEventFromMap, addToState
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
        "Speed": "Normal",
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
                
            getEventFromMap(cont, DEBUG)
            
            # Start opened according to state
            if own["Opened"]:
                animName = getAnimName(own)
                curAnim = ANIMS[animName]
                own.playAction("Door", curAnim[0], curAnim[0], play_mode=curAnim[2], speed=DOOR_SPEED)
            
        animName = getAnimName(own)
        curAnim = ANIMS[animName]
        soundVolume = 1.0 if own["Speed"] == "Run" else 0.5 if own["Speed"] == "Normal" else 0.1
        animSpeed = 1.5 if own["Speed"] == "Run" else 1.0 if own["Speed"] == "Normal" else 0.6
        
        if own.isPlayingAction():
            always.skippedTicks = 0
            own["Use"] = False
            
            # Play close sound
            if not own["Opened"]:
                frame = own.getActionFrame()
                
                if (0 <= frame <= 2 or 30 <= frame <= 32) \
                and (not own["Sound"] or own["Sound"].status == aud.AUD_STATUS_INVALID):
                    handle = own["Sound"] = playSound("Door" + own["Type"] + "Close", own.parent)
                    handle.volume *= soundVolume
                    
        else:
            always.skippedTicks = 10
        
        inventory = state["Player"]["Inventory"] # type: list[str]
        canUnlock = own["Locked"] and own["Key"] in inventory
        
        if own["Use"]:
            own["Use"] = False
            
            if not own["Locked"] or canUnlock:
                
                # Unlock door and remove key from inventory
                if canUnlock:
                    own["Locked"] = False
                    inventory.remove(own["Key"])
                    handle = own["Sound"] = playSound("Door" + own["Type"] + "Unlocked", own.parent)
                    handle.volume *= soundVolume
                
                else:
                    # Play open sound
                    if not own["Opened"]:
                        handle = own["Sound"] = playSound("Door" + own["Type"] + "Open", own.parent)
                        handle.volume *= soundVolume
                        
                    own["Opened"] = not own["Opened"]
                    own.playAction("Door", curAnim[0], curAnim[1], play_mode=curAnim[2], speed=DOOR_SPEED * animSpeed)
                    
                # Add door to state
                addToState(cont, props=["Locked", "Opened", "Direction"])
                
            else:
                handle = own["Sound"] = playSound("Door" + own["Type"] + "Locked", own.parent)
                handle.volume *= soundVolume
                

