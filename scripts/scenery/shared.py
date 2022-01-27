from bge.types import *


def getEventFromMap(cont, debug=False):
    # type: (SCA_PythonController, bool) -> None
    """ Get event from map at current object coordinates. """
    
    from ..bgf import state, getUpmostParent
    from ..map.spawner import getCurrentMap
    
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


def addToState(cont, props=[]):
    # type: (SCA_PythonController, list[str]) -> None
    """ Add object properties to state. """
    
    from ..bgf import state, getUpmostParent
    
    own = cont.owner
    parent = getUpmostParent(own)
    PROP_VALID_TYPES = (int, float, tuple, list, bool, str)
    
    event = {}
    
    for prop in own.getPropertyNames():
        
        if (not props or prop in props) and type(own[prop]) in PROP_VALID_TYPES:
            event[prop] = own[prop]
    
    state["Events"][parent["Position"]] = event

