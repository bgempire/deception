""" This module loads Tiled maps and tilesets from the folder maps and parses 
it to in-game coordinates and other relevant data. """

# Public variables
tileset = {} # type: dict[int, dict[str, object]]
maps = {} # type: dict[str, dict[str, object]]

__tilesetRaw = {} # type: dict[str, object]
__mapsRaw = {} # type: dict[str, dict[str, object]]

TILE_REAL_SIZE = 2 # meters


def load():
    # type: () -> None
    """ Initialize map loader. """
    
    from ..bgf import curPath, loadFile, loadFiles
    
    global __tilesetRaw, __mapsRaw, maps, tileset
    __tilesetRaw = loadFile(curPath / "maps/Tileset.json")
    __mapsRaw = loadFiles(curPath / "maps", pattern="Map*.json")
    tileset = __getTileset()
    maps = __getMaps()


def __getMaps():
    # type: () -> dict
    """ Get formatted maps from raw maps data. """
    
    global __mapsRaw
    maps = {}
    
    for mapName in __mapsRaw.keys():
        sourceMap = __mapsRaw[mapName]
        targetMap = {}
        
        for layer in sourceMap["layers"]:
            
            if layer["type"] == "tilelayer":
                targetMap[layer["name"]] = __getTileLayer(layer, sourceMap)
            
            elif layer["type"] == "objectgroup":
                targetMap[layer["name"]] = __getObjectLayer(layer, sourceMap)
                
            elif layer["type"] == "group":
                for subLayer in layer["layers"]:
                    if layer["type"] == "tilelayer":
                        targetMap[layer["name"] + "/" + subLayer["name"]] = __getTileLayer(subLayer, sourceMap)
                    
                    if layer["type"] == "objectgroup":
                        targetMap[layer["name"] + "/" + subLayer["name"]] = __getObjectLayer(subLayer, sourceMap)
                    
        maps[mapName] = targetMap
        
    return maps


def __getTileLayer(layer, sourceMap):
    # type: (dict[str, object], dict[str, object]) -> dict[tuple, dict[str, object]]
    
    layer = layer # type: dict[str, object]
    curLayer = {} # type: dict[tuple[int], dict[str, object]]
    offset = (
        layer.get("offsetx", 0) / sourceMap["tilewidth"] * TILE_REAL_SIZE, 
        layer.get("offsety", 0) / sourceMap["tileheight"] * TILE_REAL_SIZE,
    ) # type: tuple[float]
    mapHeight = sourceMap["height"] # type: int
    mapWidth = sourceMap["width"] # type: int
    properties = __getProperties(layer)
    
    for tileIndex in range(mapWidth * mapHeight):
        x = tileIndex % mapWidth
        y = tileIndex // mapWidth
        curTile = layer["data"][tileIndex] - 1
        
        if curTile > 0:
            mapTile = __getMapTile(curTile, offset, properties=properties)
            
            if mapTile != None:
                tilePos = (x * TILE_REAL_SIZE, -y * TILE_REAL_SIZE)
                curLayer[tilePos] = mapTile
                
    return curLayer


def __getObjectLayer(layer, sourceMap):
    # type: (dict[str, object], dict[str, object]) -> dict[tuple, dict[str, object]]
    
    layer = layer # type: dict[str, object]
    curLayer = {} # type: dict[tuple[int], dict[str, object]]
    offset = (
        layer.get("offsetx", 0) / sourceMap["tilewidth"] * TILE_REAL_SIZE, 
        layer.get("offsety", 0) / sourceMap["tileheight"] * TILE_REAL_SIZE,
    ) # type: tuple[float]
    objects = layer["objects"] # type: list[dict[str, object]]
    properties = __getProperties(layer)
    
    for obj in objects:
        tilePos = (obj["x"] // sourceMap["tilewidth"], obj["y"] // sourceMap["tileheight"]) # type: tuple[int]
        curObj = {
            "Id": obj["id"],
            "Name": obj["name"],
            "Rotation": obj["rotation"],
            "Offset": offset,
        }
        curObj.update(properties)
        curObj.update(__getProperties(obj))
        curLayer[tilePos] = curObj
                
    return curLayer


def __getMapTile(tileId, offset=(0.0, 0.0), properties={}):
    # type: (int, tuple[float], dict[str, object]) -> dict[str, object]
    """ Get tile data, including id, name and rotation. """
    
    global tileset
    
    tileBin = bin(tileId)[2:].replace("b", "").zfill(32)
    rotBits = tileBin[0:3]
    
    data = {
        "Id" : int(tileBin[3:], 2),
        "Rotation" : 0,
        "Name" : "",
        "Offset": offset
    }
    data.update(properties)
    
    if rotBits == "101": data["Rotation"] = 90
    elif rotBits == "110": data["Rotation"] = 180
    elif rotBits == "011": data["Rotation"] = 270
    
    if data["Id"] in tileset.keys():
        data.update(tileset[data["Id"]])
        return data


def __getTileset():
    # type: () -> dict
    """ Get formatted tiles from raw tileset data. """
    
    from pathlib import Path
    
    global __tilesetRaw
    tileset = {}
    
    for tile in __tilesetRaw["tiles"]:
        tileset[tile["id"]] = {
            "Name" : Path(tile["image"]).stem,
        }
        
    return tileset


def __getProperties(obj):
    # type: (dict[str, object]) -> dict[str, object]
    
    properties = {} # type: dict[str, object]
    propertiesRaw = obj.get("properties") # type: list[dict[str, object]]
    
    if propertiesRaw:
        for prop in propertiesRaw:
            if prop["type"] == "color":
                properties[prop["name"]] = __colorHexToRgba(prop["value"])
            else:
                properties[prop["name"]] = prop["value"]
                
    if obj.get("tintcolor"):
        properties["Color"] = __colorHexToRgba(obj["tintcolor"])
            
    return properties


def __colorHexToRgba(colorHex):
    # type: (str) -> tuple[float]
    """ Convert hex color to RGA tuple (#ff00ff00 -> (1.0, 0.0, 1.0, 0.0)). """
    
    colorHex = colorHex.lstrip("#")
    
    if len(colorHex) == 6:
        colorHex = "ff" + colorHex
        
    value = list(int(colorHex[i:i+2], 16) / 255 for i in (0, 2, 4, 6))
    value = [round(i, 3) for i in value]
    return (value[1], value[2], value[3], value[0])

