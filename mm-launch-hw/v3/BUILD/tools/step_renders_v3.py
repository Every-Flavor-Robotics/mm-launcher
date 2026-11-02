"""Assembly step renders for BUILD/ASSEMBLY.md (960 x 720, Workbench), v3 step labels. Not part of the build.

    cad py tools/step_renders_v3.py /tmp/<copy>/model.blend      # run from v3/BUILD; never pass blender/model.blend

v3 port of blender/tools/step_renders.py (prior art, unchanged method). That script hard-codes v2 labels ("2b" floor
bench, "3", the 11a.0 prop view) and opens blender/model.blend; this one takes v3's checks.json labels and renders from
a copy. Each view shows what is on the bench or the machine at the END of a checks.json `assembly_order` step: the main
assembly is every non-bench entry up to that step plus every bench that has merged by then; a bench view is that bench's
entries only. The model is drawn the right way up even where the BOM builds a part upside down (step 1). The blend is
never saved.
"""
import fnmatch, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.dirname(HERE)
V3 = os.path.dirname(BUILD)
OUT = os.path.join(BUILD, "renders")
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from cadlib import render as R  # noqa: E402

ORDER = json.load(open(os.path.join(V3, "blender", "checks.json")))["assembly_order"]
LABEL = [e["step"].split(" ")[0] for e in ORDER]


def matches(name, globs):
    return any(fnmatch.fnmatchcase(name, g) for g in globs)


def visible_set(upto, bench=None):
    i_end = LABEL.index(upto)
    globs = []
    if bench:
        for e in ORDER[:i_end + 1]:
            if e.get("bench") == bench:
                globs += e["objects"]
        return globs
    merged = {e["merge"] for e in ORDER[:i_end + 1] if "merge" in e}
    for e in ORDER[:i_end + 1]:
        if "bench" not in e or e["bench"] in merged:
            globs += e["objects"]
    return globs


def set_pose(**deg):
    for o in bpy.data.objects:
        if o.type == 'EMPTY' and o.name.startswith("PIV_") and "joint_axis" in o.keys():
            if o.get("joint_kind") == "prismatic":
                continue
            r = [0.0, 0.0, 0.0]
            r["XYZ".index(o["joint_axis"])] = math.radians(deg.get(o.name, 0.0))
            o.rotation_euler = r
    bpy.context.view_layer.update()


def show_only(globs, hide=()):
    shown = []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        on = matches(o.name, globs) and not matches(o.name, hide)
        o.hide_render = not on
        if on:
            shown.append(o)
    return shown


def frame(objs, view_dir, margin=1.12):
    """ortho camera along view_dir, fitted to the objects' world bounding boxes"""
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2
    d = Vector(view_dir).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((0, 1, 0))
    right = d.cross(up).normalized()
    upv = right.cross(d).normalized()
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    w = max((p - c).dot(right) for p in corners) * 2
    h = max((p - c).dot(upv) for p in corners) * 2
    R.camera(tuple(c - d * 1500), tuple(c), ortho=max(w, h * 960 / 720) * margin)


def shoot(name, upto, view, bench=None, pose=None, hide=(), margin=1.12):
    """view = the direction the camera looks along (world X right, Y front, Z up)"""
    set_pose(**(pose or {}))
    objs = show_only(visible_set(upto, bench), hide)
    frame(objs, view, margin)
    p = R.shot(os.path.join(OUT, name + ".png"))
    print("STEP_RENDER %s (step %s%s): %d objects -> %s" % (name, upto, ", bench " + bench if bench else "", len(objs), p))


def main():
    blend = sys.argv[1]
    if os.path.samefile(os.path.dirname(os.path.abspath(blend)), os.path.join(V3, "blender")):
        raise SystemExit("step_renders_v3: render from a copy of model.blend, not blender/model.blend")
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=blend)
    R.setup(res=(960, 720))
    shoot("s01a_pan_drive_bench", "1a", (-1.0, -0.8, -0.6), bench="pandrive")
    shoot("s02b_hub_gear_from_below", "2b", (-0.35, -0.55, 1.0))
    shoot("s06_pod_bench", "6g", (-1.0, -0.8, -0.5), bench="pod")
    shoot("s08_tilt_servo_in_post", "8", (-1.0, -0.9, -0.6))
    shoot("s11_crown_on_beam", "11", (-1.0, -1.0, -0.7))
    shoot("s12_floor_bench", "12", (0.55, -0.8, -0.9), bench="floor")
    shoot("s14_jar_bench_from_below", "14", (-0.6, -0.8, 0.55), bench="jar", hide=("BUY_mm_fill",))


main()
