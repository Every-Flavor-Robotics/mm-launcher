"""Print time and filament estimate per STL and per plate, from geometry only (no slicer). Feeds BUILD/PRINT_PLAN.md.

    cd blender && cad py tools/print_estimate.py [--check-rig]

Prior art: the launch rig's layer-by-layer model (`../../test-prints/launch-rig/build.py` `estimate_stl`, Bambu 0.20 mm
Standard P1S speeds, 80 % motion efficiency, 1.5 s per layer, 6 min per plate). It is loaded from that file by AST, not
copied, so a fix there flows here. The one addition: `walls`. The rig model assumed 2 walls; this plan prints 3 walls
(outer + 2 inner) on the structural parts, so the wall band and its time scale with the inner-wall count.
`--check-rig` re-runs the rig's six STLs with walls=2 and prints them next to the rig's `print_estimate.json`.

Writes ../BUILD/print_estimate.json: per STL {layers, min, g, infill, walls}, and per plate the sums (+ 6 min per plate)
and a footprint check (bounding rectangles packed with BUILD/plates.json gap_mm on each bed; you still lay them out).
cadcheck's flat 12 mm3/s model (`est_g`, `est_h` in cadcheck.json) is kept alongside for comparison.
"""
import ast, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
V2 = os.path.dirname(BL)
RIG = os.path.join(os.path.dirname(V2), "test-prints", "launch-rig")
sys.path.insert(0, BL)
import bmesh  # noqa: E402,F401
from cadlib import geom as G  # noqa: E402

# --- prior art, loaded from the rig's build.py --------------------------------------------------------------------
src = open(os.path.join(RIG, "build.py")).read()
ns = {"math": math, "G": G, "os": os}
for node in ast.parse(src).body:
    if (isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "BAMBU" for t in node.targets)) or \
       (isinstance(node, ast.FunctionDef) and node.name in ("_v", "estimate_stl")):
        exec(compile(ast.Module([node], []), "launch-rig/build.py", "exec"), ns)
BAMBU = ns["BAMBU"]


def estimate(path, infill, walls=2):
    """rig estimate_stl with `walls` perimeters: the rig's model is outer + 1 inner; each extra inner wall adds
    L * inner width of wall area (taken from the sparse band) and L / inner speed of time per layer"""
    r = ns["estimate_stl"](path, infill)
    if walls == 2:
        return r
    # re-run with a widened inner wall: same code path, inner width x (walls - 1), time per mm x (walls - 1)
    iw, iv = BAMBU["inner"]
    BAMBU["inner"] = (iw * (walls - 1), iv / (walls - 1))
    try:
        r = ns["estimate_stl"](path, infill)
    finally:
        BAMBU["inner"] = (iw, iv)
    return r


# --- footprint fit: bounding rectangles + MaxRects with gap_mm between parts (a feasibility check, not a layout) ---
import struct  # noqa: E402


def bbox(path):
    d = open(path, 'rb').read(); n = struct.unpack('<I', d[80:84])[0]
    xs, ys = [], []
    for i in range(n):
        v = struct.unpack('<12f', d[84+50*i:84+50*i+48])
        xs += [v[3], v[6], v[9]]; ys += [v[4], v[7], v[10]]
    return max(xs)-min(xs), max(ys)-min(ys)

def maxrects(W, H, rects, gap):
    free = [(0, 0, W + gap, H + gap)]; placed = []
    for name, w, h in sorted(rects, key=lambda r: -max(r[1], r[2]) * min(r[1], r[2])):
        best = None
        for (fx, fy, fw, fh) in free:
            for (rw, rh, rot) in ((w + gap, h + gap, 0), (h + gap, w + gap, 1)):
                if rw <= fw + 1e-6 and rh <= fh + 1e-6:
                    s = min(fw - rw, fh - rh)
                    if best is None or s < best[0]: best = (s, fx, fy, rw, rh, rot)
        if best is None: return None, name
        _, x, y, rw, rh, rot = best; placed.append((name, x, y, rot))
        nf = []
        for (fx, fy, fw, fh) in free:
            if x >= fx + fw or x + rw <= fx or y >= fy + fh or y + rh <= fy: nf.append((fx, fy, fw, fh)); continue
            if x > fx: nf.append((fx, fy, x - fx, fh))
            if x + rw < fx + fw: nf.append((x + rw, fy, fx + fw - x - rw, fh))
            if y > fy: nf.append((fx, fy, fw, y - fy))
            if y + rh < fy + fh: nf.append((fx, y + rh, fw, fy + fh - y - rh))
        free = [a for a in nf if not any(a != b and a[0] >= b[0] and a[1] >= b[1] and a[0]+a[2] <= b[0]+b[2] and a[1]+a[3] <= b[1]+b[3] for b in nf)]
    return placed, None

# --- plan: STL -> (infill, walls); plates -> STLs --------------------------------------------------------------------
STL = os.path.join(V2, "stl")
PLAN = json.load(open(os.path.join(V2, "BUILD", "plates.json")))


def main():
    if "--check-rig" in sys.argv:
        ref = json.load(open(os.path.join(RIG, "print_estimate.json")))
        inf = {"rig_guard": 15, "rig_cover": 15, "rig_rear_cup": 15, "flywheel": 100, "backplate": 40, "nip_wheel": 50}
        for nm, i in inf.items():
            r = estimate(os.path.join(RIG, "stl", nm + ".stl"), i)
            print("RIGCHECK %-13s here %5.1f min %5.1f g | rig %5.1f min %5.1f g" % (nm, r["min"], r["g"], ref[nm]["min"], ref[nm]["g"]))
        return
    cc = json.load(open(os.path.join(BL, "cadcheck.json")))["checks"]["parts"]["rows"]
    cc = {r["stl"]: r for r in cc}
    out = {"_label": "estimate from geometry, not sliced (launch-rig layer model, Bambu 0.20 mm Standard speeds)",
           "_model": dict(BAMBU), "stl": {}, "plates": {}}
    for plate in PLAN["plates"]:
        tot_min = tot_g = 0.0
        for it in plate["items"]:
            f, q = it["stl"], it.get("qty", 1)
            if f not in out["stl"]:
                r = estimate(os.path.join(STL, f + ".stl"), it["infill"], it["walls"])
                c = cc.get(f.split("/")[-1], {})
                r.update(infill=it["infill"], walls=it["walls"], cadcheck_g=c.get("est_g"), cadcheck_h=c.get("est_h"))
                out["stl"][f] = r
                print("PART %-24s %3d%% %dw %6.1f min %6.1f g  (cadcheck %s g, %s h)" % (f, it["infill"], it["walls"], r["min"], r["g"], c.get("est_g"), c.get("est_h")))
            tot_min += q * out["stl"][f]["min"]
            tot_g += q * out["stl"][f]["g"]
        tot_min += BAMBU["plate_min"]
        rects = []
        for it in plate["items"]:
            w, h = bbox(os.path.join(STL, it["stl"] + ".stl"))
            rects += [(it["stl"], w, h)] * it.get("qty", 1)
        fit = {pr: ("fits" if maxrects(W, H, rects, PLAN["gap_mm"])[0] else "no") for pr, (W, H) in PLAN["beds"].items()}
        out["plates"][plate["name"]] = {"printer": plate["printer"], "colour": plate["colour"], "min": round(tot_min, 1),
                                        "h": round(tot_min / 60.0, 2), "g": round(tot_g, 1), "fit": fit,
                                        "bbox_area_mm2": round(sum(w * h for _, w, h in rects))}
        print("PLATE %-28s %-4s %s %5.2f h %6.1f g fit %s" % (plate["name"], plate["printer"], plate["colour"], tot_min / 60.0, tot_g, fit))
    out["total"] = {"h": round(sum(p["h"] for p in out["plates"].values()), 2),
                    "g": round(sum(p["g"] for p in out["plates"].values()), 1)}
    for col in ("A", "B", "any"):
        out["total"]["g_" + col] = round(sum(p["g"] for p in out["plates"].values() if p["colour"] == col), 1)
    json.dump(out, open(os.path.join(V2, "BUILD", "print_estimate.json"), "w"), indent=1)
    print("TOTAL %s" % out["total"])


main()
