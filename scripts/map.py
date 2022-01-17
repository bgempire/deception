import bge
from bge.types import *
import json
from pathlib import Path
from ast import literal_eval
from math import radians
import sys
from pprint import pprint, pformat
from .bgf import dump
from mathutils import Vector

mapLoader = None # type: MapLoader
MAP_RADIUS = 10


def getTime() -> float:
    return bge.logic.getRealTime()


def getMapPosition(obj):
    # type: (KX_GameObject) -> tuple[int]
    
    return (
        int(((obj.worldPosition.x // 10) * 10) + 5), 
        -int(((obj.worldPosition.y // 10) * 10) + 5), 
    )


class JsonLoader:
    
    def __init__(self):
        # type: () -> None
        self.rootPath = Path(__file__).parent.parent.resolve()
        
        
    def loadFile(self, path):
        # type: (Path | str) -> dict
        """ Load JSON file from path. """
        path = self.rootPath / path if type(path) == str else path
        with open(path.as_posix(), "r") as openedFile:
            return json.load(openedFile)
            
            
    def loadFiles(self, path, prefix="", merge=False):
        # type: (Path, str, bool) -> dict[str, dict]
        """ Load all JSON files from path. """
        path = self.rootPath / path
        data = {}
        for file_ in path.iterdir():
            if file_.name.startswith(prefix) and file_.name.endswith(".json"):
                loadedData = self.loadFile(file_)
                if merge: data.update(loadedData)
                else: data[file_.stem] = loadedData
        return data


class MapLoader(JsonLoader):
    
    def __init__(self, tileset="maps/Tileset.json"):
        # type: (str) -> None
        """ Initialize map loader with specific tileset. """
        super().__init__()
        tilesetRaw = self.loadFile(tileset)
        mapsRaw = self.loadFiles("maps", prefix="Map")
        
        self.tiles = self.getTiles(tilesetRaw)
        self.maps = self.getMaps(mapsRaw)
        
    
    def getMapTile(self, tileId):
        # type: (int) -> dict[str, object]
        """ Get tile data, including id, name and rotation. """
        tileBin = bin(tileId)[2:].replace("b", "").zfill(32)
        rotBits = tileBin[0:3]
        
        data = {
            "Id" : int(tileBin[3:], 2),
            "Rotation" : 0,
            "Name" : "",
        }
        
        if rotBits == "101": data["Rotation"] = 90
        elif rotBits == "110": data["Rotation"] = 180
        elif rotBits == "011": data["Rotation"] = 270
        
        if data["Id"] in self.tiles.keys():
            data.update(self.tiles[data["Id"]])
            return data
            
            
    def getTiles(self, tilesetRaw):
        # type: (dict) -> dict
        """ Get formatted tiles from a raw tileset data. """
        tiles = {}
        for tile in tilesetRaw["tiles"]:
            tiles[tile["id"]] = {
                "Name" : Path(tile["image"]).stem,
            }
        return tiles
        
        
    def getMaps(self, mapsRaw):
        # type: (dict) -> dict[str, dict]
        """ Get formatted maps from raw maps data. """
        maps = {}
        
        for map_ in mapsRaw.keys():
            sourceMap = mapsRaw[map_]
            targetMap = {}
            
            for layer in sourceMap["layers"]:
                curLayer = {}
                getSignal = lambda num: 0.5 if num > 0 else -0.5
                offsetX = getSignal(layer.get("offsetx")) if layer.get("offsetx") else 0
                offsetY = getSignal(layer.get("offsety")) if layer.get("offsety") else 0
                
                for y in range(sourceMap["height"]):
                    for x in range(sourceMap["width"]):
                        tileIndex = (y % sourceMap["height"]) * sourceMap["height"] + x
                        curTile = layer["data"][tileIndex] - 1
                        mapTile = self.getMapTile(curTile)
                        if mapTile is not None:
                            curLayer[(x + offsetX, y + offsetY)] = mapTile
                        
                targetMap[layer["name"]] = curLayer
                        
            maps[map_] = targetMap
            
        return maps


class MapSpawner:
    
    def __init__(self, cont):
        # type: (SCA_PythonController) -> None
        """ Map spawner and manager. """
        
        global mapLoader
        self.object = cont.owner
        self.mapLoader = mapLoader
        self.spawnMap()
        
    
    def getMap(self):
        # type: () -> dict[str, object]
        """ Map spawner and manager. """
        if "-" in sys.argv:
            path = Path(sys.argv[-1])
            if path.exists():
                return self.mapLoader.maps[path.stem]
        
        if "Map" in self.object.groupObject and self.object.groupObject["Map"] in self.mapLoader.maps.keys():
            return self.mapLoader.maps[self.object.groupObject["Map"]]
        else:
            for key in self.mapLoader.maps.keys():
                return self.mapLoader.maps[key]
                
    
    def spawnMap(self):
        # type: () -> None
        curMap = self.getMap()
        
        if not "MapObjs" in self.object:
            self.object["MapObjs"] = {}
            
        for layer in curMap.keys():
            
            if not layer in self.object["MapObjs"].keys():
                self.object["MapObjs"][layer] = {}
                
            layerSplit = layer.split(":")
            height = 0
            
            if len(layerSplit) == 2:
                height = literal_eval(layerSplit[1])
                del layerSplit
                
            for coord in curMap[layer].keys():
                curTile = curMap[layer][coord]
                coord3d = coord + tuple([height])
                coord3d = (coord3d[0] * 2, -coord3d[1] * 2, coord3d[2])
                obj = None
                
                if curTile["Name"] == "Player":
                    obj = self.object.scene["Player"] # type: KX_GameObject
                    
                else:
                    obj = self.object.scene.addObject(curTile["Name"]) # type: KX_GameObject
                    
                obj.worldPosition = coord3d
                obj.worldOrientation = [0, 0, radians(-curTile["Rotation"])]
                self.object["MapObjs"][layer][coord] = obj
                
                if curTile["Name"] == "Player":
                    obj.worldPosition.z += 1


def spawner(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    global mapLoader
    
    if always.positive:
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            mapLoader = MapLoader()
            dump(mapLoader.maps)
            print("> Map initializated")
                
        if not "MapSpawner" in own:
            own["MapSpawner"] = MapSpawner(cont)