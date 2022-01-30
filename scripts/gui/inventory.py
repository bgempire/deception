import bge
from bge.types import *
from ..bgf import state


def inventorySlot(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner # type: KX_GameObject
    group = own.groupObject
    always = cont.sensors["Always"] # type: SCA_ISensor
    
    text = own.childrenRecursive.get("ItemQuantity") # type: KX_FontObject
    icon = own.childrenRecursive.get("ItemIcon") # type: KX_GameObject
    
    if always.positive and group and "Slot" in group:
        slot = group["Slot"] # type: int
        inventory = state["Player"]["Inventory"] # type: list[str]
        inventoryExclusive = tuple(set(inventory))
        
        if len(inventoryExclusive) > slot:
            text.text = str(inventory.count(inventoryExclusive[slot]))
            icon.replaceMesh("Item" + inventoryExclusive[slot])
        
        else:
            text.text = ""
            icon.replaceMesh("ItemIcon")

