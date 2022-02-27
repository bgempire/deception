import bge
from bge.types import *


DEBUG = 0
DEFAULT_PROPS = {
    "Item": "",
    "Taken": False,
    "Use": False,
}


def container(cont):
    # type: (SCA_PythonController) -> None
    """ Generic behavior for any item container such as drawers, closets, boxes, etc. """
    
    own = cont.owner
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            __init(cont)
            
        if own["Use"]:
            __use(cont)


def __init(cont):
    # type: (SCA_PythonController) -> None
    
    from .helper import getEventFromMap
    
    own = cont.owner
    
    for prop in DEFAULT_PROPS.keys():
        own[prop] = DEFAULT_PROPS[prop]
        if DEBUG: own.addDebugProperty(prop)
        
    getEventFromMap(cont, DEBUG)


def __use(cont):
    # type: (SCA_PythonController) -> None
    
    from .helper import addToState
    from ..bgf import state, database, playSound
    
    own = cont.owner
    
    own["Use"] = False
    
    if own["Item"] and not own.get("Empty"):
        if not own["Taken"]:
            items = database["Items"] # type: dict[str, dict[str, object]]
            sound = items.get(own["Item"], {}).get("Sound", 1)
            
            own["Sound"] = playSound("ItemPickup" + str(sound), own.parent)
            
            # Add item to player's inventory
            state["Player"]["Inventory"].append(own["Item"])
            state["Player"]["Inventory"].sort()
            own["Taken"] = True
            
            # Add container to state
            addToState(cont, props=["Taken", "Item"])
            own.sendMessage("UpdateDescription", ",".join(["ContainerTake", own["Item"]]))
            
        else:
            own.sendMessage("UpdateDescription", ",".join(["ContainerTaken", own["Item"]]))
            
    else:
        own.sendMessage("UpdateDescription", ",".join(["ContainerEmpty"]))

