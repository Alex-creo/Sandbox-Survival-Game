from dataclasses import dataclass


@dataclass(frozen=True)
class PartSpec:
    name: str
    category: str
    size: tuple
    mass: float
    color: tuple
    mesh: str = 'box'


CATALOG = {
    'block': PartSpec('Structural block','Building blocks',(1,1,1),12,(.80,.63,.36,1)),
    'plate': PartSpec('Metal plate','Building blocks',(2,2,.18),18,(.42,.49,.54,1)),
    'wheel': PartSpec('Wheel','Wheels',(.9,.9,.4),8,(.12,.15,.18,1),'cylinder'),
    'axle': PartSpec('Axle','Mechanical parts',(.2,.2,1.8),7,(.53,.61,.65,1),'cylinder'),
    'engine': PartSpec('Engine','Engines',(1,.8,.7),30,(.88,.31,.16,1)),
    'seat': PartSpec('Seat','Steering',(.8,.8,.65),8,(.13,.29,.34,1)),
    'hinge': PartSpec('Hinge','Mechanical parts',(.45,.45,.6),4,(.77,.74,.52,1),'cylinder'),
    'booster': PartSpec('Rocket booster','Rocket boosters',(.6,.6,1.2),15,(.89,.47,.18,1),'cylinder'),
    'spring': PartSpec('Suspension strut','Suspension',(.25,.25,1.2),6,(.33,.35,.40,1),'cylinder'),
    'battery': PartSpec('Battery','Electrical components',(.7,.5,.65),12,(.24,.56,.49,1)),
    'turbine': PartSpec('Turbine housing','Turbines',(1.2,1.2,.7),25,(.51,.58,.61,1),'cylinder'),
    'crate': PartSpec('Cargo crate','Miscellaneous',(1.3,1.3,1.3),20,(.64,.39,.20,1)),
    'car': PartSpec('Dune runner','Cars',(1.8,3.4,.65),650,(.96,.54,.18,1)),
}
CATEGORIES = ['Building blocks','Engines','Wheels','Steering','Suspension','Mechanical parts',
              'Electrical components','Rocket boosters','Turbines','Miscellaneous']
MATERIALS = {'Standard': (.65,.05), 'Rubber': (1.1,.15), 'Ice': (.08,.02)}
