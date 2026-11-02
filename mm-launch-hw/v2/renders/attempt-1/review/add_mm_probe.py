import bpy, sys, bmesh
from mathutils import Matrix, Vector
sys.path.insert(0, "/Users/alxchunlin/code-stuff/alex-3d-skills-pin/skills/print-cad-blender/scripts")
# ellipsoid 13 x 13 x 7 and a true lentil (two spherical caps, 13 dia x 7 thick) edge-on, side by side in the +60 parked pocket
def ellipsoid(name, c, n):
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1.0); bm.to_mesh(me); bm.free()
    q = Vector((0,0,1)).rotation_difference(Vector(n).normalized())
    ob.matrix_world = Matrix.Translation(c) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((6.5,6.5,3.5,1))
    return ob
def lentil(name, c, n):
    # sphere radius R with cap height h=3.5 and chord 13: R = (6.5^2+3.5^2)/(2*3.5)
    R = (6.5**2 + 3.5**2) / 7.0
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=48, radius=R)
    # intersect two spheres: keep vertices projected: z' = sign(z)*max(0, ...) -> build by clamping
    for v in bm.verts:
        pass
    bm.free()
    import math
    verts=[]; faces=[]
    NU, NV = 48, 24
    for i in range(NV+1):
        t = i / NV  # 0..1 from +z pole to -z pole along the profile
        rho = 6.5 * math.sin(math.pi * t)
        # cap surface z for given rho
        zc = math.sqrt(max(R*R - rho*rho, 0)) - (R - 3.5)
        z = zc if t <= 0.5 else -zc
        for j in range(NU):
            a = 2*math.pi*j/NU
            verts.append((rho*math.cos(a), rho*math.sin(a), z))
    for i in range(NV):
        for j in range(NU):
            a=i*NU+j; b=i*NU+(j+1)%NU; faces.append((a,b,b+NU,a+NU))
    me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(me); bm.free()
    q = Vector((0,0,1)).rotation_difference(Vector(n).normalized())
    ob.matrix_world = Matrix.Translation(c) @ q.to_matrix().to_4x4()
    return ob
cy = 18.187
ellipsoid("ZMM_ellA", (7.0, cy, 269.5), (1,0,0)); ellipsoid("ZMM_ellB", (14.0, cy, 269.5), (1,0,0))
lentil("ZMM_lenA", (7.0, cy, 269.5), (1,0,0)); lentil("ZMM_lenB", (14.0, cy, 269.5), (1,0,0))
bpy.ops.wm.save_as_mainfile(filepath="/tmp/rv1/model_mm.blend")
