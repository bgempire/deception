import bge
from bge.types import *


def door(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            pass