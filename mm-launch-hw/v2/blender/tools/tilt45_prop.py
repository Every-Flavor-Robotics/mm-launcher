"""45 deg assembly prop for BOM step 11a.0 (review 7, A7-01). Tool STL only, not in the assembly.

    cd blender && cad py tools/tilt45_prop.py [--blend OUT.blend]     # writes ../stl/tools/tilt45_prop.stl

Step 11a needs the pod at tilt 45 (FST_gcap_5 is reachable only there), but the tilt servo is unpowered at that step.
11a.0 takes the right post cover off and slides the tilt servo +X about 10 out of the journal-plate socket, so the pod
swings freely. Unpowered, the pod's CG (motor forward of and below the tilt axis) swings it nose-down; this prop holds
it at 45 instead:

- a pad whose top is the plane of the nip cover's flat underside at tilt 45 (measured here by rays on the built
  model, so it follows params), x inset 3 from the cover's sides, y PAD_Y, standing on the turntable top (IF_TT_Z1);
- a low foot running +X to the right post's front face (found by a ray). The pod pushes the pad back (-Y) as well as
  down (the underside slopes about 26 deg), and the foot hands that push to the post instead of to friction.

The pad starts at y 31.5: behind it are the groove cap disc (R 24) and FST_gcap_5 (10, 16.2). With --blend the script
also saves a scratch copy of the model with the prop as PRT_tilt45_prop on PIV_pan, so `cad q` and `cad check --only
service` can measure it at tilt 45 (it can't live in the real model: at tilt < 45 the pod would sweep through it).
Print it base down (the turntable face on the bed): every face is vertical or faces up, no supports.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
sys.path.insert(0, BL)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=os.path.join(BL, "model.blend"))
from cadlib import geom as G, export as E  # noqa: E402
import params as P  # noqa: E402

TILT = 45.0
PAD_Y = (31.5, 53.0)        # pad depth along y at tilt 45 (the cover's flat underside runs about y 6..55 there); y0 keeps
                            # cadcheck's 14 mm hand radius clear of FST_gcap_5 (10, 16.2): at y0 28 it fell back to the L-key
PAD_INSET = 3.0             # pad inset from the cover's +-X sides (the cover's edge break is EB 1.0)
FOOT_X1 = 56.0              # foot reaches 10 past the post's corner round (flat front face from x ~45)
FOOT_DY = 0.3               # foot back face this far in front of the post face: slides in, bears after 0.3
FOOT_W, FOOT_H = 11.7, 10.0


def set_tilt(deg):
    for o in bpy.data.objects:
        if o.type == 'EMPTY' and o.name.startswith("PIV_") and "joint_axis" in o.keys():
            r = [0.0, 0.0, 0.0]
            if o.name == "PIV_tilt":
                r["XYZ".index(o["joint_axis"])] = math.radians(deg)
            elif "couple_to" in o.keys():
                continue
            if o.get("joint_kind") != "prismatic":
                o.rotation_euler = r
    bpy.context.view_layer.update()


def world_bvh(names):
    vs, fs = [], []
    for n in names:
        ob = bpy.data.objects[n]
        M = ob.matrix_world
        k = len(vs)
        vs += [M @ v.co for v in ob.data.vertices]
        fs += [[k + i for i in p.vertices] for p in ob.data.polygons]
    return BVHTree.FromPolygons(vs, fs)


def first_hit(tree, o, d):
    h = tree.ray_cast(Vector(o), Vector(d).normalized())
    return h[0]


def main():
    argv = sys.argv[1:]
    blend_out = argv[argv.index("--blend") + 1] if "--blend" in argv else None
    out = os.path.join(os.path.dirname(BL), "stl", "tools", "tilt45_prop.stl")
    set_tilt(TILT)
    cover = bpy.data.objects["PRT_nip_cover"]
    cx = [(cover.matrix_world @ v.co).x for v in cover.data.vertices]
    x0, x1 = min(cx) + PAD_INSET, max(cx) - PAD_INSET
    tree = world_bvh(["PRT_nip_cover"])
    zb = P.IF_TT_Z1
    # underside plane z = a + b*y from vertical rays at both pad ends, both sides
    pts = []
    for x in (x0 + 1.0, x1 - 1.0):
        for y in PAD_Y:
            h = first_hit(tree, (x, y, zb + 0.5), (0, 0, 1))
            assert h is not None, "no nip cover over (%.1f, %.1f) at tilt %g" % (x, y, TILT)
            pts.append(h)
    b = ((pts[1].z - pts[0].z) / (pts[1].y - pts[0].y) + (pts[3].z - pts[2].z) / (pts[3].y - pts[2].y)) / 2
    a = sum(p.z - b * p.y for p in pts) / 4
    flat = max(abs(p.z - (a + b * p.y)) for p in pts)
    assert flat < 0.05, "cover underside is not one plane over the pad (%.3f)" % flat
    # the right post's front face, straight ahead of the foot
    post = world_bvh(["PRT_post_R"])
    pf = first_hit(post, (FOOT_X1 - 4.0, 60.0, zb + FOOT_H / 2), (0, -1, 0))
    assert pf is not None
    fy0 = pf.y + FOOT_DY
    zp = lambda y: a + b * y                                       # noqa: E731
    pad = G.prism("t45pad", [(PAD_Y[0], zb), (PAD_Y[1], zb), (PAD_Y[1], zp(PAD_Y[1])), (PAD_Y[0], zp(PAD_Y[0]))],
                  x0, x1, 'X')
    G.bevel(pad, P.EB)
    foot = G.box("t45foot", x1 - 4.0, FOOT_X1, fy0, fy0 + FOOT_W, zb, zb + FOOT_H)
    G.bevel(foot, P.EB)
    ob = G.csg(pad, add=[foot])
    # the bevel takes EB off the contact face's edges only; the face itself stays on the plane
    set_tilt(0.0)
    vol = G.solid_stats(ob)[1]
    ob["print_rot"] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    E.write_stl(out, E.print_tris(ob))
    xs = [(ob.matrix_world @ v.co) for v in ob.data.vertices]
    lo = Vector((min(v.x for v in xs), min(v.y for v in xs), min(v.z for v in xs)))
    hi = Vector((max(v.x for v in xs), max(v.y for v in xs), max(v.z for v in xs)))
    print("PROP underside plane at tilt %g: z = %.3f %+.4f*y (%.1f deg), flat to %.3f; pad x %.1f..%.1f y %.1f..%.1f, "
          "height %.1f (back) / %.1f (front)" % (TILT, a, b, math.degrees(math.atan(-b)), flat, x0, x1, PAD_Y[0],
                                                PAD_Y[1], zp(PAD_Y[0]) - zb, zp(PAD_Y[1]) - zb))
    print("PROP post front face y %.3f, foot y %.2f..%.2f x %.1f..%.1f; bbox %s..%s = %.1f x %.1f x %.1f; volume %.1f cm3"
          % (pf.y, fy0, fy0 + FOOT_W, x1 - 4.0, FOOT_X1, tuple(round(c, 2) for c in lo), tuple(round(c, 2) for c in hi),
             hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, vol / 1000.0))
    print("PROP -> %s" % out)
    if blend_out:
        piv = bpy.data.objects["PIV_pan"]
        ob.name = ob.data.name = "PRT_tilt45_prop"
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        bpy.data.collections["Printed"].objects.link(ob)
        ob.parent = piv
        ob.matrix_parent_inverse = piv.matrix_world.inverted()
        for k, v in (("stl", "tools/tilt45_prop"), ("orient", "base down"), ("supports", "no"), ("infill", 20),
                     ("kind", "PRT"), ("joint", "PIV_pan")):
            ob[k] = v
        for o in [o for o in bpy.data.objects if o.users_collection and o.users_collection[0].name.startswith("scratch")]:
            bpy.data.objects.remove(o)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend_out), copy=True)
        print("PROP scratch blend with PRT_tilt45_prop -> %s" % blend_out)


main()
