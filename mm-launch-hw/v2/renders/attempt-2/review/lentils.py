import bpy, math, bmesh
from mathutils import Matrix, Vector
def lentil(name, c, D, T):
    r=D/2; h=T/2; R=(r*r+h*h)/(2*h)
    me=bpy.data.meshes.new(name); ob=bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    verts=[]; faces=[]; NU,NV=64,32
    for i in range(NV+1):
        t=i/NV; rho=r*math.sin(math.pi*t)
        zc=math.sqrt(max(R*R-rho*rho,0))-(R-h); z=zc if t<=0.5 else -zc
        for j in range(NU):
            a=2*math.pi*j/NU; verts.append((z, rho*math.cos(a), rho*math.sin(a)))  # axis along x (edge-on, thickness along x)
    for i in range(NV):
        for j in range(NU):
            a=i*NU+j; b=i*NU+(j+1)%NU; faces.append((a,b,b+NU,a+NU))
    me.from_pydata(verts,[],faces); me.update()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(me); bm.free()
    ob.matrix_world=Matrix.Translation(c)
cx, cy, fl = 10.5, 18.187, 263.0
for tag,D,T in (("N",13.0,7.0),("S",12.5,6.5),("M",12.8,6.8)):
    for k,s in (("a",-1),("b",1)):
        lentil("ZMM_%s%s"%(tag,k), (cx+s*(T/2+0.0), cy, fl+D/2+0.02), D, T)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/rv2/probe/model_mm.blend")
