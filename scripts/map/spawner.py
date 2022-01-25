""" This module is responsible for spawning the map in-game using data from 
the loader module. """

import bge
from bge.types import *


DEBUG = 0
MAP_RADIUS = 40 # meters
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
    
    global MAP_RADIUS
    own = cont.owner
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    spawnAll = own.groupObject.get("SpawnAll", False)
    MAP_RADIUS = own.groupObject.get("MapRadius", 30)
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            __init(cont)
            
        __setCurPosFromCamera(cont)
        
        if own["Timer"] >= 0:
            __spawnMap(cont, own.scene["MapPosition"], all=spawnAll)
            
            own["Timer"] = -1


def getCurrentMap(cont, spawnerObj=None):
    # type: (SCA_PythonController, KX_GameObject) -> dict[str, dict[tuple, dict]]
    
    import sys
    from pathlib import Path
    from .loader import maps
    
    own = cont.owner
    currentMap = {}
    
    # Get map from map spawner object
    if spawnerObj:
        
        if "-" in sys.argv:
            path = Path(sys.argv[-1])
            
            if path.exists():
                currentMap = maps[path.stem]
        
        elif "Map" in own.groupObject and own.groupObject["Map"] in maps.keys():
            currentMap = maps[own.groupObject["Map"]]
            
        else:
            for key in maps.keys():
                currentMap = maps[key]
                
    # Get existing map from scene
    elif "CurMap" in own.scene:
        currentMap = own.scene["CurMap"]
            
    return currentMap


def __despawnMap(cont, curPos):
    # type: (SCA_PythonController, list[int]) -> None
    
    own = cont.owner
    mapObjs = own["MapObjs"] # type: dict[str, dict[tuple, KX_GameObject]]
    
    for layer in mapObjs.keys():
        for coord in list(mapObjs[layer].keys()):
            if not __isPositionBetween(curPos, coord):
                mapObjs[layer][coord].endObject()
                del mapObjs[layer][coord]


def __getHeightFromLayer(layer):
    # type: (str) -> int
    
    from ast import literal_eval
    
    layerSplit = layer.split(":")
    return literal_eval(layerSplit[1]) if len(layerSplit) == 2 else 0


def __init(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    global DEBUG
    DEBUG = own.groupObject.get("Debug", False) if own.groupObject else False
    
    for key in DEFAULT_PROPS.keys():
        own[key] = DEFAULT_PROPS[key]
        if DEBUG: own.addDebugProperty(key, True)
        
    own.scene["CurMap"] = getCurrentMap(cont, spawnerObj=own)
    
    __setPlayer(cont)
        
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
    own["CurPos"] = str(tuple(map(round, (camera.worldPosition.x, camera.worldPosition.y))))


def __setPlayer(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    if not own["PlayerSet"]:
        coord, curTile, height = __getPlayerFromMap(cont)
        
        if coord and curTile:
            obj = own.scene.get("Player") # type: KX_GameObject
            
            if obj:
                coord3d = coord + tuple([height])
                __setTile(obj, curTile, coord3d)
                obj.worldPosition.z += 1
                obj.scene["MapPosition"] = __getMapPosition(obj)
                own["PlayerSet"] = True
        

def __getPlayerFromMap(cont):
    # type: (SCA_PythonController) -> tuple[tuple[int], dict[str, object], str]
    
    own = cont.owner
    curMap = own.scene["CurMap"] # type: dict[str, dict[tuple, dict[str, object]]]
    
    for layer in curMap.keys():
        if "event" in layer.lower():
            for coord in curMap[layer].keys():
                curTile = curMap[layer][coord]
                
                if curTile["Name"] == "Player":
                    return [coord, curTile, curTile.get("Properties", {}).get("Height", 0)]
                    
    return [None, None, None]


def __spawnActors(cont, curPos, all=False):
    # type: (SCA_PythonController, list[int], bool) -> None
    
    from ..bgf import database
    
    own = cont.owner
    curMap = own.scene["CurMap"] # type: dict[str, dict[tuple, dict[str, object]]]
    
    if not "MapActors" in own:
        own["MapActors"] = {}
        
    mapActors = own["MapActors"] # type: dict[str, dict[tuple, KX_GameObject]]
    
    for layer in curMap.keys():
        
        if not "event" in layer.lower():
            continue
        
        if not layer in mapActors.keys():
            mapActors[layer] = {}
            
        for coord in curMap[layer].keys():
            curTile = curMap[layer][coord]
            coord3d = coord + tuple([curTile.get("Height", 0)])
            
            if all or __isPositionBetween(curPos, coord):
                
                if curTile["Name"] in database["Actors"].keys():
                    obj = own.scene.addObject(curTile["Name"]) # type: KX_GameObject
                    __setTile(obj, curTile, coord3d)
                    mapActors[layer][coord] = obj


def __spawnMap(cont, curPos, all=False):
    # type: (SCA_PythonController, tuple[int], bool) -> None
    
    from math import radians
    
    own = cont.owner
    
    if curPos != own["LastPosition"] and (not all or not "MapObjs" in own):
        curMap = own.scene["CurMap"] # type: dict[str, dict[str, object]]
        
        if not "MapObjs" in own:
            own["MapObjs"] = {}
            
            for layer in curMap.keys():
                own["MapObjs"][layer] = {}
            
        mapObjs = own["MapObjs"] # type: dict[str, dict[tuple, KX_GameObject]]
        
        if not all:
            __despawnMap(cont, curPos)
            
        __spawnActors(cont, curPos, all=all)
        
        for layer in curMap.keys():
            
            if "event" in layer.lower():
                continue
            
            height = __getHeightFromLayer(layer)
            
            if not layer in mapObjs.keys():
                mapObjs[layer] = {}
                
            for coord in curMap[layer].keys():
                curTile = curMap[layer][coord]
                
                if all or __isPositionBetween(curPos, coord) and not coord in mapObjs[layer].keys():
                    coord3d = coord + tuple([height])
                    obj = own.scene.addObject(curTile["Name"]) # type: KX_GameObject
                    __setTile(obj, curTile, coord3d)
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
        int(((obj.worldPosition.y // 10) * 10) + 5), 
    )


def __setTile(obj, tile, coord3d):
    # type: (KX_GameObject, dict[str, object], tuple[int]) -> None
    
    from math import radians
    
    obj["Position"] = coord3d[0:2]
    obj.worldPosition = coord3d
    obj.worldPosition.x += tile.get("Offset", (0, 0))[0]
    obj.worldPosition.y += -tile.get("Offset", (0, 0))[1]
    obj.worldOrientation = [0, 0, radians(-tile.get("Rotation", 0))]

