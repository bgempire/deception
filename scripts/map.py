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
    return bge.logic.getClockTime()


def getMapPosition(obj):
    # type: (KX_GameObject) -> tuple[int]
    
    return (
        int(((obj.worldPosition.x // 10) * 10 // 2) + 5), 
        -int(((obj.worldPosition.y // 10) * 10 // 2) + 5), 
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
        
    
    def getMapTile(self, tileId, offset=(0.0, 0.0)):
        # type: (int, tuple[float]) -> dict[str, object]
        """ Get tile data, including id, name and rotation. """
        tileBin = bin(tileId)[2:].replace("b", "").zfill(32)
        rotBits = tileBin[0:3]
        
        data = {
            "Id" : int(tileBin[3:], 2),
            "Rotation" : 0,
            "Name" : "",
            "Offset": offset
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
            tileWidth = sourceMap["tilewidth"]
            tileHeight = sourceMap["tileheight"]
            
            for layer in sourceMap["layers"]:
                curLayer = {}
                offsetX = layer.get("offsetx", 0) / tileWidth
                offsetY = layer.get("offsety", 0) / tileHeight
                rangeX = range(max(sourceMap["width"], sourceMap["height"]))
                rangeY = range(min(sourceMap["width"], sourceMap["height"]))
                
                for x in rangeX:
                    for y in rangeY:
                        tileIndex = (y % sourceMap["height"]) * sourceMap["height"] + x
                        curTile = layer["data"][tileIndex] - 1
                        
                        if curTile:
                            mapTile = self.getMapTile(curTile, (offsetX, offsetY))
                            
                            if mapTile != None:
                                curLayer[(x, y)] = mapTile
                        
                targetMap[layer["name"]] = curLayer
                        
            maps[map_] = targetMap
            
        return maps


class MapSpawner:
    
    def __init__(self, cont):
        # type: (SCA_PythonController) -> None
        """ Map spawner and manager. """
        
        global mapLoader
        self.playerSet = False
        self.object = cont.owner
        self.mapLoader = mapLoader
        self.lastPosition = None
        self.curMap = self.__getMap()
        
    
    @staticmethod
    def __getHeightFromLayer(layer):
        # type: (str) -> int
        
        layerSplit = layer.split(":")
        
        if len(layerSplit) == 2:
            return literal_eval(layerSplit[1])
        else:
            return 0
    
        
    @staticmethod
    def __isPositionBetween(curPos, tilePos):
        # type: (tuple[int], tuple[int]) -> int
        
        return curPos[0] - MAP_RADIUS <= tilePos[0] <= curPos[0] + MAP_RADIUS \
            and curPos[1] - MAP_RADIUS <= tilePos[1] <= curPos[1] + MAP_RADIUS
    
    
    def __getMap(self):
        # type: () -> dict[str, dict[tuple, dict]]
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
                
    
    def despawnMap(self, curPos, all=False):
        # type: (list[int], bool) -> None
        
        mapObjs = self.object["MapObjs"] # type: dict[str, dict[tuple, KX_GameObject]]
        print('run despawnMap', getTime())
        
        for layer in mapObjs.keys():
            for coord in list(mapObjs[layer].keys()):
                if all or not self.__isPositionBetween(curPos, coord):
                    mapObjs[layer][coord].endObject()
                    del mapObjs[layer][coord]
    
    
    def spawnMap(self, curPos, all=False):
        # type: (list[int], bool) -> None
        
        if curPos != self.lastPosition:
            curMap = self.curMap
            
            if not "MapObjs" in self.object:
                self.object["MapObjs"] = {}
                
            mapObjs = self.object["MapObjs"] # type: dict[str, dict[tuple, KX_GameObject]]
            self.despawnMap(curPos, all=all)
            self.spawnActors(curPos, all=all)
                
            for layer in curMap.keys():
                
                if layer.lower().startswith("actor"):
                    continue
                
                height = self.__getHeightFromLayer(layer)
                
                if not layer in mapObjs.keys():
                    mapObjs[layer] = {}
                    
                for coord in curMap[layer].keys():
                    curTile = curMap[layer][coord]
                    
                    if all or self.__isPositionBetween(curPos, coord):
                        coord3d = coord + tuple([height])
                        coord3d = (coord3d[0] * 2, -coord3d[1] * 2, coord3d[2])
                        obj = self.object.scene.addObject(curTile["Name"]) # type: KX_GameObject
                        obj.worldPosition = coord3d
                        obj.worldPosition.x += curTile["Offset"][0] * 2
                        obj.worldPosition.y += -curTile["Offset"][1] * 2
                        obj.worldOrientation = [0, 0, radians(-curTile["Rotation"])]
                        mapObjs[layer][coord] = obj
                        
            self.lastPosition = curPos
            print('run spawnMap', getTime())
    
    
    def spawnActors(self, curPos, all=False):
        # type: (list[int], bool) -> None
        curMap = self.curMap
        
        if not "MapActors" in self.object:
            self.object["MapActors"] = {}
            
        mapActors = self.object["MapActors"] # type: dict[str, dict[tuple, KX_GameObject]]
        
        for layer in curMap.keys():
            
            if not layer.lower().startswith("actor"):
                continue
            
            height = self.__getHeightFromLayer(layer)
            
            if not layer in mapActors.keys():
                mapActors[layer] = {}
                
            for coord in curMap[layer].keys():
                curTile = curMap[layer][coord]
                
                if all or self.__isPositionBetween(curPos, coord):
                    coord3d = coord + tuple([height])
                    coord3d = (coord3d[0] * 2, -coord3d[1] * 2, coord3d[2])
                    setPlayer = curTile["Name"] == "Player" and not self.playerSet
                    
                    if setPlayer:
                        obj = self.object.scene["Player"] # type: KX_GameObject
                        obj.worldPosition = coord3d
                        obj.worldOrientation = [0, 0, radians(-curTile["Rotation"])]
                        obj.worldPosition.z += 1
                        obj.scene["MapPosition"] = getMapPosition(obj)
                        self.playerSet = True
                        
                    elif curTile["Name"] != "Player":
                        obj = self.object.scene.addObject(curTile["Name"]) # type: KX_GameObject
                        obj.worldPosition = coord3d
                        obj.worldOrientation = [0, 0, radians(-curTile["Rotation"])]
                        mapActors[layer][coord] = obj
            
        print('run spawnActors', getTime())


def spawner(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    global mapLoader
    spawnAll = 1
    
    if always.positive:
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            mapLoader = MapLoader()
            dump(mapLoader.maps)
            print("> Map initializated")
            
        if "MapPosition" in own.scene:
            
            if not "MapSpawner" in own:
                own["MapSpawner"] = mapSpawner = MapSpawner(cont)
                mapSpawner.spawnMap(own.scene["MapPosition"], all=spawnAll)
                
            if "MapSpawner" in own:
                mapSpawner = own["MapSpawner"] # type: MapSpawner