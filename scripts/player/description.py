import bge
from bge.types import *


DESCRIPTION_TIME_ON_SCREEN = 3.0 # seconds


def description(cont):
    # type: (SCA_PythonController) -> None
    
    from ..bgf import state, _
    
    own = cont.owner # type: KX_GameObject
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    message = cont.sensors["Message"] # type: KX_NetworkMessageSensor
    itemToLower = lambda name: name[0].lower() + name[1:] # type: (str) -> str
    
    if always.positive:
        if state["UseDescription"] and own["Timer"] >= 0:
            state["UseDescription"] = ""
    
    if message.positive:
        own["Timer"] = -DESCRIPTION_TIME_ON_SCREEN
        body = message.bodies[0].split(",")
        
        if body[0] == "ContainerTake":
            itemName, pronoun = _getItemAndPronoun(body[1], pronoun="A")
            state["UseDescription"] = _(body[0]).format(pronoun, itemToLower(itemName))
        
        elif body[0] == "ContainerTaken":
            state["UseDescription"] = _(body[0])
        
        elif body[0] == "ContainerEmpty":
            state["UseDescription"] = _(body[0])
        
        elif body[0] == "DoorLocked":
            state["UseDescription"] = _(body[0])
        
        elif body[0] == "DoorUnlocked":
            itemName, pronoun = _getItemAndPronoun(body[1], pronoun="The")
            state["UseDescription"] = _(body[0]).format(pronoun, itemToLower(itemName))
            
            
def _getItemAndPronoun(item, pronoun="The"):
    # type(str, str) -> tuple[str]
    
    from ..bgf import database, _
    
    items = database["Items"] # type: dict[str, dict[str, object]]
    
    if item in items.keys():
        curItem = items[item]
        return (_("Item" + item), _(pronoun + curItem["Pronoum"]))

