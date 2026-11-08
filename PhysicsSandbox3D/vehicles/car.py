from panda3d.bullet import BulletVehicle, ZUp
from panda3d.core import Vec3
from components.parts import Part
from engine.geometry import shape


class Car(Part):
    def __init__(self, app, kind, uid, pos, **kwargs):
        super().__init__(app, kind, uid, pos, **kwargs)
        self.body.setDeactivationEnabled(False)
        self.body.setCcdMotionThreshold(.5); self.body.setCcdSweptSphereRadius(.5)
        shape(self.visual,pos=(0,-.1,.65),scale=(1.45,1.6,.6),color=(.12,.23,.27,1))
        shape(self.visual,pos=(0,.85,.5),scale=(1.6,.7,.2),color=(.97,.65,.28,1))
        for x in (-.65,.65):
            shape(self.visual,pos=(x,1.72,.1),scale=(.32,.06,.16),color=(1,.94,.72,1))
        self.vehicle = BulletVehicle(app.physics.world,self.body)
        self.vehicle.setCoordinateSystem(ZUp)
        app.physics.world.attachVehicle(self.vehicle)
        self.wheel_nodes = []
        for x,y,front in [(-1,1.15,True),(1,1.15,True),(-1,-1.15,False),(1,-1.15,False)]:
            wheel_node = app.render.attachNewNode('car wheel')
            shape(wheel_node,'cylinder',scale=(.78,.78,.32),hpr=(0,90,0),color=(.09,.11,.13,1))
            # Bullet's wheel axis is X; rotate the procedural cylinder onto X.
            wheel_node.getChild(0).setHpr(0,0,90)
            wheel = self.vehicle.createWheel(); wheel.setNode(wheel_node.node())
            wheel.setChassisConnectionPointCs(Vec3(x,y,0))
            wheel.setFrontWheel(front); wheel.setWheelDirectionCs(Vec3(0,0,-1))
            wheel.setWheelAxleCs(Vec3(1,0,0)); wheel.setWheelRadius(.39)
            wheel.setMaxSuspensionTravelCm(35); wheel.setSuspensionStiffness(35)
            wheel.setWheelsDampingRelaxation(2.3); wheel.setWheelsDampingCompression(4.4)
            wheel.setFrictionSlip(2); wheel.setRollInfluence(.1)
            self.wheel_nodes.append(wheel_node)
        self.steer = 0

    def control(self, dt, keys):
        axis = float(keys.get('a',0))-float(keys.get('d',0))
        self.steer += (axis*28-self.steer)*min(1,dt*7)
        force = 2100 if keys.get('w') else (-1400 if keys.get('s') else 0)
        brake = 90 if keys.get('space') else (2 if not force else 0)
        if keys.get('s') and self.vehicle.getCurrentSpeedKmHour()>5: force=0; brake=45
        for i in range(4):
            self.vehicle.applyEngineForce(force if i>=2 else 0,i)
            self.vehicle.setBrake(brake,i)
        for i in (0,1): self.vehicle.setSteeringValue(self.steer,i)

    def destroy(self):
        if self.app.player.in_vehicle is self: self.app.player.exit()
        self.app.physics.world.removeVehicle(self.vehicle)
        for node in self.wheel_nodes: node.removeNode()
        super().destroy()
