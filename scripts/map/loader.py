""" This module loads Tiled maps and tilesets from the folder maps and parses 
it to in-game coordinates and other relevant data. """

# Public variables
tileset = {} # type: dict[int, dict[str, object]]
maps = {} # type: dict[str, dict[str, object]]

__tilesetRaw = {} # type: dict[str, object]
__mapsRaw = {} # type: dict[str, dict[str, object]]


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
        tileWidth = sourceMap["tilewidth"]
        tileHeight = sourceMap["tileheight"]
        
        for layer in sourceMap["layers"]:
            curLayer = {}
            offsetX = layer.get("offsetx", 0) / tileWidth
            offsetY = layer.get("offsety", 0) / tileHeight
            mapHeight = sourceMap["height"]
            mapWidth = sourceMap["width"]
            rangeX = range(max(mapWidth, mapHeight))
            rangeY = range(min(mapWidth, mapHeight))
            
            for x in rangeX:
                for y in rangeY:
                    tileIndex = y % mapHeight if mapHeight < mapWidth else y % mapWidth
                    tileIndex =  (x * mapHeight) + tileIndex
                    curTile = layer["data"][tileIndex] - 1
                    
                    if curTile > 0:
                        mapTile = __getMapTile(curTile, (offsetX, offsetY))
                        
                        if mapTile != None:
                            tilePosX = x if mapHeight > mapWidth else y
                            tilePosY = y if mapHeight > mapWidth else x
                            tilePos = (tilePosX, tilePosY)
                                
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

