"""Assembly step renders for BUILD/ASSEMBLY.md (960 x 720, Workbench). Not part of the build.

    cd blender && cad py tools/step_renders.py [PROP_BLEND]

Each view shows what is on the bench or the machine at the END of a checks.json `assembly_order` step: the main
assembly is every non-bench entry up to that step plus every bench that has merged by then; a bench view is that
bench's entries only. PROP_BLEND (default /tmp/mm_prop_model.blend, written by `cad py tools/tilt45_prop.py --blend`)
adds the 11a.0 view: post cover off, tilt servo slid +X 10 out of its socket, pod at 45 on the printed prop.
The model is drawn the right way up even where the BOM builds a part upside down (step 1).
"""
import fnmatch, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
OUT = os.path.join(os.path.dirname(BL), "BUILD", "renders")
sys.path.insert(0, BL)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from cadlib import render as R  # noqa: E402

ORDER = json.load(open(os.path.join(BL, "checks.json")))["assembly_order"]
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
            v = math.radians(deg.get(o.name, 0.0))
            if o.get("joint_kind") == "prismatic":
                continue
            r = [0.0, 0.0, 0.0]
            r["XYZ".index(o["joint_axis"])] = v
            o.rotation_euler = r
    bpy.context.view_layer.update()


def show_only(globs, extra=()):
    shown = []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        on = matches(o.name, globs) or o.name in extra
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
    # ortho width: the bbox corners projected on the camera plane
    up = Vector((0, 0, 1))
    right = d.cross(up).normalized()
    upv = right.cross(d).normalized()
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    w = max((p - c).dot(right) for p in corners) * 2
    h = max((p - c).dot(upv) for p in corners) * 2
    ortho = max(w, h * 960 / 720) * margin
    R.camera(tuple(c - d * 1500), tuple(c), ortho=ortho)


def shoot(name, upto, view, bench=None, pose=None, extra=(), hide=(), focus=None, margin=1.12):
    """view = the direction the camera looks along (world X right, Y front, Z up); focus = names to frame on"""
    set_pose(**(pose or {}))
    objs = [o for o in show_only(visible_set(upto, bench), extra) if not matches(o.name, hide)]
    for o in bpy.data.objects:
        if o.type == 'MESH' and matches(o.name, hide):
            o.hide_render = True
    frame([bpy.data.objects[n] for n in focus] if focus else objs, view, margin)
    p = R.shot(os.path.join(OUT, name + ".png"))
    print("STEP_RENDER %s: %d objects -> %s" % (name, len(objs), p))


def main():
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=os.path.join(BL, "model.blend"))
    R.setup(res=(960, 720))
    shoot("s02_floor_plate_bench", "2b", (-0.6, 0.8, -0.9), bench="floor")
    shoot("s03_base_turntable_done", "3", (-1.0, -1.0, -0.8))
    shoot("s06_pod_bench", "6g", (-1.0, -0.8, -0.5), bench="pod")
    shoot("s08_pod_in_posts_tilt_servo", "8", (-1.0, -0.9, -0.6))
    shoot("s11_feeder_on_beam", "11", (-1.0, -1.0, -0.7))
    prop = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mm_prop_model.blend"
    if os.path.exists(prop):
        bpy.ops.wm.open_mainfile(filepath=prop)
        R.setup(res=(960, 720))
        for n in ("BUY_servo_tilt", "BUY_horn_tilt", "PRT_tilt_horn_adapter") + tuple(
                o.name for o in bpy.data.objects if o.name.startswith("FST_tilt_horn_")):
            ob = bpy.data.objects.get(n)
            if ob is not None:
                ob.location.x += 10.0
        # the prop is a tool, not a machine part: drawn in the style guide's first series blue (#1f4fd8) so it reads
        # apart from the two PLA colours
        m = bpy.data.materials.new("tool_blue")
        m.diffuse_color = (0.0137, 0.0782, 0.686, 1.0)
        pr = bpy.data.objects["PRT_tilt45_prop"]
        pr.data.materials.clear()
        pr.data.materials.append(m)
        kw = dict(pose={"PIV_tilt": 45}, extra=("PRT_tilt45_prop",), hide=("PRT_post_R_cover", "FST_postcover_*"))
        shoot("s11a0_pod_on_45_prop", "11", (-0.9, -1.0, -0.45), **kw)
        shoot("s11a0_prop_closeup", "11", (-0.8, -1.0, -0.25), focus=("PRT_tilt45_prop", "PRT_nip_cover", "PRT_groove_cap"),
              margin=1.0, **kw)


main()
