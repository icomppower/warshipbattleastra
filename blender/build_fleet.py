"""Iron Tide: original Blender fleet. Run with Blender 4.3+ or Python + bpy.
Produces editable .blend, articulated GLBs, and a fleet preview.
Model coordinates: +Y bow, +Z up, waterline Z=0. No downloaded game assets.
"""
import bpy, math, random, os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'dist','assets'); os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
random.seed(84)
def mat(name,color,metal=0,rough=.65):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
steel=mat('Ocean grey painted steel',(.24,.32,.36),.48)
light=mat('Upper works light grey',(.42,.48,.48),.3)
dark=mat('Dark gunmetal',(.065,.095,.11),.7)
deck=mat('Weathered teak deck',(.43,.32,.19))
red=mat('Antifouling hull red',(.24,.065,.045),.25)
black=mat('Funnel caps and rubber',(.025,.035,.039))
window=mat('Bridge glazing',(.035,.12,.17),.65,.2)
white=mat('Canvas and lifeboats',(.70,.71,.65))
brass=mat('Propeller bronze',(.43,.29,.09),.75)
def assign(o,name,ma,parent=None):
 o.name=name;o.data.materials.append(ma)
 if parent:o.parent=parent
 return o
def cube(name,loc,scale,ma,parent=None,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 assign(o,name,ma,parent)
 if bevel:
  mod=o.modifiers.new('Chamfered plate edges','BEVEL');mod.width=bevel;mod.segments=1;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
def cyl(name,loc,r,depth,ma,parent=None,vertices=12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);return assign(bpy.context.object,name,ma,parent)
def beam(name,a,b,r,ma,parent=None,verts=8):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,ma,parent,verts);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def mesh(name,verts,faces,ma,parent=None):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);return assign(o,name,ma,parent)
def empty(name,loc=(0,0,0)):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=loc;return o
def hull(root,L,W):
 # Multi-station cruiser stern and raked clipper bow, 3-dimensional cross sections.
 stations=[(-.5,.22),(-.46,.62),(-.37,.91),(-.2,1),(0,1),(.2,.95),(.34,.73),(.43,.39),(.5,.015)]
 rings=[]
 for sy,sw in stations:
  y=sy*L; bow=max(0,sy-.2)*3
  rings.append([(-W*sw*.40,y,-2.7),(-W*sw*.5,y,.25),(-W*sw*.48,y,3.1+bow),(W*sw*.48,y,3.1+bow),(W*sw*.5,y,.25),(W*sw*.40,y,-2.7)])
 verts=[p for ring in rings for p in ring];faces=[]
 for i in range(len(rings)-1):
  for j in range(6):faces.append((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j))
 faces.extend([tuple(range(5,-1,-1)),tuple((len(rings)-1)*6+j for j in range(6))]);mesh('Armored hull',verts,faces,steel,root)
 for side in [-1,1]:
  for i in range(len(stations)-1):
   y1,w1=stations[i];y2,w2=stations[i+1]
   mesh('Waterline boot stripe',[(side*W*w1*.501,y1*L,-.25),(side*W*w2*.501,y2*L,-.25),(side*W*w2*.501,y2*L,.25),(side*W*w1*.501,y1*L,.25)],[(0,1,2,3)],dark,root)
  for y in range(int(-L*.40),int(L*.33),3):
   if abs(y)<L*.3:cylport=beam('Hull porthole',(side*(W*.497),y,1.7),(side*(W*.508),y,1.7),.16,dark,root)
 verts=[]
 for y,w in stations:verts.extend([(-W*w*.468,y*L,3.16+max(0,y-.2)*3),(W*w*.468,y*L,3.16+max(0,y-.2)*3)])
 mesh('Teak main deck',verts,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(stations)-1)],deck,root)
 # Longitudinal plank seams and plate lines.
 for x in range(-int(W*.35),int(W*.35)+1):
  beam('Deck plank seam',(x,-L*.32,3.18),(x,L*.26,3.18),.012,dark,root,4)
 for side in [-1,1]:
  pts=[]
  for y,w in stations[1:-1]:pts.append((side*W*w*.465,y*L,4.0+max(0,y-.2)*3))
  for a,b in zip(pts,pts[1:]):
   beam('Safety railing top',a,b,.045,light,root,6);beam('Safety railing lower',(a[0],a[1],a[2]-.4),(b[0],b[1],b[2]-.4),.032,light,root,6)
   dist=(Vector(b)-Vector(a)).length
   for j in range(int(dist/2.2)+1):
    v=Vector(a).lerp(Vector(b),j/max(1,int(dist/2.2)));beam('Railing stanchion',(v.x,v.y,v.z-.85),v,.04,light,root,6)
def turret(root,name,y,z,barrels,caliber):
 t=empty(name,(0,y,z));t.parent=root
 # Components modeled locally; pivot is preserved in GLB for in-game traverse.
 cyl('Turret barbette',(0,0,.35),2.65,1.05,steel,t,16)
 cube('Sloped armored gunhouse',(0,.15,1.2),(5.5,5.4,1.9),light,t,.65)
 cube('Turret roof',(0,-.1,2.22),(4.6,4.5,.12),steel,t)
 for k in range(barrels):
  x=(k-(barrels-1)/2)*1.25
  beam('Gun sleeve',(x,1.8,1.2),(x,4.8,1.47),caliber*.65,dark,t)
  beam('Main gun barrel',(x,3.3,1.37),(x,9,1.8),caliber*.40,steel,t)
  beam('Open muzzle',(x,8.85,1.79),(x,9.04,1.805),caliber*.32,black,t)
 for x in [-2.55,2.55]:cube('Rangefinder ear',(x,0,1.6),(.45,2.4,.5),dark,t)
 cyl('Turret roof hatch',(1,-1.2,2.32),.45,.12,dark,t)
 return t
def build_ship(kind,L,W):
 root=empty(kind)
 hull(root,L,W)
 # Multilevel superstructure with bridge wings and sloping conning tower.
 cube('Boat deck',(0,-2,4.0),(W*.68,L*.42,1.7),steel,root,.4)
 cube('Citadel',(0,3,5.7),(W*.53,L*.23,2.0),light,root,.45)
 cube('Bridge block',(0,L*.105,8.1),(W*.43,6.0,3.2),steel,root,.45)
 cube('Bridge overhang',(0,L*.105,9.8),(W*.65,6.5,.35),light,root,.15)
 cube('Wheelhouse',(0,L*.105,10.8),(W*.39,4.8,1.6),light,root,.25)
 for x in [-2,-1,0,1,2]:cube('Bridge forward window',(x,L*.105+2.43,10.95),(.65,.06,.6),window,root)
 for side in [-1,1]:
  for y in [-1.5,0,1.5]:cube('Bridge side window',(side*W*.197,L*.105+y,10.95),(.06,.65,.6),window,root)
  cube('Bridge wing',(side*W*.29,L*.10,8.65),(W*.18,3,.4),light,root)
  cyl('Optical director',(side*W*.29,L*.1,9.2),.42,.8,dark,root)
 cyl('Fire control tower',(0,L*.09,12.2),1.9,1.2,steel,root)
 beam('Main rangefinder',(-3.1,L*.09,12.9),(3.1,L*.09,12.9),.29,dark,root)
 # Funnels with piping and protective grilles.
 for y in [-L*.08,-L*.19] if kind!='destroyer' else [-L*.10]:
  cube('Funnel casing',(0,y,8),(3.4,4.8,5.0),steel,root,.65)
  cube('Funnel cap',(0,y,10.65),(3.6,4.95,.45),black,root,.5)
  for x in [-.9,0,.9]:cube('Funnel grille',(x,y,10.92),(.12,3.6,.12),light,root)
  for s in [-1,1]:beam('Steam pipe',(s*1.85,y+1,5),(s*1.85,y+1,10),.12,dark,root)
 # Tripod mast, yards, radar frame, rigging.
 mastY=L*.025
 for x,y in [(-1.5,mastY-2),(1.5,mastY-2),(0,mastY+1)]:beam('Tripod mast',(x,y,6),(0,mastY,18),.14,dark,root)
 beam('Mast pole',(0,mastY,16),(0,mastY,21),.10,dark,root)
 beam('Signal yard',(-4,mastY,16),(4,mastY,16),.1,steel,root)
 for x in [-3,-1,1,3]:beam('Signal halyard',(x,mastY,16),(x*.3,mastY,8),.025,white,root,4)
 cube('Radar aerial',(0,mastY,19),(3.5,.13,1.6),dark,root)
 for x in [-1.5,-.75,0,.75,1.5]:beam('Radar vertical grid',(x,mastY+.1,18.3),(x,mastY+.1,19.7),.025,light,root,4)
 for z in [18.4,18.9,19.4]:beam('Radar horizontal grid',(-1.6,mastY+.1,z),(1.6,mastY+.1,z),.025,light,root,4)
 beam('Aft mast',(0,-L*.30,4),(0,-L*.30,12),.12,dark,root)
 beam('Radio rigging',(0,mastY,20),(0,-L*.30,12),.025,dark,root,4)
 # Turrets retained as independently animated hierarchies.
 mounts=[(L*.31,3.3),(L*.20,5.0),(-L*.33,3.3)] if kind=='battleship' else [(L*.32,3.3),(L*.22,4.6),(-L*.34,3.3)] if kind=='cruiser' else [(L*.33,3.3),(-L*.34,3.3)]
 for i,(y,z) in enumerate(mounts):turret(root,'MainTurret_'+str(i),y,z,3 if kind=='battleship' else 2 if kind=='cruiser' else 1,.55 if kind=='battleship' else .35)
 for side in [-1,1]:
  for y in [-L*.23,-L*.02,L*.19]:
   x=side*W*.36;cyl('Secondary barbette',(x,y,4),.85,.9,steel,root)
   cube('Twin secondary shield',(x,y,4.6),(1.7,1.7,1.3),light,root,.22)
   for offset in [-.25,.25]:beam('Secondary gun',(x,y+offset,4.65),(x+side*2.3,y+offset,4.8),.085,dark,root)
  for y in [-L*.29,-L*.16,L*.02,L*.26]:
   x=side*W*.34;cyl('AA gun tub',(x,y,4),.63,.45,light,root)
   beam('AA gun',(x,y,4.2),(x+side*1.0,y+.2,5),.065,dark,root)
  # Lifeboats, davits, anchors and deck furniture.
  for y in [-L*.08,-L*.18]:
   x=side*W*.32
   boat=cube('Lifeboat',(x,y,6.0),(1.2,4,.8),white,root,.5)
   cube('Lifeboat interior',(x,y,6.42),(.75,2.9,.1),deck,root,.1)
   for yy in [y-1.3,y+1.3]:beam('Boat davit',(x-side*.8,yy,5.5),(x,yy,7.3),.07,steel,root)
  for y in [-L*.4,L*.4]:
   for dy in [-.5,.5]:cyl('Mooring bollard',(side*W*.22,y+dy,3.6),.16,.8,dark,root)
  beam('Anchor shank',(side*W*.28,L*.39,1),(side*W*.28,L*.39,2.3),.12,dark,root)
  beam('Anchor fluke',(side*W*.28-.5,L*.39,1.2),(side*W*.28+.5,L*.39,1.2),.1,dark,root)
 for y in [L*.39,-L*.4]:cyl('Capstan',(0,y,3.6),.48,.7,dark,root)
 for y in [-L*.26,0,L*.16]:cube('Deck hatch',(W*.2,y,3.3),(1.2,1.6,.16),steel,root,.12)
 if kind!='battleship':
  for side in [-1,1]:
   for dy in [-.4,.4]:beam('Torpedo tube',(side*W*.30,-L*.22+dy,4.5),(side*(W*.30+3),-L*.22+dy,4.5),.25,dark,root)
 # Consolidate static meshes to a small number of material primitives.
 static=[o for o in root.children if o.type=='MESH']
 bpy.ops.object.select_all(action='DESELECT')
 for o in static:o.select_set(True)
 bpy.context.view_layer.objects.active=static[0];bpy.ops.object.join();bpy.context.object.name=kind+'_StaticDetail'
 for t in [o for o in root.children if o.name.startswith('MainTurret')]:
  parts=[o for o in t.children if o.type=='MESH'];bpy.ops.object.select_all(action='DESELECT')
  for o in parts:o.select_set(True)
  bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();bpy.context.object.name=t.name+'_Guns'
 def selecttree(o):
  o.select_set(True)
  for c in o.children:selecttree(c)
 bpy.ops.object.select_all(action='DESELECT');selecttree(root)
 bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,kind+'.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True)
 return root
fleet=[]
for kind,L,W in [('battleship',86,13.6),('cruiser',70,10.5),('destroyer',55,7.8)]:fleet.append(build_ship(kind,L,W))
# Spread out the three editable models for the .blend asset workspace.
for i,r in enumerate(fleet):r.location.x=(i-1)*32
world=bpy.context.scene.world or bpy.data.worlds.new('World');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.24,.29,1)
bpy.ops.object.light_add(type='AREA',location=(40,20,80));bpy.context.object.data.energy=3500;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=60
bpy.ops.object.light_add(type='SUN',location=(0,0,50));bpy.context.object.rotation_euler=(.4,-.5,-.5);bpy.context.object.data.energy=3
bpy.ops.object.camera_add(location=(135,135,120));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=175;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','Iron_Tide_Fleet.blend'))
scene.render.filepath=os.path.join(ROOT,'blender','fleet-preview.png');bpy.ops.render.render(write_still=True)
print('FLEET_BUILD_COMPLETE')
