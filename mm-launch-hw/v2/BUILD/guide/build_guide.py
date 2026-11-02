"""Build steps.json and the self-contained assembly_guide.html. Plain Python 3, no Blender.

    python3 build_guide.py            # needs assembly.glb from export_glb.py next to it

Reads (never writes) ../ASSEMBLY.md, ../PRINT_PLAN.md data (../plates.json, ../print_estimate.json), ../renders/,
../../blender/{checks.json,manifest.json}, ../../renders/attempt-7/ and the alex-style web files. Writes steps.json and
assembly_guide.html in this folder.

Step mapping: every ASSEMBLY.md step is tied to the checks.json assembly_order entries with the same label (8a, 8b share
one heading; 11a.1-11a.9 is entry 11a). Its new objects are the entries' globs resolved against the GLB node names, minus
anything an earlier step already placed. Fastener counts in the step text are compared with the manifest's per-fastener
step labels (the model calls step 8 "8c"). A step is "clean" when its entries exist, every glob that names a part the
text asks for resolves, and the counts agree; otherwise it is "flagged" with the reason. Hand-written per-step data
(explode directions, poses, camera directions, warnings) is in CURATED below, with the ASSEMBLY.md / MEASURE_FIRST.md
line each warning comes from.
"""
import base64
import fnmatch
import html
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.dirname(HERE)
V2 = os.path.dirname(BUILD)
BL = os.path.join(V2, "blender")
A7 = os.path.join(V2, "renders", "attempt-7")
STYLE = "/Users/alxchunlin/code-stuff/alex-style-guide/web"
GLB = os.path.join(HERE, "assembly.glb")
OUT_HTML = os.path.join(HERE, "assembly_guide.html")
OUT_STEPS = os.path.join(HERE, "steps.json")
THREE = "0.170.0"   # the version the style guide's ax-three.js is written against

# ---------------------------------------------------------------- curated per-step data
# Directions are in the design frame (+X right, +Y front/muzzle, +Z up). "explode" maps object globs to a direction
# (length scales the travel); fasteners not listed back out along -into from the manifest (nuts move along +into).
# "view" is where the camera sits relative to the focus parts. "pose" sets pan/tilt on entering the step.
UP, DOWN, RIGHT, LEFT, FRONT, BACK = [0, 0, 1], [0, 0, -1], [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]
STUD = [0, -0.95, -0.32]          # nip stud axis, from FST_nip_stud.into
DEFAULT_VIEW = [1.0, 1.25, 0.9]

CURATED = {
    "0": dict(view=[1.0, 1.3, 0.8],
              warnings=[
                  ("critical", "All three servos ship as bus ID 1. Give pan, tilt and feeder different IDs and label each "
                               "servo before anything else: after step 11a they share one bus.", "ASSEMBLY 0"),
                  ("warning", "Command each servo to mid (500 on the 0..1000 scale) before its horn goes on, and don't turn "
                              "the output by hand after that. Mid is pan 0, tilt 0 and the feeder's park position.",
                   "ASSEMBLY 0"),
                  ("warning", "Measure first: MEASURE_FIRST.md done and the model rebuilt if anything changed, before the "
                              "plates that depend on it.", "ASSEMBLY 0"),
                  ("warning", "Clean every Ø2.5 pilot with a Ø2.5 drill if your printer prints holes small. A forced "
                              "screw splits the boss.", "ASSEMBLY 0")]),
    "1": dict(explode={"BUY_dewalt_adapter": DOWN}, view=[1.0, -0.8, -0.35],
              warnings=[("warning", "Measure first (item 6): the adapter's corner hole size is unknown. If the holes are "
                                    "Ø3 or bigger the self-tappers won't bite; use machine screws and nuts, or epoxy. "
                                    "Screw tips must stay 3 or more above the battery face (4.56 now).", "MEASURE_FIRST 6")]),
    "1a": dict(explode={"BUY_horn_pan": [0, 0, -1.2]}, view=[1.0, 1.0, -0.3],
               warnings=[("warning", "Measure first (item 3): check the horn's bolt circle against the dimples before "
                                     "drilling through.", "MEASURE_FIRST 3")]),
    "1b": dict(explode={"BUY_servo_pan": [0, 0, -1.2], "PRT_pan_servo_clamp": [0, 0, -2.0]}, view=[1.0, 1.0, -0.3],
               warnings=[("warning", "Press the pinion onto the spline with the servo still at mid.", "ASSEMBLY 1b")]),
    "1c": dict(explode={"*": [0, 0, -1.0]}, view=[1.0, 1.2, -0.3]),
    "2a": dict(explode={"PRT_base_partition": UP, "BUY_motorgo_axis": [0, 1.4, 0]}, view=[-1.0, -0.6, 0.7],
               warnings=[("warning", "Measure first (item 4): the MotorGo STL shows Ø2.5 holes, so the model uses M2.5. "
                                     "If your board's holes are Ø3.2 or more, switch MG_* to M3 and rebuild before plate 9.",
                          "MEASURE_FIRST 4")]),
    "2b": dict(explode={"BUY_buck_12v": UP, "BUY_servo_controller": UP}, view=[0.6, -1.0, 0.6],
               warnings=[("warning", "Measure first (items 5, 7): the controller's holes come from a photo. Drill Ø2.5 "
                                     "through the board's own holes; the dimples are only a guess. Check the switch and "
                                     "terminal line up with the shell's two +X windows.", "MEASURE_FIRST 5")]),
    "2c": dict(explode={"PRT_post_L": UP, "PRT_post_R": UP}, view=[1.0, 1.2, 0.35],
               warnings=[("warning", "Leave the groove cap and its 6 screws in the bag. The cap goes on at 11a, after "
                                     "every bus lead is in the groove.", "ASSEMBLY 2c")]),
    "2d": dict(explode={"*": [0, 0, 1.0], "PRT_thrust_ring": [0, 0, 0.6], "PRT_hub_gear": [0, 0, -1.2]},
               view=[1.0, 1.1, -0.25],
               warnings=[("warning", "Mesh the hub gear with the pan servo at mid and the posts square across the base, so "
                                     "the pod faces +Y at pan 0.", "ASSEMBLY 2d")]),
    "3": dict(explode={"*": [0, 0, -1.0], "CAB_*": [0, 0, 0], "BUY_usbc_plug": [0, 0, 0]}, view=[1.0, -1.0, -0.25],
              warnings=[("warning", "Both U-loops must hang free under the hub gear: they are the ±90 pan slack. Turn the "
                                    "turntable to both stops before the floor closes.", "ASSEMBLY 3")]),
    "6a": dict(explode={"PRT_launcher_body": [1.2, 0, 0], "BUY_motor": [-1.3, 0, 0], "CAB_*": [0, 0, 0]},
               view=[0.35, 1.0, 0.4]),
    "6b": dict(explode={"BUY_magnet": [-0.8, 0, 0], "BUY_plink_encoder": [-1.3, 0, 0], "PRT_encoder_cap": [-1.8, 0, 0],
                        "CAB_*": [0, 0, 0]}, view=[-0.5, 1.0, 0.4],
               warnings=[("warning", "Glue the magnet with the printed jig and wait 10 min. The magnet stack's worst case "
                                     "is 0.30 against 0.30.", "ASSEMBLY 6b")]),
    "6c": dict(explode={"PRT_nip_stop": [0, 0, -1.0]}, view=[1.0, 0.6, -0.2]),
    "6d": dict(explode={"PRT_hood": [1.0, 0, 0], "PRT_journal_plate": [1.8, 0, 0]}, view=[0.5, -0.6, 0.8],
               warnings=[("warning", "The hinge axle needs a 2 mm hex bit with 104 mm of reach. Drive it here on the "
                                     "bench; there's no room for the bit later.", "ASSEMBLY 6d")]),
    "6e": dict(explode={"PRT_nip_stop_sleeve": [s * 0.7 for s in STUD], "PRT_nip_wheel": [s * 1.2 for s in STUD],
                        "FST_tw_nut": [s * 1.2 for s in STUD], "PRT_nip_leaf": [s * 1.7 for s in STUD],
                        "PRT_nip_cover": [s * 2.3 for s in STUD]}, view=[1.0, -0.35, 0.15]),
    "6f": dict(explode={"PRT_flywheel": [1.4, 0, 0], "BUY_tape": [1.4, 0, 0]}, view=[1.0, 0.9, 0.6],
               warnings=[("critical", "Butt-join the tape, no overlap. It must caliper 0.5 or less (TAPE_T) at three "
                                      "places and at the seam: an overlap doubles it and eats the 0.098 entry-arc margin.",
                          "ASSEMBLY 6f, MEASURE_FIRST 0")]),
    "6g": dict(explode={"PRT_launcher_cover": [1.2, 0, 0]}, view=[1.0, 0.9, 0.5]),
    "7": dict(explode={"*": [0, 0, 1.0]}, view=[1.0, 1.2, 0.3],
              warnings=[("warning", "Lower the pod nose-up about 20 deg, straight down, until both journals seat in the "
                                    "U-slots.", "ASSEMBLY 7")]),
    "8a, 8b": dict(explode={"BUY_horn_tilt": [1.0, 0, 0], "BUY_servo_tilt": [2.2, 0, 0]}, view=[0.5, 1.0, 0.5],
                   warnings=[("warning", "Fit the adapter to the tilt servo's spline with the servo at mid.",
                              "ASSEMBLY 8a, 8b")]),
    "8": dict(explode={"*": [1.0, 0, 0], "PRT_post_R_cover": [1.6, 0, 0], "CAB_*": [0, 0, 0]}, view=[0.6, 1.0, 0.4],
              warnings=[("warning", "Slide the servo in with the pod level (tilt 0).", "ASSEMBLY 8")]),
    "9": dict(explode={"PRT_beam": UP, "CAB_*": [0, 0, 0]}, view=[1.0, 1.2, 0.4],
              warnings=[("critical", "Don't swing the pod by hand from here on: that back-drives the tilt servo's gears. "
                                     "The tilt range is checked under power at step 15.", "ASSEMBLY 9")]),
    "10a": dict(explode={"BUY_horn_feeder": [0, 0, 1.2]}, view=[-0.6, 1.0, 0.35],
                warnings=[("warning", "Measure first (item 3): check the horn's bolt circle before drilling.",
                           "MEASURE_FIRST 3")]),
    "10b": dict(explode={"BUY_servo_feeder": [0, 0, 1.4]}, view=[-0.6, 1.0, 0.35],
                warnings=[("warning", "Servo #3 goes in at mid. There is no centre screw: the lobe cover holds it down.",
                           "ASSEMBLY 10b")]),
    "10c": dict(explode={"PRT_feeder_disc": [0, 0, -1.0], "PRT_feeder_housing": [0, 0, -1.8]}, view=[0.7, 1.0, -0.25],
                warnings=[("warning", "Fit the disc in the park position: solid disc over the outlet.", "ASSEMBLY 10c"),
                          ("warning", "Measure first (item 2): POCKET_D comes from the pocket coupon, before plate 3.",
                           "MEASURE_FIRST 2")]),
    "10d": dict(explode={"PRT_feeder_cover": UP, "CAB_*": [0, 0, 0]}, view=[-0.7, 1.0, 0.35]),
    "11": dict(explode={"*": [0, 0, 1.0]}, view=[1.0, 1.1, 0.35],
               warnings=[("warning", "Pod at tilt 0. Three of the four screws need the 2 mm L-key: the nacelle blocks a "
                                     "straight bit.", "ASSEMBLY 11")]),
    "11a.0": dict(extra=["TOOL_tilt45_prop"], pose={"tilt": 45},
                  hide=["PRT_post_R_cover", "FST_postcover_*"],
                  shift={"objects": ["BUY_servo_tilt", "BUY_horn_tilt", "PRT_tilt_horn_adapter", "FST_tilt_horn_*"],
                         "mm": [10, 0, 0]},
                  focus=["TOOL_tilt45_prop", "BUY_servo_tilt", "BUY_horn_tilt", "PRT_tilt_horn_adapter"],
                  explode={"TOOL_tilt45_prop": [0, 1.4, 0], "BUY_servo_tilt": [0, 0, 0], "BUY_horn_tilt": [0, 0, 0],
                           "PRT_tilt_horn_adapter": [0, 0, 0]},
                  view=[1.0, 1.0, 0.5],
                  warnings=[("critical", "The tilt servo can't be powered yet. Don't force the pod round: that back-drives "
                                         "the servo's gears. Free it by sliding the servo out instead.", "ASSEMBLY 11a.0"),
                            ("warning", "Don't turn the servo output while it's out, or the key won't go back in at the "
                                        "same flat.", "ASSEMBLY 11a.0"),
                            ("warning", "The prop's pad must bear on the nip cover's flat underside, not the thumbwheel "
                                        "(8.5 clear), so the gap setting is untouched.", "ASSEMBLY 11a.0")]),
    "11a.1 to 11a.9": dict(extra=["TOOL_tilt45_prop"], pose={"tilt": 45},
                           hide=["PRT_post_R_cover", "FST_postcover_*"],
                           shift={"objects": ["BUY_servo_tilt", "BUY_horn_tilt", "PRT_tilt_horn_adapter",
                                              "FST_tilt_horn_*"], "mm": [10, 0, 0]},
                           explode={"*": [0, 0, 1.0], "CAB_*": [0, 0, 0], "BUY_bus_junction": [0, 0, 1.6]},
                           view=[1.0, 1.2, 1.0],
                           warnings=[("critical", "The finished splice must be Ø10 x 20 or smaller.", "ASSEMBLY 11a.4"),
                                     ("warning", "Shield the PLA round the bore with card or foil while soldering.",
                                      "ASSEMBLY 11a.4"),
                                     ("warning", "Leave the bundle sleeve loose at the hand-over (no tie): it swings 5.66 "
                                                 "over ±90 pan.", "ASSEMBLY 11a.9")]),
    "11a.10": dict(focus=["PRT_post_R_cover", "FST_postcover_*", "BUY_servo_tilt", "BUY_horn_tilt",
                          "PRT_tilt_horn_adapter"],
                   explode={"PRT_post_R_cover": [1.6, 0, 0], "BUY_servo_tilt": [0, 0, 0], "BUY_horn_tilt": [0, 0, 0],
                            "PRT_tilt_horn_adapter": [0, 0, 0]},
                   view=[1.0, 0.8, 0.5],
                   warnings=[("warning", "Lift the pod to +46, take the prop out, lower it to the -3 stop, then slide the "
                                         "servo back. Keep the prop: it's the service fixture for the splice.",
                              "ASSEMBLY 11a.10")]),
    "12": dict(explode={"BUY_jar": [0, 0, 1.6], "BUY_mm_fill": [0, 0, 1.6], "BUY_jar_band": [0, 0, 1.0],
                        "PRT_jar_valve": [0, 0, -1.0], "PRT_jar_gate": [0, 0, -0.5], "PRT_gate_detent": [0, 1.0, 0]},
               view=[1.0, 1.2, 0.3],
               warnings=[("warning", "Measure first (item 1): caliper the jar band and lid before plate 3. A band over "
                                     "about 74 OD eats the 3.0 gap to the feeder housing.", "MEASURE_FIRST 1")]),
    "13": dict(explode={"*": [0, 0, 1.0]}, view=[1.0, 1.2, 0.35],
               warnings=[("warning", "Close the gate before you fill the jar.", "ASSEMBLY 13")]),
    "14": dict(explode={"BUY_battery": [1.2, 0, 0]}, view=[0.5, -1.0, 0.45]),
    "15": dict(view=[1.0, 1.3, 0.7],
               warnings=[("critical", "Power up with the flywheel motor disabled. Spin it up only after the servos are "
                                      "pinged, trimmed and the tilt is clamped to 0..45 in firmware.", "ASSEMBLY 15"),
                         ("warning", "If the pod isn't level at tilt 0, set a firmware offset rather than moving the horn.",
                          "ASSEMBLY 15")]),
}

# step id -> checks.json assembly_order labels
LABELS = {"8a, 8b": ["8a", "8b"], "11a.1 to 11a.9": ["11a"], "11a.0": [], "11a.10": [], "0": [], "15": []}
# manifest fastener step labels that differ from ASSEMBLY.md
MANIFEST_ALIAS = {"8": "8c"}
# steps that remove or refit fasteners placed earlier: no new-fastener count check
REFIT = {"11a.0": "removes the 4 x M3 x 14 post-cover screws from step 8",
         "11a.10": "refits the 4 x M3 x 14 post-cover screws from step 8"}
# assembly_order globs that match nothing in the model, and why it does or doesn't matter
DEAD_GLOBS = {
    "FST_ctrl_*": ("flag", "The 4 x M3 x 8 controller screws are not in the model (SHOPPING_LIST says 'Not modelled'; "
                           "they are drilled to fit). The viewer can't show them."),
    "FST_tt_*": ("note", "Glob matches nothing; the 3 hub screws of this step are FST_hub_*, which do resolve."),
    "PRT_cable_clip*": ("note", "Glob matches nothing; the model has no cable clips and ASSEMBLY.md doesn't call for any."),
    "FST_clip_*": ("note", "Glob matches nothing; no clip screws in the model or in ASSEMBLY.md."),
}

# thumbnails: path relative to BUILD/ as written in ASSEMBLY.md -> file on disk
def render_path(ref):
    ref = ref.strip("`")
    if not ref.endswith(".png"):
        ref += ".png"
    if ref.startswith("renders/"):
        return os.path.join(BUILD, ref)
    if ref.startswith("../renders/"):
        return os.path.join(V2, ref[3:])
    return None


# ---------------------------------------------------------------- markdown helpers
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


ITEM = re.compile(r"^(\s*)(-|\d+\.)\s+(.*)$")


def md_list_to_html(lines):
    """nested - / 1. lists with wrapped continuation lines -> HTML. Lines that aren't list items are paragraphs."""
    merged = []                  # join wrapped continuation lines first, so **bold** can span a line break
    for ln in lines:
        if not ln.strip():
            continue
        if ITEM.match(ln) or not merged:
            merged.append(ln.rstrip())
        else:
            merged[-1] += " " + ln.strip()
    lines = merged
    out, stack = [], []          # stack of (indent, tag)
    def close_to(indent):
        while stack and stack[-1][0] > indent:
            out.append("</li></%s>" % stack.pop()[1])
    para = []
    def flush_para():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()
    for ln in lines:
        if not ln.strip():
            continue
        m = ITEM.match(ln)
        if m:
            flush_para()
            ind = len(m.group(1))
            tag = "ol" if m.group(2)[0].isdigit() else "ul"
            close_to(ind)
            if stack and stack[-1][0] == ind:
                out.append("</li><li>%s" % inline(m.group(3)))
            else:
                out.append("<%s><li>%s" % (tag, inline(m.group(3))))
                stack.append((ind, tag))
        elif stack:
            out[-1] += " " + inline(ln.strip())
        else:
            para.append(ln.strip())
    flush_para()
    close_to(-1)
    return "".join(out)


def split_fields(body):
    """top-level '- **Label:** text' bullets (with their nested lines) -> OrderedDict label -> (text, nested lines);
    other top-level lines -> paragraphs"""
    fields, paras, cur = OrderedDict(), [], None
    for ln in body:
        m = re.match(r"^- \*\*(.+?):\*\*\s*(.*)$", ln)
        if m:
            cur = m.group(1)
            fields[cur] = [m.group(2), []]
        elif ln.startswith("  ") and cur is not None:
            fields[cur][1].append(ln[2:])
        elif ln.strip():
            cur = None
            paras.append(ln.strip())
        else:
            cur = None if not ln.strip() and cur is None else cur
    return fields, paras


def field_html(text, nested):
    head = inline(text) if text else ""
    rest = md_list_to_html(nested) if nested else ""
    if head and rest and not nested[0].lstrip().startswith(("-", "1.")):
        # wrapped continuation of the first line
        cont, lst = [], []
        for i, ln in enumerate(nested):
            if ITEM.match(ln):
                lst = nested[i:]
                break
            cont.append(ln.strip())
        head = inline(" ".join([text] + cont))
        rest = md_list_to_html(lst) if lst else ""
    return ("<p>%s</p>" % head if head else "") + rest


def field_text(text, nested):
    return " ".join([text] + [ln.strip() for ln in nested]).strip()


# ---------------------------------------------------------------- fasteners
SCREW = re.compile(r"(?:(\d+)\s*x\s*|the\s+)(?:\*\*)?(M[\d.]+)\s*x\s*(\d+)(?:\*\*)?")
NUT = re.compile(r"(?:(\d+)\s*(?:x\s*)?)?(?:captive\s+)?M3 nuts?\b")


def parse_fasteners(text):
    """'4 x M3 x 20 countersunk ST; 2 x ...' -> rows {qty, spec, note} and a Counter keyed (size, length) / 'nut'"""
    rows, count = [], Counter()
    plain = text.replace("**", "")
    for seg in [s.strip() for s in re.split(r";\s*", plain) if s.strip()]:
        seg_rows = []
        for m in SCREW.finditer(seg):
            # skip alternatives ("or M3 x 10 if you changed MG_*")
            pre = seg[max(0, m.start() - 4):m.start()]
            if "or " in pre and not m.group(1):
                continue
            qty = int(m.group(1)) if m.group(1) else 1
            count[(m.group(2), int(m.group(3)))] += qty
            seg_rows.append(qty)
        for m in NUT.finditer(seg):
            qty = int(m.group(1)) if m.group(1) else 1
            count["nut"] += qty
            seg_rows.append(qty)
        if seg_rows:
            qty = seg_rows[0]
            spec = re.sub(r"^\d+\s*x\s*", "", seg)
            rows.append({"qty": qty, "text": seg, "spec": spec})
        else:
            rows.append({"qty": None, "text": seg, "spec": seg})
    return rows, count


def manifest_count(parts, labels):
    c = Counter()
    for n, v in parts.items():
        if not n.startswith("FST_") or v.get("step") not in labels:
            continue
        spec = v.get("part", "")
        if "nut" in spec:
            c["nut"] += 1
            continue
        m = re.match(r"(M[\d.]+)_\w+ x (\d+)", spec)
        if m:
            c[(m.group(1), int(m.group(2)))] += 1
    return c


def fmt_count(c):
    return ", ".join("%d x %s" % (n, k if k == "nut" else "%s x %d" % k) for k, n in sorted(c.items(), key=str))


# ---------------------------------------------------------------- ASSEMBLY.md
def parse_assembly(path):
    lines = open(path).read().splitlines()
    steps, group, group_paras = [], None, {}
    cur = None
    step_head = re.compile(r"^### (\d+[a-z]?(?:\.\d+)?(?: to \d+[a-z]?\.\d+)?(?:, \d+[a-z]?)?)\.?\s+(.*)$")
    for ln in lines:
        if ln.startswith("## "):
            cur = None
            h = ln[3:].strip()
            m = re.match(r"Step (\d+): (.*)", h)
            if m:
                group = "Before you start"
                cur = {"id": m.group(1), "title": m.group(2)[0].upper() + m.group(2)[1:], "group": group, "body": []}
                steps.append(cur)
                continue
            group = re.sub(r"^\d+[a-z]?\.\s*", "", h)
            group_paras[group] = []
            continue
        m = step_head.match(ln)
        if m:
            cur = {"id": m.group(1), "title": m.group(2).strip(), "group": group, "body": []}
            steps.append(cur)
            continue
        if cur is not None:
            cur["body"].append(ln)
        elif group in group_paras:
            group_paras[group].append(ln)
    return steps, group_paras


# ---------------------------------------------------------------- GLB
def glb_json(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + n]), b


def thumb(path, cache):
    if path in cache:
        return cache[path]
    tmp = tempfile.mkdtemp(prefix="mmguide_")
    out = os.path.join(tmp, "t.jpg")
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "78", "-Z", "720", path, "--out", out],
                   check=True, capture_output=True)
    data = "data:image/jpeg;base64," + base64.b64encode(open(out, "rb").read()).decode()
    cache[path] = data
    return data


# ---------------------------------------------------------------- main
def main():
    checks = json.load(open(os.path.join(BL, "checks.json")))
    parts = json.load(open(os.path.join(BL, "manifest.json")))["parts"]
    plates = json.load(open(os.path.join(BUILD, "plates.json")))
    est = json.load(open(os.path.join(BUILD, "print_estimate.json")))
    gj, glb_bytes = glb_json(GLB)
    nodes = [n["name"] for n in gj["nodes"]]
    mesh_nodes = [n["name"] for n in gj["nodes"] if "mesh" in n]
    order = checks["assembly_order"]
    by_label = {e["step"].split(" ")[0]: (i, e) for i, e in enumerate(order)}

    asm_steps, group_paras = parse_assembly(os.path.join(BUILD, "ASSEMBLY.md"))
    placed, out_steps, bench_of = set(), [], {}
    thumbs_cache, thumbs = {}, {}
    used_labels = set()

    for k, s in enumerate(asm_steps):
        sid = s["id"]
        cur = CURATED.get(sid, {})
        labels = LABELS.get(sid, [sid])
        flags, notes = [], []
        entries = []
        for lab in labels:
            if lab not in by_label:
                flags.append("No checks.json assembly_order entry labelled %s." % lab)
                continue
            entries.append(by_label[lab])
            used_labels.add(lab)
        bench = next((e.get("bench") for _, e in entries if e.get("bench")), None)
        merge = next((e.get("merge") for _, e in entries if e.get("merge")), None)
        new, globs = [], []
        for _, e in entries:
            for g in e["objects"]:
                globs.append(g)
                hit = [n for n in mesh_nodes if fnmatch.fnmatchcase(n, g)]
                if not hit:
                    kind, why = DEAD_GLOBS.get(g, ("flag", "Glob matches nothing in the model."))
                    (flags if kind == "flag" else notes).append("%s: %s" % (g, why))
                for n in hit:
                    if n not in placed:
                        placed.add(n)
                        new.append(n)
                        if bench:
                            bench_of[n] = bench
        if not labels and sid not in ("0", "15", "11a.0", "11a.10"):
            flags.append("No assembly_order label for this step.")

        fields, paras = split_fields(s["body"])
        F = OrderedDict()
        for lab, (text, nested) in fields.items():
            F[lab] = {"html": field_html(text, nested), "text": field_text(text, nested)}
        tools = []
        if "Tools" in F:
            tools = [t.strip() for t in re.split(r",\s*(?![^(]*\))", F["Tools"]["text"].rstrip(".")) if t.strip()]
            tools = [inline(t) for t in tools]
        fast_rows, fast_count = [], Counter()
        if "Fasteners" in F:
            fast_rows, fast_count = parse_fasteners(F["Fasteners"]["text"])
            for r in fast_rows:
                r["text"] = inline(r["text"])
                r["spec"] = inline(r["spec"])
        mlabels = [MANIFEST_ALIAS.get(l, l) for l in labels]
        model_count = manifest_count(parts, mlabels)
        if sid in REFIT:
            fcheck = {"state": "na", "text": REFIT[sid]}
        elif not fast_count and not model_count:
            fcheck = {"state": "na", "text": "No fasteners in this step."}
        elif fast_count == model_count:
            fcheck = {"state": "good", "text": "Model agrees: " + fmt_count(model_count)}
        else:
            fcheck = {"state": "warning", "text": "ASSEMBLY.md lists %s; the model has %s." % (
                fmt_count(fast_count) or "none", fmt_count(model_count) or "none")}
            missing = fast_count - model_count
            explained = any(g == "FST_ctrl_*" for g in globs)
            if not explained:
                flags.append("Fastener counts disagree: " + fcheck["text"])

        # renders: every .png named in the step body, plus its section's
        refs = re.findall(r"`((?:\.\./)?renders/[^`]+?\.png)`", "\n".join(s["body"]))
        sect = re.findall(r"`((?:\.\./)?renders/[^`]+?\.png)`", "\n".join(group_paras.get(s["group"], [])))
        renders = []
        for ref, scope in [(r, "step") for r in refs] + [(r, "section") for r in sect]:
            p = render_path(ref)
            if p and os.path.exists(p) and ref not in [x["ref"] for x in renders]:
                key = os.path.splitext(os.path.basename(p))[0]
                thumbs[key] = thumb(p, thumbs_cache)
                renders.append({"ref": ref, "key": key, "scope": scope})
            elif p and not os.path.exists(p):
                notes.append("Render %s named in ASSEMBLY.md is missing on disk." % ref)

        def resolve(gl):
            out = []
            for g in gl:
                out += [n for n in nodes if fnmatch.fnmatchcase(n, g) and n not in out]
            return out

        extra = resolve(cur.get("extra", []))
        for g in cur.get("extra", []):
            if not resolve([g]):
                flags.append("%s is not in the GLB (no prop scratch blend at export time)." % g)
        focus = resolve(cur["focus"]) if "focus" in cur else list(new)
        if merge:
            focus = list(new) + [n for n, b in bench_of.items() if b == merge and n not in new]

        # explode vectors (design frame, unit-ish; JS scales by the step size)
        exp_rules = cur.get("explode", {})
        explode = {}
        for n in focus:
            rule = None
            for g, d in exp_rules.items():
                if g != "*" and fnmatch.fnmatchcase(n, g):
                    rule = d
                    break
            p = parts.get(n, {})
            if rule is None and n.startswith("FST_") and p.get("into"):
                into = p["into"]
                sign = 1.0 if "nut" in p.get("part", "") else -1.0
                base = exp_rules.get("*")
                # a fastener riding a merged sub-assembly moves with it, then backs out
                vec = [sign * c * 1.4 for c in into]
                if base and merge and bench_of.get(n) == merge:
                    vec = list(base)
                rule = vec
            if rule is None:
                rule = exp_rules.get("*")
            if rule is None:
                # a step with explicit rules keeps its unlisted parts still (the part the others go onto);
                # a step without any moves everything away from the visible assembly's centroid
                rule = [0, 0, 0] if exp_rules else "radial"
            explode[n] = rule

        if sid == "11a.0":
            notes.append("TOOL_tilt45_prop is a printed tool, not a design part: its placed mesh comes from the scratch blend "
                         "tools/tilt45_prop.py --blend writes (the one the step renders used). The post cover and its 4 "
                         "screws are hidden and the tilt servo, horn and adapter are shifted +X 10, as in the step render.")
        if sid == "11a.10":
            notes.append("Highlights the post cover and tilt drive going back in; they were placed at steps 8a, 8b and 8.")
        status = "flagged" if flags else "clean"
        warnings = [{"level": lv, "text": t, "source": src} for lv, t, src in cur.get("warnings", [])]
        out_steps.append(OrderedDict([
            ("index", k), ("id", sid), ("title", s["title"]), ("group", s["group"]),
            ("status", status), ("flags", flags), ("notes", notes),
            ("assembly_order", [{"label": e["step"].split(" ")[0], "index": i, "step": e["step"],
                                 "bench": e.get("bench"), "merge": e.get("merge")} for i, e in entries]),
            ("bench", bench), ("merge", merge),
            ("new_objects", new), ("focus_objects", focus), ("extra_objects", extra),
            ("hide_objects", resolve(cur.get("hide", []))),
            ("shift", {"objects": resolve(cur["shift"]["objects"]), "mm": cur["shift"]["mm"]} if "shift" in cur else None),
            ("pose", dict({"pan": 0, "tilt": 0}, **cur.get("pose", {}))),
            ("view", cur.get("view", DEFAULT_VIEW)),
            ("explode", explode),
            ("tools", tools),
            ("fasteners", fast_rows),
            ("fastener_check", fcheck),
            ("fields", [{"label": lab, "html": v["html"]} for lab, v in F.items() if lab not in ("Tools", "Fasteners")]),
            ("check", F.get("Check", {}).get("text", "")),
            ("paragraphs", [inline(p) for p in paras if not p.lower().startswith(("render", "exploded"))]),
            ("warnings", warnings),
            ("renders", renders),
        ]))

    unused = [e["step"].split(" ")[0] for e in order if e["step"].split(" ")[0] not in used_labels]
    unplaced = [n for n in mesh_nodes if n not in placed and not n.startswith("TOOL_")]

    # parts table for tooltips and the overview
    stl_plate = {}
    for p in plates["plates"]:
        for it in p["items"]:
            stl_plate[it["stl"]] = p["name"]
    first_step = {}
    for st in out_steps:
        for n in st["new_objects"]:
            first_step[n] = st["id"]
    PT = {}
    for n in mesh_nodes:
        p = parts.get(n, {})
        d = {"kind": n.split("_")[0], "step": first_step.get(n)}
        if n.startswith("PRT_"):
            d.update(stl=p.get("stl"), plate=stl_plate.get(p.get("stl")), orient=p.get("orient"), infill=p.get("infill"),
                     colour="B" if n in COLOUR_B(parts) else "A")
        elif n.startswith("BUY_"):
            d.update(mass_g=p.get("mass_g"), src=p.get("src"))
        elif n.startswith("FST_"):
            d.update(spec=p.get("part"), host=p.get("host"))
        elif n.startswith("CAB_"):
            d.update(lead=p.get("lead_len"), path=round(p["path_len"]) if p.get("path_len") else None)
        elif n.startswith("TOOL_"):
            d.update(stl="tools/tilt45_prop", plate=stl_plate.get("tools/tilt45_prop"))
        PT[n] = d

    plate_rows = []
    for p in plates["plates"]:
        e = est["plates"].get(p["name"], {})
        plate_rows.append({"name": p["name"], "printer": p["printer"], "colour": p["colour"], "subsystem": p["subsystem"],
                           "h": e.get("h"), "g": e.get("g"),
                           "items": [{"stl": it["stl"], "qty": it.get("qty", 1), "infill": it["infill"],
                                      "objects": [n for n, v in PT.items() if v.get("stl") == it["stl"]]}
                                     for it in p["items"]]})
    measure = [
        {"item": "0", "what": "Launch rig numbers: motor, rear-shaft recess, magnet, Plink pegs; TAPE_T 0.5 at step 6f",
         "before": "plates 1 and 2"},
        {"item": "1", "what": "Jar band OD, lip opening and height; lid disc diameter and thickness", "before": "plate 3"},
        {"item": "2", "what": "20 candies (MM_D, MM_T) and the pocket coupon (POCKET_D)", "before": "plate 3"},
        {"item": "3", "what": "Servo horn disc, bolt circle, hub; spline boss; servo body", "before": "plates 4, 5, 7"},
        {"item": "4", "what": "MotorGo hole size (M2.5 or M3), spacing 58.0 x 49.0, phase pads", "before": "plate 9"},
        {"item": "5", "what": "Servo controller holes (from a photo), switch and terminal positions", "before": "plates 7, 8"},
        {"item": "6", "what": "DeWalt adapter hole inset, size and depth; rail stem inset", "before": "plate 7"},
        {"item": "7", "what": "Buck flange hole spacing and body", "before": "plate 8"},
        {"item": "8", "what": "USB-C overmold, tape width, M3 nuts, 16 AWG phase wire OD", "before": "the build"},
    ]

    clean = sum(1 for s in out_steps if s["status"] == "clean")
    summary = {
        "steps": len(out_steps), "clean": clean, "flagged": len(out_steps) - clean,
        "assembly_order_entries_unused": unused, "objects_never_placed": unplaced,
    }
    steps_doc = OrderedDict([
        ("_about", "ASSEMBLY.md steps mapped to the GLB's objects (BUILD/guide/build_guide.py). new_objects: objects that "
                   "first appear in the step, from checks.json assembly_order. focus_objects: what the viewer highlights "
                   "(new objects, plus a merged bench sub-assembly). Directions are in the design frame: +X right, +Y "
                   "front, +Z up. status 'flagged' lists the reason in flags."),
        ("summary", summary),
        ("steps", out_steps),
    ])
    json.dump(steps_doc, open(OUT_STEPS, "w"), indent=1)

    meta = {
        "title": "M&M launcher v2 assembly",
        "model": "attempt 7, frozen", "cadcheck": "0 fails, 37 accepted warns",
        "objects": len(mesh_nodes), "glb_mb": round(len(glb_bytes) / 1e6, 2),
        "totals": est["total"], "estimate_label": est["_label"],
        "counts": dict(Counter(v["kind"] for v in PT.values())),
    }
    data = {"meta": meta, "steps": out_steps, "parts": PT, "plates": plate_rows, "measure": measure, "thumbs": thumbs,
            "bench_of": bench_of}

    src = os.path.join(HERE, "src")
    tpl = open(os.path.join(src, "template.html")).read()
    three_mod = open(os.path.join(STYLE, "ax-three.js")).read()
    three_mod = "\n".join(l for l in three_mod.splitlines() if not l.startswith("import "))
    three_mod = three_mod.replace("export function axScene", "function axScene")
    app = open(os.path.join(src, "app.js")).read()
    rep = {
        "/*@TOKENS_CSS@*/": open(os.path.join(STYLE, "tokens.css")).read(),
        "/*@GUIDE_CSS@*/": open(os.path.join(src, "guide.css")).read(),
        "/*@AX_FX@*/": open(os.path.join(STYLE, "ax-fx.js")).read(),
        "/*@AX_THREE@*/": three_mod,
        "/*@APP@*/": app,
        "@THREE@": THREE,
        "@DATA@": json.dumps(data, separators=(",", ":")).replace("</", "<\\/"),
        "@GLB@": base64.b64encode(glb_bytes).decode(),
    }
    for k in ("/*@AX_FX@*/", "/*@AX_THREE@*/", "/*@APP@*/"):
        # the style guide's files show usage like <script src="ax-fx.js"></script> in comments; inlined, that
        # would close the page's script element
        rep[k] = re.sub(r"</(script)", r"<\\/\1", rep[k], flags=re.I)
    for k, v in rep.items():
        assert k in tpl, k
        tpl = tpl.replace(k, v)
    open(OUT_HTML, "w").write(tpl)
    print("steps: %d (%d clean, %d flagged)" % (len(out_steps), clean, len(out_steps) - clean))
    for s in out_steps:
        print("  %-15s %-8s new %3d focus %3d  %s" % (s["id"], s["status"], len(s["new_objects"]), len(s["focus_objects"]),
                                                     "; ".join(s["flags"])[:150]))
    print("unused assembly_order entries:", unused, " never placed:", unplaced)
    print("wrote %s (%.2f MB), %s" % (OUT_HTML, os.path.getsize(OUT_HTML) / 1e6, OUT_STEPS))


def COLOUR_B(parts):
    """params.COLOUR_B, read from the source so the guide never imports the design's params (it imports bpy)"""
    txt = open(os.path.join(BL, "params.py")).read()
    m = re.search(r"COLOUR_B\s*=\s*\[(.*?)\]", txt, re.S)
    return set(re.findall(r'"(PRT_[^"]+)"', m.group(1)))


if __name__ == "__main__":
    main()
