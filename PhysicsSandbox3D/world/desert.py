import math
import random
import numpy as np
from PIL import Image
from panda3d.core import (AmbientLight, DirectionalLight, Fog, Vec3, Texture,
                         PNMImage, LODNode, Shader)
from panda3d.bullet import BulletRigidBodyNode, BulletPlaneShape
from engine.geometry import shape, mesh
from engine.config import ROOT


class Desert:
    def __init__(self, app):
        self.app = app
        app.setBackgroundColor(.10,.30,.72,1)
        ambient = AmbientLight('ambient'); ambient.setColor((.48,.49,.45,1))
        app.render.setLight(app.render.attachNewNode(ambient))
        self.sun = DirectionalLight('sun'); self.sun.setColor((1,.89,.70,1))
        self.sun.getLens().setFilmSize(90,90); self.sun.getLens().setNearFar(1,180)
        self.sun_np = app.render.attachNewNode(self.sun)
        self.sun_np.setPos(20,-35,65); self.sun_np.lookAt(0,0,0)
        app.render.setLight(self.sun_np)
        self.fog = Fog('desert haze'); self.fog.setColor(.56,.69,.75)
        self.fog.setExpDensity(.0035)
        ground = BulletRigidBodyNode('ground')
        ground.addShape(BulletPlaneShape(Vec3(0,0,1),0)); ground.setFriction(.9)
        self.ground = app.render.attachNewNode(ground)
        app.physics.world.attachRigidBody(ground)
        # One quad, a repeating procedural texture and a cheap GLSL sand material.
        self.terrain = mesh('sand', [[(-450,-450,0),(450,-450,0),(450,450,0),(-450,450,0)]])
        self.terrain.reparentTo(app.render)
        pixels = np.random.default_rng(8).integers(0,32,(128,128,1),dtype=np.uint8)
        rgb = np.clip(pixels.astype(int)+np.array([198,161,105]),0,255).astype(np.uint8)
        image = Image.fromarray(rgb)
        pnm = PNMImage(128,128,3)
        for y in range(128):
            for x in range(128): pnm.setXel(x,y,*(float(c)/255 for c in image.getpixel((x,y))))
        texture = Texture('sand'); texture.load(pnm)
        texture.setWrapU(Texture.WMRepeat); texture.setWrapV(Texture.WMRepeat)
        self.terrain.setTexture(texture)
        from panda3d.core import TextureStage
        self.terrain.setTexScale(TextureStage.getDefault(), 150)
        shader = Shader.load(Shader.SL_GLSL, str(ROOT/'assets/shaders/sand.vert'),
                             str(ROOT/'assets/shaders/sand.frag'))
        self.terrain.setShader(shader)
        self.decor = app.render.attachNewNode('desert scenery')
        rng = random.Random(21)
        for i in range(95):
            angle, distance = rng.uniform(0,math.tau), rng.uniform(28,260)
            x,y = math.sin(angle)*distance, math.cos(angle)*distance
            lod = self.decor.attachNewNode(LODNode('scenery LOD'))
            lod.setPos(x,y,0); lod.node().addSwitch(180,0)
            group = lod.attachNewNode('detail')
            if i % 3:
                h = rng.uniform(1.8,4.5)
                shape(group,'cylinder',(0,0,h/2),(.48,.48,h),(.22,.36,.21,1))
                for sign in (-1,1):
                    shape(group, pos=(sign*.45,0,h*.58), scale=(.8,.3,.28),color=(.22,.36,.21,1))
                    shape(group,'cylinder',(sign*.8,0,h*.68),(.3,.3,h*.3),(.25,.39,.22,1))
            else:
                shape(group,'cylinder',(0,0,.5),(rng.uniform(1,3),1.8,1),(.48,.40,.31,1), (20,12,8))
        for i in range(30):
            a = i*math.tau/30
            x,y = math.cos(a)*340, math.sin(a)*340
            h = rng.uniform(25,65)
            mountain = mesh('mountain', [[(-35,-25,0),(35,-25,0),(0,0,h)],
                        [(35,-25,0),(25,30,0),(0,0,h)],[(25,30,0),(-35,25,0),(0,0,h)],
                        [(-35,25,0),(-35,-25,0),(0,0,h)]])
            mountain.reparentTo(self.decor); mountain.setPos(x,y,0); mountain.setColor(.57,.46,.34,1)
        # Flat construction pad; collider remains the continuous Bullet plane.
        shape(app.render,pos=(0,8,.015),scale=(18,18,.02),color=(.67,.58,.43,1))
        for x in range(-9,10,3):
            shape(app.render,pos=(x,8,.035),scale=(.025,18,.015),color=(.79,.70,.52,1))
        for y in range(-1,18,3):
            shape(app.render,pos=(0,y,.035),scale=(18,.025,.015),color=(.79,.70,.52,1))
        import simplepbr
        self.pipeline = simplepbr.init(msaa_samples=0, max_lights=2, use_normal_maps=False,
                                       use_emission_maps=False, use_occlusion_maps=False,
                                       enable_shadows=False, shadow_bias=.0005, enable_fog=bool(app.settings['fog']))
        self.apply_quality()

    def apply_quality(self):
        high = self.app.settings['quality'] == 'high'
        self.sun.setShadowCaster(high, 1024, 1024)
        self.pipeline.enable_shadows = high
        self.pipeline.enable_fog = bool(self.app.settings['fog'])
        if self.app.settings['fog']: self.app.render.setFog(self.fog)
        else: self.app.render.clearFog()
        self.terrain.setShaderInput('haze', 1.0 if self.app.settings['fog'] else 0.0)
        self.decor.show()
        for lod in self.decor.findAllMatches('**/+LODNode'):
            lod.node().setSwitch(0, 110 if self.app.settings['quality']=='low' else 180, 0)
