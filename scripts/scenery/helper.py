from bge.types import *


def getEventFromMap(cont, debug=False):
    # type: (SCA_PythonController, bool) -> None
    """ Get event from map at current object coordinates. """
    
    from ..bgf import state, getUpmostParent
    from ..map.spawner import getCurrentMap
    
    own = cont.owner
    curMap = getCurrentMap(cont).get("Events")
    parent = getUpmostParent(own)
    
    eventsState = state["Events"] # type: dict[str, dict[tuple[int], dict[str, object]]]
    eventsLayerName = __getEventsLayerName(cont)
    
    if curMap:
        curPos = parent["Position"] # type: tuple[int]
        
        if eventsLayerName:
            curLayer = curMap[eventsLayerName]
            
            if curLayer.get(curPos):
                event = curLayer[curPos] # type: dict[str, object]
                
                for prop in event.get("Properties", {}).keys():
                    own[prop] = event["Properties"][prop]
                    if debug: own.addDebugProperty(prop)
            
            if eventsState.get(eventsLayerName, {}).get(curPos):
                event = eventsState[eventsLayerName][curPos] # type: dict[str, object]
                
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
    eventsLayerName = __getEventsLayerName(cont)
    
    if eventsLayerName:
        
        for prop in own.getPropertyNames():
            
            if (not props or prop in props) and type(own[prop]) in PROP_VALID_TYPES:
                event[prop] = own[prop]
        
        if not eventsLayerName in state["Events"]:
            state["Events"][eventsLayerName] = {}
        
        state["Events"][eventsLayerName][parent["Position"]] = event


def __getEventsLayerName(cont):
    # type: (SCA_PythonController) -> str
    
    from ..bgf import getUpmostParent
    from ..map.spawner import getCurrentMap
    
    curMap = getCurrentMap(cont).get("Events")
    parent = getUpmostParent(cont.owner)
    curPos = parent["Position"] # type: tuple[int]
    posZ = str(int(parent.worldPosition.z))
    
    for layer in curMap.keys():
        if layer.endswith(":" + posZ):
            return layer
            
    return ""

