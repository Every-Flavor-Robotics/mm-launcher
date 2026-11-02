"""M&M launcher: LAUNCH TEST RIG (parametric, headless Blender 5.1 + cadlib).

    cad build build.py                         # build, STLs, manifest, checks.json, .blend
    cad build build.py -- --render             # + renders (800 px) into renders/
    cad check launch_rig.blend checks.json cadcheck.json

What it is: the attempt-3 launcher pod cut down to what answers the physical unknowns (nip squeeze,
tape grip vs rpm, feed drop into the nip, motor + rear-shaft encoder bring-up), fixed at TILT deg
elevation on bench feet. No pan, no tilt servo, no hopper, no base.

Source of truth for every launcher dimension is mm-launch-hw/blender/build_assembly.py (attempt 3).
It is IMPORTED here, never edited: cavities, backplate, flywheel, thumbwheel, nip frame, motor and encoder
positions all come from that module, so a change there flows into the rig on the next build.

Frames: "A3 world" is X right, Y forward, Z up with the tilt axis at (x, 0, A3.T_Z) and the launcher frame
(p, q) = (Y, Z - T_Z). Every launcher solid is built in A3 world at tilt 0 and baked through M_RIG
(rotate +TILT about X around the tilt axis, then put the tilt axis AXIS_H above the table). Rig world:
table at z = 0, X right (cover side), Y forward (muzzle), Z up. Rig-only features (feet, funnel, MotorGo)
are written in rig (y, z) and mapped back with r2l().

Six printed parts:
  rig_guard   A3 body cavities (wheel, chute + tongue, nip, backplate bay, muzzle, stud slot, land) with a
              shrink-wrapped 2.6 mm skin instead of the A3 convex hull; left wall 8 mm (A3 nacelle plate +
              body wall merged, same motor-screw stack); integral leaf spring + over-travel stop (same rate,
              preload and travel as the A3 nip cover); hand-feed funnel on the A3 drop column; front foot.
  rig_cover   +X side plate (replaces A3 journal plate + cover); carries the hinge-axle thread.
  rig_rear_cup  rear cup on the motor can (A3 nacelle bore + crush ribs, shoulder on the motor's rear face) with the
              A3 encoder-cap features (Plink pegs, JST slot), MotorGo Axis standoffs on two legs, rear bench foot.
  flywheel    A3 part, unchanged.
  backplate   A3 hood, unchanged except the stud pocket opens to its +X edge.
  nip_wheel   A3 thumbwheel, unchanged.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.abspath(os.path.join(HERE, "..", ".."))                 # mm-launch-hw
SKILL = os.environ.get("CAD_SKILL", os.path.expanduser("~/code-stuff/alex-3d-skills/skills/print-cad-blender"))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
sys.path.insert(0, os.path.join(HW, "blender"))

import bpy  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402
from cadlib import geom as G, asm as A, export as E, render as R  # noqa: E402
import build_assembly as A3  # noqa: E402   attempt-3 geometry (read-only import)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

# =====================================================================================================
# PARAMETERS (mm, deg). Everything not listed here is attempt 3 (A3.*).
# =====================================================================================================
TILT = 20.0                 # fixed launch elevation (A3 tilt joint value); exit ~ TILT + 3 deg
AXIS_H = 122.0              # A3 tilt-axis height above the table (puts the nip spring block ~14 above the table)
GAP_TEST = (5.0, 12.0)      # bare gap at BDC the thumbwheel must reach: the experimental knob
GAP_BAY = (4.8, 12.5)       # backplate bay swing (A3 5.5..12.5); 4.8 keeps the A3 chute tongue at full 1.6 mm
BAY_SAMPLES = 25            # swept-band samples for the bay cut (A3: 9; 11 left 0.14 mm scallops)
GAP_HOME = A3.HOOD_GAP      # 6.5 bare = A3 operating setting = home pose of PIV_hood

X0 = 0.0                    # guard outer face = A3 motor front face
X_IN = A3.X_BODY_IN         # 8    guard inner face (wheel web 1 mm off it, as A3)
X_CI = A3.X_COVER_IN        # 31.5 guard / cover parting plane (as A3)
STUD_SLOT_R = 2.2           # stud slot through the land (shank 1.5 + 0.7)
SKIN = 2.6                  # guard skin around the A3 cavities (A3 GUARD_WALL 3.0, A3 outline = convex hull)
COVER_T = 1.6               # cover plate, 8 solid layers (pan-head screws, so no countersink depth needed)
HINGE_BOSS = (4.5, 6.0)     # radius, height of the hinge-axle thread boss on the cover's outer face
N_COVER_SCREWS = 6
MOTOR_CB_FLOOR = 4.0        # motor-screw counterbore floor x (A3: 6, which puts an M3 DIN912 head flush with the wheel web)
MOTOR_SCREW_L = 8.0         # M3 x 8 socket: 4 mm into the motor face, as A3

LEAD_SIGN = +1              # motor lead block / keyway / Plink JST toward +S (A3: -S, up the trunnion). 4-fold screw pattern: same holes
BORE_R = A3.MOTOR_D / 2 + A3.BORE_CLR        # 18.15, A3 nacelle bore
TUBE_T = 2.4
TUBE_R = BORE_R + TUBE_T
ENC_GAP = 1.5               # magnet face to MT6701 top as printed (A3 1.0). Paper shims under the Plink close it
X_PCB = -A3.MOTOR_L + A3.REAR_SHAFT_RECESS - A3.MAGNET_T - ENC_GAP - A3.PLINK_IC_TOP   # -80.75 PCB back
END_T = 4.0                 # frame rear wall (= A3 encoder-cap disc)
X_END = X_PCB - END_T       # -84.75 frame bed face
SHOULDER_X = -A3.MOTOR_L                      # shoulder ring seats on the motor's rear face: the cup's axial datum
CUP_X1 = -A3.MOTOR_L + 14.0                   # cup ring front edge (covers the A3 crush ribs at -73..-61)

STANDOFF = (3.0, 10.0)      # MotorGo standoff radius, height (header pins reach 7.25 under the board)
MG_HOLES = [(0.0, 0.0), (58.0, 0.0), (0.0, -49.0), (58.0, -49.0)]   # STEP frame (reference/mg_axis.step)
MG_Z0 = 9.0                 # rig height of the header-side hole row; board hangs under the motor between the frame legs
MG_PILOT_R = 1.05           # Ø2.1: M2.5 self-tapping (reference STL holes are Ø2.5, not the Ø3.4 the brief states)
LEG_W = 7.0                 # frame rail width (bed-level plate, END_T thick)
FRAME_FOOT_HALF = 46.0      # rear foot half-length (rig y) about the motor axis
FRAME_FOOT_X = 10.0         # rear foot depth along +X from the frame bed face

LEAF_X = (0.0, 28.0)        # integral leaf / stop / root block span: the thumbwheel rim at x 28 is exposed to +X
LEAF_K_A3 = (21.9, 2.0)     # A3 leaf width, thickness: the rig leaf keeps the same b*t^3, so the same rate and preload
ROOT_V = 34.0               # leaf root (A3 NIP_V_ROOT): 34 mm cantilever to the pads, as A3
TIP_V = A3.NIP_V_TIP        # -8
STOP_U = (A3.SHELL_U0, A3.SHELL_U0 + 4.5)    # rigid over-travel stop beam at the A3 shell's inner face (u 12)

FUNNEL_THROAT = (8.0, 23.0)  # half width, height above the tilt axis (A3 spout: Ø16, bottom 23 above the axis)
FUNNEL_MOUTH_Z = 34.0
FUNNEL_ANG = 60.0           # wall slope from horizontal
FUNNEL_T = 2.0
FUNNEL_X = (A3.CH_X0, X_CI)  # same x span as the A3 chute (13..31.5): the drop column keeps the A3 width

FOOT_T = 5.0                # bench feet thickness (world z)
NOTCH = (4.6, 10.0)         # bench-screw notch width, depth (M4 wood screw, or a clamp jaw)
GUARD_FOOT_X = (0.0, 14.0)  # front foot / post x span
GUARD_LEG_Y = (70.0, 76.0)  # front post under the muzzle (rig y)
GUARD_PAD_Y = (20.0, 98.0)

# =====================================================================================================
# FRAMES
# =====================================================================================================
_c, _s = math.cos(math.radians(TILT)), math.sin(math.radians(TILT))
M_RIG = Matrix.Translation((0, 0, AXIS_H)) @ Matrix.Rotation(math.radians(TILT), 4, 'X') @ Matrix.Translation((0, 0, -A3.T_Z))
M_RIG_INV = M_RIG.inverted()
R_TILT_INV = Matrix.Rotation(-math.radians(TILT), 3, 'X')


def l2r(pq):
    """launcher (p, q) -> rig (y, z)"""
    p, q = pq
    return (p * _c - q * _s, AXIS_H + p * _s + q * _c)


def r2l(yz):
    """rig (y, z) -> launcher (p, q)"""
    y, z = yz[0], yz[1] - AXIS_H
    return (y * _c + z * _s, -y * _s + z * _c)


def rig_pt(x, pq):
    return Vector((x,) + l2r(pq))


def a3_to_rig(v):
    return M_RIG @ Vector(v)


def rig_dir(d):
    return (M_RIG.to_3x3() @ Vector(d)).normalized()


def rig_poly(pts):
    return [r2l(p) for p in pts]


def rig_box(name, x0, x1, y0, y1, z0, z1):
    """axis-aligned box in RIG world, returned in A3 world (to join A3-world booleans)"""
    return xform(G.box(name, x0, x1, y0, y1, z0, z1), M_RIG_INV)


def eps_deg(gap):
    return math.degrees(A3._solve_eps(gap))


def stadium(c0, c1, r, n=12):
    dx, dy = c1[0] - c0[0], c1[1] - c0[1]
    a = math.atan2(dy, dx)
    pts = [(c1[0] + r * math.cos(a - math.pi / 2 + math.pi * i / n), c1[1] + r * math.sin(a - math.pi / 2 + math.pi * i / n)) for i in range(n + 1)]
    pts += [(c0[0] + r * math.cos(a + math.pi / 2 + math.pi * i / n), c0[1] + r * math.sin(a + math.pi / 2 + math.pi * i / n)) for i in range(n + 1)]
    return pts


def vadd(a, b, k=1.0):
    return (a[0] + k * b[0], a[1] + k * b[1])


S, N, WC = A3.S_DIR, A3.N_DIR, A3.WC
LS = (LEAD_SIGN * S[0], LEAD_SIGN * S[1])     # lead-side unit vector (launcher frame)
U_W = (0.0, A3.NIP_U[0], A3.NIP_U[1])        # A3-world stud axis (outward)
LEAF_T = (LEAF_K_A3[0] * LEAF_K_A3[1] ** 3 / (LEAF_X[1] - LEAF_X[0])) ** (1 / 3)     # 1.84 for a 28 mm wide leaf
LEAF_U0 = A3.LEAF_U0                          # free-state leaf inner face (pads stand LEAF_PRE into the thumbwheel)
EPS_BAY = (A3._solve_eps(GAP_BAY[1]), A3._solve_eps(GAP_BAY[0]))
BAY_POLYS = [A3.bp_band(e, 0.5) for e in A3.lin(EPS_BAY[0], EPS_BAY[1], BAY_SAMPLES)]
WCR = l2r(WC)                                 # motor axis, rig (y, z)
MG_ORIGIN = (WCR[0] + 29.0, MG_Z0)            # MotorGo STEP origin (a hole), rig (y, z): STEP +X = rig -Y, STEP +Y = rig -Z


def mg_rig(a, b):
    """MotorGo STEP (a, b) -> rig (y, z)"""
    return (MG_ORIGIN[0] - a, MG_ORIGIN[1] - b)


M_MG = G.frame(Vector((X_PCB + STANDOFF[1], MG_ORIGIN[0], MG_ORIGIN[1])), Vector((0, -1, 0)), Vector((0, 0, -1)), Vector((1, 0, 0)))

# =====================================================================================================
# A3 builders: keep them out of A3's own registries, keep their print info
# =====================================================================================================
A3_INFO = {}


def _a3_finish(ob, name, kind, color, pivot=None, **info):
    ob.name = name
    A3_INFO[name] = info
    return ob


A3.finish = _a3_finish


def xform(ob, M):
    """bake a transform; flips the winding for mirrored frames (A3's nip frame is left-handed; cadlib's xform does not flip)"""
    A3.xform(ob, M)
    ob.data.update()
    return ob


def to_rig(ob):
    return xform(ob, M_RIG)


def prot(R_a3):
    """print rotation of a part baked into rig world, from its A3-world print rotation"""
    return R_a3 @ R_TILT_INV


# =====================================================================================================
# JOINTS (rig world)
# =====================================================================================================
def joints():
    A.joint("PIV_flywheel", tuple(rig_pt(A3.WHEEL_XW, WC)), 'X', continuous=True, step=45)
    # backplate hinge, + closes the gap. Range = thumbwheel test range; home = A3 operating gap (6.5 bare)
    A.joint("PIV_hood", tuple(rig_pt(A3.WHEEL_XW, A3.HINGE)), 'X', lo=eps_deg(GAP_TEST[1]), hi=eps_deg(GAP_TEST[0]), home=0.0, step=1.0)


# =====================================================================================================
# GUARD OUTLINE: A3 cavities + SKIN, clipped to the A3 profile (the A3 hull minus the solid it does not need)
# =====================================================================================================
def cavities():
    return [A3.wheel_cavity_poly(), A3.nip_poly(), A3.muzzle_poly(), A3.chute_poly()] + BAY_POLYS + [A3.BAY_BOSS]


_LOBES = []


def convex_lobes():
    if _LOBES:
        return _LOBES
    W = SKIN
    bay_pts = [p for poly in BAY_POLYS[::4] for p in poly[::2]] + list(A3.BAY_BOSS)
    _LOBES.extend([A3.circle(WC, A3.WC_R + W, 160),
                   A3.hull_circles([(p, W) for p in bay_pts], 24),
                   A3.hull_circles([(p, W) for p in A3.muzzle_poly()], 24),
                   A3.hull_circles([(p, W) for p in A3.nip_poly()], 24),
                   A3.circle((0.0, 0.0), A3.DRUM_R, 96)])
    return _LOBES


def outline_solid(name, x0, x1, extra=()):
    """prism of the shrink-wrapped outline between x0 and x1 (A3 world)"""
    obs = [A3.lprism(name + "_l%d" % k, poly, x0, x1) for k, poly in enumerate(convex_lobes())]
    ch = A3.chute_poly()
    obs.append(A3.lprism(name + "_ch", ch, x0, x1))
    for i in range(len(ch)):           # Minkowski: chute polygon grown by SKIN (it is not convex)
        a, b = ch[i], ch[(i + 1) % len(ch)]
        if math.hypot(b[0] - a[0], b[1] - a[1]) > 0.05:
            obs.append(A3.lprism(name + "_cs%d" % i, stadium(a, b, SKIN, 6), x0, x1))
    base = G.csg(obs[0], add=obs[1:])
    base = G.csg(base, inter=[A3.lprism(name + "_P", A3.PROFILE, x0 - 1, x1 + 1)])
    if extra:                          # features that stand outside the A3 profile (land + seat, funnel closure)
        base = G.csg(base, add=[A3.lprism(name + "_x%d" % k, poly, x0, x1) for k, poly in enumerate(extra)])
    return base


def in_outline(c):
    if not A3.pip(c, A3.PROFILE):
        return False
    if math.hypot(c[0] - WC[0], c[1] - WC[1]) <= A3.WC_R + SKIN or math.hypot(*c) <= A3.DRUM_R:
        return True
    if any(A3.pip(c, L) for L in convex_lobes()[1:4]):
        return True
    ch = _CHUTE
    return A3.pip(c, ch) or A3.poly_dist(c, ch) <= SKIN


_CHUTE = A3.chute_poly()


def pick_cover_screws():
    """screw centres where a Ø5.2 disc (pilot 2.5 + 1.35 wall) is solid guard: in the outline, clear of every cavity,
    the stud slot and the hinge; spread round the outline"""
    cav = cavities()
    hinge_clear = A3.HINGE_BOSS_R + 0.5 + 3.0
    cands = []
    xs = [p[0] for p in A3.PROFILE]
    ys = [p[1] for p in A3.PROFILE]
    for i in range(int(min(xs)), int(max(xs)) + 1):
        for j in range(int(min(ys)), int(max(ys)) + 1):
            c = (float(i), float(j))
            if not in_outline(c):
                continue
            ring = [(c[0] + 2.6 * math.cos(k * math.pi / 8), c[1] + 2.6 * math.sin(k * math.pi / 8)) for k in range(16)]
            if not all(in_outline(p) for p in ring):
                continue
            if any(A3.pip(c, cv) or A3.poly_dist(c, cv) < 2.6 for cv in cav):
                continue
            if math.hypot(c[0] - A3.HINGE[0], c[1] - A3.HINGE[1]) < hinge_clear:
                continue
            if A3.seg_dist(c, A3.JACK_PT, A3.NIP_E) < 6.0:
                continue
            cands.append(c)
    return A3.spread_pick(cands, N_COVER_SCREWS, seeds=[WC])


# =====================================================================================================
# GUARD
# =====================================================================================================
def nip_prism(name, uv_poly, x0, x1):
    return A3.lprism(name, [A3.nip_pq(u, v) for u, v in uv_poly], x0, x1)


def outline_bottom(y):
    """lowest rig z of the A3 profile on the vertical line at rig y"""
    pts = [l2r(p) for p in A3.PROFILE]
    zs = []
    for i in range(len(pts)):
        (y0, z0), (y1, z1) = pts[i], pts[(i + 1) % len(pts)]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            zs.append(z0 + (z1 - z0) * (y - y0) / (y1 - y0))
    return min(zs)


def funnel_block_rig():
    """side block under / around the funnel (rig y, z): closes the -X side of the funnel, x 0..13"""
    hw, zt = FUNNEL_THROAT
    rim = hw + (FUNNEL_MOUTH_Z - zt) / math.tan(math.radians(FUNNEL_ANG)) + FUNNEL_T / math.sin(math.radians(FUNNEL_ANG))
    H = AXIS_H
    return [(-rim, H + FUNNEL_MOUTH_Z), (-12.0, H + 12.0), (12.0, H + 12.0), (rim, H + FUNNEL_MOUTH_Z)]


def funnel_walls_rig():
    hw, zt = FUNNEL_THROAT
    run = (FUNNEL_MOUTH_Z - zt) / math.tan(math.radians(FUNNEL_ANG))
    off = FUNNEL_T / math.sin(math.radians(FUNNEL_ANG))
    H = AXIS_H
    return [[(sg * hw, H + zt), (sg * (hw + run), H + FUNNEL_MOUTH_Z), (sg * (hw + run + off), H + FUNNEL_MOUTH_Z), (sg * (hw + off), H + zt)]
            for sg in (-1, 1)]


def build_guard(screws):
    land_uv = [(-10.0, A3.LAND_V[0]), (0.0, A3.LAND_V[0]), (0.0, A3.LAND_V[1]), (-10.0, A3.LAND_V[1])]
    body = outline_solid("PRT_rig_guard", X0, X_CI, extra=[[A3.nip_pq(u, v) for u, v in land_uv]])
    G.bevel(body, A3.EB)
    # integral leaf spring (A3 nip-cover leaf: same rate, preload, travel), rigid stop beam, root block
    root = nip_prism("root", [(0.0, ROOT_V), (STOP_U[1], ROOT_V), (STOP_U[1], A3.LAND_V[1]), (0.0, A3.LAND_V[1])], *LEAF_X)
    leaf = nip_prism("leaf", [(LEAF_U0, TIP_V), (LEAF_U0 + LEAF_T, TIP_V), (LEAF_U0 + LEAF_T, ROOT_V + 0.5), (LEAF_U0, ROOT_V + 0.5)], *LEAF_X)
    stop = nip_prism("stop", [(STOP_U[0], TIP_V), (STOP_U[1], TIP_V), (STOP_U[1], ROOT_V + 0.5), (STOP_U[0], ROOT_V + 0.5)], *LEAF_X)
    pads = []
    for sg in (-1, 1):
        xa, xb = A3.NIP_X + sg * 6.0 - 1.5, A3.NIP_X + sg * 6.0 + 1.5
        # (x, u) section extruded along v (nip-frame local Z): A3 pad, 3 x 4 x 2.5 (a 2.5 mm ledge on the leaf wall in print)
        sec = [(xa, LEAF_U0 + 0.3), (xb, LEAF_U0 + 0.3), (xb, LEAF_U0 - A3.PAD_H), (xa, LEAF_U0 - A3.PAD_H)]
        pd = A3.prism("pad%d" % sg, sec, -2.0, 2.0, 'Z')
        xform(pd, A3.nip_frame())
        pads.append(pd)
    fblock = A3.lprism("fblock", rig_poly(funnel_block_rig()), X0, FUNNEL_X[0])
    fwalls = [A3.lprism("fw%d" % k, rig_poly(w), FUNNEL_X[0] - 0.01, FUNNEL_X[1]) for k, w in enumerate(funnel_walls_rig())]
    ztop = max(outline_bottom(GUARD_LEG_Y[0]), outline_bottom(GUARD_LEG_Y[1])) + 8.0
    post = A3.lprism("post", rig_poly([(GUARD_LEG_Y[0], 0.0), (GUARD_LEG_Y[1], 0.0), (GUARD_LEG_Y[1], ztop), (GUARD_LEG_Y[0], ztop)]), *GUARD_FOOT_X)
    pad = A3.lprism("gpad", rig_poly([(GUARD_PAD_Y[0], 0.0), (GUARD_PAD_Y[1], 0.0), (GUARD_PAD_Y[1], FOOT_T), (GUARD_PAD_Y[0], FOOT_T)]), *GUARD_FOOT_X)
    body = G.csg(body, add=[root, leaf, stop] + pads + [fblock, post, pad])
    # ---- A3 cavities: wheel, nip, muzzle from the inner face; chute from x 13; bay over the rig range
    xi, xc = X_IN, X_CI
    sub = [A3.lprism("wc", A3.wheel_cavity_poly(), xi, xc + 1), A3.lprism("nip", A3.nip_poly(), xi, xc + 1),
           A3.lprism("mz", A3.muzzle_poly(), xi, xc + 1), A3.lprism("ch", A3.chute_poly(), A3.CH_X0, xc + 1)]
    sub += [A3.lprism("bay%d" % k, poly, xi, xc + 1) for k, poly in enumerate(BAY_POLYS)]
    sub.append(A3.lprism("bayb", A3.BAY_BOSS, xi, xc + 1))
    body = G.csg(body, sub=sub)
    body = G.csg(body, add=fwalls)          # after the chute cut, so the A3 fan cut does not trim the throat
    sub = []
    # stud slot, shank only (the rig's stud goes in from the bay side, so its head never passes the guard; A3: R3.6
    # for the head), swept over the rig bay range, from the plate's back face to just past the seat
    inner, outer = [], []
    for e in A3.lin(EPS_BAY[0] - 0.01, EPS_BAY[1] + 0.01, 9):
        p0, d = A3.stud_line(e)
        sd = A3.stud_d(e)
        inner += [(vadd(p0, d, -1.0), A3.STUD_HOLE_R), (vadd(p0, d, 0.0), A3.STUD_HOLE_R)]      # head pocket at the plate face (the tilted hex head rim)
        outer += [(vadd(p0, d, -1.0), STUD_SLOT_R), (vadd(p0, d, sd + 0.5), STUD_SLOT_R)]
    sub.append(A3.lprism("stud_i", A3.hull_circles(inner, 24), A3.NIP_X - A3.STUD_HOLE_R, A3.NIP_X + A3.STUD_HOLE_R))
    sub.append(A3.lprism("stud_o", A3.hull_circles(outer, 24), A3.NIP_X - STUD_SLOT_R, A3.NIP_X + STUD_SLOT_R))
    # leaf hole and stop window: slots swept over the stud's swing (it tilts with the backplate), teardrop tops (+x is print up)
    for nm, u0, u1, r in (("lh", LEAF_U0 - A3.PAD_H - 0.5, LEAF_U0 + LEAF_T + 0.5, 3.2), ("sw", STOP_U[0] - 0.5, STOP_U[1] + 0.5, 3.6)):
        vs = []
        for e in A3.lin(EPS_BAY[0], EPS_BAY[1], 9):
            p0, d = A3.stud_line(e)
            for u in (u0, u1):
                # where the stud line crosses the plane u (nip frame), in v
                s = u
                pt = None
                for k in range(400):
                    q = vadd(p0, d, k * 0.1)
                    du = (q[0] - A3.NIP_E[0]) * A3.NIP_U[0] + (q[1] - A3.NIP_E[1]) * A3.NIP_U[1]
                    if du >= s:
                        pt = q
                        break
                if pt is not None:
                    vs.append((pt[0] - A3.NIP_E[0]) * A3.NIP_V[0] + (pt[1] - A3.NIP_E[1]) * A3.NIP_V[1])
        v0, v1 = min(vs), max(vs)
        if nm == "lh":
            sec = A3.hull_circles([((A3.NIP_X, v0), r), ((A3.NIP_X, v1), r)], 48)
        else:
            sec = A3.hull2d(G.teardrop((A3.NIP_X, v0), r, (1, 0)) + G.teardrop((A3.NIP_X, v1), r, (1, 0)))
        t = A3.prism(nm, sec, u0, u1, 'Y')    # (x, z=v) section along local y = u
        xform(t, A3.nip_frame())
        sub.append(t)
    # shaft, motor + frame screws (counterbores from the inner face), hinge countersink on the outer face
    sub.append(A3.lcyl("sh", WC, 6.0, X0 - 1, xi + 1))
    for k, c in enumerate(A3.MOTOR_SCREWS):
        sub.append(A3.lcyl("ms%d" % k, c, 1.7, X0 - 1, xi + 1, n=16))
        sub.append(A3.lcyl("mc%d" % k, c, A3.CBORE_R, MOTOR_CB_FLOOR, xi + 1, n=20))
    sub.append(A3.lcyl("hg", A3.HINGE, 1.7, X0 - 1, xi + 1, n=16))
    sub.append(A3.cone("hgc", (A3.HINGE[0], A3.T_Z + A3.HINGE[1]), 3.4, 1.7, X0 - 0.01, X0 + 1.75, 'X', n=24))
    for k, c in enumerate(screws):
        sub.append(A3.lcyl("sp%d" % k, c, 1.25, xc - 10, xc + 1, n=16))
    xm = 0.5 * (GUARD_FOOT_X[0] + GUARD_FOOT_X[1])
    for y in GUARD_PAD_Y:
        y0, y1 = (y - 1, y + NOTCH[1]) if y == GUARD_PAD_Y[0] else (y - NOTCH[1], y + 1)
        sub.append(rig_box("gn", xm - NOTCH[0] / 2, xm + NOTCH[0] / 2, y0, y1, -1, FOOT_T + 1))
    body = G.csg(body, sub=sub)
    to_rig(body)
    return A.part(body, "PRT_rig_guard", 'PRT', "pla_b", stl="rig_guard", print_rot=prot(A3.R_NX_DOWN), infill=15, supports="no",
                  orient="outer (motor-side) wall face on the bed, as the A3 body; every feature is an extrusion along print Z")


# =====================================================================================================
# COVER
# =====================================================================================================
def build_cover(screws):
    x0, x1 = X_CI, X_CI + COVER_T
    ob = outline_solid("PRT_rig_cover", x0, x1, extra=[rig_poly(funnel_block_rig())])
    G.bevel(ob, 0.4)
    boss = A3.lcyl("hb", A3.HINGE, HINGE_BOSS[0], x1 - 0.01, x1 + HINGE_BOSS[1], n=32)
    ob = G.csg(ob, add=[boss])
    sub = [A3.lcyl("hgp", A3.HINGE, 1.25, x0 - 1, x1 + HINGE_BOSS[1] + 1, n=16)]
    for k, c in enumerate(screws):
        sub.append(A3.lcyl("s%d" % k, c, 1.7, x0 - 1, x1 + 1, n=16))
    ob = G.csg(ob, sub=sub)
    to_rig(ob)
    return A.part(ob, "PRT_rig_cover", 'PRT', "pla_b", stl="rig_cover", print_rot=prot(A3.R_NX_DOWN), infill=15, supports="no",
                  orient="inner face on the bed; hinge boss up")


# =====================================================================================================
# FRAME: motor tube + encoder end + MotorGo legs + rear foot. Prints rear face down.
# =====================================================================================================
def plink_m():
    s = LEAD_SIGN
    return A3.frame((X_PCB, A3.W_P, A3.T_Z + A3.W_Q), (0, -s * S[1], s * S[0]), (0, -s * S[0], -s * S[1]), (1, 0, 0))


def plink_holes():
    M = plink_m()
    return [(M @ Vector((sx * 8.0, sy * 8.0, 0.0))) for sx in (-1, 1) for sy in (-1, 1)]


def lead_band(r0, r1, hw=7.0):
    return [vadd(vadd(WC, LS, r0), N, hw), vadd(vadd(WC, LS, r1), N, hw), vadd(vadd(WC, LS, r1), N, -hw), vadd(vadd(WC, LS, r0), N, -hw)]


def build_frame():
    """Rear cup: grips the rear 13 mm of the can on the A3 nacelle crush ribs, its shoulder seats on the motor's rear face
    (so the Plink-to-magnet gap is set by this part alone), its end wall carries the A3 encoder-cap pegs and JST slot,
    and its bed-level plate carries the MotorGo standoffs, two legs and the rear bench foot."""
    rr = BORE_R
    ob = A3.lcyl("PRT_rig_frame", WC, TUBE_R, X_END, CUP_X1, n=128)
    plate = []
    wy, wz = WCR
    for a in (0.0, 58.0):
        y = wy + 29.0 - a
        plate.append(A3.lprism("leg", rig_poly([(y - LEG_W / 2, 0.0), (y + LEG_W / 2, 0.0), (y + LEG_W / 2, MG_Z0 + 49.0 + 2.0), (y - LEG_W / 2, MG_Z0 + 49.0 + 2.0)]), X_END, X_PCB))
        sg = 1 if y > wy else -1
        plate.append(A3.lprism("lnk", A3.hull_circles([(r2l((y, MG_Z0 + 49.0)), LEG_W / 2), (r2l((wy + sg * 12.0, wz - 14.0)), LEG_W / 2)], 24), X_END, X_PCB))
    plate.append(A3.lprism("bar", rig_poly([(wy - FRAME_FOOT_HALF, 0.0), (wy + FRAME_FOOT_HALF, 0.0), (wy + FRAME_FOOT_HALF, 7.0), (wy - FRAME_FOOT_HALF, 7.0)]), X_END, X_PCB))
    plate.append(A3.lprism("flange", rig_poly([(wy - FRAME_FOOT_HALF, 0.0), (wy + FRAME_FOOT_HALF, 0.0), (wy + FRAME_FOOT_HALF, FOOT_T), (wy - FRAME_FOOT_HALF, FOOT_T)]), X_END, X_END + FRAME_FOOT_X))
    for k, (a, b) in enumerate(MG_HOLES):
        plate.append(A3.lcyl("so%d" % k, r2l(mg_rig(a, b)), STANDOFF[0], X_PCB - 0.01, X_PCB + STANDOFF[1], n=24))
    ob = G.csg(ob, add=plate)
    sub = [A3.lcyl("bore", WC, rr, X_PCB, CUP_X1 + 1, n=128),
           A3.lprism("kw", lead_band(15.0, 27.5), X_PCB + 0.01, CUP_X1 + 1),     # keyway: the lead block slides through
           A3.lprism("jst", lead_band(12.0, 30.0), X_END - 1, X_PCB + 0.5)]      # A3 encoder-cap JST slot
    for k, (a, b) in enumerate(MG_HOLES):
        sub.append(A3.lcyl("sp%d" % k, r2l(mg_rig(a, b)), MG_PILOT_R, X_PCB + 1.0, X_PCB + STANDOFF[1] + 1, n=16))
    ya, yb = mg_rig(55.0, 0.0)[0], mg_rig(3.0, 0.0)[0]          # relief for the MotorGo header pins under the board
    sub.append(rig_box("pins", X_PCB + STANDOFF[1] - 8.5, X_PCB + STANDOFF[1] + 0.01, ya, yb, MG_Z0 - 2.0, MG_Z0 + 2.0))
    xm = X_END + FRAME_FOOT_X / 2
    for sg in (-1, 1):
        ye = wy + sg * FRAME_FOOT_HALF
        y0, y1 = (ye - NOTCH[1], ye + 1) if sg > 0 else (ye - 1, ye + NOTCH[1])
        sub.append(rig_box("fn", xm - NOTCH[0] / 2, xm + NOTCH[0] / 2, y0, y1, -1, 8.0))
    ob = G.csg(ob, sub=sub)
    # A3 crush ribs (turned 60 deg so none faces the keyway), shoulder on the motor's rear face, Plink pegs
    ribs = [A3.lprism("cr%d" % k, A3.crush_rib(A3.MOTOR_D / 2, rr + 0.4, 60.0 + 120.0 * k), -A3.MOTOR_L + 1.0, -A3.MOTOR_L + 13.0) for k in range(3)]
    sh = A3.lcyl("sho", WC, rr + 0.2, X_PCB - 0.01, SHOULDER_X, n=128)
    sh = G.csg(sh, sub=[A3.lcyl("shi", WC, 16.0, X_PCB - 1, SHOULDER_X + 1, n=96), A3.lprism("shk", lead_band(12.0, 30.0), X_PCB - 1, SHOULDER_X + 1)])
    pegs = [A3.cyl("pg%d" % i, (h.y, h.z), 1.15, X_PCB - 0.01, X_PCB + 1.5, 'X', n=16) for i, h in enumerate(plink_holes())]
    ob = G.csg(ob, add=ribs + [sh] + pegs)
    to_rig(ob)
    return A.part(ob, "PRT_rig_frame", 'PRT', "pla_a", stl="rig_rear_cup", print_rot=prot(A3.R_NX_DOWN), infill=15, supports="no",
                  orient="rear (encoder) face on the bed; cup ring, ribs, standoffs and foot flange grow up")


# =====================================================================================================
# A3 PARTS (A3 builders)
# =====================================================================================================
def build_a3_parts():
    fw = A3.build_flywheel()
    to_rig(fw)
    A.part(fw, "PRT_flywheel", 'PRT', "pla_a", joint="PIV_flywheel", stl="flywheel", print_rot=prot(A3.R_NX_DOWN), infill=100,
           supports="no", orient=A3_INFO["PRT_flywheel"]["orient"], notes="A3 part, unchanged; 12-15 mm hockey tape on the 12.8 mm land")
    hood = A3.build_hood()
    # rig change: the hex stud pocket opens to the plate's +X edge so the stud head slides in sideways
    # (the leaf is part of the guard, so the stud is threaded into the thumbwheel before the plate goes in)
    slot = A3._prism_along("slot", [(0.0, -A3.NUT_AF / 2), (14.0, -A3.NUT_AF / 2), (14.0, A3.NUT_AF / 2), (0.0, A3.NUT_AF / 2)],
                           A3.NIP_X, vadd(A3.JACK_PT, A3.NIP_U, 1.0), vadd(A3.JACK_PT, A3.NIP_U, -A3.STUD_POCKET_D))
    hood = G.csg(hood, sub=[slot])
    to_rig(hood)
    A.part(hood, "PRT_backplate", 'PRT', "pla_a", joint="PIV_hood", stl="backplate", print_rot=prot(A3.R_NX_DOWN), infill=40,
           supports="no", orient=A3_INFO["PRT_hood"]["orient"], notes="A3 hood; stud pocket opened to the +X edge")
    tw = A3.build_thumbwheel()
    to_rig(tw)
    A.part(tw, "PRT_nip_wheel", 'PRT', "pla_b", stl="nip_wheel", print_rot=prot(A3_INFO["PRT_nip_wheel"]["print_rot"]), infill=50,
           supports="no", orient=A3_INFO["PRT_nip_wheel"]["orient"], notes="A3 part, unchanged")


# =====================================================================================================
# PURCHASED
# =====================================================================================================
def build_purchased():
    wy, wz = A3.W_P, A3.T_Z + A3.W_Q
    ML, MD = A3.MOTOR_L, A3.MOTOR_D
    body = A3.cyl("BUY_motor", (wy, wz), MD / 2, -ML, A3.X_MF, 'X', n=96)
    G.bevel(body, 0.8)
    blk = A3.lprism("blk", [vadd(vadd(WC, LS, 10.0), N, 6.0), vadd(vadd(WC, LS, MD / 2 + 7), N, 6.0), vadd(vadd(WC, LS, MD / 2 + 7), N, -6.0), vadd(vadd(WC, LS, 10.0), N, -6.0)],
                    -ML + 0.5, -ML + 12.5)
    rec = A3.cyl("rec", (wy, wz), A3.REAR_ACCESS_D / 2, -ML - 1, -ML + A3.REAR_SHAFT_RECESS + 1.5, 'X', n=32)
    st = G.csg(body, add=[blk])
    st = G.csg(st, sub=[rec, A3.cyl("fb", (wy, wz), 2.6, A3.X_MF - 3, A3.X_MF + 1, 'X', n=24)])
    to_rig(st)
    A.part(st, "BUY_motor", 'BUY', (0.30, 0.42, 0.30, 1), mass_g=230, src="reference/bldc_xteam_3674_drawing.png (stator + lead block)")
    rb, fl = 2.5, 1.95
    shaft = A3.cyl("BUY_motor_shaft", (wy, wz), 2.5, A3.X_MF - 3, A3.X_MF + A3.SHAFT_LEN - 14, 'X', n=24)
    dp = [(wy + rb * math.cos(math.radians(a)), wz + rb * math.sin(math.radians(a))) for a in range(0, 360, 10) if rb * math.cos(math.radians(a)) < fl]
    dp += [(wy + fl, wz - math.sqrt(rb * rb - fl * fl)), (wy + fl, wz + math.sqrt(rb * rb - fl * fl))]
    dsh = A3.prism("dsh", A3.hull2d(dp), A3.X_MF + A3.SHAFT_LEN - 14.01, A3.X_MF + A3.SHAFT_LEN, 'X')
    rs = A3.cyl("rs", (wy, wz), 2.5, -ML + A3.REAR_SHAFT_RECESS, -ML + A3.REAR_SHAFT_RECESS + 1.4, 'X', n=24)
    shaft = G.csg(shaft, add=[dsh, rs])
    to_rig(shaft)
    A.part(shaft, "BUY_motor_shaft", 'BUY', "buy_metal", joint="PIV_flywheel", mass_g=20, src="drawing: Ø5 x 21, 14 mm D-flat; rear stub")
    mag = A3.cyl("BUY_magnet", (wy, wz), A3.MAGNET_D / 2, -ML + A3.REAR_SHAFT_RECESS - A3.MAGNET_T, -ML + A3.REAR_SHAFT_RECESS, 'X', n=24)
    to_rig(mag)
    A.part(mag, "BUY_magnet", 'BUY', (0.45, 0.45, 0.50, 1), joint="PIV_flywheel", mass_g=1, src="Ø6 x 2.5 diametric, glued to the rear shaft end")
    pk = G.import_stl(os.path.join(A3.REF, "plink_encoder.stl"), "BUY_plink_encoder")
    xform(pk, plink_m())
    to_rig(pk)
    A.part(pk, "BUY_plink_encoder", 'BUY', "pcb", mass_g=3, src="reference/plink_encoder.stl")
    mg = G.import_stl(os.path.join(A3.REF, "mg_axis.stl"), "BUY_motorgo_axis")
    xform(mg, M_MG)                       # placed straight in rig world
    A.part(mg, "BUY_motorgo_axis", 'BUY', "pcb", mass_g=25, src="reference/mg_axis.stl")
    tp = A3.cyl("BUY_tape", (wy, wz), A3.WHEEL_R + 0.5, A3.WEB_X1 + 0.05, A3.WHEEL_X1 - 2.65, 'X', n=160)
    tp = G.csg(tp, sub=[A3.cyl("ti", (wy, wz), A3.WHEEL_R + 0.02, A3.WEB_X1 - 1, A3.WHEEL_X1, 'X', n=160)])
    to_rig(tp)
    A.part(tp, "BUY_tape", 'BUY', (0.08, 0.08, 0.10, 1), joint="PIV_flywheel", mass_g=2, src="1/2 in hockey tape, 0.5 mm, one wrap on the 12.8 mm land")


# =====================================================================================================
# FASTENERS
# =====================================================================================================
A.FASTENER_SPECS.setdefault("M3_hex", (3.0, 6.0, 2.0))       # DIN 933 M3 hex head (envelope)
A.FASTENER_SPECS.setdefault("M2.5_pan", (2.5, 4.5, 1.7))


def fst(name, at_a3, into_a3, length, spec="M3_cap", joint=None, host=None, step=None):
    return A.fastener(name, tuple(a3_to_rig(at_a3)), tuple(rig_dir(into_a3)), length, spec=spec, joint=joint, host=host, step=step)


def build_fasteners(screws):
    lpt = A3.lpt
    for k, c in enumerate(A3.MOTOR_SCREWS):
        fst("FST_motor_%d" % k, lpt(MOTOR_CB_FLOOR, c), (-1, 0, 0), MOTOR_SCREW_L, host="BUY_motor", step="motor")
    for k, c in enumerate(screws):
        fst("FST_cover_%d" % k, lpt(X_CI + COVER_T, c), (-1, 0, 0), 12, spec="M3_pan", host="PRT_rig_guard", step="cover")
    fst("FST_hinge", lpt(X0, A3.HINGE), (1, 0, 0), 40, spec="M3_csk", host="PRT_rig_cover", step="cover")
    fst("FST_nip_stud", lpt(A3.NIP_X, A3.JACK_PT), U_W, A3.STUD_L, spec="M3_hex", joint="PIV_hood", step="nip")
    A.nut("FST_nip_nut", tuple(a3_to_rig(A3.nip_frame() @ Vector((A3.NIP_X, A3.TW_NUT_U[0], 0.0)))), tuple(rig_dir(U_W)), step="nip")
    wy, wz = A3.W_P, A3.T_Z + A3.W_Q
    for s in (-1, 1):
        hy = wy + s * A3.FW_T_HEAD
        fst("FST_fw_bolt_%d" % (s + 1), (A3.FW_BOLT_X, hy, wz + s * A3.FW_BOLT_OFF), (0, -s, 0), A3.FW_BOLT_L, joint="PIV_flywheel", step="flywheel")
        A.nut("FST_fw_nut_%d" % (s + 1), tuple(a3_to_rig((A3.FW_BOLT_X, wy - s * A3.FW_T_NUT, wz + s * A3.FW_BOLT_OFF))), tuple(rig_dir((0, -s, 0))),
              joint="PIV_flywheel", step="flywheel")
    for k, (a, b) in enumerate(MG_HOLES):
        y, z = mg_rig(a, b)
        A.fastener("FST_mg_%d" % k, (X_PCB + STANDOFF[1] + A3.MG_PCB_T, y, z), (-1, 0, 0), 8, spec="M2.5_pan", host="PRT_rig_frame", step="frame")


# =====================================================================================================
# CABLES: stock 80 mm phase leads reach the MotorGo pads; encoder JST through the end-wall slot
# =====================================================================================================
def build_cables():
    ML = A3.MOTOR_L
    xb = X_PCB + STANDOFF[1] + A3.MG_PCB_T + 1.5
    for k, a in enumerate((14.0, 22.0, 30.0)):          # J6/J8 phase pads along the STEP y ~ -51 edge (top edge here)
        start = vadd(vadd(WC, LS, A3.MOTOR_D / 2 + 7), N, (k - 1) * 3.5)
        mid = rig_pt(-ML + 6.5, vadd(start, LS, 4.0))
        pad = mg_rig(a, -51.0)
        pts = [rig_pt(-ML + 6.5, start), mid, Vector((xb + 3.0, mid.y, pad[1] + 2.0)), Vector((xb + 3.0, pad[0], pad[1] + 2.0)), Vector((xb, pad[0], pad[1]))]
        A.cable("CAB_phase_%d" % k, [tuple(p) for p in pts], 2.0, ("cable_red", "cable_blk", "cable_yel")[k], lead_len=80)
    j0 = vadd(WC, LS, 10.0)
    ep = mg_rig(45.0, -40.0)
    pts = [rig_pt(X_PCB + 2.5, j0), rig_pt(X_PCB - 2.0, vadd(WC, LS, 21.0)), rig_pt(X_END - 3.0, vadd(WC, LS, 30.0)),
           Vector((X_END - 3.0, ep[0], ep[1] + 10.0)), Vector((X_PCB + 2.0, ep[0], ep[1] + 4.0)), Vector((xb, ep[0], ep[1]))]
    A.cable("CAB_encoder", [tuple(p) for p in pts], 1.4, "cable_wht")


# =====================================================================================================
# DERIVED NUMBERS AND THE CHECK CONFIG (written from the same parameters)
# =====================================================================================================
def gap_ray(gap):
    """ray across the gap at the backplate's BDC point (it moves with the hinge): origin 1 mm off the plate, toward the wheel"""
    e = A3._solve_eps(gap)
    p = A3.rot2(A3.pw(A3.WHEEL_R + A3.HOOD_GAP, 0.0), e, A3.HINGE)
    d = (WC[0] - p[0], WC[1] - p[1])
    L = math.hypot(*d)
    d = (d[0] / L, d[1] / L)
    o = rig_pt(A3.WHEEL_XW, vadd(p, d, 1.0))
    w = rig_dir((0.0, d[0], d[1]))
    return {"origin": [round(v, 3) for v in o], "dir": [round(v, 5) for v in w]}


def numbers():
    out = {}
    for g in (GAP_TEST[0], GAP_HOME, 8.0, 10.0, GAP_TEST[1]):
        e = A3._solve_eps(g)
        out["gap_%.1f" % g] = {"hinge_deg": round(math.degrees(e), 2), "stud_d_mm": round(A3.stud_d(e), 2),
                               "stud_tip_above_seat_mm": round(A3.STUD_L - (A3.STUD_POCKET_D - A3.STUD_HEAD_K) - A3.stud_d(e), 2)}
    E_ = 3500.0
    b, t, L = LEAF_X[1] - LEAF_X[0], LEAF_T, ROOT_V
    k = 3 * E_ * (b * t ** 3 / 12) / L ** 3
    sig = lambda F: 6 * F * L / (b * t * t)
    out["leaf"] = {"width": b, "thickness": round(t, 3), "rate_N_mm": round(k, 2), "preload_N": round(k * A3.LEAF_PRE, 1),
                   "force_at_stop_N": round(k * (A3.LEAF_PRE + A3.LEAF_TRAVEL), 1), "root_MPa_preload": round(sig(k * A3.LEAF_PRE), 1),
                   "root_MPa_stop": round(sig(k * (A3.LEAF_PRE + A3.LEAF_TRAVEL)), 1), "a3": A3.leaf_spring()}
    e1, e2 = A3._solve_eps(6.0), A3._solve_eps(7.0)
    out["gap_mm_per_turn"] = round(0.5 / abs(A3.stud_d(e1) - A3.stud_d(e2)), 3)
    out["encoder"] = {"pcb_back_x": X_PCB, "ic_top_x": X_PCB + A3.PLINK_IC_TOP, "magnet_face_x": -A3.MOTOR_L + A3.REAR_SHAFT_RECESS - A3.MAGNET_T, "gap": ENC_GAP}
    out["rig"] = {"tilt_deg": TILT, "axis_h": AXIS_H, "wheel_axis": [round(v, 2) for v in rig_pt(A3.WHEEL_XW, WC)],
                  "hinge": [round(v, 2) for v in rig_pt(A3.WHEEL_XW, A3.HINGE)],
                  "muzzle_exit_floor": [round(v, 2) for v in rig_pt(A3.WHEEL_XW, (A3.MUZZLE_FRONT, A3.FLOOR_FIX))],
                  "nip_bdc_mid": [round(v, 2) for v in rig_pt(A3.WHEEL_XW, A3.pw(A3.WHEEL_R + GAP_HOME / 2, 0.0))],
                  "funnel_mouth_z": AXIS_H + FUNNEL_MOUTH_Z, "thumbwheel_centre": [round(v, 2) for v in a3_to_rig(A3.nip_frame() @ Vector((A3.NIP_X, A3.TW_T / 2, 0.0)))]}
    return out


def check_config():
    lo, hi = eps_deg(GAP_TEST[1]), eps_deg(GAP_TEST[0])
    mid = A3.WHEEL_XW + 1.25
    dist = []
    for g, pose, why in ((GAP_TEST[0], {"PIV_hood": round(hi, 4)}, "thumbwheel closed end"), (GAP_HOME, {}, "A3 operating gap: 6.0 over tape"),
                         (GAP_TEST[1], {"PIV_hood": round(lo, 4)}, "thumbwheel open end")):
        D = {"a": "PRT_backplate", "b": "PRT_flywheel", "pose": pose, "min": round(g - 0.15, 2), "max": round(g + 0.15, 2),
             "why": "%s: %.1f bare at the plate's BDC point" % (why, g), "ray": gap_ray(g)}
        if not pose:
            D.update(payload_mm=7.0, tape_mm=0.5, compliant="PRT_rig_guard leaf spring: 3.9 N/mm, 9 N preload on the thumbwheel stop")
        dist.append(D)
    dist.append({"a": "BUY_magnet", "b": "BUY_plink_encoder", "min": ENC_GAP - 0.2, "max": ENC_GAP + 0.2, "why": "as-printed encoder air gap"})
    emit = {"frame": "world", "center": [round(0.5 * (FUNNEL_X[0] + FUNNEL_X[1]), 2), 0.0, AXIS_H + FUNNEL_MOUTH_Z - 4.0], "normal": [0, 0, 1], "radius": 6.0, "step": 2.0}
    ang = {"center": "PIV_flywheel", "frame": "PIV_flywheel", "zero": "-Z", "positive": "-Y", "range": [10, 92]}
    return {
        "_generated_by": "build.py check_config(); edit the parameters there, not this file",
        "overtravel_deg": 0.5,
        "fits": [
            {"a": "PRT_backplate", "b": "PRT_rig_guard", "min_clearance": 0.3, "why": "A3 bay: backplate band grown 0.5 all round, 0.5 to the inner wall face"},
            {"a": "PRT_backplate", "b": "PRT_rig_cover", "min_clearance": 0.3, "why": "A3: 0.5 to the cover face"},
            {"a": "PRT_backplate", "b": "FST_hinge", "min_clearance": 0.1, "why": "hinge axle: M3 shank running in the backplate's Ø3.4 boss"},
            {"a": "BUY_motor", "b": "BUY_magnet", "min_clearance": 0.8, "why": "magnet sits in the end cap's Ø8 access hole, 1 mm radial"}],
        "allow": [
            {"a": "PRT_rig_guard", "b": "PRT_nip_wheel", "why": "leaf pads are printed in the free state and stand 2.3 mm into the thumbwheel: that overlap is the 9 N preload (A3 whitelists the same pair)"},
            {"a": "FST_nip_stud", "b": "PRT_nip_wheel", "why": "stud runs through the thumbwheel's Ø3.4 bore; the wheel rocks on its seat with the stud's tilt (-5.2..+1.4 deg)"},
            {"a": "FST_nip_stud", "b": "FST_nip_nut", "why": "the captive nut rides on the stud and tilts with it"},
            {"a": "BUY_motor", "b": "BUY_motor_shaft", "why": "rotor in its own bearings"},
            {"a": "CAB_*", "b": "BUY_motorgo_axis", "why": "leads end on the board's pads / header"},
            {"a": "CAB_encoder", "b": "BUY_plink_encoder", "why": "JST plug on the Plink"},
            {"a": "CAB_phase_*", "b": "BUY_motor", "why": "phase leads leave the motor's lead block"}],
        "fasteners": {"captive": {"FST_nip_stud": "hex head held in the backplate pocket and never driven; the thumbwheel's captive nut turns"}},
        "assembly_order": [
            {"step": "rear cup on the bench: Plink on its pegs, MotorGo on its standoffs", "objects": ["PRT_rig_frame", "BUY_plink_encoder", "BUY_motorgo_axis", "FST_mg_*"]},
            {"step": "rear cup pressed onto the motor (magnet glued); guard onto the motor face", "objects": ["BUY_motor", "BUY_motor_shaft", "BUY_magnet", "PRT_rig_guard", "FST_motor_*"]},
            {"step": "nip: thumbwheel onto the seat, stud threaded in from the bay, backplate slid onto the stud head", "objects": ["PRT_nip_wheel", "FST_nip_*", "PRT_backplate"]},
            {"step": "flywheel with tape onto the D-shaft, pinch bolts", "objects": ["PRT_flywheel", "BUY_tape", "FST_fw_*"]},
            {"step": "cover, then the hinge axle from the motor side", "objects": ["PRT_rig_cover", "FST_cover_*", "FST_hinge"]}],
        "service": [
            {"op": "re-tighten or swap the flywheel (re-tape)", "remove": ["PRT_rig_cover", "FST_cover_*", "FST_hinge"], "fasteners": ["FST_fw_bolt_*"]},
            {"op": "re-seat the MotorGo", "fasteners": ["FST_mg_*"]}],
        "drop_tests": [
            {"name": "funnel_to_tape", "mode": "slide", "stall_deg": 20, "capture_mm": 0.5, "payload_mm": 7.0, "emit": emit, "dir": [0, 0, -1],
             "poses": {"PIV_hood": [round(hi, 4), 0.0, round(eps_deg(8.0), 4)]}, "expect": {"hit": ["PRT_flywheel", "BUY_tape"], "angle": ang}},
            {"name": "funnel_wide_gap_report_only", "mode": "slide", "stall_deg": 20, "capture_mm": 0.5, "payload_mm": 7.0, "emit": emit, "dir": [0, 0, -1],
             "poses": {"PIV_hood": [round(eps_deg(10.0), 4), round(lo, 4)]}, "expect": {}}],
        "slide_out": [
            {"name": "flywheel off along +X (cover off)", "objects": ["PRT_flywheel", "BUY_tape", "FST_fw_*"],
             "ignore": ["PRT_rig_cover", "FST_cover_*", "FST_hinge", "BUY_motor_shaft", "BUY_magnet"], "dir": [1, 0, 0], "dist": 60, "step": 4, "min_clearance": 0.8},
            {"name": "cover off along +X", "objects": ["PRT_rig_cover"], "ignore": ["FST_cover_*", "FST_hinge"], "dir": [1, 0, 0], "dist": 40, "step": 4, "min_clearance": 0.0}],
        "distances": dist,
        "stacks": [
            {"name": "encoder air gap (%.1f nominal, MT6701 wants 0.5..2.0)" % ENC_GAP, "limit": 0.5, "terms": [
                {"what": "cup print: shoulder (motor rear face) to Plink seat, %.2f mm" % (SHOULDER_X - X_PCB), "tol": 0.1},
                {"what": "motor rear face flatness where the shoulder lands", "tol": 0.1},
                {"what": "magnet face via the A3 jig (shaft end 0..1 mm recessed)", "tol": 0.25},
                {"what": "Plink IC height above PCB back", "tol": 0.1},
                {"what": "PCB seat on the pegs (hot glue)", "tol": 0.05},
                {"what": "cup pushed home on the shoulder", "tol": 0.05}], "why": "measure the real gap at bring-up and shim; README step B3"},
            {"name": "magnet-to-sensor centring", "limit": 0.3, "terms": [
                {"what": "Plink pegs to the cup bore axis (same printed part)", "tol": 0.1},
                {"what": "can in bore, 3 crush ribs", "tol": 0.1},
                {"what": "Plink IC to its PCB holes", "tol": 0.1},
                {"what": "magnet on shaft via the A3 jig spigot in the Ø8 access hole", "tol": 0.1}]}],
        "flexures": [{"part": "PRT_rig_guard", "name": "nip leaf spring", "from": [round(c, 3) for c in a3_to_rig(A3.nip_frame() @ Vector((A3.NIP_X, LEAF_U0, ROOT_V)))],
                      "to": [round(c, 3) for c in a3_to_rig(A3.nip_frame() @ Vector((A3.NIP_X, LEAF_U0, TIP_V)))], "stress_mpa": numbers()["leaf"]["root_MPa_stop"],
                      "why": "34 mm cantilever, 9 N preload; A3 printed it standing up (A3-F2)"},
                     {"part": "PRT_rig_guard", "name": "over-travel stop beam", "from": [round(c, 3) for c in a3_to_rig(A3.nip_frame() @ Vector((A3.NIP_X, STOP_U[0], ROOT_V)))],
                      "to": [round(c, 3) for c in a3_to_rig(A3.nip_frame() @ Vector((A3.NIP_X, STOP_U[0], TIP_V)))], "stress_mpa": 7.0,
                      "why": "takes the leaf's 18.7 N at the stop"}],
        "exposure": {"cables_ok": ["CAB_*"]},
        "cable_leads": {"CAB_phase_*": 80},
        "printers": {"P1S": [256, 256, 256], "H2D": [325, 320, 325]}, "prefer_printer": "P1S"}


# =====================================================================================================
# PRINT-TIME ESTIMATE (estimate, not sliced) from the exported STLs in print orientation, layer by layer, using the
# published speeds of Bambu's "0.20mm Standard" P1S profile typed in below. A second opinion next to cadcheck's flat
# 12 mm3/s; slice the STLs yourself for the real number.
# =====================================================================================================
BAMBU = {"layer": 0.2, "outer": (0.42, 200.0), "inner": (0.45, 300.0), "solid": (0.42, 250.0), "sparse": (0.45, 270.0),
         "first_layer_v": (50.0, 105.0), "max_flow": 21.0, "top": 5, "bottom": 3, "eff": 0.8, "layer_s": 1.5, "plate_min": 6.0}


def _v(w, v):
    return min(v, BAMBU["max_flow"] / (w * BAMBU["layer"]))


def estimate_stl(path, infill):
    import bmesh
    ob = G.import_stl(path, "EST")
    bm0 = bmesh.new()
    bm0.from_mesh(ob.data)
    zmax = max(v.co.z for v in bm0.verts)
    h = BAMBU["layer"]
    n = int(math.ceil(zmax / h))
    L, Acum = [], [0.0]
    for i in range(n):
        z = (i + 0.5) * h
        bm = bm0.copy()
        r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z), plane_no=(0, 0, 1))
        L.append(sum(e.calc_length() for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)))
        bm.free()
        bm = bm0.copy()
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, (i + 1) * h), plane_no=(0, 0, 1), clear_outer=True)
        bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary])
        Acum.append(abs(bm.calc_volume()))
        bm.free()
    bm0.free()
    G.kill(ob)
    A_ = [max(0.0, (Acum[i + 1] - Acum[i]) / h) for i in range(n)]
    ow, ov = BAMBU["outer"]
    iw, iv = BAMBU["inner"]
    sw, sv = BAMBU["solid"]
    pw_, pv = BAMBU["sparse"]
    t = vol = 0.0
    for i in range(n):
        a = A_[i]
        if a <= 0:
            continue
        wall_a = min(a, L[i] * (ow + iw))
        above = min([A_[j] if j < n else 0.0 for j in range(i + 1, i + 1 + BAMBU["top"])])
        below = min([A_[j] if j >= 0 else 0.0 for j in range(i - BAMBU["bottom"], i)])
        solid = min(a - wall_a, max(0.0, a - above) + max(0.0, a - below))
        sparse = max(0.0, a - wall_a - solid)
        dens = infill / 100.0
        path_sparse = sparse * dens / pw_
        ti = L[i] / _v(ow, ov) + L[i] / _v(iw, iv) + solid / sw / _v(sw, sv) + path_sparse / _v(pw_, pv)
        if i == 0:
            ti = L[i] * 2 / BAMBU["first_layer_v"][0] + max(0.0, a - wall_a) / sw / BAMBU["first_layer_v"][1]
        t += ti / BAMBU["eff"] + BAMBU["layer_s"]
        vol += (wall_a + solid + sparse * dens) * h
    return {"layers": n, "min": round(t / 60.0, 1), "g": round(vol * 1.24e-3, 1)}


def estimate(stl_dir):
    infill = {"rig_guard": 15, "rig_cover": 15, "rig_rear_cup": 15, "flywheel": 100, "backplate": 40, "nip_wheel": 50}
    out = {}
    for f in sorted(os.listdir(stl_dir)):
        if f.endswith(".stl"):
            nm = f[:-4]
            out[nm] = estimate_stl(os.path.join(stl_dir, f), infill.get(nm, 15))
    tot_min = sum(r["min"] for k, r in out.items() if not k.startswith("_"))
    out["_label"] = "estimate, not sliced"
    out["_total"] = {"print_min": round(tot_min, 1), "g": round(sum(r["g"] for k, r in out.items() if not k.startswith("_")), 1),
                     "with_2_plates_h": round((tot_min + 2 * BAMBU["plate_min"]) / 60.0, 2), "model": BAMBU}
    return out


# =====================================================================================================
# BUILD / RENDER
# =====================================================================================================
PARAMS = {k: v for k, v in dict(globals()).items() if k.isupper() and isinstance(v, (int, float, tuple, list)) and k not in ("A3_INFO",)}


def build():
    A.new_scene(params=PARAMS)
    A3.TMP = G.scratch()
    joints()
    screws = pick_cover_screws()
    build_guard(screws)
    build_cover(screws)
    build_frame()
    build_a3_parts()
    build_purchased()
    build_fasteners(screws)
    build_cables()
    return screws


SHOW = ("Printed", "Purchased")       # cadlib fasteners are joined shells, so they stay out of section booleans


def section(outdir, fname, axis, val, cam_loc, cam_tgt, ortho, keep_side="-", show=SHOW):
    """cadlib render.section with the MANIFOLD solver (its EXACT solver floods the view on the guard, as A3 found on the
    flywheel). Objects that are not closed solids (imported STLs) are shown uncut if they cross the plane."""
    k = "xyz".index(axis)
    lo, hi = [-5000.0] * 3, [5000.0] * 3
    if keep_side == "-":
        lo[k] = val
    else:
        hi[k] = val
    cutter = G.box("SECTION_CUT", lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    cutter.data.materials.append(A.mat(R.CUT))
    hidden, mods = [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob is cutter or ob.hide_render or ob.get("marker"):
            continue
        cname = ob.users_collection[0].name if ob.users_collection else ""
        if cname not in show:
            ob.hide_render = True
            hidden.append(ob)
            continue
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        mn, mx = min(v[k] for v in bb), max(v[k] for v in bb)
        if (mn >= val if keep_side == "-" else mx <= val):
            ob.hide_render = True
            hidden.append(ob)
        elif mn < val < mx and G.solid_stats(ob)[0] == 0:
            m = ob.modifiers.new("sec", 'BOOLEAN')
            m.operation, m.solver, m.object = 'DIFFERENCE', 'MANIFOLD', cutter
            if hasattr(m, "material_mode"):
                m.material_mode = 'TRANSFER'
            mods.append((ob, m))
    cutter.hide_render = True
    R.camera(cam_loc, cam_tgt, ortho=ortho)
    path = R.shot(os.path.join(outdir, fname))
    for ob, m in mods:
        ob.modifiers.remove(m)
    for ob in hidden:
        ob.hide_render = False
    G.kill(cutter)
    return path


def renders(outdir):
    R.setup(res=(800, 600))
    A.set_pose()
    lo, hi = R.scene_bounds()
    c = (lo + hi) / 2
    size = max(hi - lo)
    R.camera(c + Vector((0.95, -1.0, 0.75)) * size * 1.7, c, lens=50)
    R.shot(os.path.join(outdir, "iso.png"))
    R.camera(c + Vector((-1.0, 0.9, 0.65)) * size * 1.7, c, lens=50)
    R.shot(os.path.join(outdir, "iso_rear_left.png"))
    R.camera(c + Vector((1.0, -0.25, -0.35)) * size * 1.7, c + Vector((0, 0, -15)), lens=50)
    R.shot(os.path.join(outdir, "iso_low_cover_side.png"))
    # sections: wheel plane (nip, chute, funnel), stud plane (thumbwheel, leaf, stop), motor axis (encoder gap)
    nip = rig_pt(A3.WHEEL_XW, A3.pw(A3.WHEEL_R + 3.5, 4.0))
    R.marker_lentil("LENTIL_nip", tuple(nip), tuple(rig_dir((0, -math.sin(math.radians(4.0)), -math.cos(math.radians(4.0))))))
    R.marker_lentil("LENTIL_funnel", (A3.WHEEL_XW, 0.0, AXIS_H + FUNNEL_MOUTH_Z - 6.0), (0, 0.5, 0.87))
    cen = Vector((A3.WHEEL_XW, 50.0, 90.0))
    section(outdir, "section_nip_wheel_plane.png", 'x', A3.WHEEL_XW, tuple(cen + Vector((400, 0, 0))), tuple(cen), 200, keep_side="-")
    cen2 = Vector((A3.NIP_X, 25.0, 40.0))
    section(outdir, "section_stud_leaf_plane.png", 'x', A3.NIP_X, tuple(cen2 + Vector((400, 0, 0))), tuple(cen2), 80, keep_side="-")
    for n in ("LENTIL_nip", "LENTIL_funnel"):
        G.kill(bpy.data.objects[n])
    w = rig_pt(A3.WHEEL_XW, WC)
    cen3 = Vector((-40.0, w.y, w.z))
    section(outdir, "section_motor_encoder_axis.png", 'z', w.z, tuple(cen3 + Vector((0, 0, 400))), tuple(cen3), 140, keep_side="-")
    for g in GAP_TEST:
        A.set_pose(PIV_hood=eps_deg(g))
        section(outdir, "section_nip_gap_%g.png" % g, 'x', A3.WHEEL_XW, tuple(cen + Vector((400, 0, 0))), tuple(cen), 200, keep_side="-")
    A.set_pose()
    offs = {"PRT_rig_cover": (75, 0, 0), "PRT_flywheel": (42, 0, 0), "BUY_tape": (42, 0, 0), "PRT_backplate": (22, -20, -40),
            "PRT_nip_wheel": (36, -30, -45), "PRT_rig_frame": (-95, 0, 0), "BUY_motor": (-50, 0, 0), "BUY_motor_shaft": (-50, 0, 0),
            "BUY_magnet": (-62, 0, 0), "BUY_plink_encoder": (-108, 0, 0), "BUY_motorgo_axis": (-95, 0, -35)}
    R.exploded(outdir, offsets=offs, cam=tuple(c + Vector((1.0, -1.15, 0.75)) * size * 1.9))


if __name__ == "__main__":
    screws = build()
    nums = numbers()
    nums["cover_screws_launcher_pq"] = [list(map(lambda v: round(v, 1), c)) for c in screws]
    print("NUMBERS", json.dumps(nums))
    A.PARAMS["numbers"] = json.dumps(nums)
    with open(os.path.join(HERE, "checks.json"), "w") as f:
        json.dump(check_config(), f, indent=1)
    qty = E.export_stls(os.path.join(HERE, "stl"))
    A.write_manifest(os.path.join(HERE, "manifest.json"))
    with open(os.path.join(HERE, "renders", "numbers.json"), "w") as f:
        json.dump(nums, f, indent=1)
    for cn in [c.name for c in bpy.data.collections if c.name.startswith("TMP")]:
        for o in list(bpy.data.collections[cn].objects):
            G.kill(o)
    if "--render" in argv:
        renders(os.path.join(HERE, "renders"))
    if "--estimate" in argv:
        est = estimate(os.path.join(HERE, "stl"))
        print("ESTIMATE", json.dumps(est))
        with open(os.path.join(HERE, "print_estimate.json"), "w") as f:
            json.dump(est, f, indent=1)
    E.save_blend(os.path.join(HERE, "launch_rig.blend"))
    print("BUILD_DONE stls", qty)
