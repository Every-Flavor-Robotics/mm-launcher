"""Fit-test coupons for MEASURE_FIRST.md item 2: small crops of the real parts, in their real print orientation.

    cad py tools/fit_coupons.py /tmp/<copy>/model.blend [OUT_DIR]     # run from v3/BUILD; never pass blender/model.blend

Each coupon is one printed part intersected with a world-space box (cadlib geom.csg, Manifold solver), then exported
with that part's own print_rot through cadlib export.print_tris, exactly as `cad build` exports the full STL. So the
snap or slot on the coupon prints in the same layer direction, on the same layers relative to its catch, as on the
part. Every coupon's bed face is either the part's own bed face or a flat cut parallel to it.

Pairs (A = grey, print like the parent part):
  c1  beam hook, right post front (BEAM_HOOK pos (43, 18)): a post-top crop of PRT_turntable + the matching PRT_beam crop.
  c2  hub socket: the centre of PRT_turntable (|x|, |y| <= 30, the whole 10 mm disc); push the real hub_gear into it.
  c3  crown hook, rear-left (IF_CROWN_HOOKS (-36, -22)): a PRT_feeder_crown crop + the matching PRT_beam slot crop.
  c4  MotorGo card guides: the bottom 30 mm of PRT_base_floor's partition wall and both guides; slide the real board in.

Writes OUT_DIR/<name>.stl (default ../BUILD/plates/0a-fit-coupons-grey) and prints volume, size and est. grams per coupon.
Does not save the blend.
"""
import os, sys

import bpy  # noqa: E402
from cadlib import geom as G, export as E  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.dirname(HERE)

# name: (source object, world box x0 x1 y0 y1 z0 z1)
COUPONS = {
    "c1_beam_hook_post": ("PRT_turntable", (37.0, 52.0, 11.0, 26.0, 226.0, 253.0)),
    "c1_beam_hook_beam": ("PRT_beam", (37.0, 52.0, 11.0, 26.0, 224.0, 264.0)),
    "c2_hub_socket": ("PRT_turntable", (-30.0, 30.0, -30.0, 30.0, 91.0, 103.0)),
    "c3_crown_hook_crown": ("PRT_feeder_crown", (-46.0, -26.0, -32.0, -12.0, 251.0, 276.0)),
    "c3_crown_hook_beam": ("PRT_beam", (-46.0, -26.0, -32.0, -12.0, 249.0, 264.0)),
    "c4_card_guides": ("PRT_base_floor", (-77.0, -1.0, -96.0, -58.0, -1.0, 30.0)),
}


def world_copy(src, name):
    """a new object holding src's evaluated mesh in world coordinates (identity matrix), with src's print_rot"""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = src.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    me.transform(src.matrix_world)
    ob = bpy.data.objects.new(name, me)
    G.scratch().objects.link(ob)
    ob["print_rot"] = [list(r) for r in src["print_rot"]]
    return ob


def main():
    argv = sys.argv[1:]
    blend = argv[0]
    out = argv[1] if len(argv) > 1 else os.path.join(BUILD, "plates", "0a-fit-coupons-grey")
    if os.path.samefile(os.path.dirname(os.path.abspath(blend)), os.path.join(os.path.dirname(BUILD), "blender")):
        raise SystemExit("fit_coupons: run on a copy of model.blend, not blender/model.blend")
    bpy.ops.wm.open_mainfile(filepath=blend)
    os.makedirs(out, exist_ok=True)
    for name, (src, (x0, x1, y0, y1, z0, z1)) in COUPONS.items():
        ob = world_copy(bpy.data.objects[src], name)
        G.csg(ob, inter=[G.box(name + "_box", x0, x1, y0, y1, z0, z1)])
        nm, vol = G.solid_stats(ob)
        tris = E.print_tris(ob)
        xs = [v.x for t in tris for v in t]; ys = [v.y for t in tris for v in t]; zs = [v.z for t in tris for v in t]
        p = os.path.join(out, name + ".stl")
        E.write_stl(p, tris)
        print("COUPON %-22s from %-17s vol %7.0f mm3 (%.1f g solid PLA) size %.1f x %.1f x %.1f, non-manifold %d -> %s"
              % (name, src, vol, vol * 1.24e-3, max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), nm, p))


main()
