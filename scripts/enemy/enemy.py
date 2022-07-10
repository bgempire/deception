import bge
from bge.types import *


def enemy(cont):
    # type: (SCA_PythonController) -> None

    own = cont.owner # type: Enemy
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor

    if always.positive:

        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            own = Enemy(own, cont)

        own.update()


class Enemy(KX_GameObject):

    def __init__(self, obj, cont):
        # type: (KX_GameObject, SCA_PythonController) -> None

        self.currentController = cont # type: SCA_PythonController
        """The current controller of the enemy."""


    def update(self):
        # type: () -> None

        pass
