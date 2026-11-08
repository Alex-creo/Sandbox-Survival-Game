"""Headless integration tests exercise the real Panda3D renderer and Bullet world."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('PHYSICS_SANDBOX_DATA',str(Path(tempfile.mkdtemp())/'data'))
os.environ.setdefault('MESA_SHADER_CACHE_DIR',str(Path(tempfile.gettempdir())/'physics-sandbox-mesa'))
from panda3d.core import loadPrcFileData, ClockObject, Vec3
loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\naudio-library-name null\nwin-size 1280 720\nnotify-level warning')
from engine.application import SandboxApp
from sandbox.persistence import Blueprints


class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=SandboxApp()
        cls.clock=ClockObject.getGlobalClock()
        cls.clock.setMode(ClockObject.MNonRealTime); cls.clock.setDt(1/60)

    @classmethod
    def tearDownClass(cls): cls.app.destroy()

    def setUp(self):
        app=self.app
        app.close_modal(); app.tools.cancel(); app.tools.set_selected(None); app.tools.anchor=None
        if app.player.in_vehicle: app.player.exit()
        app.registry.clear(); app.keys.clear(); app.player.node.setPos(0,-7,2)
        app.player.heading=0; app.player.pitch=-5

    def frames(self,count):
        for _ in range(count): self.app.taskMgr.step()

    def test_ground_gravity_jump_and_walk(self):
        app=self.app
        obj=app.registry.spawn('block',(3,3,5))
        self.frames(180)
        self.assertAlmostEqual(obj.node.getZ(),.5,delta=.08)
        grounded=app.player.node.getZ()
        self.assertTrue(app.player.body.canJump())
        app.player.jump(); self.frames(20)
        self.assertGreater(app.player.node.getZ(),grounded+.3)
        self.frames(100)
        start=app.player.node.getY(); app.messenger.send('w'); self.frames(60); app.messenger.send('w-up')
        self.assertGreater(app.player.node.getY(),start+3)

    def test_place_select_move_rotate_freeze_delete(self):
        app=self.app; self.frames(90)
        app.player.update(1/60)
        app.tools.begin('wheel',(.5,.7,.3,1),'Rubber',True,8)
        self.frames(1)
        self.assertIsNotNone(app.tools.ghost)
        app.tools.rotate(); app.tools.place()
        self.assertEqual(len(app.registry.objects),1)
        obj=next(iter(app.registry.objects.values()))
        app.tools.set_selected(None)
        app.camera.lookAt(obj.node)
        app.tools.select(); self.assertEqual(app.tools.selected,obj.uid)
        obj.set_color((.2,.4,.8,1)); app.tools.set_selected(None)
        self.assertAlmostEqual(obj.visual.getChild(0).getColor().z,.8,delta=.01)
        app.tools.set_selected(obj.uid)
        self.assertEqual(obj.kind,'wheel'); self.assertAlmostEqual(obj.body.getFriction(),1.1,places=3)
        app.tools.freeze(); self.assertEqual(obj.body.getMass(),0)
        app.tools.freeze(); self.assertEqual(obj.body.getMass(),8)
        app.tools.grab(); self.frames(5); app.tools.release()
        self.assertEqual(obj.body.getMass(),8)
        app.tools.delete(); self.assertFalse(app.registry.objects)
        app.tools.begin('engine',(.8,.4,.2,1),'Standard',True,30); app.tools.cancel()
        self.assertIsNone(app.tools.ghost)

    def test_overlap_rejected(self):
        app=self.app; self.frames(90); app.player.update(1/60)
        app.tools.begin('block',(.5,.5,.5,1),'Standard',False,12)
        pos=app.tools.placement(); app.registry.spawn('block',pos,dynamic=False)
        app.tools.place(); self.assertEqual(len(app.registry.objects),1)
        self.assertIsNotNone(app.tools.pending)

    def test_vehicle_acceleration_steering_braking_reverse_enter_exit(self):
        app=self.app
        car=app.registry.spawn('car',(0,0,1.4))
        self.frames(120)
        self.assertGreater(car.node.getZ(),.1)
        app.player.node.setPos(2,0,1); app.interact(); self.assertIs(app.player.in_vehicle,car)
        start=Vec3(car.node.getPos()); app.keys['w']=True; self.frames(180)
        self.assertGreater((car.node.getPos()-start).length(),8)
        self.assertGreater(abs(car.vehicle.getCurrentSpeedKmHour()),8)
        app.keys['a']=True; self.frames(45)
        self.assertGreater(abs(car.steer),15)
        app.keys.clear(); app.keys['space']=True; self.frames(120)
        self.assertLess(abs(car.vehicle.getCurrentSpeedKmHour()),5)
        app.keys.clear(); app.keys['s']=True; self.frames(120)
        self.assertLess(car.vehicle.getCurrentSpeedKmHour(),-3)
        app.keys.clear(); app.interact(); self.assertIsNone(app.player.in_vehicle)
        self.assertEqual(car.vehicle.getNumWheels(),4)

    def test_constraints_blueprint_roundtrip_and_invalid_rollback(self):
        app=self.app
        a=app.registry.spawn('block',(0,3,3)); b=app.registry.spawn('engine',(1.5,3,3))
        c=app.registry.spawn('hinge',(1.5,3,4.2))
        app.registry.connect(a.uid,b.uid)
        app.registry.connect(b.uid,c.uid,'hinge')
        self.frames(120)
        self.assertLess((a.node.getPos()-b.node.getPos()).length(),2)
        with tempfile.TemporaryDirectory() as tmp:
            saves=Blueprints(tmp); saves.write('Test build',app.registry)
            original=saves.read('Test build')
            app.registry.clear(); saves.load('Test build',app.registry)
            self.assertEqual(set(app.registry.objects),{a.uid,b.uid,c.uid})
            self.assertEqual(len(app.registry.connections),2)
            self.assertEqual(app.registry.objects[b.uid].kind,'engine')
            bad=copy.deepcopy(original); bad['objects'][0]['mass']=-5
            (Path(tmp)/'Bad.json').write_text(json.dumps(bad))
            with self.assertRaises(ValueError): saves.load('Bad',app.registry)
            self.assertEqual(len(app.registry.objects),3)
            for name in ('../escape','', 'bad/name'):
                with self.assertRaises(ValueError): saves.path(name)
            saves.delete('Test build'); self.assertNotIn('Test build',saves.names())

    def test_gui_tabs_preview_settings_and_weather(self):
        app=self.app
        app.messenger.send('tab'); self.assertTrue(app.modal); self.assertFalse(app.player.locked)
        for tab in ('OBJECTS','TRANSPORT','MOBS','GAME','MY BUILDS','PLAYERS'):
            app.ui.catalog(tab); self.frames(2)
        app.ui.catalog('OBJECTS'); app.ui.choose_category('Engines'); self.frames(3)
        self.assertEqual(app.ui.kind,'engine')
        app.ui.search.enterText('missing'); app.ui.refresh_items(); self.assertEqual(app.ui.filtered,[])
        app.ui.catalog('GAME'); app.weather.toggle(); self.assertEqual(app.weather.mode,'rain')
        app.ui.pause(); app.change_setting('quality','low'); app.change_setting('fog',False)
        app.change_setting('fov',95); self.frames(2)
        self.assertAlmostEqual(app.camLens.getHfov(),95,delta=.1)
        app.close_modal(); self.assertFalse(app.modal); self.assertTrue(app.player.locked)


if __name__=='__main__': unittest.main(verbosity=2)
