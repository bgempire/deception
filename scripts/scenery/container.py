import bge
from bge.types import *


DEBUG = 0


def container(cont):
    # type: (SCA_PythonController) -> None
    """ Generic behavior for any item container such as drawers, closets, boxes, etc. """

    own = cont.owner # type: Container
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor

    if always.positive:

        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            own = Container(own, cont)

        own.update()


class Container(KX_GameObject):
    DEFAULT_PROPS = {
        "Item": "",
        "Taken": False,
        "Use": False,
    }

    def __init__(self, obj, cont):
        # type: (KX_GameObject, SCA_PythonController) -> None

        from .helper import getEventFromMap

        self.currentController = cont # type: SCA_PythonController

        for prop in self.DEFAULT_PROPS.keys():
            self[prop] = self.DEFAULT_PROPS[prop]
            if DEBUG: self.addDebugProperty(prop)

        getEventFromMap(self.currentController, DEBUG)


    def update(self):
        # type: () -> None

        if self["Use"]:
            self.__use()


    def __use(self):
        # type: () -> None

        from .helper import addToState
        from ..bgf import state, database, playSound

        self["Use"] = False

        if self["Item"] and not self.get("Empty"):
            if not self["Taken"]:
                items = database["Items"] # type: dict[str, dict[str, object]]
                sound = items.get(self["Item"], {}).get("Sound", 1)

                self["Sound"] = playSound("ItemPickup" + str(sound), self.parent)

                # Add item to player's inventory
                state["Player"]["Inventory"].append(self["Item"])
                state["Player"]["Inventory"].sort()
                self["Taken"] = True

                # Add container to state
                addToState(self.currentController, props=["Taken", "Item"])
                self.sendMessage("UpdateDescription", ",".join(["ContainerTake", self["Item"]]))

            else:
                self.sendMessage("UpdateDescription", ",".join(["ContainerTaken", self["Item"]]))

        else:
            self.sendMessage("UpdateDescription", ",".join(["ContainerEmpty"]))
