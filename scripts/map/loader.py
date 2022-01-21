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
    
    for map_ in __mapsRaw.keys():
        sourceMap = __mapsRaw[map_]
        targetMap = {}
        
        for layer in sourceMap["layers"]:
            layer = layer # type: dict[str, object]
            curLayer = {} # type: dict[tuple[int], dict[str, object]]
            offset = (
                layer.get("offsetx", 0) / sourceMap["tilewidth"] * TILE_REAL_SIZE, 
                layer.get("offsety", 0) / sourceMap["tileheight"] * TILE_REAL_SIZE,
            ) # type: tuple[float]
            mapHeight = sourceMap["height"] # type: int
            mapWidth = sourceMap["width"] # type: int
            
            for y in range(mapWidth):
                for x in range(mapHeight):
                    tileIndex =  (y * mapHeight) + (x % mapWidth)
                    curTile = layer["data"][tileIndex] - 1
                    
                    if curTile > 0:
                        mapTile = __getMapTile(curTile, offset)
                        
                        if mapTile != None:
                            tilePos = (x * TILE_REAL_SIZE, -y * TILE_REAL_SIZE)
                            curLayer[tilePos] = mapTile
                            
            targetMap[layer["name"]] = curLayer
                    
        maps[map_] = targetMap
        
    return maps


def __getMapTile(tileId, offset=(0.0, 0.0)):
    # type: (int, tuple[float]) -> dict[str, object]
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

