import bge
from bge.types import *
from ..bgf import config, state, database, isKeyPressed, playSound
from ..bgf.operators import showMouseCursor
from mathutils import Vector


DEBUG = 0


def player(cont):
    # type: (SCA_PythonController) -> None

    own = cont.owner # type: Player
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor

    if always.positive:

        # Inicializar subclasse do jogador
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            own = Player(own, cont)

        # Rodar lógica do jogador
        own.update()


class Player(KX_GameObject):
    TIMER_INCREMENT = 1 / 60
    MOVE_SPEED_FACTOR = 2.0
    MOVE_RUN_MULTIPLIER = 2.2
    MOVE_CROUCH_MULTIPLIER = 0.55
    MOVE_STAMINA_DRAIN = 0.00075
    MOVE_STAMINA_RUN_BIAS = 0.05
    MOVE_STAMINA_TIRED_BIAS = 0.4
    MOUSE_LOOK_BIAS = 0.0006
    INVENTORY_TOGGLE_INTERVAL = 1.4 # seconds
    FLASHLIGHT_MOVE_SMOOTH = 15.0
    FLASHLIGHT_MAX_ENERGY = 2.0
    FLASHLIGHT_MAX_DISTANCE = 20.0
    FLASHLIGHT_BATTERY_DRAIN = 0.0001 # Default: 0.0001
    SOUND_STEPS_INTERVAL = 0.65 # seconds
    USE_DISTANCE = 2.0 # meters
    DEFAULT_PROPS = {
        "Crouch": False,
        "FlashlightClick": False,
        "Ground": "",
        "MoveH": 0,
        "MoveV": 0,
        "Run": False,
        "TimerSteps": 0.0,
        "TimerInventory": -INVENTORY_TOGGLE_INTERVAL,
        "OnInventory": False,
    }


    def __init__(self, obj, cont):
        # type: (KX_GameObject, SCA_PythonController) -> None

        # Criar atributos personalizados no objeto
        self.currentController = cont # type: SCA_PythonController
        """The current controller of the player."""

        # Definir câmera ativa do jogador
        self.scene.active_camera = self.childrenRecursive.get("PlayerCamera")

        # Armazenar referência ao jogador como propriedade da cena
        self.scene["Player"] = self

        global DEBUG
        DEBUG = True if self.groupObject.get("Debug") or self.get("Debug") else DEBUG

        # Criar propriedades personalizadas do jogador
        for key in self.DEFAULT_PROPS.keys():
            self[key] = self.DEFAULT_PROPS[key]
            if DEBUG: self.addDebugProperty(key, True)

        # Aumenta luz do ambiente caso debug estiver ativado
        if DEBUG:
            light = self.scene.objects.get("Hemi") # type: KX_LightObject
            if light:
                light.energy = 0.5


    def update(self):
        self["TimerInventory"] += self.TIMER_INCREMENT

        self.__inputManager()
        self.__messageManager()
        self.__mouseLook()
        self.__move()
        self.__flashlight()
        self.__sound()


    def __inputManager(self):
        # type: () -> None

        player = state["Player"]

        # Teclas pressionadas
        isUp = isKeyPressed(config["KeyUp"])
        isDown = isKeyPressed(config["KeyDown"])
        isLeft = isKeyPressed(config["KeyLeft"])
        isRight = isKeyPressed(config["KeyRight"])
        isRun = isKeyPressed(config["KeyRun"])
        isCrouch = isKeyPressed(config["KeyCrouch"])
        isFlashlight = isKeyPressed(config["KeyFlashlight"], status=1)
        isUse = isKeyPressed(config["KeyUse"], status=1)
        isInventory = isKeyPressed(config["KeyInventory"], status=1)

        # Ativar inventário
        if isInventory and self["TimerInventory"] >=0:
            self["OnInventory"] = not self["OnInventory"]
            self["TimerInventory"] = -self.INVENTORY_TOGGLE_INTERVAL
            camPos = "[50, 0]" if self["OnInventory"] else "[0, 0]"
            self.sendMessage("UpdateGui", camPos)

        # Ligar e desligar lanterna
        if isFlashlight:
            player["FlashlightOn"] = 2 if player["FlashlightOn"] == 0 else player["FlashlightOn"] - 1
            self["FlashlightClick"] = True

        # Controles caso inventário esteja fechado
        if not self["OnInventory"]:
            self["Run"] = bool(isRun) if not isCrouch else False
            self["Crouch"] = bool(isCrouch) if not isRun else False

            # Usar objeto focado
            if isUse:
                self.__use()

            # Movimento vertical
            if isUp and not isDown:
                self["MoveV"] = 1

            elif not isUp and isDown:
                self["MoveV"] = -1

            else:
                self["MoveV"] = 0

            # Movimento horizontal
            if isRight and not isLeft:
                self["MoveH"] = 1

            elif not isRight and isLeft:
                self["MoveH"] = -1

            else:
                self["MoveH"] = 0

        # Controles caso inventário esteja aberto
        else:
            self["MoveH"] = 0
            self["MoveV"] = 0
            self["Run"] = False
            self["Crouch"] = False


    def __flashlight(self):
        # type: () -> None

        from random import randint

        player = state["Player"]
        flashlight = self.childrenRecursive.get("Flashlight") # type: KX_LightObject

        if flashlight:
            # Alterar suavidade do movimento da lanterna
            flashlight.timeOffset = self.FLASHLIGHT_MOVE_SMOOTH

            # Lanterna ligada
            if player["FlashlightOn"]:
                flashlightForce = player["FlashlightOn"] if player["FlashlightOn"] == 2 else 0.5
                flashlightDistance = 1 if player["FlashlightOn"] == 2 else 0.01

                # Drenar bateria da lanterna
                if player["FlashlightBattery"] > 0:
                    player["FlashlightBattery"] -= self.FLASHLIGHT_BATTERY_DRAIN * flashlightForce
                else:
                    player["FlashlightBattery"] = 0.0

                # Definir intensidade da lanterna (ou piscar aleatóriamente caso bateria baixa)
                if 0 < player["FlashlightBattery"] < 0.3 and randint(0, 100) < 10 or player["FlashlightBattery"] == 0:
                    flashlight.energy = 0.0
                else:
                    flashlight.energy = self.FLASHLIGHT_MAX_ENERGY * flashlightForce

                # Definir distância de alcance da lanterna
                flashlight.distance = self.FLASHLIGHT_MAX_DISTANCE * flashlightDistance

            # Lanterna desligada
            else:
                flashlight.energy = 0.0


    def __messageManager(self):
        # type: () -> None

        message = self.currentController.sensors["Message"] # type: KX_NetworkMessageSensor

        if message.positive:
            for i in range(len(message.subjects)):
                subject = message.subjects[i]
                body = message.bodies[i]

                # Usar item
                if subject == "UseItem" and body:
                    inventory = state["Player"]["Inventory"] # type: list[str]
                    item = database["Items"].get(body) # type: dict[str, object]

                    # Usar item caso este seja usável
                    if item and item["Usable"]:
                        inventory.remove(body)
                        playSound("ItemPickup" + str(item["Sound"]))

                        # Executar comando do item usado
                        if item.get("Command"):
                            exec(item["Command"])


    def __mouseToCenter(self):
        windowSize = Vector((bge.render.getWindowWidth(), bge.render.getWindowHeight()))
        windowCenter = Vector((windowSize.x // 2, windowSize.y // 2))
        bge.render.setMousePosition(int(windowCenter.x), int(windowCenter.y))


    def __mouseLook(self):
        # type: () -> None

        from math import radians, degrees

        # Mostrar cursor do mouse caso inventário esteja aberto
        if self["OnInventory"]:
            showMouseCursor(self.currentController, arg="True")

        # Ativar mouse look caso inventário esteja fechado
        elif not self["OnInventory"]:

            # Esconder cursor do mouse
            showMouseCursor(self.currentController, arg="False")

            if self["TimerInventory"] >= -self.INVENTORY_TOGGLE_INTERVAL + 0.1:
                AXIS_ANGLE_LIMIT = 89.999999
                axis = self.childrenRecursive.get("CameraAxis") # type: KX_Camera
                camRot = axis.localOrientation.to_euler()
                sensitivity = config["MouseSensitivity"] # type: float

                # Corrigir eixo rotacionando além dos limites
                if degrees(camRot.x) <= -90 or degrees(camRot.x) >= 90:
                    getSignal = lambda val: 1 if val >= 0 else -1
                    camRot = axis.localOrientation.to_euler()
                    camRot.x = radians(AXIS_ANGLE_LIMIT * getSignal(degrees(camRot.x)))
                    axis.localOrientation = camRot

                # Variáveis de suporte
                windowSize = Vector((bge.render.getWindowWidth(), bge.render.getWindowHeight()))
                windowCenter = Vector((windowSize.x // 2, windowSize.y // 2))
                mousePos = Vector((bge.logic.mouse.position[0] * windowSize[0], bge.logic.mouse.position[1] * windowSize[1]))
                centerOffset = (windowCenter - mousePos) * 0.001 # type: Vector

                # Rotacionar jogador no eixo X
                if (centerOffset.x < -self.MOUSE_LOOK_BIAS or centerOffset.x > self.MOUSE_LOOK_BIAS):
                    self.applyRotation((0, 0, centerOffset[0] * sensitivity))

                # Rotacionar jogador no eixo Y
                if (centerOffset.y < -self.MOUSE_LOOK_BIAS or centerOffset.y > self.MOUSE_LOOK_BIAS):
                    if -AXIS_ANGLE_LIMIT < degrees(camRot.x) < AXIS_ANGLE_LIMIT:
                        axis.applyRotation((-centerOffset.y * sensitivity, 0, 0), True)

                self.__mouseToCenter()

            else:
                self.__mouseToCenter()


    def __move(self):
        # type: () -> None
        player = state["Player"]

        moveFactor = self.MOVE_RUN_MULTIPLIER \
            if self["Run"] and player["Stamina"] > self.MOVE_STAMINA_RUN_BIAS \
            else self.MOVE_CROUCH_MULTIPLIER if self["Crouch"] else 1.0

        moveVector = Vector([-self["MoveH"], -self["MoveV"], 0]).normalized() * self.MOVE_SPEED_FACTOR * moveFactor

        onGround = self.rayCast(self.worldPosition + Vector([0, 0, -1]), self, 1)

        # Corrigir gravidade caso esteja no chão
        if not onGround[0]:
            moveVector.z = self.localLinearVelocity.z
            self["Ground"] = ""

        elif "Ground" in onGround[0]:
            self["Ground"] = onGround[0]["Ground"]

        else:
            self["Ground"] = ""

        # Mover jogador
        self.localLinearVelocity = moveVector

        isMoving = self["MoveH"] or self["MoveV"]

        # Drenar stamina enquanto corre
        if isMoving and self["Run"] and player["Stamina"] > 0:
            player["Stamina"] -= self.MOVE_STAMINA_DRAIN

        # Recuperar stamina enquanto anda
        elif isMoving and player["Stamina"] < 1:
            player["Stamina"] += self.MOVE_STAMINA_DRAIN

        # Recuperar stamina rápido enquanto estiver parado
        elif not isMoving and player["Stamina"] < 1:
            player["Stamina"] += self.MOVE_STAMINA_DRAIN * 2


    def __sound(self):
        # type: () -> None

        import aud
        from random import choice, randint

        player = state["Player"]

        self["TimerSteps"] += self.TIMER_INCREMENT

        # Tocar clique da lanterna
        if self["FlashlightClick"]:
            playSound("FlashlightClick", self)
            self["FlashlightClick"] = False

        # Respiração caso stamina esteja baixa
        if player["Stamina"] <= self.MOVE_STAMINA_TIRED_BIAS:
            if not "Panting" in self or self["Panting"] and self["Panting"].status == aud.AUD_STATUS_INVALID:
                handle = playSound("VoiceFemalePanting1")
                handle.volume *= 0.25
                self["Panting"] = handle

        # Sons de movimento
        if (self["MoveH"] or self["MoveV"]):

            # Passos
            if self["TimerSteps"] >= 0 and self["Ground"]:
                moveFactor = 1.8 if self["Run"] and player["Stamina"] > self.MOVE_STAMINA_RUN_BIAS \
                    else 0.65 if self["Crouch"] else 1

                self["TimerSteps"] = -self.SOUND_STEPS_INTERVAL / moveFactor

                soundName = "Step"
                soundName += "Run" if self["Run"] else "Walk"
                soundName += self["Ground"]
                soundName += str(choice((1, 2)))

                handle = playSound(soundName, self)
                handle.pitch = 1 + (1 / randint(8, 15) * choice((-1, 1)))
                handle.volume *= 1 if self["Run"] else 0.06 if self["Crouch"] else 0.3


    def __use(self):
        # type: () -> None

        camera = self.scene.active_camera
        hitObject = camera.getScreenRay(0.5, 0.5, self.USE_DISTANCE)

        # Caso objeto usável estiver no alcance
        if hitObject:

            # Abrir porta
            if "Door" in hitObject:
                vect = (hitObject.parent.localPosition - self.localPosition) * hitObject.parent.localOrientation # type: Vector
                hitObject["Use"] = True

                if not hitObject["Opened"] and not hitObject.isPlayingAction():
                    hitObject["Direction"] = 1 if vect.y >= 0 else 2
                    hitObject["Speed"] = "Run" if self["Run"] else "Crouch" if self["Crouch"] else "Normal"

            # Pegar item
            elif "Container" in hitObject:
                hitObject["Use"] = True

