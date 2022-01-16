import bge
from bge.types import *


def tile(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner # type: KX_GameObject
    always = cont.sensors[0] # type: SCA_AlwaysSensor
    
    if always.positive:
        if own.groupObject and "Type" in own.groupObject:
            
            try:
                meshName = own["Name"] + str(own.groupObject["Type"]) # type: str
                own.replaceMesh(meshName, True, True)
            except Exception as e:
                print("X Invalid name:", own.groupObject["Type"], e)