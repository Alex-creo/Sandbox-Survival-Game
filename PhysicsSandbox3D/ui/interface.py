from direct.gui.DirectGui import (DirectFrame, DirectLabel, DirectButton, DirectEntry,
                                  DirectScrolledFrame, DirectOptionMenu, DirectCheckButton)
from panda3d.core import TextNode, NodePath, AmbientLight, DirectionalLight, Vec3, Texture
from sandbox.catalog import CATALOG, CATEGORIES, MATERIALS
from engine.geometry import shape

BG = (.035,.052,.068,1)
PANEL = (.065,.087,.105,1)
TILE = (.10,.13,.15,1)
INK = (.85,.89,.88,1)
MUTED = (.45,.57,.60,1)
ORANGE = (.98,.57,.23,1)
COLORS = [( .9,.61,.28,1),(.24,.57,.63,1),(.76,.28,.22,1),(.38,.56,.32,1),(.62,.67,.70,1)]


def label(parent, text, x, z, scale=.035, color=INK, align=TextNode.ALeft):
    return DirectLabel(parent=parent,text=text,pos=(x,0,z),scale=scale,text_fg=color,
                       text_align=align,frameColor=(0,0,0,0),textMayChange=True)


def button(parent, text, x, z, command, width=.37, color=TILE, text_color=INK):
    return DirectButton(parent=parent,text=text,pos=(x,0,z),text_scale=.031,
                        text_pos=(0,-.01),frameSize=(-width/2,width/2,-.037,.037),
                        frameColor=color,text_fg=text_color,relief=1,command=command,
                        rolloverSound=None,clickSound=None,pressEffect=False)


class Interface:
    def __init__(self, app):
        self.app = app; self.root = None; self.tab = 'OBJECTS'; self.category = 'Building blocks'
        self.kind = 'block'; self.color = COLORS[0]; self.material = 'Standard'; self.dynamic = True
        self.preview = None; self.preview_buffer = None
        self.hud = app.aspect2d.attachNewNode('HUD')
        label(self.hud,'PHYSICS / SANDBOX',-1.69,.89,.043)
        label(self.hud,'DESERT TEST RANGE     /     FIRST PLAYABLE',-1.69,.83,.022,MUTED)
        self.status = label(self.hud,'',-1.69,-.77,.029,ORANGE)
        label(self.hud,'WASD move   /   SPACE jump   /   E interact   /   TAB catalog   /   ESC pause',-1.69,-.88,.026)
        label(self.hud,'LMB select   G move   R rotate   F physics   J / H join   DEL remove',-1.69,-.94,.024,MUTED)
        self.cross = label(self.hud,'+',0,0,.04,INK,TextNode.ACenter)
        self.telemetry = label(self.hud,'',1.67,.90,.026,MUTED,TextNode.ARight)
        self.hud.setScale(min(1,app.getAspectRatio()/1.78))

    def destroy_menu(self):
        if self.root: self.root.destroy(); self.root = None
        if self.preview_buffer:
            self.app.graphicsEngine.removeWindow(self.preview_buffer); self.preview_buffer = None
        if self.preview: self.preview.removeNode(); self.preview = None
        if hasattr(self,'preview_camera') and self.preview_camera:
            self.preview_camera.removeNode(); self.preview_camera = None
        self.cross.show()

    def base_menu(self, title, subtitle):
        self.destroy_menu(); self.cross.hide()
        self.root = DirectFrame(parent=self.app.aspect2d,frameColor=BG,frameSize=(-1.72,1.72,-.95,.95))
        self.root.setScale(min(1,self.app.getAspectRatio()/1.78))
        label(self.root,title,-1.61,.80,.057)
        label(self.root,subtitle,-1.60,.72,.025,MUTED)
        button(self.root,'CLOSE  /  TAB',1.40,.82,self.app.close_modal,.40)

    def catalog(self, tab=None):
        if tab: self.tab=tab
        self.base_menu('THE SANDBOX','BUILD SOMETHING. BREAK SOMETHING. START AGAIN.')
        tabs = ['OBJECTS','TRANSPORT','MOBS','GAME','MY BUILDS','PLAYERS']
        for i,name in enumerate(tabs):
            button(self.root,name,-1.37+i*.55,.59,lambda n=name:self.switch(n),.51,
                   ORANGE if name==self.tab else TILE, BG if name==self.tab else INK)
        if self.tab == 'MY BUILDS': self.builds(); return
        if self.tab == 'GAME': self.game_options(); return
        if self.tab in ('MOBS','PLAYERS'):
            label(self.root,('CREATURES' if self.tab=='MOBS' else 'MULTIPLAYER')+' / PLANNED',-1.5,.28,.05)
            label(self.root,'This prototype is a local physics sandbox.',-1.5,.16,.034,MUTED)
            return
        self.search = DirectEntry(parent=self.root,initialText='',pos=(-1.58,0,.40),scale=.034,
                                  width=12,frameColor=TILE,text_fg=INK,command=lambda _:self.refresh_items())
        label(self.root,'SEARCH + ENTER',-1.58,.48,.023,MUTED)
        self.category_nodes = []
        categories = CATEGORIES if self.tab=='OBJECTS' else ['Cars','Trucks','Motorcycles','Bicycles','Airplanes','Boats']
        if self.category not in categories: self.category=categories[0]
        for i,name in enumerate(categories):
            button(self.root,name,-1.34,.23-i*.106,lambda n=name:self.choose_category(n),.52,
                   (.22,.24,.23,1) if name==self.category else PANEL)
        self.grid = DirectScrolledFrame(parent=self.root,frameSize=(-.98,.74,-.80,.46),
                                         canvasSize=(0,1.60,-2.5,0),scrollBarWidth=.035,frameColor=PANEL)
        self.grid.horizontalScroll.hide()
        label(self.root,'INSPECT / CONFIGURE',.87,.43,.025,ORANGE)
        self.detail = self.root.attachNewNode('detail')
        self.refresh_items(); self.inspect(self.kind if self.kind in self.filtered else (self.filtered[0] if self.filtered else None))

    def switch(self, name):
        self.category = 'Cars' if name=='TRANSPORT' else 'Building blocks'
        self.catalog(name)

    def choose_category(self, name):
        self.category=name; self.catalog()

    def refresh_items(self):
        query = self.search.get().lower().strip()
        self.filtered = [k for k,s in CATALOG.items() if s.category==self.category and query in s.name.lower()]
        canvas = self.grid.getCanvas()
        for child in canvas.getChildren(): child.removeNode()
        self.grid['canvasSize'] = (0,1.60,-max(1.22,((len(self.filtered)+1)//2)*.43),0)
        for i,kind in enumerate(self.filtered):
            spec = CATALOG[kind]; x=.42+(i%2)*.78; z=-.25-(i//2)*.43
            tile = button(canvas,'',x,z,lambda k=kind:self.inspect(k),.70)
            tile['frameSize']=(-.35,.35,-.18,.18)
            # Mesh silhouette icons use local generated geometry in the UI plane.
            icon = tile.attachNewNode('icon'); icon.setPos(0,-.1,.04)
            shape(icon,spec.mesh,scale=(.13,.06,.13),hpr=(25,25,0),color=spec.color)
            icon.setLightOff()
            label(tile,spec.name,0,-.12,.029,INK,TextNode.ACenter)
        if not self.filtered:
            label(canvas,'No items available in this category.',.08,-.2,.033,MUTED)
            label(canvas,'Additional transport is planned.',.08,-.28,.028,MUTED)

    def inspect(self, kind):
        for child in self.detail.getChildren(): child.removeNode()
        if not kind: return
        self.kind = kind; spec = CATALOG[kind]; self.color=spec.color
        label(self.detail,spec.name,.86,.30,.044)
        label(self.detail,f'{spec.mass:g} KG  /  BULLET RIGID BODY',.86,.21,.023,MUTED)
        if self.preview_buffer:
            self.app.graphicsEngine.removeWindow(self.preview_buffer)
            self.preview_buffer=None
        if self.preview: self.preview.removeNode()
        if hasattr(self,'preview_camera') and self.preview_camera: self.preview_camera.removeNode()
        self.preview = NodePath('preview scene')
        self.preview_model = self.preview.attachNewNode('spin')
        shape(self.preview_model,spec.mesh,scale=spec.size,color=spec.color)
        amb = AmbientLight('preview ambient'); amb.setColor((.65,.65,.65,1))
        self.preview.setLight(self.preview.attachNewNode(amb))
        sun = DirectionalLight('preview sun'); sun.setColor((.8,.8,.7,1))
        sn=self.preview.attachNewNode(sun); sn.setHpr(-30,-40,0); self.preview.setLight(sn)
        self.preview_buffer=self.app.win.makeTextureBuffer('Object preview',256,192)
        if self.preview_buffer:
            self.preview_buffer.setClearColor(PANEL)
            self.preview_camera=self.app.makeCamera(self.preview_buffer,scene=self.preview)
            self.preview_camera.reparentTo(self.preview)
            self.preview_camera.node().getLens().setAspectRatio(256/192)
            self.preview_camera.setPos(4,-6,3); self.preview_camera.lookAt(0,0,0)
            DirectFrame(parent=self.detail,frameTexture=self.preview_buffer.getTexture(),
                        frameSize=(.86,1.59,-.17,.16),frameColor=(1,1,1,1))
        label(self.detail,'COLOR',.86,-.25,.023,MUTED)
        for i,color in enumerate(COLORS):
            button(self.detail,'',.91+i*.14,-.32,lambda c=color:self.set_color(c),.10,color)
        label(self.detail,'MATERIAL',.86,-.42,.023,MUTED)
        DirectOptionMenu(parent=self.detail,items=list(MATERIALS),scale=.038,pos=(.86,0,-.49),
                         initialitem=list(MATERIALS).index(self.material),command=self.set_material,
                         frameColor=TILE,text_fg=INK,highlightColor=ORANGE)
        label(self.detail,'MASS / KG',.86,-.59,.023,MUTED)
        self.mass_entry=DirectEntry(parent=self.detail,initialText=str(spec.mass),pos=(1.22,0,-.59),
                                    scale=.035,width=9,frameColor=TILE,text_fg=INK)
        DirectCheckButton(parent=self.detail,text='Enable physics',scale=.034,pos=(.91,0,-.69),
                          indicatorValue=self.dynamic,text_fg=INK,frameColor=PANEL,command=self.set_dynamic)
        button(self.detail,'PLACE IN WORLD',1.23,-.81,self.spawn,.75,ORANGE,BG)
        if self.app.tools.selected:
            button(self.detail,'APPLY COLOR',1.23,-.91,self.recolor,.75)

    def set_color(self,color):
        self.color=color
        if self.preview: self.preview_model.setColorScale(*color)

    def set_material(self, name): self.material=name
    def set_dynamic(self,value): self.dynamic=bool(value)

    def spawn(self):
        try:
            mass=float(self.mass_entry.get())
            if not .1<=mass<=10000: raise ValueError()
        except ValueError:
            self.app.note('Mass must be between 0.1 and 10000 kg'); return
        self.app.tools.begin(self.kind,self.color,self.material,self.dynamic,mass)

    def recolor(self):
        obj=self.app.registry.objects.get(self.app.tools.selected)
        if obj: obj.set_color(self.color); self.app.note('Selected object color updated')

    def builds(self):
        label(self.root,'LOCAL BLUEPRINTS',-1.54,.37,.038,ORANGE)
        label(self.root,'Saves all spawned parts and physical connections. Loading replaces the scene.',-1.54,.27,.029,MUTED)
        self.save_name=DirectEntry(parent=self.root,initialText='My construction',pos=(-1.52,0,.10),
                                   scale=.04,width=23,frameColor=TILE,text_fg=INK)
        button(self.root,'SAVE SCENE',-.25,.11,self.save,.48,ORANGE,BG)
        label(self.root,'Saving with an existing name replaces that blueprint.',-1.52,-.01,.025,MUTED)
        listing=DirectScrolledFrame(parent=self.root,frameSize=(-1.55,1.53,-.78,-.10),
                                    canvasSize=(0,3,-max(.7,len(self.app.blueprints.names())*.12),0),
                                    scrollBarWidth=.035,frameColor=PANEL)
        for i,name in enumerate(self.app.blueprints.names()):
            label(listing.getCanvas(),name,.08,-.09-i*.12,.034)
            button(listing.getCanvas(),'LOAD',2.12,-.08-i*.12,lambda n=name:self.load(n),.35)
            button(listing.getCanvas(),'DELETE',2.58,-.08-i*.12,lambda n=name:self.confirm_delete(n),.40)
        if not self.app.blueprints.names(): label(listing.getCanvas(),'Your saved builds will appear here.',.1,-.16,.035,MUTED)

    def safe(self, action, success):
        try: action(); self.app.note(success); return True
        except (OSError,ValueError,TypeError,KeyError) as exc:
            self.app.note('Blueprint: '+str(exc)); return False

    def save(self):
        self.app.tools.release()
        if self.safe(lambda:self.app.blueprints.write(self.save_name.get().strip(),self.app.registry),'Construction saved'):
            self.catalog('MY BUILDS')

    def load(self,name):
        self.app.tools.cancel(); self.app.tools.set_selected(None); self.app.tools.anchor=None
        if self.safe(lambda:self.app.blueprints.load(name,self.app.registry),'Loaded '+name): self.app.close_modal()

    def confirm_delete(self,name):
        self.base_menu('DELETE BLUEPRINT?',name)
        button(self.root,'DELETE FILE',-.3,.2,lambda:self.delete_save(name),.55,ORANGE,BG)
        button(self.root,'CANCEL',.4,.2,lambda:self.catalog('MY BUILDS'),.55)

    def delete_save(self,name):
        self.safe(lambda:self.app.blueprints.delete(name),'Deleted '+name)
        self.catalog('MY BUILDS')

    def game_options(self):
        label(self.root,'WORLD CONTROLS',-1.5,.34,.045)
        label(self.root,'Weather: '+self.app.weather.mode.upper(),-1.5,.19,.035,MUTED)
        button(self.root,'TOGGLE RAIN',-1.15,.04,lambda:(self.app.weather.toggle(),self.catalog()),.65)
        button(self.root,'SAVE / LOAD',-.35,.04,lambda:self.catalog('MY BUILDS'),.65)
        button(self.root,'SETTINGS',.45,.04,self.pause,.65)
        label(self.root,'Clear weather and simple rain are available.',-1.5,-.15,.033)
        label(self.root,'Storms, day/night and Survival Mode are planned.',-1.5,-.24,.029,MUTED)
        button(self.root,'CLEAR SCENE',-1.15,-.46,self.confirm_clear,.65)

    def confirm_clear(self):
        self.base_menu('CLEAR ALL SPAWNED OBJECTS?','Saved blueprints remain on disk.')
        button(self.root,'CLEAR',-.3,.2,lambda:(self.app.tools.cancel(),self.app.registry.clear(),self.app.close_modal()),.55,ORANGE,BG)
        button(self.root,'CANCEL',.4,.2,lambda:self.catalog('GAME'),.55)

    def pause(self):
        self.base_menu('PAUSED','GRAPHICS / LOCAL SETTINGS')
        label(self.root,'Quality',-1.45,.34,.04)
        DirectOptionMenu(parent=self.root,items=['low','medium','high'],scale=.05,pos=(-.65,0,.34),
                         initialitem=['low','medium','high'].index(self.app.settings['quality']),
                         command=lambda value:self.setting('quality',value))
        label(self.root,'Resolution',-1.45,.15,.04)
        DirectOptionMenu(parent=self.root,items=['1280 x 720','1600 x 900','1920 x 1080'],scale=.05,pos=(-.65,0,.15),
                         initialitem=[[1280,720],[1600,900],[1920,1080]].index(self.app.settings['resolution']),
                         command=lambda value:self.setting('resolution',[int(v) for v in value.split(' x ')]))
        label(self.root,'Field of view',-1.45,-.04,.04)
        DirectOptionMenu(parent=self.root,items=['60','80','95','110'],scale=.05,pos=(-.65,0,-.04),
                         initialitem=min(range(4),key=lambda i:abs([60,80,95,110][i]-self.app.settings['fov'])),
                         command=lambda value:self.setting('fov',int(value)))
        DirectCheckButton(parent=self.root,text='Distance fog',scale=.045,pos=(-1.4,0,-.24),
                          indicatorValue=self.app.settings['fog'],command=lambda v:self.setting('fog',bool(v)),text_fg=INK)
        label(self.root,'High enables shadow mapping. Settings are saved locally.',-1.45,-.42,.03,MUTED)
        button(self.root,'RESUME',-.95,-.65,self.app.close_modal,.8,ORANGE,BG)
        button(self.root,'QUIT',.10,-.65,self.app.userExit,.8)

    def setting(self,key,value): self.app.change_setting(key,value)

    def update(self, dt):
        if self.preview: self.preview_model.setH(self.preview_model.getH()+dt*24)
        mode='DRIVING' if self.app.player.in_vehicle else 'ON FOOT'
        speed = abs(self.app.player.in_vehicle.vehicle.getCurrentSpeedKmHour()) if self.app.player.in_vehicle else 0
        self.telemetry['text']=f'{mode}   /   {len(self.app.registry.objects):03d} PARTS'+(f'   /   {speed:.0f} KM/H' if speed else '')
