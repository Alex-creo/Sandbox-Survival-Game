import uuid
from panda3d.core import Vec3, TransformState
from panda3d.bullet import BulletGenericConstraint, BulletHingeConstraint
from components.parts import Part
from vehicles.car import Car


class Registry:
    LIMIT = 250

    def __init__(self, app):
        self.app = app
        self.objects = {}; self.connections = {}

    def spawn(self, kind, pos, uid=None, **kwargs):
        if len(self.objects) >= self.LIMIT: raise ValueError('Object limit reached (250)')
        uid = uid or str(uuid.uuid4())
        if uid in self.objects: raise ValueError('Duplicate object ID')
        obj = (Car if kind=='car' else Part)(self.app,kind,uid,pos,**kwargs)
        self.objects[uid] = obj
        return obj

    def connect(self, a, b, kind='fixed', uid=None, frame_a=None, frame_b=None):
        if a==b or a not in self.objects or b not in self.objects:
            raise ValueError('Choose two different parts')
        if any(c['a']==a and c['b']==b or c['a']==b and c['b']==a for c in self.connections.values()):
            raise ValueError('These parts are already joined')
        obj_a, obj_b = self.objects[a], self.objects[b]
        if (obj_a.node.getPos()-obj_b.node.getPos()).length()>8:
            raise ValueError('Move the parts within 8 metres before attaching')
        # Shared world-space frame, expressed separately in each body's local space.
        if frame_a is None:
            midpoint = (obj_a.node.getPos()+obj_b.node.getPos())*.5
            world_frame = self.app.render.attachNewNode('joint frame'); world_frame.setPos(midpoint)
            fa = world_frame.getTransform(obj_a.node); fb = world_frame.getTransform(obj_b.node)
            world_frame.removeNode()
        else:
            fa = TransformState.makePosHpr(Vec3(*frame_a['position']),Vec3(*frame_a['rotation']))
            fb = TransformState.makePosHpr(Vec3(*frame_b['position']),Vec3(*frame_b['rotation']))
        if kind == 'hinge':
            constraint = BulletHingeConstraint(obj_a.body,obj_b.body,fa,fb,True)
            constraint.setLimit(-90,90)
        else:
            constraint = BulletGenericConstraint(obj_a.body,obj_b.body,fa,fb,True)
            for axis in range(3):
                constraint.setLinearLimit(axis,0,0); constraint.setAngularLimit(axis,0,0)
        self.app.physics.world.attachConstraint(constraint,True)
        uid = uid or str(uuid.uuid4())
        def record(t): return dict(position=list(t.getPos()),rotation=list(t.getHpr()))
        self.connections[uid] = dict(id=uid,a=a,b=b,type=kind,frame_a=record(fa),frame_b=record(fb),constraint=constraint)
        return uid

    def remove(self, uid):
        for cid, c in list(self.connections.items()):
            if uid in (c['a'],c['b']):
                self.app.physics.world.removeConstraint(c['constraint']); del self.connections[cid]
        obj = self.objects.pop(uid,None)
        if obj: obj.destroy()

    def clear(self):
        for uid in list(self.objects): self.remove(uid)

    def records(self):
        return [o.record() for o in self.objects.values()]

    def joints(self):
        return [{k:v for k,v in c.items() if k!='constraint'} for c in self.connections.values()]
