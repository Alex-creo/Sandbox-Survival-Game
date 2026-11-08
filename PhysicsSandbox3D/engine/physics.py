from panda3d.bullet import BulletWorld
from panda3d.core import Vec3


class Physics:
    STEP = 1 / 120

    def __init__(self):
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0,0,-9.81))
        self.accumulator = 0

    def update(self, dt):
        self.accumulator += min(dt, .1)
        while self.accumulator >= self.STEP:
            self.world.doPhysics(self.STEP, 1, self.STEP)
            self.accumulator -= self.STEP
