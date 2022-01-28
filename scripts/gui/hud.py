import bge
from bge.types import *
from ..bgf import state


HUD_OPACITY_BASE = 0.75
HUD_OPACITY_BAR = 0.5


def flashlight(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner # type: KX_GameObject
    always = cont.sensors["Always"] # type: SCA_ISensor
    
    if always.positive:
        flashlightBase = own.childrenRecursive.get("FlashlightBase") # type: KX_GameObject
        flashlightBattery = own.childrenRecursive.get("FlashlightBattery") # type: KX_GameObject
        flashlightOn = own.childrenRecursive.get("FlashlightOn") # type: KX_GameObject
        opacity = state["Player"]["FlashlightOn"] / 2 if state["Player"]["FlashlightBattery"] > 0 else 0.0
        frame = state["Player"]["FlashlightBattery"] * 100
        
        flashlightBase.color[3] = HUD_OPACITY_BASE if opacity else HUD_OPACITY_BASE / 2
        flashlightBattery.color[3] = opacity if opacity else HUD_OPACITY_BAR / 2
        flashlightOn.color[3] = opacity
        flashlightBattery.playAction("FlashlightBattery", frame, frame)


def stamina(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner # type: KX_GameObject
    always = cont.sensors["Always"] # type: SCA_ISensor
    
    if always.positive:
        staminaBase = own.childrenRecursive.get("StaminaBase") # type: KX_GameObject
        staminaBar = own.childrenRecursive.get("Stamina") # type: KX_GameObject
        showBar = state["Player"]["Stamina"] < 1
        frame = state["Player"]["Stamina"] * 100
        
        staminaBase.color[3] = HUD_OPACITY_BASE if showBar else 0.0
        staminaBar.color[3] = HUD_OPACITY_BAR if showBar else 0.0
        staminaBar.playAction("Stamina", frame, frame)

