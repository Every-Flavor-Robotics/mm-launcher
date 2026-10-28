"""Lentil probe for the feeder pocket (v2-A2-A1-03), after renders/attempt-2/review/lentils.py.

Adds M&M-size lentils to the built model and saves a copy; measure them with `cad q dist`:

    blender -b blender/model.blend --python blender/tools/lentil_probe.py -- [OUT.blend]
    cad q OUT.blend dist ZMM_pair_a PRT_feeder_disc     # edge-on MM_D/MM_T min pair: must overlap (negative mm3)
    cad q OUT.blend dist ZMM_pair_b PRT_feeder_disc
    cad q OUT.blend dist ZMM_flat PRT_feeder_disc       # flat MM_D/MM_T max candy: must clear (positive mm)

Sizes come from params MM_D / MM_T (min, max). The lentil is the review's lens (two spherical caps, knife rim), so a
pair fits a pocket of radius R when R^2 >= (T/2)^2 + (D/2)^2. The pair stands edge-on in the +60 deg park pocket
(PIV_feeder home), thickness along x, symmetric about the pocket centre and touching at it, on the housing floor
(FEED_FLOOR_Z): the pair's best fit. The flat candy lies centred on the floor. OUT defaults to /tmp/lentil_probe/model_mm.blend.
"""
import math, os, sys
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.environ.get("CAD_SKILL", os.path.expanduser("~/code-stuff/alex-3d-skills-pin/skills/print-cad-blender"))
sys.path.insert(0, os.path.join(SKILL, "scripts"))          # params imports cadlib.asm (for joints())
sys.path.insert(0, os.path.dirname(HERE))
import params as P  # noqa: E402


def lentil(name, c, D, T, axis="X", nu=96, nv=48):
    """lens D x T centred at c; axis = the thickness direction ('X' edge-on, 'Z' flat)"""
    r, h = D / 2.0, T / 2.0
    R = (r * r + h * h) / (2.0 * h)
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    verts, faces = [], []
    for i in range(nv + 1):
        t = i / nv
        rho = r * math.sin(math.pi * t)
        zc = math.sqrt(max(R * R - rho * rho, 0.0)) - (R - h)
        w = zc if t <= 0.5 else -zc
        for j in range(nu):
            a = 2.0 * math.pi * j / nu
            u, v = rho * math.cos(a), rho * math.sin(a)
            verts.append((w, u, v) if axis == "X" else (u, v, w))
    for i in range(nv):
        for j in range(nu):
            a = i * nu + j
            b = i * nu + (j + 1) % nu
            faces.append((a, b, b + nu, a + nu))
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.to_mesh(me)
    bm.free()
    ob.matrix_world = Matrix.Translation(Vector(c))
    return ob


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[0] if argv else "/tmp/lentil_probe/model_mm.blend"
os.makedirs(os.path.dirname(out), exist_ok=True)
a = math.radians(60.0)
cx = P.IF_JAR_XY[0] + P.FEED_RP * math.cos(a)
cy = P.IF_JAR_XY[1] + P.FEED_RP * math.sin(a)
fl = P.FEED_FLOOR_Z
d0, t0 = P.MM_D[0], P.MM_T[0]
d1, t1 = P.MM_D[1], P.MM_T[1]
for k, s in (("a", -1.0), ("b", 1.0)):
    lentil("ZMM_pair_" + k, (cx + s * t0 / 2.0, cy, fl + d0 / 2.0 + 0.02), d0, t0, "X")
lentil("ZMM_flat", (cx, cy, fl + t1 / 2.0 + 0.02), d1, t1, "Z")
need = math.sqrt((t0 / 2.0) ** 2 + (d0 / 2.0) ** 2)
print("LENTIL_PROBE pocket centre (%.3f, %.3f) floor %.2f; pocket R %.3f; pair %.1f x %.1f needs R %.3f; flat %.1f x %.1f "
      "radial clearance %.3f" % (cx, cy, fl, P.POCKET_D / 2.0, d0, t0, need, d1, t1, P.POCKET_D / 2.0 - d1 / 2.0))
bpy.ops.wm.save_as_mainfile(filepath=out)
print("LENTIL_PROBE saved", out)
