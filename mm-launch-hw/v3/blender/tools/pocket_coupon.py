"""Feeder pocket test coupon (v2-A3-A1-03). Tool STL only, not in the assembly.

    cd blender && cad py tools/pocket_coupon.py [OUT.stl]       # default ../stl/tools/test_pocket_coupon.stl

An 8 mm disc (the feeder disc's DISC_T) with four through pockets at POCKET_COUPON_D = 13.6 / 13.75 / 13.9 / 14.1, each
cut with the disc's own profile: straight bore plus the POCKET_CH 1 x 45 lead-in on the top rim. Print it like
PRT_feeder_disc (flat, chamfered face up, same material and slicer settings), so the printed bores carry the same shrink.
Pocket k (0..3, smallest first) has k + 1 R1 notches in the rim next to it.

Use: caliper 20 candies and write MM_D / MM_T (min, max) into params.py. Then, for each pocket, check
  - one flat candy of the largest diameter drops through, and
  - two of the thinnest candies stood edge-on side by side cannot both enter (push gently; they must ride on the rim).
Set POCKET_D to the smallest pocket that passes the flat candy and still blocks the pair, rebuild, and re-run
`cad check` (payload_fit and the 4 pocket ray rows follow POCKET_D).

Note: `cad build` deletes every *.stl directly in stl/ before it exports (cadlib export_stls clean=True), so run this
script after the last build, or pass an OUT path under stl/tools/ (the default since the A4 finish step; the build
leaves subfolders alone).
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
sys.path.insert(0, BL)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from cadlib import geom as G, export as E  # noqa: E402
import params as P  # noqa: E402

DIAS = getattr(P, "POCKET_COUPON_D", (13.6, 13.75, 13.9, 14.1))
T = P.DISC_Z[1] - P.DISC_Z[0]                   # 8.0, the feeder disc thickness
CH = P.POCKET_CH
RP = 14.0                                       # pocket circle: 14 * sqrt(2) = 19.8 between centres, >= 3.7 of web
R_OD = RP + max(DIAS) / 2 + CH + 3.5            # >= 3.5 of rim outside the chamfer


def build():
    disc = G.cyl("cpn", (0.0, 0.0), R_OD, 0.0, T, n=256)
    G.bevel(disc, P.EB)
    sub = []
    for k, d in enumerate(DIAS):
        a = math.radians(45.0 + 90.0 * k)
        c = (RP * math.cos(a), RP * math.sin(a))
        rp = d / 2
        sub.append(G.revolve("cpp%d" % k, [(0.0, -1.0), (rp, -1.0), (rp, T - CH), (rp + CH + 1.0, T + 1.0), (0.0, T + 1.0)],
                             center=(c[0], c[1], 0.0), n=128))
        for j in range(k + 1):                  # k + 1 notches in the rim, centred on the pocket's bearing
            b = a + math.radians(7.0 * (j - k / 2.0))
            sub.append(G.cyl("cpn%d_%d" % (k, j), (R_OD * math.cos(b), R_OD * math.sin(b)), 1.0, -1.0, T + 1.0, n=24))
    return G.csg(disc, sub=sub)


def bore(ob, k, z):
    """pocket k diameter along two axes at height z, by ray casts from its centre"""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(ob, dg)
    a = math.radians(45.0 + 90.0 * k)
    c = Vector((RP * math.cos(a), RP * math.sin(a), z))
    out = []
    for u in (Vector((1, 0, 0)), Vector((0, 1, 0))):
        h1, h2 = tree.ray_cast(c, u), tree.ray_cast(c, -u)
        out.append((h1[0] - h2[0]).length)
    return out


def main():
    argv = sys.argv[1:]
    out = argv[0] if argv else os.path.join(os.path.dirname(BL), "stl", "tools", "test_pocket_coupon.stl")
    ob = build()
    ob["print_rot"] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    for k, d in enumerate(DIAS):
        lo, hi = bore(ob, k, 1.0), bore(ob, k, T - CH - 1.0)
        print("COUPON pocket %d: nominal %.2f, bore at z 1.0 %.3f / %.3f, at z %.1f %.3f / %.3f, notches %d"
              % (k, d, lo[0], lo[1], T - CH - 1.0, hi[0], hi[1], k + 1))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    E.write_stl(out, E.print_tris(ob))
    print("COUPON OD %.1f x %.1f, %d tris -> %s" % (2 * R_OD, T, len(ob.data.polygons), out))


main()
