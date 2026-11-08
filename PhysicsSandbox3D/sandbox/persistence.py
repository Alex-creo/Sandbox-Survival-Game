"""Strict, bounded JSON blueprints. Validate before touching the live world."""
import json
import math
import re
from pathlib import Path
from engine.config import DATA
from sandbox.catalog import CATALOG


class Blueprints:
    def __init__(self, folder=None):
        self.folder = Path(folder or DATA/'saves')
        self.folder.mkdir(parents=True,exist_ok=True)

    def path(self, name):
        if not isinstance(name,str) or not re.fullmatch(r'[\w -]{1,48}',name):
            raise ValueError('Use 1-48 letters, numbers, spaces or hyphens')
        return self.folder / (name+'.json')

    def names(self):
        return sorted(p.stem for p in self.folder.glob('*.json') if not p.is_symlink())

    @staticmethod
    def validate(data):
        if not isinstance(data,dict) or data.get('version')!=1: raise ValueError('Unsupported blueprint version')
        parts,joints = data.get('objects'),data.get('connections')
        if not isinstance(parts,list) or len(parts)>250 or not isinstance(joints,list) or len(joints)>500:
            raise ValueError('Invalid blueprint size')
        ids = set(); joint_ids = set(); pairs = set()
        def vector(value, size, low, high):
            if not isinstance(value,list) or len(value)!=size: raise ValueError('Invalid vector')
            if any(type(v) not in (int,float) or not math.isfinite(v) or not low<=v<=high for v in value):
                raise ValueError('Vector is out of range')
        def number(value,lo,hi):
            if type(value) not in (int,float) or not math.isfinite(value) or not lo<=value<=hi:
                raise ValueError('Invalid physical property')
        def identifier(value):
            if not isinstance(value,str) or not re.fullmatch(r'[\w-]{1,64}',value): raise ValueError('Invalid identifier')
        for p in parts:
            if not isinstance(p,dict): raise ValueError('Invalid object')
            identifier(p.get('id'))
            if p['id'] in ids or p.get('type') not in CATALOG: raise ValueError('Duplicate or unknown object')
            ids.add(p['id'])
            vector(p.get('position'),3,-1000,1000); vector(p.get('rotation'),3,-36000,36000)
            vector(p.get('scale'),3,.1,10); vector(p.get('color'),4,0,1)
            # Cylinders use circular Bullet colliders; reject non-circular saved scaling.
            if CATALOG[p['type']].mesh=='cylinder' and abs(p['scale'][0]-p['scale'][1])>.001:
                raise ValueError('Cylinder X/Y scale must match')
            if p['type']=='car' and p['scale'] != [1,1,1]: raise ValueError('Car scale must be 1')
            number(p.get('mass'),.1,10000); number(p.get('friction'),0,3); number(p.get('restitution'),0,1)
            if type(p.get('dynamic')) is not bool: raise ValueError('Invalid physics switch')
        for c in joints:
            if not isinstance(c,dict): raise ValueError('Invalid connection')
            identifier(c.get('id'))
            pair = tuple(sorted((str(c.get('a')),str(c.get('b')))))
            if c['id'] in joint_ids or pair in pairs or c.get('a') not in ids or c.get('b') not in ids or c['a']==c['b']:
                raise ValueError('Invalid connection endpoints or duplicate connection')
            if c.get('type') not in ('fixed','hinge'): raise ValueError('Unknown connection type')
            joint_ids.add(c['id']); pairs.add(pair)
            for key in ('frame_a','frame_b'):
                frame = c.get(key)
                if not isinstance(frame,dict): raise ValueError('Invalid joint frame')
                vector(frame.get('position'),3,-100,100); vector(frame.get('rotation'),3,-36000,36000)
        return data

    def write(self, name, registry):
        path = self.path(name)
        data = self.validate(dict(version=1,objects=registry.records(),connections=registry.joints()))
        if path.is_symlink(): raise ValueError('Save cannot be a symbolic link')
        temp = path.with_suffix('.tmp')
        with temp.open('w',encoding='utf-8') as f: json.dump(data,f,indent=2,allow_nan=False)
        temp.replace(path)

    def read(self, name):
        path = self.path(name)
        if path.is_symlink() or path.stat().st_size>2_000_000: raise ValueError('Invalid save file')
        try: return self.validate(json.loads(path.read_text(encoding='utf-8')))
        except (KeyError,TypeError,json.JSONDecodeError) as exc: raise ValueError('Malformed blueprint') from exc

    def load(self, name, registry):
        data = self.read(name)
        # Stage the replacement beside the current registry; failed staging is rolled back.
        from sandbox.registry import Registry
        staged = Registry(registry.app)
        try:
            for p in data['objects']:
                staged.spawn(p['type'],p['position'],uid=p['id'],hpr=p['rotation'],
                             scale=p['scale'],color=p['color'],mass=p['mass'],
                             friction=p['friction'],restitution=p['restitution'],dynamic=p['dynamic'])
            for c in data['connections']:
                staged.connect(c['a'],c['b'],c['type'],c['id'],c['frame_a'],c['frame_b'])
        except Exception:
            staged.clear()
            raise
        registry.clear()
        registry.objects,registry.connections = staged.objects,staged.connections

    def delete(self, name):
        self.path(name).unlink()
