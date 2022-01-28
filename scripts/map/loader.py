""" This module loads Tiled maps and tilesets from the folder maps and parses 
it to in-game coordinates and other relevant data. """

# Public variables
tileset = {} # type: dict[int, dict[str, object]]
maps = {} # type: dict[str, dict[str, object]]

__tilesetRaw = {} # type: dict[str, object]
__mapsRaw = {} # type: dict[str, dict[str, object]]
__templatesRaw = {} # type: dict[str, dict[str, object]]

TILE_REAL_SIZE = 2 # meters


def load():
    # type: () -> None
    """ Initialize map loader. """
    
    from ..bgf import curPath, loadFile, loadFiles, dump
    
    global __tilesetRaw, __mapsRaw, __templatesRaw, maps, tileset
    __tilesetRaw = loadFile(curPath / "maps/tilesets/Tileset.json")
    __mapsRaw = loadFiles(curPath / "maps/maps", pattern="Map*.json")
    __templatesRaw = loadFiles(curPath / "maps/templates", pattern="*.json")
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
                    if subLayer["type"] == "tilelayer":
                        targetMap[layer["name"] + "/" + subLayer["name"]] = __getTileLayer(subLayer, sourceMap)
                    
                    elif subLayer["type"] == "objectgroup":
                        targetMap[layer["name"] + "/" + subLayer["name"]] = __getObjectLayer(subLayer, sourceMap)
                    
        maps[mapName] = targetMap
        
    return maps


def __getTileLayer(layer, sourceMap):
    # type: (dict[str, object], dict[str, object]) -> dict[tuple, dict[str, object]]
    
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
    layerProps = __getProperties(layer)
    
    for obj in objects:
        
        if obj.get("template"):
            obj = __getObjectFromTemplate(obj)
            
        tilePos = (
            obj["x"] // sourceMap["tilewidth"] * TILE_REAL_SIZE, 
            -obj["y"] // sourceMap["tileheight"] * TILE_REAL_SIZE,
        ) # type: tuple[int]
        
        curObj = {
            "Name": obj["name"],
        }
        
        if offset[0] or offset[1]:
            curObj["Offset"] = offset
        
        objProps = {}
        objProps.update(layerProps)
        objProps.update(__getProperties(obj))
        
        if obj.get("rotation"):
            curObj["Rotation"] = obj["rotation"]
            
        if objProps:
            curObj["Properties"] = objProps
            
        curLayer[tilePos] = curObj
                
    return curLayer


def __getObjectFromTemplate(obj):
    # type: (dict[str, object]) -> dict[str, object]
    
    from pathlib import Path
    from ast import literal_eval
    global __templatesRaw
    
    template = Path(obj["template"]).stem
    templateObj = literal_eval(str(__templatesRaw[template]["object"])) # type: dict[str, object]
    
    for key in templateObj.keys():
        if key not in ("properties", "rotation"):
            obj[key] = templateObj[key]
            
    obj["properties"] = obj.get("properties", [])
    objProps = [prop["name"] for prop in obj.get("properties", [])]
    
    for prop in templateObj.get("properties", []):
        if not prop["name"] in objProps:
            obj["properties"].append(prop)
            
    return obj
        

def __getMapTile(tileId, offset=(0.0, 0.0), properties={}):
    # type: (int, tuple[float], dict[str, object]) -> dict[str, object]
    """ Get tile data, including id, name and rotation. """
    
    global tileset
    
    tileBin = bin(tileId)[2:].replace("b", "").zfill(32)
    rotBits = tileBin[0:3]
    tileId = int(tileBin[3:], 2)
    
    data = {
        "Name" : "",
    }
    
    if offset[0] and offset[1]:
        data["Offset"] = offset
    
    if properties:
        data["Properties"] = properties
    
    # Set tile rotation
    tileRotation = 0
    
    if rotBits == "101":
        tileRotation = 90
    elif rotBits == "110":
        tileRotation = 180
    elif rotBits == "011":
        tileRotation = 270
    
    if tileRotation:
        data["Rotation"] = tileRotation
    
    if tileId in tileset.keys():
        data.update(tileset[tileId])
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

