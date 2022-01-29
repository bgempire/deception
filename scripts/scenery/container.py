import bge
from bge.types import *


def container(cont):
    # type: (SCA_PythonController) -> None
    """ Generic behavior for any item container such as drawers, closets, boxes, etc. """
    
    from ..bgf import state, database, playSound
    from .helper import getEventFromMap, addToState
    
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
                
            getEventFromMap(cont, DEBUG)
            
        if own["Use"]:
            own["Use"] = False
            
            if own["Item"]:
                if not own["Taken"]:
                    items = database["Items"] # type: dict[str, dict[str, object]]
                    sound = items.get(own["Item"], {}).get("Sound", 1)
                    
                    own["Sound"] = playSound("ItemPickup" + str(sound), own.parent)
                    
                    # Add item to player's inventory
                    state["Player"]["Inventory"].append(own["Item"])
                    own["Taken"] = True
                    
                    # Add container to state
                    addToState(cont, props=["Taken", "Item"])
                    own.sendMessage("UpdateDescription", ",".join(["ContainerTake", own["Item"]]))
                    
                else:
                    own.sendMessage("UpdateDescription", ",".join(["ContainerTaken", own["Item"]]))
                    
            else:
                own.sendMessage("UpdateDescription", ",".join(["ContainerEmpty"]))




