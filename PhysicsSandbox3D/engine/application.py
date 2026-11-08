import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, Vec3, ClockObject
from engine.config import load_settings, save_settings
from engine.physics import Physics
from engine.input import InputBindings
from world.desert import Desert
from world.weather import Weather
from player.controller import Player
from sandbox.registry import Registry
from sandbox.tools import Tools
from sandbox.persistence import Blueprints
from ui.interface import Interface


class SandboxApp(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse(); self.setFrameRateMeter(True)
        self.settings=load_settings(); self.camLens.setFov(self.settings['fov']); self.camLens.setNearFar(.08,700)
        self.modal=False; self.keys={}; self.physics=Physics()
        self.desert=Desert(self); self.weather=Weather(self)
        self.player=Player(self); self.registry=Registry(self); self.tools=Tools(self)
        self.blueprints=Blueprints(); self.ui=Interface(self)
        self.input=InputBindings(self)
        self.registry.spawn('car',(5,7,1.4))
        self.registry.spawn('block',(-3,6,2))
        self.note('Welcome to the desert | TAB opens the sandbox catalog | E enters a nearby car')
        self.player.lock(True)
        self.taskMgr.add(self.update,'game update')
        self.accept('window-event',self.window_event)

    def key(self,key,value): self.keys[key]=value
    def jump(self): self.keys['space']=True; self.player.jump()
    def adjust_distance(self,delta):
        if not self.modal: self.tools.distance=max(3,min(15,self.tools.distance+delta))
    def note(self,text):
        logging.info(text)
        if hasattr(self,'ui'): self.ui.status['text']=text

    def open_modal(self):
        self.tools.release(); self.modal=True; self.keys.clear(); self.player.lock(False)
    def close_modal(self):
        self.ui.destroy_menu(); self.modal=False; self.keys.clear(); self.player.lock(True)
    def menu(self):
        if self.modal: self.close_modal()
        else: self.open_modal(); self.ui.catalog()
    def pause(self):
        if self.tools.pending: self.tools.cancel(); return
        if self.modal: self.close_modal()
        else: self.open_modal(); self.ui.pause()

    def interact(self):
        if self.modal: return
        if self.player.in_vehicle: self.player.exit(); return
        cars=[obj for obj in self.registry.objects.values() if obj.kind=='car']
        cars.sort(key=lambda o:(o.node.getPos()-self.player.node.getPos()).lengthSquared())
        if cars and (cars[0].node.getPos()-self.player.node.getPos()).length()<4.5:
            self.tools.cancel(); self.player.enter(cars[0]); self.note('DRIVE | WASD / SPACE handbrake / E exit')
        else: self.note('Walk within 4.5 metres of a car to enter')

    def quick_save(self):
        if not self.modal:
            self.tools.release(); self.ui.safe(lambda:self.blueprints.write('Quicksave',self.registry),'Quicksave written')
    def quick_load(self):
        if not self.modal: self.ui.load('Quicksave')

    def change_setting(self,key,value):
        self.settings[key]=value
        if key=='fov': self.camLens.setFov(value)
        elif key in ('quality','fog'): self.desert.apply_quality()
        elif key=='resolution' and hasattr(self.win,'requestProperties'):
            props=WindowProperties(); props.setSize(*value); self.win.requestProperties(props)
        try: save_settings(self.settings)
        except OSError as exc: self.note('Settings could not be saved: '+str(exc))

    def window_event(self, window):
        if hasattr(window,'getProperties') and not window.getProperties().getForeground() and not self.modal:
            self.open_modal(); self.ui.pause()

    def update(self,task):
        dt=min(ClockObject.getGlobalClock().getDt(),.1)
        self.player.update(dt)
        if not self.modal:
            self.tools.update(dt); self.physics.update(dt); self.weather.update(dt)
        self.ui.update(dt)
        # Keep the shadow map centred on the active construction area.
        if self.settings['quality']=='high':
            p=self.player.in_vehicle.node.getPos() if self.player.in_vehicle else self.player.node.getPos()
            self.desert.sun_np.setPos(p+Vec3(20,-35,65)); self.desert.sun_np.lookAt(p)
        return task.cont
