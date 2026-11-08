from panda3d.core import Vec3
from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape, BulletCylinderShape, ZUp
from engine.geometry import shape
from sandbox.catalog import CATALOG


class Part:
    def __init__(self, app, kind, uid, pos, hpr=(0,0,0), color=None, mass=None,
                 scale=(1,1,1), friction=.65, restitution=.05, dynamic=True):
        self.app, self.kind, self.uid = app, kind, uid
        spec = CATALOG[kind]
        self.scale = tuple(scale)
        self.mass = spec.mass if mass is None else mass
        self.dynamic = dynamic
        self.color = tuple(color or spec.color)
        size = Vec3(*(a*b for a,b in zip(spec.size, scale)))
        self.body = BulletRigidBodyNode(uid)
        collider = (BulletCylinderShape(size.x/2, size.z, ZUp) if spec.mesh == 'cylinder'
                    else BulletBoxShape(size/2))
        self.body.addShape(collider)
        self.body.setMass(self.mass if dynamic else 0)
        self.body.setFriction(friction); self.body.setRestitution(restitution)
        self.body.setDeactivationEnabled(True)
        self.node = app.render.attachNewNode(self.body)
        self.node.setPos(*pos); self.node.setHpr(*hpr)
        self.node.setPythonTag('uid', uid)
        self.visual = self.node.attachNewNode('visual')
        shape(self.visual, spec.mesh, scale=tuple(size), color=self.color)
        if kind == 'engine':
            for x in (-.32,0,.32):
                shape(self.visual, 'cylinder', (x,0,.44), (.15,.4,.22), (.2,.23,.25,1))
        if kind == 'seat':
            shape(self.visual, pos=(0,.3,.45), scale=(.8,.15,.9), color=self.color)
        if kind == 'booster':
            shape(self.visual, 'cylinder', (0,0,-.64), (.8,.8,.15), (.18,.2,.22,1))
        app.physics.world.attachRigidBody(self.body)

    def set_color(self, color):
        self.color = tuple(color)
        self.visual.clearColorScale()
        # Replace the base tint so repeated edits do not compound.
        for child in self.visual.getChildren(): child.setColor(*color)

    def freeze(self):
        self.dynamic = not self.dynamic
        self.body.setMass(self.mass if self.dynamic else 0)
        self.body.setActive(True)

    def record(self):
        return dict(id=self.uid, type=self.kind, position=list(self.node.getPos()),
                    rotation=list(self.node.getHpr()), scale=list(self.scale), color=list(self.color),
                    mass=self.mass, friction=self.body.getFriction(),
                    restitution=self.body.getRestitution(), dynamic=self.dynamic)

    def destroy(self):
        if self.body in self.app.physics.world.getRigidBodies():
            self.app.physics.world.removeRigidBody(self.body)
        self.node.removeNode()
