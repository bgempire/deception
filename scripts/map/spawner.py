""" This module is responsible for spawning the map in-game using data from 
the loader module. """

import bge
from bge.types import *


DEBUG = 0
MAP_RADIUS = 10 # meters
SPAWN_UPDATE_INTERVAL = 1 # seconds
DEFAULT_PROPS = {
    "MapPositionStr": "",
    "CurPos": "",
    "PlayerSet": False,
    "CurMap": {},
    "LastPosition": tuple(),
}


def main(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    spawnAll = own.groupObject.get("SpawnAll", False)
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            __init(cont)
            
        __setCurPosFromCamera(cont)
        
        if own["Timer"] >= 0:
            __spawnMap(cont, own.scene["MapPosition"], all=spawnAll)
            
            own["Timer"] = -1


def __despawnMap(cont, curPos, all=False):
    # type: (SCA_PythonController, list[int], bool) -> None
    
    own = cont.owner
    mapObjs = own["MapObjs"] # type: dict[str, dict[tuple, KX_GameObject]]
    
    for layer in mapObjs.keys():
        for coord in list(mapObjs[layer].keys()):
            if all or not __isPositionBetween(curPos, coord):
                mapObjs[layer][coord].endObject()
                del mapObjs[layer][coord]


def __getHeightFromLayer(layer):
    # type: (str) -> int
    
    from ast import literal_eval
    
    layerSplit = layer.split(":")
    return literal_eval(layerSplit[1]) if len(layerSplit) == 2 else 0


def __getMap(cont):
    # type: (SCA_PythonController) -> dict[str, dict[tuple, dict]]
    
    import sys
    from pathlib import Path
    from .loader import maps
    
    own = cont.owner
    
    if "-" in sys.argv:
        path = Path(sys.argv[-1])
        
        if path.exists():
            return maps[path.stem]
    
    if "Map" in own.groupObject and own.groupObject["Map"] in maps.keys():
        return maps[own.groupObject["Map"]]
    else:
        for key in maps.keys():
            return maps[key]


def __init(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    global DEBUG
    DEBUG = own.groupObject.get("Debug", False) if own.groupObject else False
    
    for key in DEFAULT_PROPS.keys():
        own[key] = DEFAULT_PROPS[key]
        if DEBUG: own.addDebugProperty(key, True)
        
    own["CurMap"] = __getMap(cont)
        
    print("> Map initializated")


def __isPositionBetween(curPos, tilePos):
    # type: (tuple[int], tuple[int]) -> int
    
    return curPos[0] - MAP_RADIUS <= tilePos[0] <= curPos[0] + MAP_RADIUS \
        and curPos[1] - MAP_RADIUS <= tilePos[1] <= curPos[1] + MAP_RADIUS


def __setCurPosFromCamera(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    camera = own.scene.active_camera
    
    curPos = __getMapPosition(camera)
    own.scene["MapPosition"] = curPos
    own["MapPositionStr"] = str(curPos)
    own["CurPos"] = str(tuple(map(round, [camera.worldPosition.x, -camera.worldPosition.y])))


def __spawnActors(cont, curPos, all=False):
    # type: (SCA_PythonController, list[int], bool) -> None
    
    from math import radians
    
    own = cont.owner
    curMap = own["CurMap"] # type: dict[str, object]
    
    if not "MapActors" in own:
        own["MapActors"] = {}
        
    mapActors = own["MapActors"] # type: dict[str, dict[tuple, KX_GameObject]]
    
    for layer in curMap.keys():
        
        if not layer.lower().startswith("actor"):
            continue
        
        height = __getHeightFromLayer(layer)
        
        if not layer in mapActors.keys():
            mapActors[layer] = {}
            
        for coord in curMap[layer].keys():
            curTile = curMap[layer][coord]
            
            if all or __isPositionBetween(curPos, coord):
                coord3d = coord + tuple([height])
                coord3d = (coord3d[0] * 2, -coord3d[1] * 2, coord3d[2])
                setPlayer = curTile["Name"] == "Player" and not own["PlayerSet"]
                
                if setPlayer and own.scene.get("Player"):
                    obj = own.scene["Player"] # type: KX_GameObject
                    obj.worldPosition = coord3d
                    obj.worldOrientation = [0, 0, radians(-curTile["Rotation"])]
                    obj.worldPosition.z += 1
                    obj.scene["MapPosition"] = __getMapPosition(obj)
                    own["PlayerSet"] = True
                    
                elif curTile["Name"] != "Player":
                    obj = own.scene.addObject(curTile["Name"]) # type: KX_GameObject
                    obj.worldPosition = coord3d
                    obj.worldOrientation = [0, 0, radians(-curTile["Rotation"])]
                    mapActors[layer][coord] = obj


def __spawnMap(cont, curPos, all=False):
    # type: (SCA_PythonController, tuple[int], bool) -> None
    
    from math import radians
    
    own = cont.owner
    
    if curPos != own["LastPosition"] and (not all or not "MapObjs" in own):
        curMap = own["CurMap"] # type: dict[str, object]
        
        if not "MapObjs" in own:
            own["MapObjs"] = {}
            
        mapObjs = own["MapObjs"] # type: dict[str, dict[tuple, KX_GameObject]]
        __despawnMap(cont, curPos, all=all)
        __spawnActors(cont, curPos, all=all)
            
        for layer in curMap.keys():
            
            if layer.lower().startswith("actor"):
                continue
            
            height = __getHeightFromLayer(layer)
            
            if not layer in mapObjs.keys():
                mapObjs[layer] = {}
                
            for coord in curMap[layer].keys():
                curTile = curMap[layer][coord]
                
                if all or __isPositionBetween(curPos, coord):
                    coord3d = coord + tuple([height])
                    coord3d = (coord3d[0] * 2, -coord3d[1] * 2, coord3d[2])
                    obj = own.scene.addObject(curTile["Name"]) # type: KX_GameObject
                    obj.worldPosition = coord3d
                    obj.worldPosition.x += curTile["Offset"][0] * 2
                    obj.worldPosition.y += -curTile["Offset"][1] * 2
                    obj.worldOrientation = [0, 0, radians(-curTile["Rotation"])]
                    mapObjs[layer][coord] = obj
                    
        own["LastPosition"] = curPos


# HELPER FUNCTIONS

def __getTime():
    # type: () -> float
    
    return round(bge.logic.getClockTime(), 2)


def __getMapPosition(obj):
    # type: (KX_GameObject) -> tuple[int]
    
    return (
        int(((obj.worldPosition.x // 10) * 10) + 5), 
        -int(((obj.worldPosition.y // 10) * 10) + 5), 
    )