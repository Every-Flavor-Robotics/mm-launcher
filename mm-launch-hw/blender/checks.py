"""Automated checks for the M&M launcher assembly (attempt 3).

Run:  Blender -b blender/mm_launcher.blend --python blender/checks.py -- --out renders/attempt-N/checks.json [--renders]

Reports
  * per printed part (Printed + Tools): non-manifold edges, volume, print-orientation bbox vs P1S / H2D, downward overhang
    area steeper than 45 deg (bed excluded), ray-cast wall thickness, volume-based filament / time estimate;
  * pairwise interference of every printed + purchased solid at 15 poses (pan -90/0/90 x tilt -3/0/22.5/45/46), BVH
    pre-filter + Manifold boolean intersection volume;
  * fasteners and cable routes against every solid on a DIFFERENT pivot (they sit in their own pilot holes by design),
    and fasteners against PURCHASED parts on the SAME pivot (e.g. adapter bolts vs the battery);
  * 2.5 mm L-key access to both flywheel pinch bolts at tilt 45 with the cover off (long leg swung -30..+30 deg);
  * feeder index geometry (park / fire positions vs the outlet) and the compliant-nip stud / leaf-spring numbers;
  * a tilt sweep -5..50 deg (2.5 deg) of minimum clearance between the tilting launcher and the pan stage;
  * a drop-path tracer: rays from the Ø16 outlet spout fall, slide on walls (stall below 20 deg) and record where the
    candy first meets the tape, at tilt 0..45 and two backplate settings;
  * service sweeps: cover off + flywheel off at tilt 45, encoder cap off at tilt 45;
  * centre of mass / static tip angle at every pose, hopper capacity, backplate gap range.
"""
import bpy, bmesh, json, math, os, sys, time
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(os.path.dirname(bpy.data.filepath), "..", "renders", "checks.json")
DO_RENDERS = "--renders" in argv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_assembly as B   # geometry parameters (module import does not rebuild)

P1S = (256.0, 256.0, 256.0)
H2D = (325.0, 320.0, 325.0)
PLA_DENSITY = 1.24e-3        # g / mm^3
FLOW = 12.0                  # mm^3 / s effective average for PLA on P1S/H2D at 0.2 mm layers
WALL_MIN = 1.6
VOL_TOL = 0.5                # mm^3: intersections below this are contact, not interference

# Mated purchased pairs whose placeholder solids overlap by design (documented in BOM_AND_ASSEMBLY.md).
WHITELIST = {
    frozenset(("BUY_battery", "BUY_dewalt_adapter")): "battery rail stem slides into the adapter",
    frozenset(("BUY_servo_pan", "BUY_horn_pan")): "spline inside horn hub",
    frozenset(("BUY_servo_tilt", "BUY_horn_tilt")): "spline inside horn hub",
    frozenset(("BUY_servo_feeder", "BUY_horn_feeder")): "spline inside horn hub",
    frozenset(("PRT_nip_cover", "PRT_nip_wheel")): "leaf-spring pads drawn in their free (printed) shape: the 2.0 mm overlap is the "
                                                   "assembly preload deflection (~9 N)",
}
# fasteners that thread into a purchased part by design (same pivot)
FST_BUY_OK = {("FST_motor_", "BUY_motor"): "M3 x 10 into the motor's tapped front-face holes"}
POSES = [(p, t) for p in (-90, 0, 90) for t in (B.TILT_MIN, 0, 22.5, 45, B.TILT_MAX)]


def set_pose(pan=0.0, tilt=0.0, hood=0.0):
    O = bpy.data.objects
    O["PIV_pan"].rotation_euler = (0, 0, math.radians(pan))
    O["PIV_tilt"].rotation_euler = (math.radians(tilt), 0, 0)
    O["PIV_pan_pinion"].rotation_euler = (0, 0, math.radians(-pan))
    O["PIV_hood"].rotation_euler = (hood, 0, 0)
    bpy.context.view_layer.update()


def world_bm(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    return bm


def nonmanifold(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bnd = sum(1 for e in bm.edges if e.is_boundary)
    vol = bm.calc_volume(signed=True)
    area = sum(f.calc_area() for f in bm.faces)
    bm.free()
    return nm, bnd, vol, area


def print_verts(ob):
    R = Matrix(ob["print_rot"]) if "print_rot" in ob else Matrix.Identity(3)
    return [R @ (ob.matrix_world @ v.co) for v in ob.data.vertices], R


def overhang_and_walls(ob):
    vs, R = print_verts(ob)
    zmin = min(v.z for v in vs)
    me = ob.data
    me.calc_loop_triangles()
    tris = [(vs[t.vertices[0]], vs[t.vertices[1]], vs[t.vertices[2]]) for t in me.loop_triangles]
    over = 0.0
    for a, b, c in tris:
        n = (b - a).cross(c - a)
        A = n.length / 2
        if A < 1e-9:
            continue
        n.normalize()
        zc = (a.z + b.z + c.z) / 3 - zmin
        if n.z < -math.cos(math.radians(45)) - 1e-3 and zc > 0.25:
            over += A
    bvh = BVHTree.FromPolygons([v.co for v in me.vertices], [tuple(t.vertices) for t in me.loop_triangles])
    thin, samples, tmin = 0, 0, 1e9
    where = []
    for p in me.loop_triangles:
        if p.area < 0.3:
            continue
        n = p.normal
        o = p.center - n * 0.01
        hit = bvh.ray_cast(o, -n, 50.0)
        if hit[0] is None:
            continue
        d = hit[3] + 0.01
        if hit[1].dot(n) > -0.5:
            continue
        samples += 1
        tmin = min(tmin, d)
        if d < WALL_MIN - 0.05:
            thin += 1
            w = ob.matrix_world @ p.center
            where.append((round(d, 2), [round(w.x, 1), round(w.y, 1), round(w.z, 1)]))
    xs = [v.x for v in vs]; ys = [v.y for v in vs]; zs = [v.z for v in vs]
    dims = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    return dims, over, thin, samples, (tmin if samples else None), sorted(where)[:12]


def fits(d, vol):
    s = sorted(d[:2])
    v = sorted(vol[:2])
    return s[0] <= v[0] and s[1] <= v[1] and d[2] <= vol[2]


def estimate(vol, area, infill):
    shell = min(vol, area * 0.84)            # 2 perimeters / 4-5 top-bottom layers ~ 0.84 mm skin
    used = shell + max(0.0, vol - shell) * infill / 100.0
    grams = used * PLA_DENSITY
    hours = used / FLOW / 3600.0 + 0.1
    return grams, hours


def bvh_world(ob):
    bm = world_bm(ob)
    t = BVHTree.FromBMesh(bm)
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    bm.free()
    return t, lo, hi


TMPC = None


def tmpcoll():
    global TMPC
    if TMPC is None:
        TMPC = bpy.data.collections.new("CHK_TMP")
        bpy.context.scene.collection.children.link(TMPC)
    return TMPC


def world_copy(ob):
    me = bpy.data.meshes.new(ob.name + "_w")
    bm = world_bm(ob)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(ob.name + "_w", me)
    tmpcoll().objects.link(o)
    return o


def inter_volume(a, b, solver):
    A, B_ = world_copy(a), world_copy(b)
    m = A.modifiers.new("i", 'BOOLEAN')
    m.operation = 'INTERSECT'
    m.solver = solver
    m.object = B_
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(A.evaluated_get(dg))
    bm = bmesh.new()
    bm.from_mesh(me)
    v = abs(bm.calc_volume())
    lo = hi = None
    if len(bm.verts):
        xs = [x.co for x in bm.verts]
        lo = [round(min(c[i] for c in xs), 1) for i in range(3)]
        hi = [round(max(c[i] for c in xs), 1) for i in range(3)]
    bm.free()
    for o in (A, B_):
        mm = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(mm)
    bpy.data.meshes.remove(me)
    return v, lo, hi


def pivot_key(ob):
    p = ob.parent
    while p is not None:
        if p.name.startswith("PIV_"):
            return p.name
        p = p.parent
    return "base"


def ancestors(ob):
    s = set()
    p = ob.parent
    while p is not None:
        s.add(p.name)
        p = p.parent
    return s


BUY_MASS_G = {"BUY_battery": 620, "BUY_dewalt_adapter": 90, "BUY_buck_12v": 180, "BUY_motorgo_axis": 25, "BUY_servo_controller": 30,
              "BUY_servo_pan": 66, "BUY_servo_tilt": 66, "BUY_servo_feeder": 66, "BUY_horn_pan": 4, "BUY_horn_tilt": 4, "BUY_horn_feeder": 4,
              "BUY_motor": 200, "BUY_magnet": 1, "BUY_plink_encoder": 3, "BUY_usbc_plug": 0}


def centroid(ob):
    bm = world_bm(ob)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    v6 = 0.0
    c = Vector((0, 0, 0))
    for f in bm.faces:
        a, b, d = (l.vert.co for l in f.loops)
        vol = a.dot(b.cross(d))
        v6 += vol
        c += vol * (a + b + d) / 4.0
    bm.free()
    if abs(v6) < 1e-9:
        bb = [ob.matrix_world @ Vector(x) for x in ob.bound_box]
        return sum(bb, Vector()) / 8
    return c / v6


def stability(printed, bought, grams):
    half = 120.0
    out = {}
    for pan, tilt in POSES:
        set_pose(pan, tilt)
        M = 0.0
        S = Vector((0, 0, 0))
        for ob in printed:
            m = grams.get(ob.name, 0.0)
            S += m * centroid(ob)
            M += m
        for ob in bought:
            m = BUY_MASS_G.get(ob.name, 0.0)
            if m:
                bb = [ob.matrix_world @ Vector(x) for x in ob.bound_box]
                S += m * (sum(bb, Vector()) / 8)
                M += m
        cg = S / M
        margin = half - max(abs(cg.x), abs(cg.y))
        out["pan%+d_tilt%s" % (pan, tilt)] = {"mass_g": round(M), "cg_mm": [round(cg.x, 1), round(cg.y, 1), round(cg.z, 1)],
                                              "edge_margin_mm": round(margin, 1),
                                              "static_tip_angle_deg": round(math.degrees(math.atan2(margin, cg.z)), 1)}
    set_pose(0, 0)
    return out


def hopper_capacity():
    a = math.radians(B.HOP_FLARE_ANG)
    r0, h1, h2 = B.HOP_BORE_R, B.HOP_BARREL_H, B.HOP_BARREL_H + B.HOP_FLARE_H
    r2 = r0 + B.HOP_FLARE_H / math.tan(a)
    disc_top = B.DISC_T + 0.4
    v = math.pi * r0 ** 2 * (h1 - disc_top) + math.pi / 3 * (h2 - h1) * (r0 ** 2 + r0 * r2 + r2 ** 2)
    mm = math.pi / 6 * 13 * 13 * 7          # plain M&M lentil ~ 620 mm3
    return {"usable_volume_cm3": round(v / 1000, 1), "mms_at_0.6_packing": int(v * 0.6 / mm), "required": 60}


# ------------------------------------------------------------------------------------------------
# interference
# ------------------------------------------------------------------------------------------------

def interference(solids, manifold_ok, extra=(), extra_rule=None):
    """solids x solids (plus extra x solids under extra_rule) at every pose"""
    res = {}
    for pan, tilt in POSES:
        set_pose(pan, tilt)
        trees = {o.name: bvh_world(o) for o in list(solids) + list(extra)}
        found, contacts = [], 0
        pairs = [(solids[i], solids[j]) for i in range(len(solids)) for j in range(i + 1, len(solids))]
        if extra_rule:
            pairs = [(e, s) for e in extra for s in solids if extra_rule(e, s)]
        for a, b in pairs:
            ta, la, ha = trees[a.name]
            tb, lb, hb = trees[b.name]
            if any(ha[k] < lb[k] - 0.01 or hb[k] < la[k] - 0.01 for k in range(3)):
                continue
            ov = ta.overlap(tb)
            if not ov:
                continue
            solver = 'MANIFOLD' if (manifold_ok.get(a.name) and manifold_ok.get(b.name)) else 'EXACT'
            v, lo, hi = inter_volume(a, b, solver)
            if v < VOL_TOL:
                contacts += 1
                continue
            found.append({"a": a.name, "b": b.name, "volume_mm3": round(v, 2), "tri_overlaps": len(ov), "solver": solver,
                          "region_min": lo, "region_max": hi, "whitelisted": WHITELIST.get(frozenset((a.name, b.name)))})
        res["pan%+d_tilt%s" % (pan, tilt)] = {"touching_pairs_zero_volume": contacts, "overlaps": found}
    set_pose(0, 0)
    return res


# ------------------------------------------------------------------------------------------------
# clearance sweep
# ------------------------------------------------------------------------------------------------

def world_tris(obs):
    verts, polys = [], []
    for ob in obs:
        me = ob.data
        me.calc_loop_triangles()
        base = len(verts)
        M = ob.matrix_world
        verts += [M @ v.co for v in me.vertices]
        polys += [tuple(base + i for i in t.vertices) for t in me.loop_triangles]
    return verts, polys


BEARING_PAIRS = [{"PRT_journal_plate", "PRT_yoke_arm_R"}, {"PRT_journal_plate", "PRT_arm_cap_R"}, {"PRT_journal_plate", "PRT_servo_pocket_tilt"},
                 {"PRT_nacelle", "PRT_yoke_arm_L"}, {"PRT_nacelle", "PRT_arm_cap_L"}, {"PRT_nacelle", "PRT_arm_cover_L"},
                 {"PRT_horn_adapter_tilt", "PRT_servo_pocket_tilt"}, {"BUY_horn_tilt", "PRT_servo_pocket_tilt"}]
BEARING_R = 18.5     # journals R15 in R15.2 bores, collars R17 0.2 off the arm faces: designed running fits


def min_dist(a, b, skip_axis=False):
    """min distance between two objects: vertices of each against the other's BVH (current pose).
    skip_axis ignores samples within BEARING_R of the tilt axis (designed journal / collar running fits)."""
    va, pa = world_tris([a])
    vb, pb = world_tris([b])
    ta = BVHTree.FromPolygons(va, pa)
    tb = BVHTree.FromPolygons(vb, pb)
    near_axis = lambda v: math.hypot(v.y, v.z - B.T_Z) < BEARING_R
    if ta.overlap(tb) and not skip_axis:
        return 0.0
    d = 1e9
    for v in va:
        if skip_axis and near_axis(v):
            continue
        r = tb.find_nearest(v, 50.0)
        if r[0] is not None and not (skip_axis and near_axis(r[0])):
            d = min(d, r[3])
    for v in vb:
        if skip_axis and near_axis(v):
            continue
        r = ta.find_nearest(v, 50.0)
        if r[0] is not None and not (skip_axis and near_axis(r[0])):
            d = min(d, r[3])
    return d


def tilt_sweep(launcher, static):
    out = []
    for i in range(23):
        tilt = -5.0 + 2.5 * i
        set_pose(0, tilt)
        boxes = {o.name: bvh_world(o)[1:] for o in launcher + static}
        best = (1e9, None, None)
        best_ex = (1e9, None, None)
        best_feed = (1e9, None, None)
        for a in launcher:
            la, ha = boxes[a.name]
            for b in static:
                lb, hb = boxes[b.name]
                if any(ha[k] < lb[k] - 12 or hb[k] < la[k] - 12 for k in range(3)):
                    continue
                servo_internal = {a.name, b.name} in ({"PRT_horn_adapter_tilt", "BUY_servo_tilt"}, {"BUY_horn_tilt", "BUY_servo_tilt"},
                                                       {"PRT_horn_adapter_tilt", "PRT_journal_plate"})
                if frozenset((a.name, b.name)) in WHITELIST or servo_internal:
                    continue
                d = min_dist(a, b, skip_axis={a.name, b.name} in BEARING_PAIRS)
                if d < best[0]:
                    best = (d, a.name, b.name)
                stop_pair = {a.name, b.name} == {"PRT_journal_plate", "PRT_yoke_arm_R"}
                if not stop_pair and d < best_ex[0]:
                    best_ex = (d, a.name, b.name)
                feed_stack = b.name.startswith(("PRT_feeder", "PRT_hopper", "PRT_servo_pocket_feeder", "PRT_servo_clamp_feeder",
                                                "BUY_servo_feeder", "PRT_horn_adapter_feeder", "BUY_horn_feeder", "FST_cap_"))
                if feed_stack and d < best_feed[0]:
                    best_feed = (d, a.name, b.name)
        out.append({"tilt_deg": tilt, "min_clearance_mm": round(best[0], 2), "pair": [best[1], best[2]],
                    "min_clearance_excluding_hard_stop_mm": round(best_ex[0], 2), "pair_excluding_stop": [best_ex[1], best_ex[2]],
                    "min_clearance_to_feeder_plate_hopper_feeder_servo_mm": round(best_feed[0], 2), "pair_feeder": [best_feed[1], best_feed[2]]})
    set_pose(0, 0)
    return out


# ------------------------------------------------------------------------------------------------
# drop-path tracer
# ------------------------------------------------------------------------------------------------
TAPE_T = 0.5
MM_T = 7.0
STALL_DEG = 20.0
G = Vector((0, 0, -1))


def launcher_frame():
    M = bpy.data.objects["PIV_tilt"].matrix_world
    return M, M.inverted()


def trace_drops(tilt, hood_eps, static_names):
    set_pose(0, tilt, hood_eps)
    obs = [bpy.data.objects[n] for n in static_names]
    v, p = world_tris(obs)
    bvh = BVHTree.FromPolygons(v, p)
    Mt, Mi = launcher_frame()
    W2 = Vector((B.W_P, B.W_Q))

    def lpq(P):
        L = Mi @ P
        return Vector((L.y, L.z)), L.x

    def wheel_gap(P):
        pq, x = lpq(P)
        return (pq - W2).length - B.WHEEL_R, pq, x

    def wheel_visible(P):
        """no wall between P and the wheel rim"""
        pq, x = lpq(P)
        rel = pq - W2
        dist = rel.length
        if dist < B.WHEEL_R + 0.1:
            return True
        dirL = -rel.normalized()
        dW = (Mt.to_3x3() @ Vector((0, dirL.x, dirL.y))).normalized()
        h = bvh.ray_cast(P + dW * 0.2, dW, dist - B.WHEEL_R - 0.2)
        return h[0] is None

    def psi(pq):
        rel = pq - W2
        return math.degrees(math.atan2(-rel.x, -rel.y))

    results = []
    pts = [(0.0, 0.0)]
    for ring in (1, 2, 3):
        rr = 2.5 * ring
        n = 6 * ring
        pts += [(rr * math.cos(2 * math.pi * k / n), rr * math.sin(2 * math.pi * k / n)) for k in range(n)]
    for dx, dy in pts:
        P = Vector((B.OUTLET_XY[0] + dx, B.OUTLET_XY[1] + dy, B.SPOUT_Z0 - 0.2))
        path = [P.copy()]
        mode, n = "fall", None
        outcome, where = "max_steps", None
        for step in range(900):
            if mode == "fall":
                h = bvh.ray_cast(P, G, 400.0)
                hit_d = h[3] if h[0] is not None else 400.0
                s = 0.0
                contact = None
                while s < hit_d:
                    Q = P + G * s
                    g_, pq, x = wheel_gap(Q)
                    if g_ <= TAPE_T and B.WHEEL_X0 < x < B.WHEEL_X1:
                        contact = (Q, pq)
                        break
                    s += 0.4
                if contact:
                    path.append(contact[0])
                    outcome, where = "tape", psi(contact[1])
                    break
                if h[0] is None:
                    outcome = "lost"
                    path.append(P + G * 150)
                    break
                n = h[1].normalized()
                if n.dot(G) > 0:
                    n = -n
                P = h[0] + n * 0.05
                path.append(P.copy())
                mode = "slide"
                continue
            d = G - G.dot(n) * n
            if d.length < 1e-6:
                outcome = "stall"
                break
            d.normalize()
            slope = math.degrees(math.asin(max(-1.0, min(1.0, -d.z))))
            g_, pq, x = wheel_gap(P)
            if g_ <= MM_T and wheel_visible(P):
                outcome, where = "tape", psi(pq)
                break
            if slope < STALL_DEG:
                outcome, where = "stall", [round(c, 1) for c in P]
                break
            hw = bvh.ray_cast(P, d, 1.0)
            if hw[0] is not None:
                n2 = hw[1].normalized()
                if n2.dot(d) > 0:
                    n2 = -n2
                P = hw[0] + n2 * 0.05
                n = n2
                path.append(P.copy())
                continue
            Pn = P + d * 1.0
            ha = bvh.ray_cast(Pn + n * 0.8, -n, 2.5)
            if ha[0] is not None:
                n2 = ha[1].normalized()
                if n2.dot(n) < 0:
                    n2 = -n2
                P = ha[0] + n2 * 0.05
                n = n2
            else:
                P = Pn
                mode = "fall"
            path.append(P.copy())
        results.append({"start_dxdy": [round(dx, 1), round(dy, 1)], "outcome": outcome,
                        "psi_deg": round(where, 1) if isinstance(where, float) else where, "path": [list(map(lambda c: round(c, 2), q)) for q in path]})
    set_pose(0, 0)
    tape = [r["psi_deg"] for r in results if r["outcome"] == "tape"]
    good = [p for p in tape if 0.0 <= p <= 135.0]
    summ = {"tilt_deg": tilt, "rays": len(results), "tape_contact": len(tape),
            "first_contact_on_descending_rear_tape_psi_0_135": len(good),
            "psi_min": round(min(tape), 1) if tape else None, "psi_max": round(max(tape), 1) if tape else None,
            "stalled": sum(1 for r in results if r["outcome"] == "stall"), "lost": sum(1 for r in results if r["outcome"] == "lost"),
            "other": sum(1 for r in results if r["outcome"] == "max_steps")}
    return summ, results


# ------------------------------------------------------------------------------------------------
# service sweeps
# ------------------------------------------------------------------------------------------------

def sweep_remove(movers, delta_world_fn, steps, solids, ignore):
    """move `movers` along a path and report the first overlap with any other solid"""
    O = bpy.data.objects
    saved = {m: O[m].matrix_world.copy() for m in movers}
    others = [o for o in solids if o.name not in movers and o.name not in ignore]
    first = None
    for k in range(1, steps + 1):
        dv = delta_world_fn(k)
        for m in movers:
            O[m].matrix_world = Matrix.Translation(dv) @ saved[m]
        bpy.context.view_layer.update()
        trees = {o.name: bvh_world(o) for o in [O[m] for m in movers] + others}
        for m in movers:
            ta, la, ha = trees[m]
            for o in others:
                tb, lb, hb = trees[o.name]
                if any(ha[i] < lb[i] - 0.01 or hb[i] < la[i] - 0.01 for i in range(3)):
                    continue
                if ta.overlap(tb):
                    v, lo, hi = inter_volume(O[m], o, 'MANIFOLD')
                    if v >= VOL_TOL:
                        first = {"step": k, "offset_mm": [round(c, 1) for c in dv], "mover": m, "hit": o.name, "volume_mm3": round(v, 2)}
                        break
            if first:
                break
        if first:
            break
    for m in movers:
        O[m].matrix_world = saved[m]
    bpy.context.view_layer.update()
    return first


def service_checks(solids):
    O = bpy.data.objects
    out = {}
    set_pose(0, 45)
    Mt = O["PIV_tilt"].matrix_world.to_3x3()
    u_l = Vector((0, 0.26, -0.97)).normalized()           # cover slide direction in the launcher frame
    u_w = Mt @ u_l
    xw = Vector((1, 0, 0))
    # screws (4 cover + right clamp screw) are taken out first; the cover then slides in its own plane out from
    # under the journal-plate lap, forward-down, and lifts away once clear
    hit = sweep_remove(["PRT_launcher_cover"], lambda k: u_w * 2.0 * k, 45, solids, ignore=set())
    out["cover_slide_90mm_in_plane_at_tilt45"] = hit or "clear"
    # flywheel off along +X (cover already off), bolts and magnet travel with it
    fw = ["PRT_flywheel"] + [o.name for o in bpy.data.objects if o.name.startswith("FST_fw_")]
    hit = sweep_remove(fw, lambda k: xw * 2.0 * k, 70, solids, ignore={"PRT_launcher_cover", "BUY_motor", "BUY_magnet"})
    out["flywheel_off_140mm_along_x_at_tilt45_cover_removed"] = hit or "clear"
    enc = ["PRT_encoder_cap", "BUY_plink_encoder"]
    hit = sweep_remove(enc, lambda k: -xw * 0.5 * k, 20, solids, ignore=set())
    out["encoder_cap_off_10mm_along_-x_at_tilt45"] = hit or "clear"
    set_pose(0, 0)
    return out


def lkey_access(solids, fst):
    """L-key (r 1.3 = 2.5 hex) in each pinch-bolt socket at tilt 45, launcher cover removed, long leg swung -30..+30 deg"""
    O = bpy.data.objects
    set_pose(0, 0)
    out = []
    ignore = {"PRT_launcher_cover"}
    others = [o for o in solids + fst if o.name not in ignore and not o.name.startswith("FST_cover_")]
    for s in (-1, 1):
        for th in (-30, -15, 0, 15, 30):
            set_pose(0, 0)
            k = B.lkey("CHK_LKEY", s, th)
            set_pose(0, 45)
            tk, lk, hk = bvh_world(k)
            hits = []
            for o in others:
                if o.name == "FST_fw_bolt_%d" % (s + 1):
                    continue                       # the key sits in this bolt's socket
                to, lo, ho = bvh_world(o)
                if any(hk[i] < lo[i] - 0.01 or ho[i] < lk[i] - 0.01 for i in range(3)):
                    continue
                if tk.overlap(to):
                    v, a, b = inter_volume(k, o, 'MANIFOLD' if not o.name.startswith("CAB_") else 'EXACT')
                    if v >= 0.05:
                        hits.append("%s (%.2f mm3)" % (o.name, v))
            out.append({"bolt": "FST_fw_bolt_%d" % (s + 1), "long_leg_deg": th, "hits": hits or "clear"})
            me = k.data
            O.remove(k)
            bpy.data.meshes.remove(me)
    set_pose(0, 0)
    return out


def feeder_index():
    """distance from each pocket centre to the outlet centre at park and fire positions"""
    res = {}
    oc = B.OUTLET_XY
    for label, rot in (("park_0", 0.0), ("fire_+30", B.FEED_FIRE), ("fire_-30", -B.FEED_FIRE)):
        d = []
        for a in B.pocket_angles(rot):
            a = math.radians(a)
            c = (B.HOP_C[0] + B.FEED_RP * math.cos(a), B.HOP_C[1] + B.FEED_RP * math.sin(a))
            d.append(math.hypot(c[0] - oc[0], c[1] - oc[1]))
        over = [round(x, 1) for x in d if x < B.POCKET_D / 2 + B.OUTLET_R]
        res[label] = {"pockets_overlapping_outlet": len(over), "their_centre_offsets_mm": over,
                      "nearest_pocket_edge_to_outlet_edge_mm": round(min(d) - B.POCKET_D / 2 - B.OUTLET_R, 1)}
    res["rule"] = "park 0 = solid over the outlet; fire = +30 or -30 (alternate) then back to 0: one pocket per command"
    return res


def nip_numbers():
    out = {"leaf_spring": B.leaf_spring(), "stud": "M3 x %d hex head" % B.STUD_L, "settings": []}
    for g in (B.NIP_SET[0], B.HOOD_GAP, 8.0, B.NIP_SET[1], B.HOOD_GAP_MAX):
        e = B._solve_eps(g)
        d = B.stud_d(e)
        out["settings"].append({"bdc_gap_bare_mm": g, "stud_tip_u_mm": round(B.STUD_L - d, 2),
                                "nut_engaged": (B.STUD_L - d) >= B.TW_NUT_U[1],
                                "tip_inside_shell_outer_face": (B.STUD_L - d) <= B.SHELL_U0 + B.SHELL_T + 0.01})
    out["note"] = ("thumbwheel = min-gap stop on the seat; plate opens against the leaf (rate %.1f N/mm at the stud); "
                   "%.1f mm of extra opening before the leaf bottoms on the shell" % (B.leaf_spring()["rate_N_per_mm"], B.LEAF_TRAVEL))
    return out


# ------------------------------------------------------------------------------------------------

def render_traces(traces, outdir):
    """section through the wheel plane with the traced drop paths as thin rods"""
    B.render_setup()
    for o in bpy.data.objects:
        if o.type == 'EMPTY':
            o.hide_render = True
    made = []
    for o in bpy.data.objects:
        if o.name.startswith(("FST_", "CAB_")):
            o.hide_render = True
    for (tilt, label), res in traces.items():
        set_pose(0, tilt, 0.0)
        made = []
        for i, r in enumerate(res):
            pts = [Vector(p) for p in r["path"]]
            if len(pts) < 2:
                continue
            pts = [Vector((B.WHEEL_XW + 2.0, q.y, q.z)) for q in pts]
            col = (0.1, 0.55, 0.2, 1) if r["outcome"] == "tape" else (0.85, 0.1, 0.1, 1)
            cu = bpy.data.curves.new("TR%d" % i, 'CURVE')
            cu.dimensions = '3D'
            sp = cu.splines.new('POLY')
            sp.points.add(len(pts) - 1)
            for k, q in enumerate(pts):
                sp.points[k].co = (q.x, q.y, q.z, 1)
            cu.bevel_depth = 0.25
            ob = bpy.data.objects.new("TRACE_%d" % i, cu)
            bpy.context.scene.collection.objects.link(ob)
            m = B.mat(col)
            cu.materials.append(m)
            made.append(ob)
        lp = Vector((0, 15, 25))
        Mt = bpy.data.objects["PIV_tilt"].matrix_world
        c = Mt @ Vector((B.WHEEL_XW, 15, -35))
        B.render_section(outdir, "x", B.WHEEL_XW, "feed_trace_tilt%d_%s.png" % (int(tilt), label), (900, c.y, c.z), (0, c.y, c.z), 170,
                         only_cut=False, scope={"PIV_tilt", "PIV_pan"})
        for ob in made:
            cu = ob.data
            bpy.data.objects.remove(ob)
            bpy.data.curves.remove(cu)
    set_pose(0, 0)


def main():
    t0 = time.time()
    printed = [o for o in bpy.data.collections["Printed"].objects if o.type == 'MESH']
    tools = [o for o in bpy.data.collections["Tools"].objects if o.type == 'MESH']
    bought = [o for o in bpy.data.collections["Purchased"].objects if o.type == 'MESH']
    fst = [o for o in bpy.data.collections["Fasteners"].objects if o.type == 'MESH']
    cab = [o for o in bpy.data.collections["Cables"].objects if o.type == 'MESH']
    set_pose(0, 0)
    report = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "printer_volumes_mm": {"P1S": P1S, "H2D": H2D},
              "parts": [], "interference": {}, "summary": {}}
    manifold_ok = {}
    tot_g = tot_h = 0.0
    seen_stl = set()
    grams_by_obj = {}
    for ob in sorted(printed + tools, key=lambda o: o.name):
        nm, bnd, vol, area = nonmanifold(ob)
        dims, over, thin, samples, tmin, where = overhang_and_walls(ob)
        infill = ob.get("infill", 20)
        g, h = estimate(abs(vol), area, infill)
        stl = ob.get("stl")
        first = stl not in seen_stl
        seen_stl.add(stl)
        if first:
            tot_g += g
            tot_h += h
        manifold_ok[ob.name] = (nm == 0 and vol > 0)
        grams_by_obj[ob.name] = g
        report["parts"].append({
            "object": ob.name, "stl": (stl + ".stl") if stl else None, "non_manifold_edges": nm, "boundary_edges": bnd,
            "volume_mm3": round(vol, 1), "print_bbox_mm": [round(d, 1) for d in dims],
            "fits_P1S": fits(dims, P1S), "fits_H2D": fits(dims, H2D),
            "overhang_area_gt45_mm2": round(over, 1), "orientation": ob.get("orient", ""), "supports": ob.get("supports", ""),
            "wall_samples": samples, "wall_samples_below_1.6mm": thin, "min_wall_ray_mm": round(tmin, 2) if tmin else None, "thin_samples_world_xyz": where,
            "infill_pct": infill, "est_filament_g": round(g, 1), "est_print_h": round(h, 2)})
    for ob in bought + fst + cab:
        nm, bnd, vol, area = nonmanifold(ob)
        manifold_ok[ob.name] = (nm == 0 and vol > 0 and not ob.name.startswith("CAB_"))
    solids = printed + bought
    print("CHK parts done", round(time.time() - t0, 1))
    report["interference"] = interference(solids, manifold_ok)
    print("CHK interference done", round(time.time() - t0, 1))
    piv = {o.name: pivot_key(o) for o in solids + fst + cab}
    report["fastener_cable_cross_pivot"] = interference(solids, manifold_ok, extra=fst + cab, extra_rule=lambda e, s: piv[e.name] != piv[s.name])
    print("CHK cross-pivot done", round(time.time() - t0, 1))

    def same_piv_buy(e, s):
        if not s.name.startswith("BUY_") or piv[e.name] != piv[s.name]:
            return False
        return not any(e.name.startswith(a) and s.name == b for (a, b) in FST_BUY_OK)
    report["fastener_vs_purchased_same_pivot"] = interference(solids, manifold_ok, extra=fst, extra_rule=same_piv_buy)
    report["fastener_vs_purchased_whitelist"] = {"%s* x %s" % k: v for k, v in FST_BUY_OK.items()}
    print("CHK same-pivot FST/BUY done", round(time.time() - t0, 1))
    report["lkey_pinch_bolt_access_tilt45_cover_off"] = lkey_access(solids, fst)
    print("CHK lkey done", round(time.time() - t0, 1))
    report["feeder_index"] = feeder_index()
    t_tip = B.FW_T_HEAD - B.FW_BOLT_L
    report["flywheel_pinch_bolts"] = {"bolt": "M3 x %d socket head" % B.FW_BOLT_L, "head_seat_t_mm": round(B.FW_T_HEAD, 2),
                                      "tip_t_mm": round(t_tip, 2), "nut_t_mm": [round(-B.FW_T_NUT, 2), round(-B.FW_T_NUT - 2.4, 2)],
                                      "tip_past_nut_mm": round(-(B.FW_T_NUT + 2.4) - t_tip, 2),
                                      "tip_inside_hub_surface_mm": round(B.FW_T_SURF + t_tip, 2),
                                      "note": "t = distance along the bolt from the point nearest the shaft axis; nut fully engaged when tip_past_nut > 0"}
    report["compliant_nip"] = nip_numbers()
    launcher = [o for o in solids + fst + cab if "PIV_tilt" in ancestors(o)]
    static = [o for o in solids + fst if "PIV_pan" in ancestors(o) and "PIV_tilt" not in ancestors(o)]
    report["tilt_sweep"] = tilt_sweep(launcher, static)
    print("CHK sweep done", round(time.time() - t0, 1))
    feed_static = ["PRT_launcher_body", "PRT_journal_plate", "PRT_launcher_cover", "PRT_hood", "PRT_feeder_plate"]
    eps_tuned = B._solve_eps(9.0)
    report["feed_trace"] = {"model": "37 rays over the Ø16 spout; fall, slide on walls (stall < %.0f deg); first tape contact = within %.1f mm "
                                     "of the rim (falling) or local gap <= %.0f mm with no wall between (sliding)" % (STALL_DEG, TAPE_T, MM_T),
                            "settings": {"operating": "gap 6.5 at BDC (as modelled; 6.0 with 0.5 mm tape)", "uncompressed_9mm": "gap 9.0 at BDC (eps %.2f deg)" % math.degrees(eps_tuned)},
                            "results": []}
    traces = {}
    for label, eps in (("operating", 0.0), ("uncompressed_9mm", eps_tuned)):
        for tilt in (0.0, 15.0, 22.5, 30.0, 45.0):
            summ, res = trace_drops(tilt, eps, feed_static)
            summ["setting"] = label
            report["feed_trace"]["results"].append(summ)
            if tilt in (0.0, 45.0) and label == "operating":
                traces[(tilt, label)] = res
    print("CHK trace done", round(time.time() - t0, 1))
    report["service"] = service_checks(solids)
    print("CHK service done", round(time.time() - t0, 1))
    set_pose(0, 0)
    report["stability"] = stability(printed, bought, grams_by_obj)
    report["hopper_capacity"] = hopper_capacity()
    report["backplate_gap_mm"] = {"nominal": B.HOOD_GAP, "min_at_full_close": round(B.gap_bdc(B.EPS_CLOSE), 2),
                                  "max_at_full_open": round(B.gap_bdc(B.EPS_OPEN), 2),
                                  "hinge_travel_deg": [round(math.degrees(B.EPS_OPEN), 2), round(math.degrees(B.EPS_CLOSE), 2)]}
    unint = [(k, f) for k, v in report["interference"].items() for f in v["overlaps"] if not f["whitelisted"]]
    xp = [(k, f) for k, v in report["fastener_cable_cross_pivot"].items() for f in v["overlaps"]]
    xp += [(k, f) for k, v in report["fastener_vs_purchased_same_pivot"].items() for f in v["overlaps"]]
    lk = [r for r in report["lkey_pinch_bolt_access_tilt45_cover_off"] if r["hits"] != "clear"]
    nm_parts = [p["object"] for p in report["parts"] if p["non_manifold_edges"] or p["volume_mm3"] <= 0]
    too_big = [p["object"] for p in report["parts"] if not (p["fits_P1S"] or p["fits_H2D"])]
    not_p1s = [p["object"] for p in report["parts"] if not p["fits_P1S"]]
    thin = [(p["object"], p["wall_samples_below_1.6mm"], p["min_wall_ray_mm"]) for p in report["parts"] if p["wall_samples_below_1.6mm"]]
    sweep = report["tilt_sweep"]
    clr45 = [s for s in sweep if s["tilt_deg"] == 45.0][0]
    clr0 = [s for s in sweep if s["tilt_deg"] == 0.0][0]
    stop_hi = min(s["tilt_deg"] for s in sweep if s["min_clearance_mm"] <= 0.05 and s["tilt_deg"] > 20)
    stop_lo = max(s["tilt_deg"] for s in sweep if s["min_clearance_mm"] <= 0.05 and s["tilt_deg"] < 20) if any(s["min_clearance_mm"] <= 0.05 and s["tilt_deg"] < 20 for s in sweep) else None
    report["summary"] = {
        "printed_objects": len(printed), "tool_objects": len(tools), "unique_stls": len(seen_stl), "purchased_objects": len(bought),
        "fasteners": len(fst), "cables": len(cab),
        "non_manifold_printed_parts": nm_parts, "parts_not_fitting_any_printer": too_big, "parts_not_fitting_P1S": not_p1s,
        "unintended_interferences": len(unint), "unintended_list": ["%s: %s x %s (%.1f mm3)" % (k, f["a"], f["b"], f["volume_mm3"]) for k, f in unint],
        "fastener_cable_cross_pivot_and_fst_vs_buy_overlaps": len(xp), "fastener_cable_list": ["%s: %s x %s (%.1f mm3)" % (k, f["a"], f["b"], f["volume_mm3"]) for k, f in xp],
        "tilt_clearance_at_0_deg_excl_stop_mm": clr0["min_clearance_excluding_hard_stop_mm"],
        "tilt_clearance_at_45_deg_excl_stop_mm": clr45["min_clearance_excluding_hard_stop_mm"],
        "first_contact_tilt_up_deg": stop_hi, "first_contact_tilt_down_deg": stop_lo,
        "feeder_stack_clearance_mm_by_tilt": {str(t["tilt_deg"]): t["min_clearance_to_feeder_plate_hopper_feeder_servo_mm"] for t in sweep},
        "feed_trace": [{k: r[k] for k in ("setting", "tilt_deg", "rays", "first_contact_on_descending_rear_tape_psi_0_135", "psi_min", "psi_max", "stalled", "lost")}
                       for r in report["feed_trace"]["results"]],
        "service": report["service"],
        "lkey_positions_blocked": ["%s @ %d deg: %s" % (r["bolt"], r["long_leg_deg"], r["hits"]) for r in lk],
        "lkey_positions_checked": len(report["lkey_pinch_bolt_access_tilt45_cover_off"]),
        "feeder_index": {k: v for k, v in report["feeder_index"].items() if k != "rule"},
        "nip_leaf_spring": report["compliant_nip"]["leaf_spring"],
        "flywheel_pinch_bolts": report["flywheel_pinch_bolts"],
        "parts_with_thin_wall_samples": thin,
        "est_total_filament_g": round(tot_g, 0), "est_total_print_h": round(tot_h, 1),
        "min_tip_angle_deg": min(v["static_tip_angle_deg"] for v in report["stability"].values()),
        "hopper_mms": report["hopper_capacity"]["mms_at_0.6_packing"],
        "backplate_gap_mm": report["backplate_gap_mm"],
        "all_pass": (not nm_parts and not too_big and not unint and not xp and not lk),
        "runtime_s": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(report, f, indent=1)
    print("CHECKS_SUMMARY", json.dumps(report["summary"], indent=1))
    if DO_RENDERS:
        render_traces(traces, os.path.dirname(os.path.abspath(OUT)))


main()
