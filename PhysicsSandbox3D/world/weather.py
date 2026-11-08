"""Weather boundary for later storms and time-of-day lighting."""
import random
from panda3d.core import LineSegs, TransparencyAttrib


class Weather:
    def __init__(self, app):
        self.app = app
        self.mode = 'clear'
        self.root = app.render.attachNewNode('rain')
        rng = random.Random(12)
        lines = LineSegs('rain streaks'); lines.setColor(.65,.8,.92,.65)
        for _ in range(180):
            x,y,z = rng.uniform(-16,16),rng.uniform(-16,16),rng.uniform(0,16)
            lines.moveTo(x,y,z); lines.drawTo(x-.05,y,z-.55)
        self.rain = self.root.attachNewNode(lines.create()); self.rain.setLightOff()
        self.rain.setShaderOff(); self.rain.setTransparency(TransparencyAttrib.MAlpha)
        self.root.hide(); self.phase = 0

    def toggle(self):
        self.mode = 'rain' if self.mode == 'clear' else 'clear'
        self.root.show() if self.mode == 'rain' else self.root.hide()

    def update(self, dt):
        self.phase = (self.phase+dt*12)%8
        p = self.app.camera.getPos(self.app.render)
        self.root.setPos(p.x,p.y,p.z+3-self.phase)
