import bge
from bge.types import *


def enemy(cont):
    # type: (SCA_PythonController) -> None
    
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            __init(cont)
            
        # TODO


def __init(cont):
    # type: (SCA_PythonController) -> None
    
    pass