import bge
import aud
from bge.types import *


DEBUG = 0


def door(cont):
    # type: (SCA_PythonController) -> None
    """ Generic behavior of any door. """

    own = cont.owner # type: Door
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor

    if always.positive:

        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            own = Door(own, cont)

        own.update()


class Door(KX_GameObject):
    DOOR_SPEED = 0.6
    DOOR_UPDATE_SPEED = 10 # skipped ticks
    ANIMS = {
        "Open1": (0, 20, bge.logic.KX_ACTION_MODE_PLAY),
        "Close1": (20, 0, bge.logic.KX_ACTION_MODE_PLAY),
        "Open2": (30, 50, bge.logic.KX_ACTION_MODE_PLAY),
        "Close2": (50, 30, bge.logic.KX_ACTION_MODE_PLAY),
    }
    DEFAULT_PROPS = {
        "Direction": 1,
        "Key": "",
        "Locked": False,
        "Opened": False,
        "Sound": None,
        "Speed": "Normal",
        "Use": False,
    }

    def __init__(self, obj, cont):
        # type: (KX_GameObject, SCA_PythonController) -> None

        from .helper import getEventFromMap

        self.currentController = cont # type: SCA_PythonController

        for prop in self.DEFAULT_PROPS.keys():
            self[prop] = self.DEFAULT_PROPS[prop]
            if DEBUG: self.addDebugProperty(prop)

        getEventFromMap(cont, DEBUG)

        # Start opened according to state
        if self["Opened"]:
            animName = self.__getAnimName()
            curAnim = self.ANIMS[animName]
            self.playAction("Door", curAnim[0], curAnim[0], play_mode=curAnim[2], speed=self.DOOR_SPEED)


    def update(self):
        # type: () -> None

        always = self.currentController.sensors["Always"] # type: SCA_AlwaysSensor

        if self.isPlayingAction():
            always.skippedTicks = 0
            self["Use"] = False

            # Play close sound
            if not self["Opened"]:
                frame = self.getActionFrame()

                if (0 <= frame <= 2 or 30 <= frame <= 32) \
                and (not self["Sound"] or self["Sound"].status == aud.AUD_STATUS_INVALID):
                    self.__playSound("Close")

        else:
            always.skippedTicks = self.DOOR_UPDATE_SPEED

        # Process door use
        if self["Use"]:
            self.__use()


    def __use(self):
        # type: () -> None

        from ..bgf import state
        from .helper import addToState

        animName = self.__getAnimName()
        curAnim = self.ANIMS[animName]
        animSpeed = 1.5 if self["Speed"] == "Run" else 1.0 if self["Speed"] == "Normal" else 0.6

        inventory = state["Player"]["Inventory"] # type: list[str]
        canUnlock = self["Locked"] and self["Key"] in inventory

        self["Use"] = False

        if not self["Locked"] or canUnlock:

            # Unlock door and remove key from inventory
            if canUnlock:
                self["Locked"] = False
                inventory.remove(self["Key"])
                self.sendMessage("UpdateDescription", ",".join(["DoorUnlocked", self["Key"]]))
                self.__playSound("Unlocked")

            else:
                # Play open sound
                if not self["Opened"]:
                    self.__playSound("Open")

                self["Opened"] = not self["Opened"]
                self.playAction("Door", curAnim[0], curAnim[1], play_mode=curAnim[2], speed=self.DOOR_SPEED * animSpeed)

            # Add door to state
            addToState(self.currentController, props=["Locked", "Opened", "Direction"])

        else:
            self.__playSound("Locked")
            self.sendMessage("UpdateDescription", ",".join(["DoorLocked"]))


    def __playSound(self, doorAction):
        # type: (str) -> aud.Handle

        from ..bgf import playSound

        soundVolume = 1.0 if self["Speed"] == "Run" else 0.5 if self["Speed"] == "Normal" else 0.2
        soundPitch = 1.0 if self["Speed"] == "Run" else 0.85 if self["Speed"] == "Normal" else 0.7

        handle = self["Sound"] = playSound("Door" + self["Type"] + doorAction, self.parent)
        handle.volume *= soundVolume
        handle.pitch *= soundPitch

        return handle


    def __getAnimName(self):
        # type: () -> str

        return ("Open" if not self["Opened"] else "Close") + str(self["Direction"])

