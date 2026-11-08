import math
from panda3d.core import Vec3, WindowProperties, BitMask32
from panda3d.bullet import BulletCharacterControllerNode, BulletCapsuleShape, ZUp
from engine.geometry import shape


class Player:
    def __init__(self, app):
        self.app = app
        self.body = BulletCharacterControllerNode(BulletCapsuleShape(.35,1.05,ZUp), .3, 'player')
        self.body.setGravity(9.81); self.body.setJumpSpeed(5.8); self.body.setMaxJumpHeight(1.7)
        self.node = app.render.attachNewNode(self.body); self.node.setPos(0,-7,2)
        self.node.setCollideMask(BitMask32.allOn())
        self.avatar = shape(self.node,'cylinder',(0,0,0),(.6,.6,1.65),(.22,.43,.48,1))
        self.avatar.hide()  # Visible in third-person vehicle view only.
        app.physics.world.attachCharacter(self.body)
        self.heading = 0; self.pitch = -5
        self.locked = False; self.in_vehicle = None

    def lock(self, value):
        self.locked = value
        if self.app.win and hasattr(self.app.win,'requestProperties'):
            props = WindowProperties(); props.setCursorHidden(value)
            self.app.win.requestProperties(props)
            if value: self.center_mouse()

    def center_mouse(self):
        if hasattr(self.app.win,'movePointer'):
            self.app.win.movePointer(0,self.app.win.getXSize()//2,self.app.win.getYSize()//2)

    def jump(self):
        if not self.app.modal and not self.in_vehicle and self.body.canJump(): self.body.doJump()

    def update(self, dt):
        app = self.app
        if self.locked and not app.modal and hasattr(app.win,'getPointer'):
            pointer = app.win.getPointer(0)
            dx,dy = pointer.getX()-app.win.getXSize()//2, pointer.getY()-app.win.getYSize()//2
            self.heading -= dx*.13; self.pitch = max(-85,min(85,self.pitch-dy*.13))
            self.center_mouse()
        if self.in_vehicle:
            self.body.setLinearMovement(Vec3(0),False)
            self.in_vehicle.control(dt, app.keys if not app.modal else {})
            car = self.in_vehicle.node
            target = car.getPos()+Vec3(0,0,1)
            behind = car.getQuat().xform(Vec3(0,-8,4))
            app.camera.setPos(target+behind); app.camera.lookAt(target)
            return
        self.node.setH(self.heading)
        forward = float(app.keys.get('w',0))-float(app.keys.get('s',0))
        side = float(app.keys.get('d',0))-float(app.keys.get('a',0))
        velocity = Vec3(side,forward,0)
        if velocity.lengthSquared()>1: velocity.normalize()
        velocity *= 9 if app.keys.get('shift') else 5
        if app.modal: velocity = Vec3(0)
        self.body.setLinearMovement(velocity,True)
        if self.node.getZ() < -15 or max(abs(self.node.getX()),abs(self.node.getY())) > 420:
            self.node.setPos(0,-7,3)
        app.camera.setPos(self.node.getPos()+Vec3(0,0,.65))
        app.camera.setHpr(self.heading,self.pitch,0)

    def enter(self, car):
        self.in_vehicle = car
        self.app.physics.world.removeCharacter(self.body)
        self.node.hide()

    def exit(self):
        car = self.in_vehicle
        if not car: return
        self.node.setPos(car.node.getPos()+car.node.getQuat().xform(Vec3(2.5,0,1)))
        self.app.physics.world.attachCharacter(self.body)
        self.in_vehicle = None
        self.app.note('Exited vehicle')
