from panda3d.core import Vec3, Point3, BitMask32, TransparencyAttrib
from engine.geometry import shape
from sandbox.catalog import CATALOG, MATERIALS


class Tools:
    def __init__(self, app):
        self.app = app
        self.selected = None; self.pending = None; self.ghost = None
        self.angle = 0; self.distance = 5; self.grabbed = None; self.anchor = None
        self.color = (.83,.64,.35,1); self.material = 'Standard'; self.dynamic = True; self.mass = None

    def ray(self):
        app = self.app
        start = app.camera.getPos(app.render)
        direction = app.camera.getQuat(app.render).getForward()
        result = app.physics.world.rayTestClosest(start,start+direction*40,BitMask32.allOn())
        if result.hasHit():
            node = app.render.find('**/'+result.getNode().getName())
            uid = node.getPythonTag('uid') if not node.isEmpty() else None
            return uid, result.getHitPos()
        return None, start+direction*self.distance

    def select(self):
        if self.app.modal: return
        if self.pending: self.place(); return
        uid,_ = self.ray()
        self.set_selected(uid if uid in self.app.registry.objects else None)

    def set_selected(self, uid):
        if self.selected in self.app.registry.objects:
            self.app.registry.objects[self.selected].visual.clearColorScale()
        self.selected = uid
        if uid:
            obj = self.app.registry.objects[uid]
            obj.visual.setColorScale(1.2,1.15,.7,1)
            self.app.note(CATALOG[obj.kind].name+' selected | G move, R rotate, F freeze, Del remove')

    def begin(self, kind, color, material, dynamic, mass):
        if self.app.player.in_vehicle:
            self.app.note('Exit the vehicle before placing parts'); return
        self.cancel()
        self.pending = kind; self.color = color; self.material = material; self.dynamic = dynamic; self.mass = mass
        spec = CATALOG[kind]
        self.ghost = shape(self.app.render,spec.mesh,scale=spec.size,color=(*color[:3],.45))
        self.ghost.setTransparency(TransparencyAttrib.MAlpha); self.ghost.setLightOff(); self.ghost.setShaderOff()
        self.app.close_modal(); self.app.note('PLACE | Mouse aim / R rotate / Wheel distance / Left confirm / Right cancel')

    def cancel(self):
        if self.ghost: self.ghost.removeNode()
        self.ghost = None; self.pending = None
        self.release()

    def placement(self):
        camera = self.app.camera
        direction = camera.getQuat(self.app.render).getForward()
        pos = camera.getPos(self.app.render)+direction*self.distance
        size = CATALOG[self.pending].size
        pos.z = max(size[2]/2+.12,pos.z)
        return pos

    def place(self):
        pos = self.placement()
        if (pos-self.app.player.node.getPos()).length()<2:
            self.app.note('Place farther from the player'); return
        spec = CATALOG[self.pending]
        # Bullet overlap test at the proposed transform, ignoring the character by distance above.
        from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape
        probe = BulletRigidBodyNode('placement probe'); probe.addShape(BulletBoxShape(Vec3(*spec.size)*.48))
        np = self.app.render.attachNewNode(probe); np.setPos(pos); np.setH(self.angle)
        contacts = self.app.physics.world.contactTest(probe)
        blocked = any(c.getNode0().getName()!='ground' and c.getNode1().getName()!='ground'
                      for c in contacts.getContacts())
        np.removeNode()
        if blocked: self.app.note('Placement overlaps an object; move the preview'); return
        try:
            friction,bounce = MATERIALS[self.material]
            obj = self.app.registry.spawn(self.pending,pos,hpr=(self.angle,0,0),color=self.color,
                                         dynamic=self.dynamic,mass=self.mass,friction=friction,restitution=bounce)
            self.cancel(); self.set_selected(obj.uid)
        except ValueError as exc: self.app.note(str(exc))

    def delete(self):
        if not self.app.modal and self.selected:
            self.release(); self.app.registry.remove(self.selected); self.selected = None

    def rotate(self):
        if self.app.modal: return
        self.angle = (self.angle+15)%360
        obj = self.app.registry.objects.get(self.selected)
        if not self.pending and obj:
            obj.node.setH(obj.node.getH()+15); obj.body.setActive(True)

    def freeze(self):
        if self.app.modal: return
        obj = self.app.registry.objects.get(self.selected)
        if obj:
            obj.freeze(); self.app.note('Physics '+('enabled' if obj.dynamic else 'disabled'))

    def grab(self):
        if self.app.modal or self.pending: return
        if self.grabbed: self.release(); return
        obj = self.app.registry.objects.get(self.selected)
        if obj:
            self.grabbed = (obj,obj.dynamic)
            obj.body.setMass(0); self.app.note('Moving part | G or right mouse to release')

    def release(self):
        if self.grabbed:
            obj,dynamic = self.grabbed
            obj.body.setMass(obj.mass if dynamic else 0)
            obj.body.setLinearVelocity(Vec3(0)); obj.body.setAngularVelocity(Vec3(0)); obj.body.setActive(True)
            self.grabbed = None

    def attach(self, hinge=False):
        if self.app.modal: return
        uid = self.selected
        if not uid: self.app.note('Select a part first'); return
        if not self.anchor:
            self.anchor = uid; self.app.note('Select a second part and press J (fixed) or H (hinge)'); return
        try:
            self.app.registry.connect(self.anchor,uid,'hinge' if hinge else 'fixed')
            self.app.note('Parts joined with a physical '+('hinge' if hinge else 'fixed constraint'))
        except ValueError as exc: self.app.note(str(exc))
        self.anchor = None

    def update(self, dt):
        if self.pending:
            self.ghost.setPos(self.placement()); self.ghost.setH(self.angle)
        if self.grabbed and not self.app.modal:
            obj,_ = self.grabbed
            pos = self.app.camera.getPos(self.app.render)+self.app.camera.getQuat(self.app.render).getForward()*self.distance
            pos.z = max(CATALOG[obj.kind].size[2]/2+.12,pos.z)
            obj.node.setPos(pos); obj.body.setActive(True)
