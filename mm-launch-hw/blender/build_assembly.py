"""M&M launcher turret: parametric Blender assembly (attempt 3).

Run headless (Blender 5.1):
    Blender -b --python build_assembly.py                      # build, save .blend, export STLs
    Blender -b --python build_assembly.py -- --render <dir>    # also render the view set

World frame: X right, Y forward (muzzle at pan 0), Z up, origin on the table under the
pan axis. Units: 1 Blender unit = 1 mm. Every printed part is built as a manifold solid
with the Manifold boolean solver. Collections: Printed, Purchased, Fasteners, Cables, Tools.

Launcher frame (used for every 2D launcher profile): p = world Y, q = world Z - T_Z at tilt 0,
origin on the tilt axis. The flywheel spins with its BOTTOM moving forward (+p), so the rear
half of the tape moves DOWN into the nip between the wheel and the hinged backplate below it.
psi = angle around the wheel centre measured from bottom dead centre toward the rear.
"""
import bpy, bmesh, math, os, sys, struct
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "reference")
STL_DIR = os.path.join(ROOT, "stl")
BLEND_PATH = os.path.join(HERE, "mm_launcher.blend")

# =====================================================================================
# PARAMETERS (mm, degrees)
# =====================================================================================
# --- detailing standard ---------------------------------------------------------------
EB = 1.0                   # edge break (bevel) on every printed part
CR = 6.0                   # standard small corner radius (BASE_CORNER_R is the one large radius)
# --- base -------------------------------------------------------------------------
BASE_HALF = 120.0          # base is 240 x 240
BASE_CORNER_R = 16.0
WALL = 3.0
FLOOR_T = 3.0              # removable floor plate z 0..3
BASE_H = 90.0              # deck top
DECK_T = 4.0
DECK_Z0 = BASE_H - DECK_T  # 86
DECK_HOLE_R = 20.3         # hub journal Ø40 in Ø40.6

# --- pan stage ----------------------------------------------------------------------
RING_R0, RING_R1, RING_H = 70.0, 82.0, 2.0      # bearing ring on turntable underside
TT_Z0 = BASE_H + RING_H                         # 92 turntable underside
TT_T = 10.0
TT_Z1 = TT_Z0 + TT_T                            # 102 turntable top
TT_R = 112.0
TT_GROOVE_W, TT_GROOVE_D = 14.0, 6.0
HUB_BORE_R = 14.0
HUB_R = 20.0
GEAR_M, GEAR_N = 1.5, 36
GEAR_Z0, GEAR_Z1 = 77.5, 85.0
GEAR_BACKLASH = 0.15
PINION_XY = (0.0, GEAR_M * GEAR_N)              # 1:1 pair, centre distance 54
SPINE_T = 4.0

# --- tilt axis and launcher ---------------------------------------------------------
T_Z = 222.0                 # tilt axis height
TILT_MIN, TILT_MAX = -3.0, 46.0     # printed hard stops (firmware clamps commands to 0..45)
W_P, W_Q = 37.0, -52.0      # wheel centre relative to the tilt axis (launcher frame)
X_MF = 0.0                  # motor front face plane (world X)
NAC_PLATE_T = 4.0           # nacelle front plate, sandwiched between motor face and body wall
BODY_WALL = 4.0
X_BODY_OUT = X_MF + NAC_PLATE_T         # 4   left wall outer face
X_BODY_IN = X_BODY_OUT + BODY_WALL      # 8   left wall inner face
X_COVER_IN = 31.5                       # cover / journal plate inner face
COVER_T = 4.0
X_COVER_OUT = X_COVER_IN + COVER_T      # 35.5
WHEEL_R = 35.0              # rim (tape land) radius before tape
WHEEL_FLANGE_R = 36.0
WHEEL_X0, WHEEL_X1 = 12.5, 29.5         # rim width 17 = 14 land + 2 x 1.5 flanges
WHEEL_XW = 0.5 * (WHEEL_X0 + WHEEL_X1)  # 21 wheel plane
HUB_X0 = 9.0                # wheel's -X face, 1 mm off the wall; hub on the shaft from here (x 9..21 = 12 mm)
WEB_X1 = WHEEL_X0 + 1.6     # web on the MOTOR side (x 9..14.1, full R36: it is also the -X flange), so the cup
                            # between hub and rim opens toward +X (the cover side) for the pinch-bolt L-key
FW_HUB_R = 13.5
FW_HUB_X1 = 25.0            # hub end (inside the cup)
FW_RIM_T = 3.5              # rim thickness under the tape land (inner radius 31.5)
SHAFT_LEN = 21.0
CH_X0 = WHEEL_XW - 8.0      # chute / fan left wall (x 13..31.5)
DRUM_R = 20.0               # feed drum about the tilt axis (stays under the outlet spout at every tilt)
FAN_A0, FAN_A1 = -27.0, 75.0            # fan opening, deg from launcher-up toward the muzzle
OUTLET_R = 8.0
COL_MARGIN = 1.0            # clearance kept around the Ø16 drop column at tilt 0..45
WC_R = 38.5                 # wheel cavity radius (2.5 to the flange)
FIN_R0, FIN_R1 = 37.5, 39.1 # chute front-wall fin (1.5 from the flange, 1.6 thick)
LIP_PSI = 100.0             # the fin ends here: candy leaves the chute onto the descending rear tape
GUARD_WALL = 3.0
# backplate (the brief's "hood", here UNDER the wheel), hinged at its top end
HOOD_GAP = 6.5              # as-modelled operating gap, bare rim to plate (concentric here): 6.0 with 0.5 mm tape = 1 mm squeeze on a 7 mm M&M
HOOD_GAP_MIN, HOOD_GAP_MAX = 5.5, 12.5  # backplate bay (swing) range at BDC; thumbwheel adjusts 5.5..10, the rest is jam relief
HOOD_T = 6.0
PSI_C, PSI_TOP, BP_PSI0 = 78.0, 112.0, -3.0   # concentric to PSI_C, funnel to PSI_TOP, plate ends just past BDC
G_IN = 21.0                 # funnel width at the top of the plate
HINGE_OFF, HINGE_BOSS_R = 2.0, 4.3
JACK_PSI = 45.0             # nip stud leaves the plate's back face here (line nearly tangent to the hinge arc)
CLAMP_PSI = 30.0            # side clamp screws (through arc slots) lock the plate here
MUZZLE_FRONT = W_P + 62.0   # 99
MUZZLE_ROOF = W_Q - WHEEL_R + 5.0  # -82 muzzle roof underside (5 above the tape bottom)
ROOF_P0 = W_P + 30.0
MUZZLE_FLARE = 4.0
MOTOR_D, MOTOR_L = 35.9, 74.0
REAR_ACCESS_D = 8.0         # rear end-cap access hole
REAR_SHAFT_RECESS = 0.5     # shaft end below the rear face (0..1)
JIG_SPIGOT_D, JIG_SPIGOT_L = 7.8, 1.0   # magnet jig locates on the motor's Ø8 rear access hole (concentric with the bearing)
JIG_PLUG_R = 17.8           # jig plug relieved 0.35 radial in the Ø36.3 bore so the spigot alone centres it
MAGNET_D, MAGNET_T = 6.0, 2.5
ENC_GAP = 1.0               # magnet face to MT6701 top
PLINK_IC_TOP = 3.25         # from STL: IC top above PCB back
NAC_RW, NAC_RT = 26.5, 17.0 # nacelle capsule radii around the motor axis and the tilt axis
BORE_CLR = 0.2              # motor can in the nacelle bore
# --- yoke -------------------------------------------------------------------------
ARM_T = 14.0
ARM_L_X = (-102.0, -88.0)
ARM_R_X = (40.0, 54.0)
ARM_HALF_TOP, ARM_HALF_BOT = 24.0, 32.0
JOURNAL_R = 15.0
BORE_R = 15.2
COLLAR_R = 17.0
CAP_H = 30.0                # feeder plate underside 30 above the tilt axis; Ø22 spout reaches down to +23
TUBE_BORE_R = 10.0
PLATE_Z0 = T_Z + CAP_H      # feeder plate underside
PLATE_T = 6.0
PLATE_FRONT_Y = 13.0        # feeder plate front edge over the launcher
SPOUT_R, SPOUT_Z0 = 11.0, T_Z + 23.0
STOP_R0, STOP_R1 = 19.0, 23.5           # hard-stop lugs (journal plate vs right arm)
STOP_LUG_A, STOP_LUG_HW = -90.0, 8.0    # launcher lug centre / half width (deg from +p)
# --- feeder / hopper ---------------------------------------------------------------
FEED_XY = (WHEEL_XW, -45.0)  # feeder axis; pockets pass over the outlet at (XW, 0)
FEED_RP = 45.0
DISC_R = 56.0
DISC_T = 8.0
POCKET_D = 15.5
N_POCKETS = 6
HOP_BORE_R = 58.0
HOP_WALL = 2.4
HOP_BARREL_H = 18.0
HOP_FLARE_H = 22.0
HOP_FLARE_ANG = 60.0
BAFFLE_RAMP = 30.0          # baffle leading edges ramp at 30 deg (both ends: the index alternates +30 / -30)
# Feeder index: PARK = 0 deg (servo centre) puts SOLID disc over the outlet (pockets straddle it at +-30 deg).
# Fire = move to +30 (or -30), the pocket that was filling at 60 (or 120) deg is now over the outlet and drops; return
# to 0. Alternate the side each shot. Exactly one pocket crosses the outlet per fire command.
OUTLET_ANG = 90.0           # outlet direction from the feeder axis (deg, world XY)
POCKET_PHASE = 30.0         # pockets at OUTLET_ANG + 30 + 60k at park
FEED_FIRE = 30.0            # fire stroke (deg), alternating sign


def pocket_angles(rot):
    return [OUTLET_ANG + POCKET_PHASE + 360.0 * k / N_POCKETS + rot for k in range(N_POCKETS)]
# --- servos (Hiwonder HTS-35H class) ------------------------------------------------
SERVO_L, SERVO_W, SERVO_H = 40.0, 20.14, 40.0
SERVO_SPLINE_OFF = 10.0     # spline axis 10 mm from the body centre along its length
SPLINE_H = 3.9
HORN_D, HORN_T = 20.0, 2.5
HORN_BC, HORN_HOLE = 14.0, 2.2
HORN_RECESS = 1.0
ADAPTER_R, ADAPTER_T = 13.0, 4.0
HEX_AF = 12.0
HEX_KEY_L = 8.0
HEX_CLR = 0.15
KEY_HOLE_D = 6.5            # through the hex key: drive the horn centre screw after the horn is fixed
NUT_AF = 5.7                # M3 nut trap across flats
SERVO_TOP_W = -7.7          # servo top face below the mount face (pocket frame)
CLAMP_BOSS_U = -25.0        # clamp screw bosses on the long walls
# --- electronics placement ---------------------------------------------------------
MG_X0, MG_Z0 = -30.0, 16.5  # MotorGo STEP-origin hole in world X / Z
MG_STANDOFF = 12.5          # partition face to PCB component face
MG_PCB_T = 1.77             # PCB top (pads) in the STEP frame, measured from mg_axis.stl
MG_WALL_Y = -87.0           # partition inner face
USB_STEP = (57.6, -14.0, 7.97)
NICHE_DEPTH = 30.0
BAY_CLR = 2.0               # battery to bay walls, each side
BATT = (10.0, 125.0, -115.0, -39.0, 4.6, 74.6)       # x0 x1 y0 y1 z0 z1 (115 x 76 x 70)
ADAPTER = (24.0, 110.6, -106.5, -47.5, 62.6, 86.0)
ADAPTER_SCREW_L = 25.0      # countersunk from the deck top; tip ends 2.4 above the battery face
ADAPTER_CB = 5.5            # nut counterbore depth in the adapter's battery-side face
BUCK_C = (-76.0, -19.0)
CTRL = (73.0, 115.0, 20.0, 78.0)                      # PCB footprint x0 x1 y0 y1
CTRL_BOSS_H = 5.0

# PLA colours for renders (two coordinated colours) + purchased neutrals
COL_A = (0.80, 0.78, 0.74, 1)   # warm grey PLA: structure
COL_B = (0.76, 0.33, 0.17, 1)   # terracotta PLA: moving launcher, adapters, accents
COL = dict(metal=(0.55, 0.56, 0.58, 1), dark=(0.12, 0.12, 0.13, 1), pcb=(0.10, 0.22, 0.14, 1),
           white_pcb=(0.90, 0.90, 0.88, 1), dewalt=(0.95, 0.72, 0.10, 1), black=(0.06, 0.06, 0.06, 1),
           motor=(0.30, 0.42, 0.30, 1), magnet=(0.45, 0.45, 0.50, 1), cable_red=(0.70, 0.12, 0.10, 1),
           cable_blk=(0.08, 0.08, 0.08, 1), cable_yel=(0.85, 0.70, 0.10, 1), cable_wht=(0.85, 0.85, 0.85, 1),
           screw=(0.35, 0.35, 0.37, 1))

# =====================================================================================
# GEOMETRY LIBRARY
# =====================================================================================
TMP = None


def _scene_setup():
    global TMP
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = 'MILLIMETERS'
    TMP = bpy.data.collections.new("TMP")
    sc.collection.children.link(TMP)


def _map(u, v, w, axis):
    if axis == 'Z':
        return (u, v, w)
    if axis == 'X':
        return (w, u, v)
    if axis == 'Y':
        return (u, w, v)
    raise ValueError(axis)


def tmp():
    global TMP
    try:
        ok = TMP is not None and TMP.name in bpy.data.collections
    except ReferenceError:
        ok = False
    if not ok:
        TMP = bpy.data.collections.new("TMP")
        bpy.context.scene.collection.children.link(TMP)
    return TMP


def _obj(name, bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    tmp().objects.link(ob)
    return ob


def loft(name, poly0, poly1, w0, w1, axis='Z'):
    """Closed solid between two same-count 2D rings at w0 and w1."""
    bm = bmesh.new()
    vb = [bm.verts.new(_map(p[0], p[1], w0, axis)) for p in poly0]
    vt = [bm.verts.new(_map(p[0], p[1], w1, axis)) for p in poly1]
    n = len(vb)
    bm.faces.new(vb[::-1])
    bm.faces.new(vt)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    return _obj(name, bm)


def prism(name, poly, w0, w1, axis='Z'):
    return loft(name, poly, poly, w0, w1, axis)


def nseg(r):
    return int(max(16, min(128, round(r * 2.4))))


def circle(c, r, n=None, a0=0.0):
    n = n or nseg(r)
    return [(c[0] + r * math.cos(a0 + 2 * math.pi * i / n), c[1] + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def cyl(name, c, r, w0, w1, axis='Z', n=None, a0=0.0):
    return prism(name, circle(c, r, n, a0), w0, w1, axis)


def cone(name, c, r0, r1, w0, w1, axis='Z', n=None):
    n = n or nseg(max(r0, r1))
    return loft(name, circle(c, r0, n), circle(c, r1, n), w0, w1, axis)


def hexagon(c, af, a0=0.0):
    r = af / 2 / math.cos(math.pi / 6)
    return circle(c, r, 6, a0)


def box(name, x0, x1, y0, y1, z0, z1):
    return prism(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, 'Z')


def arc(c, r, a0, a1, n=None):
    n = n or max(4, int(abs(a1 - a0) / (2 * math.pi) * nseg(r)))
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def rrect(x0, x1, y0, y1, r, n=6):
    r = min(r, (x1 - x0) / 2 - 1e-3, (y1 - y0) / 2 - 1e-3)
    pts = []
    for (cx, cy, a) in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            t = math.radians(a + 90 * i / n)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def hull2d(pts):
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 1e-9:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 1e-9:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def hull_circles(circs, n=72):
    pts = []
    for (c, r) in circs:
        pts += circle(c, r, max(12, int(n * r / 40) + 12)) if r > 0 else [c]
    return hull2d(pts)


def revolve(name, prof, center=(0, 0, 0), n=96, a0=0.0, a1=None):
    """Revolve a closed (r, z) profile about a Z axis through center. Partial if a1 given."""
    bm = bmesh.new()
    full = a1 is None
    steps = n if full else max(2, int(n * abs(a1 - a0) / (2 * math.pi)))
    rings = []
    for i in range(steps if full else steps + 1):
        t = a0 + (2 * math.pi * i / n if full else (a1 - a0) * i / steps)
        rings.append([bm.verts.new((center[0] + r * math.cos(t), center[1] + r * math.sin(t), center[2] + z)) for r, z in prof])
    m = len(prof)
    nr = len(rings)
    for i in range(nr if full else nr - 1):
        A, B = rings[i], rings[(i + 1) % nr]
        for k in range(m):
            kk = (k + 1) % m
            bm.faces.new((A[k], A[kk], B[kk], B[k]))
    if not full:
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1][::-1])
    return _obj(name, bm)


def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    ob.modifiers.clear()
    old = ob.data
    ob.data = me
    bpy.data.meshes.remove(old)
    return ob


def _kill(ob):
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me and me.users == 0:
        bpy.data.meshes.remove(me)


def csg(base, add=(), sub=(), inter=()):
    """Union `add`, subtract `sub`, intersect `inter` (Manifold solver), apply, delete tools."""
    tools = []
    for op, lst in (('UNION', add), ('DIFFERENCE', sub), ('INTERSECT', inter)):
        for t in lst:
            if t is None:
                continue
            m = base.modifiers.new("b", 'BOOLEAN')
            m.operation = op
            m.solver = 'MANIFOLD'
            m.object = t
            tools.append(t)
    apply_mods(base)
    for t in tools:
        _kill(t)
    return base


def bevel(ob, w, seg=1, angle=40.0):
    m = ob.modifiers.new("bev", 'BEVEL')
    m.width = w
    m.segments = seg
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.use_clamp_overlap = True
    m.harden_normals = False
    return apply_mods(ob)


def xform(ob, M):
    ob.data.transform(M)
    if M.to_3x3().determinant() < 0:      # mirrored frame: keep normals pointing out
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
    ob.data.update()
    return ob


def frame(origin, u, v, w):
    M = Matrix.Identity(4)
    for i in range(3):
        M[i][0], M[i][1], M[i][2], M[i][3] = u[i], v[i], w[i], origin[i]
    return M


def join(name, obs):
    """Join disjoint/overlapping shells as one object without booleans (purchased placeholders only)."""
    bm = bmesh.new()
    for o in obs:
        bm.from_mesh(o.data)
    for o in obs:
        _kill(o)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    tmp().objects.link(ob)
    return ob


def gear_poly(m, z, c=(0, 0), backlash=GEAR_BACKLASH, phase=0.0, n_inv=7):
    rp = m * z / 2
    ra = rp + m
    rf = rp - 1.25 * m
    alpha = math.radians(20)
    rb = rp * math.cos(alpha)
    inv = lambda a: math.tan(a) - a
    half_p = math.pi / (2 * z) - backlash / (2 * rp)
    pts = []
    r_start = max(rb, rf)
    for k in range(z):
        th = phase + 2 * math.pi * k / z
        flank = []
        for i in range(n_inv + 1):
            r = r_start + (ra - r_start) * i / n_inv
            a = math.acos(min(1.0, rb / r))
            flank.append((r, half_p + inv(alpha) - inv(a)))
        a_root = flank[0][1]
        pts.append((rf, th - a_root - 0.25 * (2 * math.pi / z - 2 * a_root)))
        if rf < r_start:
            pts.append((rf, th - a_root))
        for r, a in flank:
            pts.append((r, th - a))
        for r, a in reversed(flank):
            pts.append((r, th + a))
        if rf < r_start:
            pts.append((rf, th + a_root))
        pts.append((rf, th + a_root + 0.25 * (2 * math.pi / z - 2 * a_root)))
    return [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for r, a in pts]


def teardrop_x(c, r):
    """Teardrop cross-section (in a plane) with the point toward +v; used for horizontal bosses/holes."""
    pts = circle(c, r, 24, 0)
    pts = [p for p in pts if p[1] - c[1] <= r * math.sin(math.radians(45)) + 1e-6]
    pts.append((c[0], c[1] + r * math.sqrt(2)))
    return hull2d(pts)


# =====================================================================================


# =====================================================================================
# 2D HELPERS
# =====================================================================================
def lin(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def pw(r, psi):
    """launcher (p, q) at radius r around the wheel centre, psi deg from BDC toward the rear"""
    a = math.radians(psi)
    return (W_P - r * math.sin(a), W_Q - r * math.cos(a))


def pt(r, a):
    """launcher (p, q) at radius r around the tilt axis, a deg from launcher-up toward the muzzle"""
    a = math.radians(a)
    return (r * math.sin(a), r * math.cos(a))


def psi_of(p):
    return math.degrees(math.atan2(-(p[0] - W_P), -(p[1] - W_Q)))


def rot2(p, ang, c=(0.0, 0.0)):
    x, y = p[0] - c[0], p[1] - c[1]
    ca, sa = math.cos(ang), math.sin(ang)
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def pip(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def poly_dist(p, poly):
    return min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def vadd(a, b, k=1.0):
    return (a[0] + k * b[0], a[1] + k * b[1])


def tangent_point(E, C, r, side):
    dx, dy = C[0] - E[0], C[1] - E[1]
    d = math.hypot(dx, dy)
    ang = math.atan2(dy, dx) + side * math.asin(r / d)
    L = math.sqrt(d * d - r * r)
    return (E[0] + L * math.cos(ang), E[1] + L * math.sin(ang))


def spread_pick(cands, n, seeds=()):
    """greedy farthest-point pick of n candidates"""
    picked = list(seeds)
    out = []
    pool = list(cands)
    while len(out) < n and pool:
        if not picked:
            best = pool[0]
        else:
            best = max(pool, key=lambda c: min(math.hypot(c[0] - q[0], c[1] - q[1]) for q in picked))
        out.append(best)
        picked.append(best)
        pool.remove(best)
    return out


# =====================================================================================
# LAUNCHER GEOMETRY (computed once, launcher frame)
# =====================================================================================
_SN = math.hypot(W_P, W_Q)
S_DIR = (W_P / _SN, W_Q / _SN)          # unit, tilt axis -> wheel axis (nacelle spine)
N_DIR = (-S_DIR[1], S_DIR[0])           # perpendicular, front-up side
MOTOR_ROT = math.degrees(math.atan2(-S_DIR[1], -S_DIR[0]))   # lead block points at the tilt axis
WC = (W_P, W_Q)


def gap_at(psi):
    if psi <= PSI_C:
        return HOOD_GAP
    s = min(1.0, (psi - PSI_C) / (PSI_TOP - PSI_C))
    return HOOD_GAP + (G_IN - HOOD_GAP) * s * s


HINGE = pw(WHEEL_R + G_IN + HOOD_T + HINGE_OFF, PSI_TOP)
FLOOR_Q = W_Q - WHEEL_R - HOOD_GAP      # nominal plate surface at BDC (-96)


def bp_band(eps=0.0, grow=0.0, n=56):
    """backplate band (launcher frame) rotated by eps (rad, + closes the gap) about the hinge"""
    a0 = BP_PSI0 - math.degrees(grow / (WHEEL_R + HOOD_GAP))
    a1 = PSI_TOP + math.degrees(grow / (WHEEL_R + G_IN))
    inner = [pw(WHEEL_R + gap_at(ps) - grow, ps) for ps in lin(a1, a0, n)]
    outer = [pw(WHEEL_R + gap_at(ps) + HOOD_T + grow, ps) for ps in lin(a0, a1, n)]
    return [rot2(p, eps, HINGE) for p in inner + outer]


def gap_bdc(eps):
    pts = [rot2(pw(WHEEL_R + HOOD_GAP, ps), eps, HINGE) for ps in lin(-2, 2, 9)]
    return min(math.hypot(p[0] - W_P, p[1] - W_Q) for p in pts) - WHEEL_R


def _solve_eps(target):
    """gap at BDC falls monotonically as eps grows"""
    lo, hi = -0.3, 0.3
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if gap_bdc(m) > target:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


EPS_CLOSE = _solve_eps(HOOD_GAP_MIN)
EPS_OPEN = _solve_eps(HOOD_GAP_MAX)
BAY_EPS = lin(EPS_OPEN, EPS_CLOSE, 9)
BAY_POLYS = [bp_band(e, 0.5) for e in BAY_EPS]
BAY_BOSS = circle(HINGE, HINGE_BOSS_R + 0.5, 24)
CLAMP_PT = pw(WHEEL_R + HOOD_GAP + HOOD_T / 2, CLAMP_PSI)
JACK_PT = pw(WHEEL_R + HOOD_GAP + HOOD_T, JACK_PSI)
_jv = (JACK_PT[0] - HINGE[0], JACK_PT[1] - HINGE[1])
_jl = math.hypot(*_jv)
JACK_DIR = (-_jv[1] / _jl, _jv[0] / _jl)     # closing direction at the jack point
JACK_X = (WHEEL_XW - 6.0, WHEEL_XW + 6.0)


def clamp_slot_ends():
    return [rot2(CLAMP_PT, e, HINGE) for e in (EPS_OPEN - 0.004, EPS_CLOSE + 0.004)]


# feed chute ----------------------------------------------------------------------------
E_FRONT = (OUTLET_R + COL_MARGIN + 0.5, -math.sqrt(DRUM_R ** 2 - (OUTLET_R + COL_MARGIN + 0.5) ** 2))
FIN_TAN = tangent_point(E_FRONT, WC, FIN_R1, -1)
PSI_TAN = psi_of(FIN_TAN)
P1_REAR = pt(DRUM_R, FAN_A0)
# Rear wall ends in a 1.6 mm tongue that laps 1.2 mm inside the backplate's top end (shingled: no crack faces the flow)
TONGUE_PSI0, TONGUE_PSI1 = PSI_TOP - 6.0, PSI_TOP + 4.0
TONGUE_T = 1.6


def _tongue_in():
    """bay grow (0.5) + the deepest intrusion of the swinging plate surface under the tongue (envelope over every hinge
    angle, compared at equal psi) + 0.3 margin"""
    worst = 0.0
    src = [(ps, WHEEL_R + gap_at(ps)) for ps in lin(80.0, PSI_TOP, 160)]
    for e in lin(EPS_OPEN, EPS_CLOSE, 15):
        moved = []
        for ps, r0 in src:
            q = rot2(pw(r0, ps), e, HINGE)
            moved.append((psi_of(q), math.hypot(q[0] - W_P, q[1] - W_Q)))
        for k in range(len(moved) - 1):
            (pa, ra), (pb, rb) = moved[k], moved[k + 1]
            if TONGUE_PSI0 - 1.0 <= pa <= PSI_TOP and pb != pa:
                worst = max(worst, WHEEL_R + gap_at(pa) - ra)
    return 0.5 + worst + 0.3


TONGUE_IN = _tongue_in()
REAR_WALL_ANG = 81.0        # launcher frame; 36 deg in world at tilt 45


def r_tongue(ps):
    return WHEEL_R + gap_at(ps) - TONGUE_IN - TONGUE_T


def _isect(P, a_deg, Q, b_deg):
    d1 = (math.cos(math.radians(a_deg)), math.sin(math.radians(a_deg)))
    d2 = (math.cos(math.radians(b_deg)), math.sin(math.radians(b_deg)))
    den = d1[0] * (-d2[1]) - d1[1] * (-d2[0])
    rx, ry = Q[0] - P[0], Q[1] - P[1]
    t = (rx * (-d2[1]) - ry * (-d2[0])) / den
    return (P[0] + t * d1[0], P[1] + t * d1[1])


J_REAR = pw(r_tongue(TONGUE_PSI1), TONGUE_PSI1)
P1_IN = pt(DRUM_R - 2.0, FAN_A0)
K_REAR = _isect(J_REAR, 180.0 - REAR_WALL_ANG, P1_IN, -104.0)
A_CH = 45.0 + math.degrees(math.asin((OUTLET_R + COL_MARGIN) / DRUM_R))   # drum arc kept from here round the back
# keep the tight (1.5 mm) wheel cavity up the rear until the chute front wall is >= 1.6 mm thick against the normal cavity
FIN_PSI_END = PSI_TAN + math.degrees(math.atan(math.sqrt((WC_R + 1.6) ** 2 - FIN_R1 ** 2) / FIN_R1)) + 1.0


def chute_poly():
    pts = [pt(30.0, a) for a in lin(FAN_A1, FAN_A0, 14)]
    pts += [P1_REAR, P1_IN, K_REAR]
    pts += [pw(r_tongue(ps), ps) for ps in lin(TONGUE_PSI1, TONGUE_PSI0, 8)]
    # square tongue tip: step out perpendicular to the tongue face (not radially) so the tip has no acute corner
    f0, f1 = pw(r_tongue(TONGUE_PSI0), TONGUE_PSI0), pw(r_tongue(TONGUE_PSI0 + 0.5), TONGUE_PSI0 + 0.5)
    tx, ty = f1[0] - f0[0], f1[1] - f0[1]
    tl = math.hypot(tx, ty)
    nx, ny = ty / tl, -tx / tl
    if (f0[0] + nx - W_P) ** 2 + (f0[1] + ny - W_Q) ** 2 < (f0[0] - W_P) ** 2 + (f0[1] - W_Q) ** 2:
        nx, ny = -nx, -ny
    pts += [(f0[0] + nx * (TONGUE_T + TONGUE_IN + 0.8), f0[1] + ny * (TONGUE_T + TONGUE_IN + 0.8)), pw(WHEEL_R + 8.0, 104.0)]
    pts += [pw(FIN_R1, ps) for ps in lin(LIP_PSI, PSI_TAN, 8)]
    pts += [E_FRONT, pt(DRUM_R, FAN_A1)]
    return pts


def wheel_cavity_poly():
    pts = []
    for i in range(180):
        ps = -180 + 2 * i
        pts.append(pw(FIN_R0 if LIP_PSI - 0.5 <= ps <= FIN_PSI_END else WC_R, ps))
    return pts


def nip_poly():
    pts = [WC] + [pw(WHEEL_R + gap_at(ps) + 0.6, ps) for ps in lin(-8.0, TONGUE_PSI0 - 2.0, 60)]
    return pts


def _bay_front():
    return max(p[0] for poly in BAY_POLYS for p in poly if p[1] > FLOOR_Q - HOOD_T - 8)


FLOOR_FIX = FLOOR_Q - (HOOD_GAP_MAX - HOOD_GAP) - 0.6     # fixed exit floor, below the plate at max open
FIX_P0 = _bay_front() + 1.5


def muzzle_poly():
    f, r, mf = FLOOR_FIX, MUZZLE_ROOF, MUZZLE_FRONT
    return [(W_P, f), (mf - MUZZLE_FLARE, f), (mf + 1, f - MUZZLE_FLARE - 1), (mf + 1, r + MUZZLE_FLARE + 1),
            (mf - MUZZLE_FLARE, r), (ROOF_P0, r), (ROOF_P0 - 12, r + 12), (W_P, r + 12)]


def guard_profile(grow=0.0):
    g = grow
    circs = [((0, 0), g)]
    for i in range(72):
        a = A_CH + (360.0 - A_CH) * i / 71
        circs.append((pt(DRUM_R, a), g))
    circs += [(K_REAR, 3.5 + g), (J_REAR, 3.5 + g), (WC, WC_R + GUARD_WALL + g), (HINGE, HINGE_BOSS_R + 0.5 + 3.5 + g)]
    for poly in BAY_POLYS:
        circs += [(p, 3.5 + g) for p in poly[::3]]
    circs += [((MUZZLE_FRONT - CR, MUZZLE_ROOF + 7 - CR), CR + g), ((MUZZLE_FRONT - CR, FLOOR_FIX - 7 + CR), CR + g)]
    return hull_circles(circs, 64)


PROFILE = guard_profile()
LAUNCHER_CAVITIES = [chute_poly(), wheel_cavity_poly(), nip_poly(), muzzle_poly()] + BAY_POLYS + [BAY_BOSS]


def _top_line_dir():
    """direction of the guard's top chamfer (drum top -> tangent on the wheel wrap)"""
    tp = tangent_point(pt(DRUM_R, 0.0), WC, WC_R + GUARD_WALL, 1)
    d = (tp[0], tp[1] - DRUM_R)
    L = math.hypot(*d)
    return (d[0] / L, d[1] / L)


TOP_DIR = _top_line_dir()
TOP_N = (-TOP_DIR[1], TOP_DIR[0])        # upward normal of the top chamfer


JP_DIAG = (-math.sqrt(0.5), -math.sqrt(0.5))


def jp_union(r, off):
    """journal plate region before clipping by PROFILE, grown by `off` (lap steps): the arc of radius r+off from straight
    below the tilt axis round the front, leaving tangentially to meet the top chamfer at 90 deg; below the arc the parting
    line runs down-back at 45 deg so it meets the guard's lower-rear edge almost square (no knife-edge wedges)."""
    R = r + off
    # diagonal through (0, -r) offset by `off` along its outward normal; start the arc where it meets the grown circle
    a = off * math.sqrt(0.5)
    b = math.sqrt(2.0) * r
    c = a * a + (r + a) ** 2 - R * R
    t = (-b + math.sqrt(b * b - 4 * c)) / 2
    s0 = (a - math.sqrt(0.5) * t, -r - a - math.sqrt(0.5) * t)
    a_start = math.atan2(s0[1], s0[0])
    a_end = math.atan2(-TOP_N[0], TOP_N[1])                 # arc tangent == top-chamfer normal here
    arc = [(R * math.cos(a_start + (a_end - a_start) * i / 64), R * math.sin(a_start + (a_end - a_start) * i / 64)) for i in range(65)]
    e = arc[-1]
    far_top = (e[0] + 120 * TOP_N[0], e[1] + 120 * TOP_N[1])
    far_bot = (s0[0] + 160 * JP_DIAG[0], s0[1] + 160 * JP_DIAG[1])
    return [far_bot] + arc + [far_top, (-300.0, 300.0), (-300.0, -300.0)]


JP_R = 24.5
JP_REGION = jp_union(JP_R, 0.0)


def _surface_along(P, d, poly, step=0.25):
    """walk from P along d until leaving poly"""
    q = P
    for _ in range(800):
        nq = vadd(q, d, step)
        if not pip(nq, poly):
            return q
        q = nq
    return q


JACK_SURF = _surface_along(JACK_PT, (-JACK_DIR[0], -JACK_DIR[1]), PROFILE)

# ---------------------------------------------------------------------------------------------------------------------
# COMPLIANT NIP (attempt 3). The backplate is no longer locked. One M3 hex-head STUD sits head-down in a hex pocket on the
# plate's back face (at JACK_PT, on the wheel plane) and passes out through a slot in the guard. A printed THUMBWHEEL with
# a captive nut runs on the stud and rests on a flat SEAT LAND on the guard: it is a MINIMUM-GAP STOP (the plate cannot
# close past it). A PLA LEAF SPRING inside the terracotta NIP COVER presses the thumbwheel onto the seat with ~9 N, so
# the plate is held at the set gap with that preload and can open (thick candy) by lifting the wheel against the leaf.
# Local nip frame: X = world x, U = outward along the stud (-JACK_DIR), V = along the guard toward the hinge.
# ---------------------------------------------------------------------------------------------------------------------
NIP_X = 19.5                   # stud 1.5 mm off the wheel plane (thumbwheel clears the cover's end walls)
SEAT_H = 2.2                   # seat land proud of the guard surface at the stud (the guard bulges 1.7 at v 10..14)
JD = JACK_DIR
NIP_U = (-JD[0], -JD[1])
NIP_V = (-JD[1], JD[0])
NIP_E = vadd(JACK_SURF, NIP_U, SEAT_H)          # seat plane origin (launcher p, q); u = 0 is the seat face
NIP_SET = (5.5, 10.0)          # thumbwheel adjustment range, bare gap at BDC (the bay still allows 12.5 as jam relief)
STUD_HOLE_R = 3.6              # the hex head (6.35 across corners) is pushed in from outside through the guard
STUD_HEAD_AF, STUD_HEAD_K = 5.5, 2.0            # DIN 933 M3 hex head
STUD_POCKET_D = 2.2
STUD_L = 20.0                  # M3 x 20 hex head (tip shows through a Ø8 window in the cover shell: gap indicator)
TW_R, TW_T = 8.5, 5.0          # thumbwheel Ø17 x 5
TW_NUT_U = (0.8, 3.2)          # captive nut inside the thumbwheel
LAND_V = (-12.0, 46.0)         # flat land on the guard (seat + cover screw rail), u from -10 to 0
LEAF_T, LEAF_PRE, PAD_H = 2.0, 2.3, 2.5         # leaf thickness, assembly preload deflection, contact pad height
LEAF_U0 = TW_T + PAD_H - LEAF_PRE               # free-state leaf inner face (5.5)
LEAF_TRAVEL = 2.5              # extra lift before the leaf bottoms on the shell (over-travel stop)
SHELL_U0 = LEAF_U0 + LEAF_T + LEAF_PRE + LEAF_TRAVEL   # 12.0 shell inner face
SHELL_T = 2.0
NIP_V_ROOT = 34.0              # leaf root (cantilever length to the pads = 34)
NIP_V_TIP = -8.0
NIP_V_SKIRT = (LAND_V[0], LAND_V[0] + 2.0)
NIP_V_END = 46.0
NIP_XC = (X_BODY_OUT, X_COVER_IN)          # same width as the land: the cover's +X face is the body/cover parting plane
NIP_END_T = 2.0
NIP_SLIT = 0.8
NIP_SCREW_V = 39.0
NIP_SCREW_X = (10.0, 26.0)


def nip_pq(u, v):
    return (NIP_E[0] + u * NIP_U[0] + v * NIP_V[0], NIP_E[1] + u * NIP_U[1] + v * NIP_V[1])


def nip_frame():
    """local (x, u, v) -> world"""
    o = (0.0, NIP_E[0], T_Z + NIP_E[1])
    return frame(o, (1, 0, 0), (0, NIP_U[0], NIP_U[1]), (0, NIP_V[0], NIP_V[1]))


def stud_line(eps):
    """stud base (plate back face) and outward unit direction at backplate rotation eps"""
    p0 = rot2(JACK_PT, eps, HINGE)
    d = rot2(NIP_U, eps)
    return p0, d


def stud_d(eps):
    """distance along the stud from the plate's back face to the seat plane"""
    p0, d = stud_line(eps)
    return (NIP_E[0] - p0[0]) * d[0] + (NIP_E[1] - p0[1]) * d[1]


def leaf_spring():
    """cantilever leaf numbers (PLA E ~3.5 GPa)"""
    E = 3500.0
    b = (NIP_XC[1] - NIP_END_T - NIP_SLIT) - (NIP_XC[0] + NIP_END_T + NIP_SLIT)
    L = NIP_V_ROOT
    I = b * LEAF_T ** 3 / 12.0
    k = 3 * E * I / L ** 3
    sig = lambda F: 6 * F * L / (b * LEAF_T ** 2)
    F0 = k * LEAF_PRE
    return {"width_mm": round(b, 1), "length_mm": L, "thickness_mm": LEAF_T, "rate_N_per_mm": round(k, 2),
            "preload_N": round(F0, 1), "root_stress_preload_MPa": round(sig(F0), 1),
            "force_at_stop_N": round(k * (LEAF_PRE + LEAF_TRAVEL), 1), "root_stress_at_stop_MPa": round(sig(k * (LEAF_PRE + LEAF_TRAVEL)), 1)}


def pick_screws():
    """journal-plate and cover screw positions: in solid body behind them, clear of every cavity"""
    lug = [pt(r, 90 - a) for r in (STOP_R0 - 2, STOP_R1 + 2) for a in (STOP_LUG_A - STOP_LUG_HW - 6, STOP_LUG_A + STOP_LUG_HW + 6)]
    slot = clamp_slot_ends()
    jack_seg = (JACK_PT, vadd(JACK_SURF, JACK_DIR, -6))
    xs = [p[0] for p in PROFILE]
    ys = [p[1] for p in PROFILE]
    jp_c, cv_c = [], []
    for i in range(int(min(xs)), int(max(xs)) + 1):
        for j in range(int(min(ys)), int(max(ys)) + 1):
            c = (float(i), float(j))
            if not pip(c, PROFILE) or poly_dist(c, PROFILE) < 5.2:
                continue
            if any(pip(c, cav) or poly_dist(c, cav) < 3.4 for cav in LAUNCHER_CAVITIES):
                continue
            if seg_dist(c, *slot) < 6.0 or seg_dist(c, *jack_seg) < 6.0 or math.hypot(c[0] - HINGE[0], c[1] - HINGE[1]) < 8:
                continue
            in_jp = pip(c, JP_REGION)
            dj = poly_dist(c, JP_REGION)
            if in_jp and dj > 5.2 and math.hypot(*c) > COLLAR_R + 3.6:
                lugpoly = [lug[0], lug[1], lug[3], lug[2]]
                if not pip(c, lugpoly):
                    jp_c.append(c)
            elif (not in_jp) and dj > 5.5 and c[0] >= 34.0:
                cv_c.append(c)
    jp = spread_pick(jp_c, 3, seeds=[(0.0, 0.0)])
    cv = spread_pick(cv_c, 4, seeds=[(0.0, 0.0)])
    return jp, cv


JP_SCREWS, COVER_SCREWS = pick_screws()
NAC_SCREWS = [vadd(WC, S_DIR, -33.0), vadd(WC, S_DIR, 22.0)]
MOTOR_SCREWS = [vadd(WC, (math.cos(math.radians(MOTOR_ROT + 45 + 90 * k)), math.sin(math.radians(MOTOR_ROT + 45 + 90 * k))), 12.5) for k in range(4)]
ENC_SCREWS = [vadd(WC, N_DIR, 21.5), vadd(WC, N_DIR, -21.5)]
PCB_BACK_X = -MOTOR_L + REAR_SHAFT_RECESS - MAGNET_T - ENC_GAP - PLINK_IC_TOP   # -80.25
NAC_X0 = PCB_BACK_X


# =====================================================================================
# REGISTRY
# =====================================================================================
PARTS = {}      # object name -> info
COLLS = {}
KIND_COLL = {'PRT': 'Printed', 'BUY': 'Purchased', 'FST': 'Fasteners', 'CAB': 'Cables', 'TOOL': 'Tools'}


def coll(name):
    if name not in COLLS:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLLS[name] = c
    return COLLS[name]


MATS = {}


def mat(rgba):
    key = tuple(round(x, 3) for x in rgba)
    if key not in MATS:
        m = bpy.data.materials.new("M_%d" % len(MATS))
        m.diffuse_color = rgba
        m.roughness = 0.6
        MATS[key] = m
    return MATS[key]


PIV = {}


def finish(ob, name, kind, color, pivot=None, **info):
    """Rename, move to collection, colour, parent to a pivot, register."""
    ob.name = name
    ob.data.name = name
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll(KIND_COLL[kind]).objects.link(ob)
    ob.data.materials.clear()
    ob.data.materials.append(mat(color))
    if pivot:
        p = PIV[pivot]
        ob.parent = p
        ob.matrix_parent_inverse = p.matrix_world.inverted()
    info.update(kind=kind, pivot=pivot)
    PARTS[name] = info
    ob["kind"] = kind
    for k, v in info.items():
        if isinstance(v, (int, float, str)):
            ob[k] = v
    return ob


def make_pivots():
    def emp(name, loc, parent=None):
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = 'ARROWS'
        e.empty_display_size = 25
        e.location = loc
        bpy.context.scene.collection.objects.link(e)
        if parent:
            e.parent = PIV[parent]
            e.matrix_parent_inverse = PIV[parent].matrix_world.inverted()
        PIV[name] = e
        bpy.context.view_layer.update()
        return e
    emp("PIV_pan", (0, 0, TT_Z0))
    emp("PIV_tilt", (0, 0, T_Z), "PIV_pan")
    emp("PIV_flywheel", (WHEEL_XW, W_P, T_Z + W_Q), "PIV_tilt")
    emp("PIV_feeder", (FEED_XY[0], FEED_XY[1], PLATE_Z0 + PLATE_T), "PIV_pan")
    emp("PIV_pan_pinion", (PINION_XY[0], PINION_XY[1], GEAR_Z0))
    emp("PIV_hood", (WHEEL_XW, HINGE[0], T_Z + HINGE[1]), "PIV_tilt")
    PIV["PIV_pan"]["axis"] = "Z"
    PIV["PIV_tilt"]["axis"] = "X (hard stops -3..46 deg, firmware 0..45)"
    PIV["PIV_flywheel"]["axis"] = "X (bottom of the wheel moves forward: rotate negative about +X)"
    PIV["PIV_feeder"]["axis"] = "Z (park 0 = solid over the outlet; fire = +30 or -30 (alternate), then back to 0)"
    PIV["PIV_pan_pinion"]["axis"] = "Z (turns -pan, 1:1 gear)"
    PIV["PIV_hood"]["axis"] = "X (backplate hinge; adjustment only, %.2f..%.2f deg)" % (math.degrees(EPS_OPEN), math.degrees(EPS_CLOSE))


# rotations for print orientation (applied to world-frame mesh at home pose)
R_ID = Matrix.Identity(3)
R_FLIP = Matrix.Rotation(math.pi, 3, 'X')          # upside down
R_NX_DOWN = Matrix.Rotation(-math.pi / 2, 3, 'Y')  # world -X face onto the bed
R_PX_DOWN = Matrix.Rotation(math.pi / 2, 3, 'Y')   # world +X face onto the bed


def to_world_yz(pts):
    return [(p, T_Z + q) for p, q in pts]


def lprism(name, pts, x0, x1):
    """prism of a launcher-frame (p, q) polygon between world x0 and x1"""
    return prism(name, to_world_yz(pts), x0, x1, 'X')


def lcyl(name, c, r, x0, x1, n=None):
    return cyl(name, (c[0], T_Z + c[1]), r, x0, x1, 'X', n=n)


def sector(r0, r1, a0, a1, n=12, c=(0.0, 0.0)):
    """annular sector, angles in deg from +p (CCW), launcher frame"""
    o = [(c[0] + r1 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r1 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    i_ = [(c[0] + r0 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), c[1] + r0 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return o + i_


# =====================================================================================
# SERVO SUB-ASSEMBLY (pocket frame: u along servo length, v width, w = spline axis,
# origin = spline axis on the mount face, servo on the -w side)
# =====================================================================================


def servo_buy(name, M, pivot):
    u0, u1 = -SERVO_SPLINE_OFF - SERVO_L / 2, -SERVO_SPLINE_OFF + SERVO_L / 2
    b = box(name, u0, u1, -SERVO_W / 2, SERVO_W / 2, SERVO_TOP_W - SERVO_H, SERVO_TOP_W)
    bevel(b, 1.0)
    s = cyl(name + "s", (0, 0), 3.0, SERVO_TOP_W, SERVO_TOP_W + SPLINE_H - 0.6)
    i = cyl(name + "i", (0, 0), 3.0, SERVO_TOP_W - SERVO_H - SPLINE_H, SERVO_TOP_W - SERVO_H)
    ob = csg(b, add=[s, i])
    xform(ob, M)
    return finish(ob, name, 'BUY', COL['dark'], pivot, part="Hiwonder HTS-35H bus servo")


def horn_buy(name, M, pivot):
    hub = cyl(name + "h", (0, 0), 4.5, SERVO_TOP_W + 0.2, SERVO_TOP_W + 1.6)
    d = cyl(name, (0, 0), HORN_D / 2, SERVO_TOP_W + 1.6, SERVO_TOP_W + 1.6 + HORN_T)
    holes = [cyl(name + "x%d" % k, (HORN_BC / 2 * math.cos(k * math.pi / 4), HORN_BC / 2 * math.sin(k * math.pi / 4)), HORN_HOLE / 2, -60, 10, n=12) for k in range(8)]
    ctr = cyl(name + "c", (0, 0), 1.6, -60, 10, n=12)
    ob = csg(d, add=[hub], sub=holes + [ctr])
    xform(ob, M)
    return finish(ob, name, 'BUY', COL['metal'], pivot, part="round 8-hole servo horn (Ø20)")


def horn_adapter(name, M, pivot):
    """Shared horn adapter: Ø26 disc, Ø20.2 x 1.0 horn recess (servo side), 8 pilot dimples, 12 AF hex key
    with a Ø6.5 hole on axis so the horn's centre screw is driven AFTER the horn is screwed to the adapter."""
    w0 = SERVO_TOP_W + 1.6 + HORN_T - HORN_RECESS        # -4.6
    w1 = w0 + ADAPTER_T                                    # -0.6
    d = cyl(name, (0, 0), ADAPTER_R, w0, w1)
    bevel(d, 0.6)
    key = prism(name + "k", hexagon((0, 0), HEX_AF), w1 - 1.0, w1 + HEX_KEY_L)
    bevel(key, 0.5)
    rec = cyl(name + "r", (0, 0), (HORN_D + 0.2) / 2, w0 - 1, w0 + HORN_RECESS)
    thru = cyl(name + "t", (0, 0), KEY_HOLE_D / 2, w0 - 1, w1 + HEX_KEY_L + 1)
    dimples = [cone(name + "dm%d" % k, (HORN_BC / 2 * math.cos(k * math.pi / 4), HORN_BC / 2 * math.sin(k * math.pi / 4)), 0.7, 0.05,
                    w0 + HORN_RECESS - 0.01, w0 + HORN_RECESS + 0.6, n=12) for k in range(8)]
    ob = csg(d, add=[key], sub=[rec, thru] + dimples)
    xform(ob, M)
    return finish(ob, name, 'PRT', COL_B, pivot, stl="horn_adapter", print_rot=M.to_3x3().inverted(),
                  infill=40, supports="no", orient="recess side down, hex key up", qty_note="x3, one per servo")


def servo_pocket(name, M, pivot, variant="std"):
    """Pocket that holds the servo body against its top face; bolts to a flat mount face (w = 0)."""
    u_lo, u_hi = -SERVO_SPLINE_OFF - SERVO_L / 2, -SERVO_SPLINE_OFF + SERVO_L / 2   # -30, 10
    c = 0.3
    wall = 2.4
    wb = SERVO_TOP_W - SERVO_H        # -47.7 servo bottom
    if variant == "pan":
        fl = rrect(-40, 40, -40, 40, CR)
        holes = [(sx * 34, sy * 34) for sx in (-1, 1) for sy in (-1, 1)]
    else:
        fl = rrect(-42, 21.5, -16, 16, CR)
        holes = [(-38, -10), (-38, 10), (17, -10), (17, 10)]
    tp = 5.2
    plate = prism(name, fl, -tp, 0)
    bevel(plate, EB)
    walls = prism(name + "w", rrect(u_lo - c - wall, u_hi + c + wall, -SERVO_W / 2 - c - wall, SERVO_W / 2 + c + wall, 2), wb, -tp + 0.01)
    vb = SERVO_W / 2 + c + wall + 1.6
    bosses = [cyl(name + "bo%d" % i, (CLAMP_BOSS_U, s_ * vb), 3.6, wb, -tp + 0.01) for i, s_ in enumerate((-1, 1))]
    ue = u_lo - c - wall                                   # outer face of the -u end wall
    bosses += [box(name + "rb%d" % i, ue - 4.0, ue + 0.5, min(s_ * 3.0, s_ * 4.7), max(s_ * 3.0, s_ * 4.7), wb, -tp + 0.01) for i, s_ in enumerate((-1, 1))]  # cable channel ribs
    inner = prism(name + "i", rrect(u_lo - c, u_hi + c, -SERVO_W / 2 - c, SERVO_W / 2 + c, 1), wb - 1, -tp)
    lip = box(name + "lip", u_lo - c - 0.5, u_lo + 8, -SERVO_W / 2 - c - 0.5, SERVO_W / 2 + c + 0.5, SERVO_TOP_W, -tp + 0.02)
    hole = cyl(name + "h", (0, 0), 14.0, -tp - 0.1, 1)
    shole = [cyl(name + "sh%d" % i, h, 1.7, -10, 1, n=16) for i, h in enumerate(holes)]
    pil = [cyl(name + "pi%d" % i, (CLAMP_BOSS_U, s_ * vb), 1.25, wb - 1, wb + 10, n=16) for i, s_ in enumerate((-1, 1))]
    notch = box(name + "n", ue - 1, u_lo + 1, -3.0, 3.0, wb - 1, wb + 9)                     # servo lead exit at the clamp end
    fnotch = box(name + "fn", ue - 12, ue + 0.5, -3.0, 3.0, -tp - 1, 1)                       # lead passes the flange
    ob = csg(plate, add=[walls] + bosses)
    ob = csg(ob, sub=[inner])
    ob = csg(ob, add=[lip])
    relief = cyl(name + "rl", (0, 0), HORN_D / 2 + 0.8, SERVO_TOP_W + 0.5, -tp + 0.01)
    ob = csg(ob, sub=[hole, notch, fnotch, relief] + shole + pil)
    xform(ob, M)
    stl = "servo_pocket_pan" if variant == "pan" else "servo_pocket"
    return finish(ob, name, 'PRT', COL_A, pivot, stl=stl, print_rot=(Matrix.Rotation(math.pi, 3, 'X') @ M.to_3x3().inverted()),
                  infill=30, supports="no", orient="mount face down, walls up")


def servo_clamp(name, M, pivot):
    u_lo, u_hi = -30.0, 10.0
    wb = SERVO_TOP_W - SERVO_H
    vb = SERVO_W / 2 + 0.3 + 2.4 + 1.6
    pl = prism(name, hull_circles([((CLAMP_BOSS_U, -vb), 5.0), ((CLAMP_BOSS_U, vb), 5.0), ((u_lo - 1.7, -11.8), 1.0), ((u_lo - 1.7, 11.8), 1.0),
                                   ((u_hi + 1.7, -11.8), 1.0), ((u_hi + 1.7, 11.8), 1.0)]), wb - 4, wb)
    bevel(pl, 0.8)
    holes = [cyl(name + "h%d" % i, (CLAMP_BOSS_U, s_ * vb), 1.7, wb - 5, wb + 1, n=16) for i, s_ in enumerate((-1, 1))]
    idl = cyl(name + "id", (0, 0), 4.5, wb - 5, wb + 1)
    ob = csg(pl, sub=holes + [idl])
    xform(ob, M)
    return finish(ob, name, 'PRT', COL_A, pivot, stl="servo_clamp", print_rot=M.to_3x3().inverted(),
                  infill=30, supports="no", orient="flat")


def servo_set(tag, M, pivot_static, pivot_moving, variant="std"):
    servo_pocket("PRT_servo_pocket_%s" % tag, M, pivot_static, variant)
    servo_clamp("PRT_servo_clamp_%s" % tag, M, pivot_static)
    servo_buy("BUY_servo_%s" % tag, M, pivot_static)
    horn_buy("BUY_horn_%s" % tag, M, pivot_moving)
    horn_adapter("PRT_horn_adapter_%s" % tag, M, pivot_moving)


M_PAN = frame((PINION_XY[0], PINION_XY[1], GEAR_Z0 - 0.5), (0, -1, 0), (1, 0, 0), (0, 0, 1))
M_TILT = frame((ARM_R_X[1], 0, T_Z), (0, 0, 1), (0, 1, 0), (-1, 0, 0))
M_FEED = frame((FEED_XY[0], FEED_XY[1], PLATE_Z0), (0, 1, 0), (-1, 0, 0), (0, 0, 1))   # servo body trails behind the axis
TILT_CLAMP_X = ARM_R_X[1] - (SERVO_TOP_W - SERVO_H) + 4.0     # clamp outer face, world x

# =====================================================================================
# BASE
# =====================================================================================
B_BOSSES = [(-113, -72), (-110, 110), (110, 110), (113, -28), (0, 113), (-30, -113)]
DECK_POSTS = [(PINION_XY[0] + sx * 34, PINION_XY[1] + sy * 34) for sx in (-1, 1) for sy in (-1, 1)]
ADAPTER_HOLES = [(ADAPTER[0] + 6, ADAPTER[3] - 6), (ADAPTER[1] - 6, ADAPTER[3] - 6), (ADAPTER[0] + 6, ADAPTER[2] + 6), (ADAPTER[1] - 6, ADAPTER[2] + 6)]


def mg_hole_world(sx, sy):
    return (MG_X0 - sx, MG_Z0 - sy)


USB_W = (MG_X0 - USB_STEP[0], MG_Z0 - USB_STEP[1])        # world x, z of the USB-C axis
MG_PCB_Y = MG_WALL_Y + MG_STANDOFF + MG_PCB_T               # world y of STEP z = 0


def build_base_shell():
    H, r = BASE_HALF, BASE_CORNER_R
    outer = prism("PRT_base_shell", rrect(-H, H, -H, H, r, 8), FLOOR_T, BASE_H)
    bevel(outer, EB)
    inner = prism("s_in", rrect(-H + WALL, H - WALL, -H + WALL, H - WALL, r - WALL, 8), FLOOR_T - 1, DECK_Z0)
    ob = csg(outer, sub=[inner])
    add = []
    # battery bay partitions (2 mm clearance to the 115 x 76 x 70 envelope)
    add.append(box("bay_f", 2, H - 1, BATT[3] + BAY_CLR, BATT[3] + BAY_CLR + 3, FLOOR_T, DECK_Z0 + 0.5))
    add.append(box("bay_e", BATT[0] - BAY_CLR - 3, BATT[0] - BAY_CLR, -H + 1, BATT[3] + BAY_CLR + 1, FLOOR_T, DECK_Z0 + 0.5))
    # adapter locating fence on deck underside
    a = ADAPTER
    fo = prism("af_o", rrect(a[0] - 2.4, a[1] + 2.4, a[2] - 2.4, a[3] + 2.4, 2), DECK_Z0 - 3.5, DECK_Z0 + 0.5)
    fi = prism("af_i", rrect(a[0] - 0.4, a[1] + 0.4, a[2] - 0.4, a[3] + 0.4, 1), DECK_Z0 - 5, DECK_Z0 + 1)
    fence = csg(fo, sub=[fi])
    add.append(fence)
    # MotorGo partition, standoffs (teardrop, point toward world +Z = print-down side is safe)
    add.append(box("mgw", -100, -20, MG_WALL_Y - 3, MG_WALL_Y, FLOOR_T, DECK_Z0 + 0.5))
    for i, (sx, sy) in enumerate(((0, 0), (58, 0), (0, -49), (58, -49))):
        hx, hz = mg_hole_world(sx, sy)
        so = prism("so%d" % i, teardrop_x((hx, hz), 3.0), MG_WALL_Y - 0.5, MG_WALL_Y + MG_STANDOFF, 'Y')
        add.append(so)
    # USB niche walls
    nx0, nx1 = USB_W[0] - 18, USB_W[0] + 18
    nz0, nz1 = USB_W[1] - 18, USB_W[1] + 18
    ny0, ny1 = -H + 1, MG_WALL_Y - 3
    add.append(box("n_l", nx0 - 3, nx0, ny0, ny1 + 0.5, nz0 - 3, nz1 + 3))
    add.append(box("n_r", nx1, nx1 + 3, ny0, ny1 + 0.5, nz0 - 3, nz1 + 3))
    add.append(box("n_b", nx0 - 3, nx1 + 3, ny0, ny1 + 0.5, nz0 - 3, nz0))
    add.append(box("n_t", nx0 - 3, nx1 + 3, ny0, ny1 + 0.5, nz1, nz1 + 3))
    # floor-plate screw columns
    for i, (x, y) in enumerate(B_BOSSES):
        add.append(cyl("bb%d" % i, (x, y), 5.0, FLOOR_T, DECK_Z0 + 0.5))
    # deck posts for the pan servo pocket
    for i, (x, y) in enumerate(DECK_POSTS):
        add.append(cyl("dp%d" % i, (x, y), 4.5, GEAR_Z0 - 0.5, DECK_Z0 + 0.5))
    # UART lead clip rail on the floor-boss row (two hook clips), see build_cables
    ob = csg(ob, add=add)
    sub = []
    sub.append(cyl("dh", (0, 0), DECK_HOLE_R, DECK_Z0 - 1, BASE_H + 1))
    by0, by1, bz1 = BATT[2] - BAY_CLR, BATT[3] + BAY_CLR, BATT[5] + BAY_CLR
    sub.append(box("bay_o", H - 6, H + 1, by0, by1, FLOOR_T - 1, bz1))
    sub.append(box("bay_c", H - 11, H + 1, -H - 1, by1, FLOOR_T - 1, bz1))   # open the rear-right corner
    # 1 mm x 45 deg lead-in chamfer round the battery opening in the right wall
    ch = loft("bay_ch", [(by0 - 1.0, FLOOR_T - 1), (by1 + 1.0, FLOOR_T - 1), (by1 + 1.0, bz1 + 1.0), (by0 - 1.0, bz1 + 1.0)],
              [(by0, FLOOR_T - 1), (by1, FLOOR_T - 1), (by1, bz1), (by0, bz1)], H + 0.01, H - 1.0, 'X')
    sub.append(ch)
    sub.append(box("bay_wire", BATT[0] - BAY_CLR - 4, BATT[0] - BAY_CLR + 1, -68, -52, 64, 76))
    for i, (x, y) in enumerate(ADAPTER_HOLES):
        sub.append(cyl("ah%d" % i, (x, y), 1.7, DECK_Z0 - 4, BASE_H + 1, n=16))
        sub.append(cone("ac%d" % i, (x, y), 1.7, 3.4, BASE_H - 1.7, BASE_H + 0.01, n=24))
    # USB-C plug cutout in the partition (12.5 x 7 overmold + 1 mm all round)
    sub.append(prism("usb", rrect(USB_W[0] - 4.5, USB_W[0] + 4.5, USB_W[1] - 7.25, USB_W[1] + 7.25, 3), MG_WALL_Y - 4, MG_WALL_Y + 1, 'Y'))
    # niche void through the rear wall
    sub.append(box("nv", nx0, nx1, -H - 1, ny1, nz0, nz1))
    # standoff pilots
    for i, (sx, sy) in enumerate(((0, 0), (58, 0), (0, -49), (58, -49))):
        hx, hz = mg_hole_world(sx, sy)
        sub.append(cyl("sp%d" % i, (hx, hz), 1.25, MG_WALL_Y + MG_STANDOFF - 10, MG_WALL_Y + MG_STANDOFF + 1, 'Y', n=16))
    # floor screw pilots
    for i, (x, y) in enumerate(B_BOSSES):
        sub.append(cyl("bp%d" % i, (x, y), 1.25, FLOOR_T - 1, FLOOR_T + 12, n=16))
    for i, (x, y) in enumerate(DECK_POSTS):
        sub.append(cyl("dpp%d" % i, (x, y), 1.25, GEAR_Z0 - 1, GEAR_Z0 + 8, n=16))
    # buck intake louvres (left wall, low) and exhaust louvres (left wall, high)
    for k in range(9):
        y = BUCK_C[1] - 32 + 8 * k
        sub.append(prism("lv%d" % k, rrect(y - 1.5, y + 1.5, 10, 30, 1.4), -H - 1, -H + WALL + 1, 'X'))
        sub.append(prism("hv%d" % k, rrect(y - 1.5, y + 1.5, 52, 76, 1.4), -H - 1, -H + WALL + 1, 'X'))
    # rear wall vents above the niche / MotorGo
    for k in range(5):
        x = -64 + 6 * k
        sub.append(prism("rv%d" % k, rrect(x - 1.5, x + 1.5, 56, 78, 1.4), -H - 1, -H + WALL + 1, 'Y'))
    # front wall vents (cross flow past the servo controller)
    for k in range(6):
        x = 70 + 7 * k
        sub.append(prism("fv%d" % k, rrect(x - 1.5, x + 1.5, 30, 70, 1.4), H - WALL - 1, H + 1, 'Y'))
    # deck corner vents outside the turntable
    for k in range(5):
        sub.append(prism("dv%d" % k, rrect(-112 + 5 * k, -109 + 5 * k, -112 + 5 * k + 0, -96 + 5 * k, 1.4), DECK_Z0 - 1, BASE_H + 1))
    # servo controller access notch (switch, buttons, screw terminal) in the right wall
    sub.append(prism("sw", rrect(CTRL[2] + 6, CTRL[3] - 6, FLOOR_T - 4, 19, 3), H - WALL - 1, H + 1, 'X'))
    ob = csg(ob, sub=sub)
    # zip-tie anchor bar inside the niche (added after the void)
    bar = box("bar", nx0 - 0.5, nx1 + 0.5, -H + 6, -H + 10, USB_W[1] - 10.5, USB_W[1] - 7.5)
    ob = csg(ob, add=[bar])
    return finish(ob, "PRT_base_shell", 'PRT', COL_A, None, stl="base_shell", print_rot=R_FLIP, infill=15, supports="no",
                  orient="upside down: deck face on the bed, walls up")


UART_CLIPS = [(-40.0, 30.0), (40.0, 40.0)]


def build_base_floor():
    H, r = BASE_HALF, BASE_CORNER_R
    pl = prism("PRT_base_floor", rrect(-H, H, -H, H, r, 8), 0, FLOOR_T)
    bevel(pl, EB)
    add, sub = [], []
    bx, by = BUCK_C
    for s in (-1, 1):
        add.append(cyl("bk%d" % s, (bx, by + s * 33.4), 4.0, FLOOR_T - 0.5, FLOOR_T + 4))
        sub.append(cyl("bkp%d" % s, (bx, by + s * 33.4), 1.25, FLOOR_T, FLOOR_T + 5, n=16))
    cx, cy = 0.5 * (CTRL[0] + CTRL[1]), 0.5 * (CTRL[2] + CTRL[3])
    for sx in (-1, 1):
        for sy in (-1, 1):
            add.append(cyl("cb%d%d" % (sx, sy), (cx + sx * 17.5, cy + sy * 25.5), 3.5, FLOOR_T - 0.5, FLOOR_T + CTRL_BOSS_H))
            sub.append(cone("cd%d%d" % (sx, sy), (cx + sx * 17.5, cy + sy * 25.5), 0.05, 0.9, FLOOR_T + CTRL_BOSS_H - 0.8, FLOOR_T + CTRL_BOSS_H + 0.01, n=12))
            # corner fences (L) that locate the PCB at +0.4 regardless of the hole guess
            xc = CTRL[1] + 0.4 if sx > 0 else CTRL[0] - 0.4
            yc = CTRL[3] + 0.4 if sy > 0 else CTRL[2] - 0.4
            add.append(box("fx%d%d" % (sx, sy), min(xc, xc + sx * 1.6), max(xc, xc + sx * 1.6), min(yc - sy * 5, yc + sy * 1.6), max(yc - sy * 5, yc + sy * 1.6), FLOOR_T - 0.5, FLOOR_T + CTRL_BOSS_H + 3))
            add.append(box("fy%d%d" % (sx, sy), min(xc - sx * 5, xc + sx * 1.6), max(xc - sx * 5, xc + sx * 1.6), min(yc, yc + sy * 1.6), max(yc, yc + sy * 1.6), FLOOR_T - 0.5, FLOOR_T + CTRL_BOSS_H + 3))
    # UART lead clips: two printed hooks on the floor (lead pressed in, dab of hot glue)
    for i, (x, y) in enumerate(UART_CLIPS):
        add.append(box("uc%d" % i, x - 4, x + 4, y - 4, y + 4, FLOOR_T - 0.5, FLOOR_T + 7.6))
        sub.append(box("ucs%d" % i, x - 5, x + 5, y - 1.6, y + 1.6, FLOOR_T + 1.0, FLOOR_T + 5.5))
    for i, (x, y) in enumerate(B_BOSSES):
        sub.append(cyl("fh%d" % i, (x, y), 1.7, -1, FLOOR_T + 1, n=16))
        sub.append(cone("fc%d" % i, (x, y), 3.4, 1.7, -0.01, 1.7, n=24))
    for sx in (-1, 1):
        for sy in (-1, 1):
            sub.append(cyl("ft%d%d" % (sx, sy), (sx * 95, sy * 95), 7.0, -1, 1.0))
    ob = csg(pl, add=add)
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_base_floor", 'PRT', COL_A, None, stl="base_floor", print_rot=R_ID, infill=15, supports="no",
                  orient="flat, bosses up")


def build_pan_hub():
    g = prism("PRT_pan_hub", gear_poly(GEAR_M, GEAR_N), GEAR_Z0, GEAR_Z1)
    j = cyl("j", (0, 0), HUB_R, GEAR_Z1 - 0.01, TT_Z0)
    bore = cyl("b", (0, 0), HUB_BORE_R, GEAR_Z0 - 1, TT_Z0 + 1)
    ch = cone("bc", (0, 0), HUB_BORE_R + 1.0, HUB_BORE_R - 0.01, GEAR_Z0 - 0.01, GEAR_Z0 + 1.0)
    pil = [cyl("hp%d" % k, (17 * math.cos(math.radians(120 * k)), 17 * math.sin(math.radians(120 * k))), 1.25, TT_Z0 - 10, TT_Z0 + 1, n=16) for k in range(3)]
    ob = csg(g, add=[j])
    ob = csg(ob, sub=[bore, ch] + pil)
    return finish(ob, "PRT_pan_hub", 'PRT', COL_B, "PIV_pan", stl="pan_hub", print_rot=R_ID, infill=40, supports="no",
                  orient="gear face down")


def build_pan_pinion():
    g = prism("PRT_pan_pinion", gear_poly(GEAR_M, GEAR_N, c=PINION_XY, phase=math.radians(5)), GEAR_Z0, GEAR_Z1)
    sock = prism("s", hexagon(PINION_XY, HEX_AF + 2 * HEX_CLR, math.pi / 2), GEAR_Z0 - 1, GEAR_Z1 + 1)
    ob = csg(g, sub=[sock])
    return finish(ob, "PRT_pan_pinion", 'PRT', COL_B, "PIV_pan_pinion", stl="pan_pinion", print_rot=R_ID, infill=40, supports="no",
                  orient="flat")


# =====================================================================================
# PAN STAGE
# =====================================================================================
ARM_FOOT_HOLES_L = [(-81, -24), (-81, -12), (-81, 12), (-81, 24)]
ARM_FOOT_HOLES_R = [(58, -21), (58, 21), (64, -29), (64, 29)]
SPINE_HOLES = [(-60, -11.0), (-60, 11.0), (28, -11.0), (28, 11.0)]
CAP_SCREW_Y = 19.6
BONNET_SCREW_Z = (TT_Z1 + 10, T_Z - 20)
BONNET_DEPTH = 10.0
CAB_NOTCH_Y = (-11.0, -4.0)
FOOT_T = 8.0
CBORE_R, CBORE_D = 3.25, 3.2             # Ø6.5 x 3.2 counterbore for M3 socket heads


def build_turntable():
    t = cyl("PRT_turntable", (0, 0), TT_R, TT_Z0, TT_Z1)
    bevel(t, EB)
    ro = cyl("ro", (0, 0), RING_R1, TT_Z0 - RING_H, TT_Z0 + 0.5)
    ri = cyl("ri", (0, 0), RING_R0, TT_Z0 - RING_H - 1, TT_Z0 + 1)
    ringo = csg(ro, sub=[ri])
    ob = csg(t, add=[ringo])
    sub = [cyl("c", (0, 0), 12.0, TT_Z0 - 5, TT_Z1 + 1)]
    sub.append(box("gl", -TT_R - 1, 0, -TT_GROOVE_W / 2, TT_GROOVE_W / 2, TT_Z1 - TT_GROOVE_D, TT_Z1 + 1))
    sub.append(box("gr", 0, ARM_R_X[1] + 8, -TT_GROOVE_W / 2, TT_GROOVE_W / 2, TT_Z1 - TT_GROOVE_D, TT_Z1 + 1))
    for k in range(3):
        x, y = 17 * math.cos(math.radians(120 * k)), 17 * math.sin(math.radians(120 * k))
        sub.append(cyl("hh%d" % k, (x, y), 1.7, TT_Z0 - 1, TT_Z1 + 1, n=16))
        sub.append(cyl("hc%d" % k, (x, y), 3.0, TT_Z1 - TT_GROOVE_D - 2, TT_Z1 + 1, n=20))
    for i, (x, y) in enumerate(ARM_FOOT_HOLES_L + ARM_FOOT_HOLES_R + SPINE_HOLES):
        sub.append(cyl("ap%d" % i, (x, y), 1.25, TT_Z1 - 8, TT_Z1 + 1, n=16))
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_turntable", 'PRT', COL_A, "PIV_pan", stl="turntable", print_rot=R_FLIP, infill=15, supports="no",
                  orient="upside down: top face on the bed (grooves open at the bed), bearing ring up")


def build_spine():
    x0, x1 = ARM_L_X[1] + 14, ARM_R_X[0]
    s = prism("PRT_turntable_spine", rrect(x0, x1, -16, 16, CR), TT_Z1, TT_Z1 + SPINE_T)
    bevel(s, EB)
    sub = []
    for i, (x, y) in enumerate(SPINE_HOLES):
        sub.append(cyl("h%d" % i, (x, y), 1.7, TT_Z1 - 1, TT_Z1 + 5, n=16))
        sub.append(cone("c%d" % i, (x, y), 1.7, 3.2, TT_Z1 + SPINE_T - 1.5, TT_Z1 + SPINE_T + 0.01, n=20))
    ob = csg(s, sub=sub)
    return finish(ob, "PRT_turntable_spine", 'PRT', COL_B, "PIV_pan", stl="turntable_spine", print_rot=R_ID, infill=30, supports="no",
                  orient="flat")


def arm_profile():
    return [(-ARM_HALF_BOT, TT_Z1), (ARM_HALF_BOT, TT_Z1), (ARM_HALF_TOP, T_Z), (-ARM_HALF_TOP, T_Z)]


def stop_lug_arm(name, a0, a1, x_face, depth):
    """right-arm hard stop: annular sector on the arm inner face; radial contact faces, outer arc drafted 45 deg (prints upright)"""
    tip = sector(STOP_R0, STOP_R1, a0, a1, 10, (0.0, 0.0))
    root = sector(STOP_R0, STOP_R1 + 0.8, a0, a1, 10, (0.0, 0.0))
    return loft(name, to_world_yz(root), to_world_yz(tip), x_face + 0.01, x_face - depth, 'X')


STOP_DEPTH = 3.1
STOP_A_HI = (STOP_LUG_A + STOP_LUG_HW + TILT_MAX, STOP_LUG_A + STOP_LUG_HW + TILT_MAX + 12.0)   # contacts at +46
STOP_A_LO = (STOP_LUG_A - STOP_LUG_HW + TILT_MIN - 12.0, STOP_LUG_A - STOP_LUG_HW + TILT_MIN)   # contacts at -3


def build_arm(side):
    x0, x1 = ARM_L_X if side == "L" else ARM_R_X
    a = prism("PRT_yoke_arm_" + side, arm_profile(), x0, x1, 'X')
    bevel(a, EB)
    add, sub = [], []
    if side == "L":
        add.append(box("foot", x1 - 0.5, x1 + 14, -ARM_HALF_BOT, ARM_HALF_BOT, TT_Z1, TT_Z1 + FOOT_T))
        holes = ARM_FOOT_HOLES_L
    else:
        for s in (-1, 1):
            add.append(box("foot%d" % s, x1 - 0.5, x1 + 15.5, min(s * 15, s * (ARM_HALF_BOT + 2)), max(s * 15, s * (ARM_HALF_BOT + 2)), TT_Z1, TT_Z1 + FOOT_T))
        holes = ARM_FOOT_HOLES_R
        add.append(stop_lug_arm("stA", STOP_A_HI[0], STOP_A_HI[1], x0, STOP_DEPTH))
        add.append(stop_lug_arm("stB", STOP_A_LO[0], STOP_A_LO[1], x0, STOP_DEPTH))
    ob = csg(a, add=add)
    sub.append(cyl("bore", (0, T_Z), BORE_R, x0 - 5, x1 + 1, 'X'))
    sub.append(box("groove", x0 - 1, x1 + 15, -TT_GROOVE_W / 2, TT_GROOVE_W / 2, TT_Z1 - 1, TT_Z1 + 4))  # cable passage at the foot
    for i, (x, y) in enumerate(holes):
        sub.append(cyl("fh%d" % i, (x, y), 1.7, TT_Z1 - 1, TT_Z1 + 9, n=16))
        sub.append(cyl("fc%d" % i, (x, y), CBORE_R, TT_Z1 + FOOT_T - CBORE_D, TT_Z1 + FOOT_T + 1, n=20))
    xc = 0.5 * (x0 + x1)
    for s in (-1, 1):
        sub.append(cyl("cp%d" % s, (xc, s * CAP_SCREW_Y), 1.25, T_Z - 14, T_Z + 1, n=16))
    if side == "L":
        for s in (-1, 1):
            for z in BONNET_SCREW_Z:
                sub.append(cyl("bp%d_%d" % (s, z), (s * 16.5, z), 1.25, x0 - 1, x0 + 10, 'X', n=16))
    else:
        u, v = -38, 10
        for s in (-1, 1):
            sub.append(cyl("tp%d" % s, (s * v, T_Z + u), 1.25, x1 - 10, x1 + 1, 'X', n=16))
            sub.append(cyl("cp2%d" % s, (s * 16.5, TT_Z1 + 16), 1.25, x1 - 10, x1 + 1, 'X', n=16))
    ob = csg(ob, sub=sub)
    if side == "L":
        rot, ori = R_NX_DOWN, "lying on its outer face (foot grows up)"
    else:
        rot, ori = R_ID, "upright, foot on the bed (the bore is an open U at the top; stop lugs have 45 deg drafted sides)"
    return finish(ob, "PRT_yoke_arm_" + side, 'PRT', COL_A, "PIV_pan", stl="yoke_arm_" + side.lower(), print_rot=rot, infill=30,
                  supports="no", orient=ori)


def build_cap(side):
    x0, x1 = ARM_L_X if side == "L" else ARM_R_X
    c = prism("PRT_arm_cap_" + side, rrect(-ARM_HALF_TOP, ARM_HALF_TOP, T_Z - 6, T_Z + CAP_H, 3.0), x0, x1, 'X')
    bevel(c, EB)
    cut = box("cut", x0 - 1, x1 + 1, -40, 40, T_Z - 10, T_Z)
    ob = csg(c, sub=[cut])
    sub = [cyl("bore", (0, T_Z), BORE_R, x0 - 1, x1 + 1, 'X')]
    xc = 0.5 * (x0 + x1)
    for s in (-1, 1):
        sub.append(cyl("cs%d" % s, (xc, s * CAP_SCREW_Y), 1.7, T_Z - 1, T_Z + CAP_H + 1, n=16))
    if side == "L":
        sub.append(box("cn", x0 - 1, x1 + 1, CAB_NOTCH_Y[0], CAB_NOTCH_Y[1], T_Z + CAP_H - 5.2, T_Z + CAP_H + 1))   # feeder bus to the plate groove
    else:
        for s in (-1, 1):
            sub.append(cyl("tp%d" % s, (s * 10, T_Z + 17), 1.25, x1 - 10, x1 + 1, 'X', n=16))
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_arm_cap_" + side, 'PRT', COL_A, "PIV_pan", stl="arm_cap_" + side.lower(), print_rot=R_NX_DOWN, infill=30,
                  supports="no", orient="lying on its side face")


def build_bonnet():
    """Left cable bonnet: covers the hollow left journal end, 10 mm deep, and carries phases + encoder cable down to the turntable groove."""
    x0 = ARM_L_X[0]
    zt = PLATE_Z0 + PLATE_T          # runs up flush with the feeder-plate top: the bus enters the cap notch inside it
    fl = prism("PRT_arm_cover_L", rrect(-20.5, 20.5, TT_Z1 - 10, zt, CR), x0 - 2, x0, 'X')
    bul = prism("bul", rrect(-13, 13, TT_Z1 - 10, zt, CR), x0 - BONNET_DEPTH - 2, x0 - 1, 'X')
    ob = csg(fl, add=[bul], sub=[box("bc", x0 - 20, x0 + 5, -40, 40, TT_Z1 - 20, TT_Z1 + 0.5)])
    bevel(ob, EB)
    hol = prism("hol", rrect(-10.4, 10.4, TT_Z1 - 8, zt - 3.0, 4), x0 - BONNET_DEPTH, x0 + 1, 'X')
    sub = [hol]
    for s in (-1, 1):
        for z in BONNET_SCREW_Z:
            sub.append(cyl("h%d_%d" % (s, z), (s * 16.5, z), 1.7, x0 - BONNET_DEPTH - 3, x0 + 1, 'X', n=16))
            sub.append(cyl("hc%d_%d" % (s, z), (s * 16.5, z), CBORE_R, x0 - BONNET_DEPTH - 3, x0 - 2.0, 'X', n=20))
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_arm_cover_L", 'PRT', COL_B, "PIV_pan", stl="arm_cover_l", print_rot=R_PX_DOWN, infill=20, supports="no",
                  orient="flange (arm side) down, channel open to the bed")


COVER_R_TOP = T_Z - 47.0


def build_cover_r():
    x1 = ARM_R_X[1]
    fl = prism("PRT_arm_cover_R", rrect(-20.5, 20.5, TT_Z1 + 10, COVER_R_TOP + CR, CR), x1, x1 + 3.0, 'X')
    bul = prism("bul", rrect(-13, 13, TT_Z1 - 10, COVER_R_TOP + CR, CR), x1, x1 + 8, 'X')
    ob = csg(fl, add=[bul], sub=[box("bc", x1 - 5, x1 + 20, -40, 40, TT_Z1 - 20, TT_Z1 + 0.5),
                                 box("bt", x1 - 5, x1 + 20, -40, 40, COVER_R_TOP, COVER_R_TOP + 20)])
    bevel(ob, EB)
    hol = prism("hol", rrect(-10.4, 10.4, TT_Z1 - 8, COVER_R_TOP + 2, 4), x1 - 1, x1 + 6, 'X')
    sub = [hol]
    for s in (-1, 1):
        sub.append(cyl("h%d" % s, (s * 16.5, TT_Z1 + 16), 1.7, x1 - 1, x1 + 9, 'X', n=16))
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_arm_cover_R", 'PRT', COL_B, "PIV_pan", stl="arm_cover_r", print_rot=R_NX_DOWN, infill=20, supports="no",
                  orient="flange (arm side) down, channel open to the bed")


SVC_Y, SVC_Z0, SVC_W = 22.5, T_Z - 45.5, 2.4
FSH_T = 2.4                 # feeder shroud wall
FSH_CHAMFER_RUN = 10.0


def build_tilt_servo_cover():
    """Terracotta housing over the tilt servo: arm-width block from the arm face to past the clamp, flush with the cap top.
    Held by the two (longer) clamp screws through its end wall."""
    x0, x1 = ARM_R_X[1], TILT_CLAMP_X + 0.2 + SVC_W
    zt = T_Z + CAP_H
    o = prism("PRT_tilt_servo_cover", rrect(-SVC_Y, SVC_Y, SVC_Z0, zt, CR), x0, x1, 'X')
    o = csg(o, sub=[prism("chf", pod_chamfer_cut((SVC_Y, zt), POD_CHAMFER_RUN, +1, 0.0), x0 - 1, x1 + 1, 'X')])
    bevel(o, EB)
    i = prism("i", rrect(-SVC_Y + SVC_W, SVC_Y - SVC_W, SVC_Z0 + SVC_W, zt - SVC_W, CR - SVC_W), x0 - 1, x1 - SVC_W, 'X')
    i = csg(i, sub=[prism("chfi", pod_chamfer_cut((SVC_Y, zt), POD_CHAMFER_RUN, +1, SVC_W), x0 - 2, x1 + 2, 'X')])
    notch = box("n", x0 - 1, x0 + 8, -3.5, 3.5, SVC_Z0 - 1, SVC_Z0 + SVC_W + 1)
    vb = SERVO_W / 2 + 0.3 + 2.4 + 1.6
    sub = [i, notch]
    for s in (-1, 1):
        sub.append(cyl("h%d" % s, (s * vb, T_Z + CLAMP_BOSS_U), 1.7, x1 - 5, x1 + 1, 'X', n=16))
        sub.append(cone("c%d" % s, (s * vb, T_Z + CLAMP_BOSS_U), 1.7, 3.4, x1 - 1.7, x1 + 0.01, 'X', n=24))
    for k in range(4):   # vent slots in the end wall
        z = T_Z - 8 + 6 * k
        sub.append(prism("v%d" % k, rrect(-9, 9, z - 1.2, z + 1.2, 1.1), x1 - 5, x1 + 1, 'X'))
    ob = csg(o, sub=sub)
    return finish(ob, "PRT_tilt_servo_cover", 'PRT', COL_B, "PIV_pan", stl="tilt_servo_cover", print_rot=R_PX_DOWN, infill=20,
                  supports="no", orient="end wall on the bed, open side up")


POD_CHAMFER_RUN = 14.0      # chamfer echoing the pod's top chamfer angle (servo housing, feeder shroud)


def pod_chamfer_cut(corner, run, side, inset):
    """(y, z) triangle-ish region that cuts a corner at the pod's top-chamfer angle. corner = (y, z) of a top corner on the
    +y side (side=+1, chamfer descends toward +y like the pod's) or a bottom corner (side=-1, mirrored about z, chamfer rises
    toward -y). inset moves the cut line inward (for constant-wall inner cavities)."""
    sl = -TOP_DIR[1] / TOP_DIR[0]                       # drop per unit run
    y, z = corner
    n = math.hypot(1.0, sl)
    if side > 0:
        a = (y - run, z)
        b = (y, z - run * sl)
        off = (-sl / n * inset, -1.0 / n * inset)       # toward the inside (-y, -z)
        pts = [(a[0] + off[0] - 50 * 1 / n, a[1] + off[1] + 50 * sl / n), (b[0] + off[0] + 50 * 1 / n, b[1] + off[1] - 50 * sl / n)]
        return [pts[0], pts[1], (y + 60, z + 60), (y - 60, z + 60)]
    a = (y + run, z)
    b = (y, z + run * sl)
    off = (sl / n * inset, 1.0 / n * inset)             # toward the inside (+y, +z)
    pts = [(a[0] + off[0] + 50 / n, a[1] + off[1] - 50 * sl / n), (b[0] + off[0] - 50 / n, b[1] + off[1] + 50 * sl / n)]
    return [pts[1], (y - 60, z - 60), (y + 60, z - 60), pts[0]]


def sweep_env(poly, t0, t1, grow, n=180):
    """2D region swept by a star-shaped (about the origin) polygon rotating t0..t1 deg about the origin, grown by `grow`"""
    def r_at(ph):
        # ray from the origin at angle ph: furthest crossing with the polygon
        d = (math.cos(ph), math.sin(ph))
        best = 0.0
        m = len(poly)
        for i in range(m):
            a, b = poly[i], poly[(i + 1) % m]
            ex, ey = b[0] - a[0], b[1] - a[1]
            den = d[0] * ey - d[1] * ex
            if abs(den) < 1e-12:
                continue
            t = (a[0] * ey - a[1] * ex) / den
            u = (a[0] * d[1] - a[1] * d[0]) / den
            if t > 0 and -1e-9 <= u <= 1 + 1e-9:
                best = max(best, t)
        return best
    base = [r_at(2 * math.pi * i / n) for i in range(n)]
    out = []
    for i in range(n):
        ph = 2 * math.pi * i / n
        r = 0.0
        for t in lin(t0, t1, int(abs(t1 - t0)) + 2):
            j = int(round((ph - math.radians(t)) / (2 * math.pi) * n)) % n
            r = max(r, base[j], base[(j + 1) % n], base[j - 1])
        out.append(((r + grow) * math.cos(ph), (r + grow) * math.sin(ph)))
    return out


def build_feeder_shroud():
    """Terracotta shroud round the feeder servo, pocket and clamp under the feeder plate (same idea as the tilt-servo
    housing: held by the two clamp screws through its floor). Its face toward the pod is the pod's swept envelope (+2.5),
    a cylinder about the tilt axis, so it clears the launcher at every tilt; the rear-bottom edge carries the pod chamfer."""
    w_top = -0.3
    wb = SERVO_TOP_W - SERVO_H
    w_bot = wb - 4.0 - FSH_T
    lo_u, hi_u, hv = -43.5, 23.0, 20.5
    o = prism("PRT_feeder_shroud", rrect(lo_u - FSH_T, hi_u + FSH_T + 12.0, -hv - FSH_T, hv + FSH_T, CR), w_bot, w_top)
    o = csg(o, sub=[box("fr", hi_u + FSH_T, hi_u + 40.0, -40.0, 40.0, w_bot - 1, w_top + 1)])   # square front corners
    # open toward the pod (the swept-envelope cut trims side walls and floor square; no oblique front-wall slivers)
    i = prism("i", rrect(lo_u, hi_u + 20.0, -hv, hv, CR - FSH_T), w_bot + FSH_T, w_top + 1)
    xform(o, M_FEED)
    xform(i, M_FEED)
    # rear-bottom edge chamfer at the pod's chamfer angle (mirrored); the cavity gets the same chamfer inset by the wall
    corner = (FEED_XY[1] + lo_u - FSH_T, PLATE_Z0 + w_bot)
    o = csg(o, sub=[prism("chf", pod_chamfer_cut(corner, FSH_CHAMFER_RUN, -1, 0.0), -60, 120, 'X')])
    i = csg(i, sub=[prism("chfi", pod_chamfer_cut(corner, FSH_CHAMFER_RUN, -1, FSH_T), -60, 120, 'X')])
    holes = []
    vb = SERVO_W / 2 + 0.3 + 2.4 + 1.6
    for s_ in (-1, 1):
        holes.append(cyl("h%d" % s_, (CLAMP_BOSS_U, s_ * vb), 1.7, w_bot - 1, w_bot + FSH_T + 1, n=16))
        holes.append(cone("c%d" % s_, (CLAMP_BOSS_U, s_ * vb), 3.4, 1.7, w_bot - 0.01, w_bot + 1.7, n=24))
    holes.append(cyl("idl", (0, 0), 5.0, w_bot - 1, w_bot + FSH_T + 1, n=24))      # servo idler boss clearance
    for h in holes:
        xform(h, M_FEED)
    ob = csg(o, sub=[i] + holes)
    # pod clearance: swept envelope of the guard profile over the hard-stop range (+-2 deg) grown 2.5, and the right arm/cap
    env = sweep_env(guard_profile(), TILT_MIN - 2.0, TILT_MAX + 2.0, 3.0)
    cut = lprism("env", env, -10.0, ARM_R_X[0] + 2.0)
    arm = box("arm", ARM_R_X[0] - 0.8, ARM_R_X[1] + 1, -ARM_HALF_BOT - 1, ARM_HALF_BOT + 1, TT_Z1, PLATE_Z0 + 1)
    ob = csg(ob, sub=[cut, arm])
    bevel(ob, 0.6)
    return finish(ob, "PRT_feeder_shroud", 'PRT', COL_B, "PIV_pan", stl="feeder_shroud", print_rot=Matrix.Rotation(math.pi / 2, 3, 'X'),
                  infill=20, supports="no", orient="rear face on the bed: walls, floor and both chamfer faces are vertical or <= 45 deg")


HOP_C = FEED_XY
OUTLET_XY = (WHEEL_XW, 0.0)
HOP_LUG_ANG = (200, 270, 340)   # rear lugs; screws come up from under the plate
HOP_LUG_R = HOP_BORE_R + HOP_WALL + 4.6
FEED_FLANGE_HOLES = [(-38, -10), (-38, 10), (17, -10), (17, 10)]
PLATE_GROOVE = [(ARM_L_X[0] + 1, -7.5), (-45.0, -7.5), (-22.0, -70.0), (6.0, -84.0), (FEED_XY[0], -84.0)]


def build_feeder_plate():
    circs = [((ARM_L_X[0] + 4, -20), 4), ((ARM_L_X[0] + 4, 20), 4), ((ARM_R_X[1] - 4, -20), 4), ((ARM_R_X[1] - 4, 20), 4),
             (HOP_C, HOP_BORE_R + 12), (OUTLET_XY, 12)]
    p = prism("PRT_feeder_plate", hull_circles(circs, 96), PLATE_Z0, PLATE_Z0 + PLATE_T)
    bevel(p, EB)
    spout = cyl("spout", OUTLET_XY, SPOUT_R, SPOUT_Z0, PLATE_Z0 + 0.5)
    bevel(spout, 0.8)
    p = csg(p, add=[spout])
    cutf = prism("cf", rrect(ARM_L_X[1] + 2, ARM_R_X[0] - 2, PLATE_FRONT_Y, 60, CR), PLATE_Z0 - 1, PLATE_Z0 + PLATE_T + 1)
    sub = [cutf, cyl("out", OUTLET_XY, OUTLET_R, SPOUT_Z0 - 1, PLATE_Z0 + PLATE_T + 1),
           cone("outc", OUTLET_XY, OUTLET_R, OUTLET_R + 1.5, PLATE_Z0 + PLATE_T - 1.5, PLATE_Z0 + PLATE_T + 0.01),
           cyl("fd", HOP_C, 10.0, PLATE_Z0 - 1, PLATE_Z0 + PLATE_T + 1)]
    for side in ("L", "R"):
        x0, x1 = ARM_L_X if side == "L" else ARM_R_X
        for s in (-1, 1):
            c = (0.5 * (x0 + x1), s * CAP_SCREW_Y)
            sub.append(cyl("cs%s%d" % (side, s), c, 1.7, PLATE_Z0 - 1, PLATE_Z0 + PLATE_T + 1, n=16))
            sub.append(cone("cc%s%d" % (side, s), c, 1.7, 3.4, PLATE_Z0 + PLATE_T - 1.75, PLATE_Z0 + PLATE_T + 0.01, n=24))   # flush countersunk heads
    for i, (u, v) in enumerate(FEED_FLANGE_HOLES):
        hw = M_FEED @ Vector((u, v, 0))
        sub.append(cyl("ff%d" % i, (hw.x, hw.y), 1.25, PLATE_Z0 - 1, PLATE_Z0 + PLATE_T + 1, n=16))
    for k, a in enumerate(HOP_LUG_ANG):
        x, y = HOP_C[0] + HOP_LUG_R * math.cos(math.radians(a)), HOP_C[1] + HOP_LUG_R * math.sin(math.radians(a))
        sub.append(cyl("lp%d" % k, (x, y), 1.7, PLATE_Z0 - 1, PLATE_Z0 + PLATE_T + 1, n=16))
        sub.append(cone("lc%d" % k, (x, y), 3.4, 1.7, PLATE_Z0 - 0.01, PLATE_Z0 + 1.7, n=24))
    # bus groove on the underside: left cap notch -> feeder servo flange notch
    for i in range(len(PLATE_GROOVE) - 1):
        (xa, ya), (xb, yb) = PLATE_GROOVE[i], PLATE_GROOVE[i + 1]
        sub.append(prism("gv%d" % i, hull_circles([((xa, ya), 3.0), ((xb, yb), 3.0)], 24), PLATE_Z0 - 1, PLATE_Z0 + 3.0))
    ob = csg(p, sub=sub)
    return finish(ob, "PRT_feeder_plate", 'PRT', COL_A, "PIV_pan", stl="feeder_plate", print_rot=R_FLIP, infill=25, supports="no",
                  orient="upside down: top face on the bed, spout and groove up")


def build_feeder_disc():
    z0 = PLATE_Z0 + PLATE_T + 0.4
    d = cyl("PRT_feeder_disc", HOP_C, DISC_R, z0, z0 + DISC_T)
    bevel(d, EB)
    boss = cyl("boss", HOP_C, 9.0, PLATE_Z0 + 0.6, z0 + 0.5)
    ob = csg(d, add=[boss])
    sub = [prism("hex", hexagon(HOP_C, HEX_AF + 2 * HEX_CLR, math.pi / 2), PLATE_Z0 - 1, PLATE_Z0 + 0.6 + HEX_KEY_L + 0.5)]
    for a in pocket_angles(0.0):
        a = math.radians(a)
        c = (HOP_C[0] + FEED_RP * math.cos(a), HOP_C[1] + FEED_RP * math.sin(a))
        sub.append(cyl("pk%d" % int(math.degrees(a)), c, POCKET_D / 2, z0 - 1, z0 + DISC_T + 1))
        sub.append(cone("pc%d" % int(math.degrees(a)), c, POCKET_D / 2 - 0.01, POCKET_D / 2 + 1.5, z0 + DISC_T - 1.5, z0 + DISC_T + 0.01))
    for k in range(N_POCKETS):
        a = math.radians(OUTLET_ANG + 360 * k / N_POCKETS)          # agitator dimples (blind) between the pockets
        c = (HOP_C[0] + 26 * math.cos(a), HOP_C[1] + 26 * math.sin(a))
        sub.append(cyl("ag%d" % k, c, 5.0, z0 + DISC_T - 1.5, z0 + DISC_T + 1))
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_feeder_disc", 'PRT', COL_B, "PIV_feeder", stl="feeder_disc", print_rot=R_FLIP, infill=30, supports="no",
                  orient="upside down: top face on the bed, drive boss up")


def hopper_profile():
    a = math.radians(HOP_FLARE_ANG)
    t = HOP_WALL
    r0 = HOP_BORE_R
    h1, h2 = HOP_BARREL_H, HOP_BARREL_H + HOP_FLARE_H
    I0, I1, I2 = (r0, 0.0), (r0, h1), (r0 + HOP_FLARE_H / math.tan(a), h2)
    s = t * (1 - math.sin(a)) / math.cos(a)
    O1 = (r0 + t, h1 - t * math.cos(a) + s * math.sin(a))
    s2 = t * math.cos(a) / math.sin(a)
    O2 = (I2[0] + t * math.sin(a) + s2 * math.cos(a), h2)
    return [I0, (r0 + t, 0.0), O1, O2, (O2[0], h2 + 3), (I2[0] - 0.01, h2 + 3), I2, I1], I2, O2


def build_hopper():
    zp = PLATE_Z0 + PLATE_T
    prof, I2, O2 = hopper_profile()
    hp = revolve("PRT_hopper", prof, (HOP_C[0], HOP_C[1], zp), n=128)
    add = []
    for k, a in enumerate(HOP_LUG_ANG):
        a = math.radians(a)
        add.append(revolve("lug%d" % k, [(HOP_BORE_R + 0.5, 0), (HOP_LUG_R + 5.5, 0), (HOP_LUG_R + 5.5, 5.0), (HOP_BORE_R + 0.5, 5 + HOP_LUG_R + 5 - HOP_BORE_R)],
                           (HOP_C[0], HOP_C[1], zp), n=360, a0=a - math.radians(7), a1=a + math.radians(7)))
    # knock-off baffle above the outlet: 45 deg top, both ends ramped 30 deg so a candy standing on edge is pushed down, not sheared
    d0 = DISC_T + 0.4 + 1.0
    ang = math.atan2(OUTLET_XY[1] - HOP_C[1], OUTLET_XY[0] - HOP_C[0])
    hw = math.radians(24)
    baf = revolve("baf", [(29.0, d0), (HOP_BORE_R + 0.5, d0), (HOP_BORE_R + 0.5, d0 + HOP_BORE_R + 0.5 - 29.0)],
                  (HOP_C[0], HOP_C[1], zp), n=360, a0=ang - hw, a1=ang + hw)
    rise = 6.0
    run = rise / math.tan(math.radians(BAFFLE_RAMP))
    cut = []
    for s in (-1, 1):
        ae = ang + s * hw
        er = (math.cos(ae), math.sin(ae))
        et = (-math.sin(ae) * s, math.cos(ae) * s)        # tangential, pointing out of the baffle at this end
        # triangle in (t, z): from the end face inward by `run`, rising `rise` at the end face
        tri = [(1.5, d0 - 1.0), (1.5, d0 + rise), (0.0, d0 + rise), (-run, d0 - 1.0)]
        M = frame((HOP_C[0], HOP_C[1], zp), (et[0], et[1], 0), (0, 0, 1), (er[0], er[1], 0))
        c = prism("rc%d" % s, tri, 26.0, HOP_BORE_R + 3.0, 'Z')
        xform(c, M)
        cut.append(c)
    baf = csg(baf, sub=cut)
    add.append(baf)
    ob = csg(hp, add=add)
    sub = []
    for k, a in enumerate(HOP_LUG_ANG):
        x, y = HOP_C[0] + HOP_LUG_R * math.cos(math.radians(a)), HOP_C[1] + HOP_LUG_R * math.sin(math.radians(a))
        sub.append(cyl("lh%d" % k, (x, y), 1.25, zp - 1, zp + 7, n=16))
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_hopper", 'PRT', COL_A, "PIV_pan", stl="hopper", print_rot=R_FLIP, infill=15, supports="no",
                  orient="upside down: top rim on the bed (flare leans 30 deg, baffle top 45 deg, ramps 30 deg)")


def build_hopper_lid():
    zp = PLATE_Z0 + PLATE_T
    prof, I2, O2 = hopper_profile()
    ztop = zp + HOP_BARREL_H + HOP_FLARE_H + 3
    lid = prism("PRT_hopper_lid", hull_circles([(HOP_C, O2[0] + 1.0), ((HOP_C[0], HOP_C[1] - O2[0] - 8), 6)], 128), ztop, ztop + 3)
    bevel(lid, EB)
    plug_o = cyl("po", HOP_C, I2[0] - 0.4, ztop - 2.8, ztop + 0.5)
    plug_i = cyl("pi", HOP_C, I2[0] - 2.4, ztop - 4, ztop + 0.01)
    plug = csg(plug_o, sub=[plug_i])
    ob = csg(lid, add=[plug])
    ob = csg(ob, sub=[cyl("grip", (HOP_C[0], HOP_C[1] - O2[0] - 8), 3.0, ztop - 1, ztop + 4)])
    return finish(ob, "PRT_hopper_lid", 'PRT', COL_B, "PIV_pan", stl="hopper_lid", print_rot=R_FLIP, infill=15, supports="no",
                  orient="upside down: top face on the bed, locating ring up")


# =====================================================================================
# LAUNCHER (tilting)
# =====================================================================================
HOOD_X0, HOOD_X1 = X_BODY_IN + 0.5, X_COVER_IN - 0.5


def build_launcher_body():
    """Guard body: left wall + perimeter, open on the +X side (journal plate + cover close it)."""
    xo, xi, xc = X_BODY_OUT, X_BODY_IN, X_COVER_IN
    body = lprism("PRT_launcher_body", PROFILE, xo, xc)
    # flat land on the rear underside: thumbwheel seat + nip-cover screw rail (full body width: prints from the bed)
    land = lprism("land", [nip_pq(-10.0, LAND_V[0]), nip_pq(0.0, LAND_V[0]), nip_pq(0.0, LAND_V[1]), nip_pq(-10.0, LAND_V[1])], xo, xc)
    body = csg(body, add=[land])
    bevel(body, EB)
    sub = [lprism("wc", wheel_cavity_poly(), xi, xc + 1), lprism("nip", nip_poly(), xi, xc + 1),
           lprism("mz", muzzle_poly(), xi, xc + 1), lprism("ch", chute_poly(), CH_X0, xc + 1)]
    for k, poly in enumerate(BAY_POLYS):
        sub.append(lprism("bay%d" % k, poly, xi, xc + 1))
    sub.append(lprism("bayb", BAY_BOSS, xi, xc + 1))
    body = csg(body, sub=sub)
    sub = []
    # stud slot: the hex head passes in from outside; covers the stud's swing over the whole hinge range
    circs = []
    for e in lin(EPS_OPEN - 0.01, EPS_CLOSE + 0.01, 7):
        p0, d = stud_line(e)
        circs += [(vadd(p0, d, -1.0), STUD_HOLE_R), (vadd(p0, d, stud_d(e) + 2.0), STUD_HOLE_R)]
    sub.append(lprism("stud", hull_circles(circs, 24), NIP_X - STUD_HOLE_R, NIP_X + STUD_HOLE_R))
    for k, x in enumerate(NIP_SCREW_X):
        a, b = nip_pq(0.5, NIP_SCREW_V), nip_pq(-7.0, NIP_SCREW_V)
        sub.append(_boss_along("nsp%d" % k, x, b, a, 1.25))
    sub.append(lcyl("sh", WC, 6.0, xo - 1, xi + 1))
    for k, c in enumerate(MOTOR_SCREWS + NAC_SCREWS):
        sub.append(lcyl("ms%d" % k, c, 1.7, xo - 1, xi + 1, n=16))
        sub.append(lcyl("mc%d" % k, c, CBORE_R, xi - 2.0, xi + 1, n=20))
    # hinge axle: countersunk M3 from the outside of the left wall, threads into the journal plate
    sub.append(lcyl("hg", HINGE, 1.7, xo - 1, xi + 1, n=16))
    sub.append(cone("hgc", (HINGE[0], T_Z + HINGE[1]), 3.4, 1.7, xo - 0.01, xo + 1.75, 'X', n=24))
    for k, c in enumerate(JP_SCREWS + COVER_SCREWS):
        sub.append(lcyl("sp%d" % k, c, 1.25, xc - 10, xc + 1, n=16))
    body = csg(body, sub=sub)
    return finish(body, "PRT_launcher_body", 'PRT', COL_B, "PIV_tilt", stl="launcher_body", print_rot=R_NX_DOWN, infill=25,
                  supports="no", orient="left (motor) wall outer face on the bed; profile extruded so every wall is vertical")


def _boss_along(name, x, a, b, r):
    """cylinder between launcher points a and b (both at world x), axis in the y-z plane"""
    A = Vector((x, a[0], T_Z + a[1]))
    B = Vector((x, b[0], T_Z + b[1]))
    L = (B - A).length
    c = cyl(name, (0, 0), r, 0, L, 'Z', n=20 if r > 2 else 16)
    d = (B - A).normalized()
    R = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
    xform(c, Matrix.Translation(A) @ R)
    return c


def jp_cover_layers(kind):
    """journal plate / cover split with a stepped lap: the plate's outer layers overlap the cover's rebated edge."""
    steps = [(X_COVER_IN, X_COVER_IN + 2.0, 0.0), (X_COVER_IN + 2.0, X_COVER_OUT, 2.0)]
    out = []
    for k, (x0, x1, off) in enumerate(steps):
        if kind == "jp":
            out.append((x0, x1, jp_union(JP_R, off)))
        else:
            out.append((x0, x1, jp_union(JP_R, off + 0.3)))
    return out


def build_journal_plate():
    """Closes the drum, chute and hinge side; carries the right journal + hex socket for the tilt servo and the
    launcher hard-stop lug. Screwed to the body (3 screws), stays in the yoke when the cover is removed."""
    parts = []
    for k, (x0, x1, reg) in enumerate(jp_cover_layers("jp")):
        pr = lprism("jpl%d" % k, PROFILE, x0, x1)
        rg = lprism("jpr%d" % k, reg, x0 - 0.01, x1 + 0.01)
        parts.append(csg(pr, inter=[rg]))
    ob = parts[0]
    ob = csg(ob, add=parts[1:])
    bevel(ob, EB)
    col = lcyl("col", (0, 0), COLLAR_R, X_COVER_OUT - 0.01, ARM_R_X[0] - 0.2)
    jr = lcyl("jr", (0, 0), JOURNAL_R, ARM_R_X[0] - 0.21, ARM_R_X[1] - 0.3)
    bevel(jr, 0.6)
    lug = lprism("lug", sector(STOP_R0, STOP_R1, STOP_LUG_A - STOP_LUG_HW, STOP_LUG_A + STOP_LUG_HW, 8), X_COVER_OUT - 0.01, X_COVER_OUT + 3.1)
    ob = csg(ob, add=[col, jr, lug])
    sub = [prism("hex", to_world_yz(hexagon((0, 0), HEX_AF + 2 * HEX_CLR, math.pi / 2)), ARM_R_X[1] - 0.3 - HEX_KEY_L - 0.5, ARM_R_X[1] + 1, 'X')]
    for k, c in enumerate(JP_SCREWS):
        sub.append(lcyl("s%d" % k, c, 1.7, X_COVER_IN - 1, X_COVER_OUT + 1, n=16))
        sub.append(cone("c%d" % k, (c[0], T_Z + c[1]), 1.7, 3.4, X_COVER_OUT - 1.75, X_COVER_OUT + 0.01, 'X', n=24))
    sub.append(lcyl("hg", HINGE, 1.25, X_COVER_IN - 1, X_COVER_OUT + 1, n=16))      # hinge axle pilot
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_journal_plate", 'PRT', COL_B, "PIV_tilt", stl="journal_plate", print_rot=R_NX_DOWN, infill=30,
                  supports="no", orient="inner face on the bed; lap steps, collar, journal and stop lug grow up (1 mm steps)")


def build_launcher_cover():
    """Wheel-side cover: 4 countersunk screws (all in front of the right arm at tilt 0 and 45), no through features,
    so it lifts 2 mm and slides out forward-down with the pod in the yoke (wheel access at tilt 45)."""
    parts = []
    for k, (x0, x1, reg) in enumerate(jp_cover_layers("cover")):
        pr = lprism("cvl%d" % k, PROFILE, x0, x1)
        rg = lprism("cvr%d" % k, reg, x0 - 0.01, x1 + 0.01)
        parts.append(csg(pr, sub=[rg]))
    ob = parts[0]
    ob = csg(ob, add=parts[1:])
    bevel(ob, EB)
    sub = []
    for k, c in enumerate(COVER_SCREWS):
        sub.append(lcyl("s%d" % k, c, 1.7, X_COVER_IN - 1, X_COVER_OUT + 1, n=16))
        sub.append(cone("c%d" % k, (c[0], T_Z + c[1]), 1.7, 3.4, X_COVER_OUT - 1.75, X_COVER_OUT + 0.01, 'X', n=24))
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_launcher_cover", 'PRT', COL_B, "PIV_tilt", stl="launcher_cover", print_rot=R_NX_DOWN, infill=25,
                  supports="no", orient="inner face on the bed; rebated edge steps in toward the top")


def build_hood():
    """Backplate (the brief's hood) under the wheel: concentric 0..78 deg behind BDC, quadratic funnel to 112 deg,
    hinged at its top end. Not locked: a hex-head stud sits head-down in a hex pocket on its back face; the thumbwheel on
    the stud (outside the guard) is the minimum-gap stop and the nip-cover leaf spring preloads it closed."""
    h = lprism("PRT_hood", bp_band(0.0, 0.0), HOOD_X0, HOOD_X1)
    boss = lcyl("bs", HINGE, HINGE_BOSS_R, HOOD_X0, HOOD_X1, n=32)
    h = csg(h, add=[boss])
    bevel(h, 0.8)
    sub = [lcyl("hg", HINGE, 1.7, HOOD_X0 - 1, HOOD_X1 + 1, n=16),
           _prism_along("sp", hexagon((0, 0), STUD_HEAD_AF + 0.2, 0.0), NIP_X, vadd(JACK_PT, NIP_U, 1.0), vadd(JACK_PT, NIP_U, -STUD_POCKET_D))]
    h = csg(h, sub=sub)
    return finish(h, "PRT_hood", 'PRT', COL_A, "PIV_hood", stl="hood", print_rot=R_NX_DOWN, infill=40, supports="no",
                  orient="on its side face (profile extruded, all walls vertical; stud pocket has a vertex up)")


def _prism_along(name, poly, x, a, b):
    """prism of a 2D polygon (s = world X offset, t = in-plane normal) from launcher point a to b at world x"""
    A = Vector((x, a[0], T_Z + a[1]))
    B = Vector((x, b[0], T_Z + b[1]))
    L = (B - A).length
    w = (B - A).normalized()
    u = Vector((1, 0, 0))
    v = w.cross(u)
    ob = prism(name, poly, 0.0, L, 'Z')
    xform(ob, frame(A, u, v, w))
    return ob


def build_thumbwheel():
    """Ø18 x 5 knurled thumbwheel with a captive M3 nut: runs on the stud and rests on the seat land (min-gap stop)."""
    w = cyl("PRT_nip_wheel", (NIP_X, 0.0), TW_R, 0.0, TW_T, 'Y', n=64)
    bevel(w, 0.6)
    sub = [cyl("h", (NIP_X, 0.0), 1.7, -1, TW_T + 1, 'Y', n=16),
           prism("nt", hexagon((NIP_X, 0.0), NUT_AF, 0.0), -1.0, TW_NUT_U[1], 'Y')]
    for k in range(12):
        a = 2 * math.pi * k / 12
        sub.append(cyl("kn%d" % k, (NIP_X + TW_R * math.cos(a), TW_R * math.sin(a)), 0.9, -1, TW_T + 1, 'Y', n=12))
    ob = csg(w, sub=sub)
    M = nip_frame()
    xform(ob, M)
    Uw = Vector((0, NIP_U[0], NIP_U[1]))
    R = Uw.rotation_difference(Vector((0, 0, -1))).to_matrix()
    return finish(ob, "PRT_nip_wheel", 'PRT', COL_B, "PIV_tilt", stl="nip_wheel", print_rot=R, infill=50, supports="no",
                  orient="outer face on the bed, nut trap up (press the nut in, dab of superglue)")


def build_nip_cover():
    """Terracotta cover over the thumbwheel, sitting on the flat land on the pod's rear underside (same footprint as the
    land, so its +X face continues the body/cover parting plane). Its inner LEAF (2 mm PLA cantilever from the screw block,
    34 mm to the pads) presses the thumbwheel onto the seat. Printed in its free shape: the two pads stand LEAF_PRE into
    the thumbwheel, which is the assembly preload. The rigid shell stops the leaf after a further 2.5 mm (over-travel
    stop). Held by 2 x M3 into the land; remove it to turn the thumbwheel."""
    x0, x1 = NIP_XC
    v0, v1 = LAND_V
    uo = SHELL_U0 + SHELL_T
    # profile in (u, v): square where it sits on the land, CR rounds on the two outer long edges
    prof = [(0.0, v0)]
    prof += [(uo - CR + CR * math.sin(math.radians(a)), v0 + CR - CR * math.cos(math.radians(a))) for a in range(0, 91, 10)]
    prof += [(uo - CR + CR * math.cos(math.radians(a)), v1 - CR + CR * math.sin(math.radians(a))) for a in range(0, 91, 10)]
    prof += [(0.0, v1)]
    outer = prism("PRT_nip_cover", prof, x0, x1, 'X')
    bevel(outer, EB)
    xa, xb = x0 + NIP_END_T, x1 - NIP_END_T
    # inside: wheel, leaf, travel; the corner under the rounded skirt edge is rounded concentrically (constant 2 mm wall)
    rc = (uo - CR, v0 + CR)
    cprof = [(-1.0, NIP_V_SKIRT[1]), (rc[0], NIP_V_SKIRT[1])]
    cprof += [(rc[0] + (CR - 2.0) * math.sin(math.radians(a)), rc[1] - (CR - 2.0) * math.cos(math.radians(a))) for a in range(10, 90, 10)]
    cprof += [(SHELL_U0, rc[1]), (SHELL_U0, NIP_V_ROOT), (-1.0, NIP_V_ROOT)]
    cav = prism("cav", cprof, xa, xb, 'X')
    ob = csg(outer, sub=[cav])
    # leaf (attached to the block at v = NIP_V_ROOT) with two contact pads and a stud hole
    lx0, lx1 = xa + NIP_SLIT, xb - NIP_SLIT
    leaf = box("leaf", lx0, lx1, LEAF_U0, LEAF_U0 + LEAF_T, NIP_V_TIP, NIP_V_ROOT + 0.5)
    pads = [box("pad%d" % s, NIP_X + s * 6.0 - 1.5, NIP_X + s * 6.0 + 1.5, LEAF_U0 - PAD_H, LEAF_U0 + 0.01, -2.0, 2.0) for s in (-1, 1)]
    ob = csg(ob, add=[leaf] + pads)
    sub = [cyl("sh", (NIP_X, 0.0), 3.5, LEAF_U0 - 1, LEAF_U0 + LEAF_T + 1, 'Y', n=24),
           cyl("sw", (NIP_X, 0.0), 4.0, SHELL_U0 - 1, uo + 1, 'Y', n=32)]
    for k, x in enumerate(NIP_SCREW_X):
        sub.append(cyl("s%d" % k, (x, NIP_SCREW_V), 1.7, -1.0, uo + 1, 'Y', n=16))
        sub.append(cyl("c%d" % k, (x, NIP_SCREW_V), CBORE_R, uo - CBORE_D, uo + 1, 'Y', n=20))
    ob = csg(ob, sub=sub)
    xform(ob, nip_frame())
    Vw = Vector((0, NIP_V[0], NIP_V[1]))
    R = Vw.rotation_difference(Vector((0, 0, -1))).to_matrix()
    return finish(ob, "PRT_nip_cover", 'PRT', COL_B, "PIV_tilt", stl="nip_cover", print_rot=R, infill=30, supports="no",
                  orient="screw-block end on the bed; leaf, end walls and shell grow up as vertical walls; skirt bridges at the top")


FW_SLOT_X = (WEB_X1, FW_HUB_X1 + 1.0)   # clamp halves are cantilevers off the web (x 14.1..25)
FW_BOLT_X = 19.5            # pinch-bolt plane: over the shaft (ends at x 21), 3.9 mm above the web for the L-key leg
FW_BOLT_OFF = 6.5
FW_BOLT_L = 20.0            # M3 x 20 socket head: passes fully through the nut, tip stays inside the hub
FW_HEAD_H = 3.0
FW_T_SURF = math.sqrt(FW_HUB_R ** 2 - FW_BOLT_OFF ** 2)     # 11.83: hub surface along the bolt line
FW_T_HEAD = FW_T_SURF - FW_HEAD_H - 0.3                     # head seat (under-head face), 0.3 below flush
FW_T_NUT = FW_T_HEAD                                        # nut seat on the opposite side (point-symmetric)


def build_flywheel():
    """Ø70 PLA flywheel. The web is on the MOTOR side (x 9..14.1, R36, doubling as the -X flange), so the cup between hub
    and rim opens toward +X: with the cover off (tilt 45) a 2.5 mm L-key goes in along a pinch-bolt axis and its long leg
    leaves +X past the rim. 2-slot clamping hub (halves cantilever off the web), two point-symmetric M3 x 20 pinch bolts
    with nuts in traps (self-balancing), 12 mm on the D-shaft."""
    wy, wz = W_P, T_Z + W_Q
    web = cyl("PRT_flywheel", (wy, wz), WHEEL_FLANGE_R, HUB_X0, WEB_X1, 'X', n=160)
    rim = cyl("rim", (wy, wz), WHEEL_R, WEB_X1 - 0.01, WHEEL_X1, 'X', n=160)
    flR = cyl("flR", (wy, wz), WHEEL_FLANGE_R, WHEEL_X1 - 1.6, WHEEL_X1, 'X', n=160)
    # 45 deg underside under the +X flange (it is the top flange in print orientation)
    flC = loft("flC", circle((wy, wz), WHEEL_R - 0.01, 160), circle((wy, wz), WHEEL_FLANGE_R, 160), WHEEL_X1 - 2.6, WHEEL_X1 - 1.59, 'X')
    ob = csg(web, add=[rim, flR, flC])
    ob = csg(ob, sub=[cyl("ri", (wy, wz), WHEEL_R - FW_RIM_T, WEB_X1, WHEEL_X1 + 1, 'X', n=128)])
    hub = cyl("hub", (wy, wz), FW_HUB_R, HUB_X0, FW_HUB_X1, 'X')
    bevel(hub, 0.6)
    ob = csg(ob, add=[hub])
    sub = []
    rb, flat = 2.55, 2.0
    dpts = [(wy + rb * math.cos(math.radians(a)), wz + rb * math.sin(math.radians(a))) for a in range(0, 360, 10) if rb * math.cos(math.radians(a)) < flat]
    dpts += [(wy + flat, wz - math.sqrt(rb * rb - flat * flat)), (wy + flat, wz + math.sqrt(rb * rb - flat * flat))]
    sub.append(prism("bore", hull2d(dpts), HUB_X0 - 1, FW_HUB_X1 + 1, 'X'))
    sub.append(cone("bch", (wy, wz), 3.3, 2.0, HUB_X0 - 0.01, HUB_X0 + 1.3, 'X', n=32))        # lead-in chamfer
    for s in (-1, 1):
        # radial slot (plane through the axis, along +-q) and the tangential pinch bolt crossing it
        sub.append(box("sl%d" % s, FW_SLOT_X[0], FW_SLOT_X[1], wy - 0.8, wy + 0.8, min(wz, wz + s * (FW_HUB_R + 1)), max(wz, wz + s * (FW_HUB_R + 1))))
        bz = wz + s * FW_BOLT_OFF
        sub.append(cyl("bh%d" % s, (FW_BOLT_X, bz), 1.7, wy - FW_HUB_R - 1, wy + FW_HUB_R + 1, 'Y', n=16))
        head_end = s          # point-symmetric: head on +p for the upper bolt, on -p for the lower
        yh = wy + head_end * (FW_HUB_R + 1)
        ych = wy + head_end * FW_T_HEAD
        sub.append(cyl("cb%d" % s, (FW_BOLT_X, bz), 3.1, min(yh, ych), max(yh, ych), 'Y', n=20))
        # counterbore and nut trap open radially outward (U-channels): no knife-edge where they leave the hub cylinder
        sub.append(box("cbu%d" % s, FW_BOLT_X - 3.1, FW_BOLT_X + 3.1, min(yh, ych), max(yh, ych), min(bz, bz + s * 10), max(bz, bz + s * 10)))
        ynt = wy - head_end * FW_T_NUT
        ynt2 = wy - head_end * (FW_HUB_R + 1)
        sub.append(prism("nt%d" % s, hexagon((FW_BOLT_X, bz), NUT_AF, 0.0), min(ynt, ynt2), max(ynt, ynt2), 'Y'))
        sub.append(box("ntu%d" % s, FW_BOLT_X - NUT_AF / 2, FW_BOLT_X + NUT_AF / 2, min(ynt, ynt2), max(ynt, ynt2), min(bz, bz + s * 10), max(bz, bz + s * 10)))
    for k in range(6):
        a = math.radians(21.0 + 60 * k)
        sub.append(cyl("lw%d" % k, (wy + 21.5 * math.cos(a), wz + 21.5 * math.sin(a)), 4.5, HUB_X0 - 1, WEB_X1 + 1, 'X'))
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_flywheel", 'PRT', COL_A, "PIV_flywheel", stl="flywheel", print_rot=R_NX_DOWN, infill=100, supports="no",
                  orient="motor-side web face on the bed; rim and hub grow up (top flange has a 45 deg underside)",
                  notes="wrap 12-15 mm hockey tape on the 12.8 mm land")


def crush_rib(r0, r1, ang_from_s, w=1.6):
    """small radial rib (launcher frame) around the motor axis WC, angle measured from S_DIR"""
    a = math.atan2(S_DIR[1], S_DIR[0]) + math.radians(ang_from_s)
    c, s_ = math.cos(a), math.sin(a)
    t = (-s_, c)
    pts = [(WC[0] + r * c + h * t[0], WC[1] + r * s_ + h * t[1]) for (r, h) in ((r0, -w / 2), (r1, -w / 2), (r1, w / 2), (r0, w / 2))]
    return pts


def nacelle_profile():
    return hull_circles([(WC, NAC_RW), ((0.0, 0.0), NAC_RT)], 128)


def build_nacelle():
    """Motor nacelle + left trunnion in one part: capsule from the motor axis to the tilt axis. Holds the motor
    (front plate sandwiched by the 4 motor screws), carries the leads up an internal duct into the trunnion bore,
    and ends in the thrust collar and left journal."""
    x0, x1 = NAC_X0, X_MF + NAC_PLATE_T
    ob = lprism("PRT_nacelle", nacelle_profile(), x0, x1)
    bevel(ob, EB)
    col = lcyl("col", (0, 0), COLLAR_R, ARM_L_X[1] + 0.2, x0 + 0.5)
    jr = lcyl("jr", (0, 0), JOURNAL_R, ARM_L_X[0] + 0.5, ARM_L_X[1] + 0.21)
    bevel(jr, 0.6)
    ob = csg(ob, add=[col, jr])
    rr = MOTOR_D / 2 + BORE_CLR
    S, N = S_DIR, N_DIR
    slot = [vadd(WC, N, 7.0), vadd(vadd(WC, S, -27.0), N, 7.0), vadd(vadd(WC, S, -27.0), N, -7.0), vadd(WC, N, -7.0)]
    sub = [lcyl("bore", WC, rr, x0 - 1, X_MF, n=128), lcyl("sh", WC, 6.0, X_MF - 1, x1 + 1),
           lprism("slot", slot, x0 - 1, -56.0),
           lprism("duct", hull_circles([(vadd(WC, S, -20.0), 7.5), (vadd((0, 0), S, 2.0), 7.5)], 32), -76.0, -56.0),
           lcyl("tb", (0, 0), TUBE_BORE_R, ARM_L_X[0] - 1, -56.0),
           loft("tbc", to_world_yz(circle((0, 0), TUBE_BORE_R + 4.0, 48)), to_world_yz(circle((0, 0), TUBE_BORE_R - 0.01, 48)),
                ARM_L_X[0] + 0.5 - 0.01, ARM_L_X[0] + 0.5 + 4.0, 'X')]
    for k, c in enumerate(MOTOR_SCREWS):
        sub.append(lcyl("ms%d" % k, c, 1.7, X_MF - 1, x1 + 1, n=16))
    for k, c in enumerate(NAC_SCREWS):
        sub.append(lcyl("ns%d" % k, c, 1.25, X_MF - 6, x1 + 1, n=16))
    for k, c in enumerate(ENC_SCREWS):
        sub.append(lcyl("es%d" % k, c, 1.25, x0 - 1, x0 + 10, n=16))
    for xc in (-16.0, -34.0, -52.0):   # diamond vents under the can (45 deg edges in print orientation)
        sub.append(prism("vw%d" % int(xc), [(xc - 7, W_P), (xc, W_P - 6), (xc + 7, W_P), (xc, W_P + 6)], T_Z + W_Q - NAC_RW - 2, T_Z + W_Q - 8, 'Z'))
    ob = csg(ob, sub=sub)
    # three line-to-line crush ribs at the rear of the can bore (printed holes run ~0.1 small, so they crush to centre the can)
    ribs = [lprism("cr%d" % k, crush_rib(MOTOR_D / 2, rr + 0.4, 120.0 * k), -MOTOR_L + 1.0, -MOTOR_L + 13.0) for k in range(3)]
    ob = csg(ob, add=ribs)
    return finish(ob, "PRT_nacelle", 'PRT', COL_B, "PIV_tilt", stl="nacelle", print_rot=R_PX_DOWN, infill=25, supports="no",
                  orient="front plate on the bed, journal up (duct roof bridges 15 mm)")


def plink_frame():
    S = S_DIR
    return frame((NAC_X0, W_P, T_Z + W_Q), (0, S[1], -S[0]), (0, S[0], S[1]), (1, 0, 0))


def plink_holes_world():
    M = plink_frame()
    return [(M @ Vector((sx * 8.0, sy * 8.0, 0.0))) for sx in (-1, 1) for sy in (-1, 1)]


def cap_profile():
    return hull_circles([(WC, NAC_RW), (vadd(WC, S_DIR, -26.0), 8.0)], 96)


def build_encoder_cap():
    x0 = NAC_X0
    rr = MOTOR_D / 2 + BORE_CLR
    disc = lprism("PRT_encoder_cap", cap_profile(), x0 - 4, x0)
    bevel(disc, EB)
    sp_o = lcyl("spo", WC, rr - 0.25, x0 - 0.01, x0 + 4.5, n=128)
    ribs = [lprism("rb%d" % k, crush_rib(rr - 0.5, rr, 120.0 * k), x0 + 0.5, x0 + 4.5) for k in range(3)]
    sp_o = csg(sp_o, add=ribs)
    sp_i = lcyl("spi", WC, 16.0, x0 - 1, x0 + 5, n=96)
    spig = csg(sp_o, sub=[sp_i])
    pegs = [cyl("pg%d" % i, (h.y, h.z), 1.15, x0 - 0.01, x0 + 1.5, 'X', n=16) for i, h in enumerate(plink_holes_world())]
    ob = csg(disc, add=[spig] + pegs)
    S, N = S_DIR, N_DIR
    cut = [vadd(vadd(WC, S, -12.0), N, 7.0), vadd(vadd(WC, S, -30.0), N, 7.0), vadd(vadd(WC, S, -30.0), N, -7.0), vadd(vadd(WC, S, -12.0), N, -7.0)]
    sub = [lprism("slot", cut, x0 - 0.5, x0 + 6)]
    for k, c in enumerate(ENC_SCREWS):
        sub.append(lcyl("eh%d" % k, c, 1.7, x0 - 5, x0 + 1, n=16))
        sub.append(cone("ec%d" % k, (c[0], T_Z + c[1]), 3.4, 1.7, x0 - 4.01, x0 - 4 + 1.7, 'X', n=24))
    ob = csg(ob, sub=sub)
    return finish(ob, "PRT_encoder_cap", 'PRT', COL_B, "PIV_tilt", stl="encoder_cap", print_rot=R_NX_DOWN, infill=40, supports="no",
                  orient="back face on the bed, spigot and pegs up")


def build_encoder_jig():
    """Glue jig (tool): plugs into the nacelle bore from the rear, holds the magnet centred on the shaft end
    in a Ø6.1 x 2.0 pocket while the glue cures."""
    x0 = NAC_X0
    plug = lcyl("TOOL_encoder_jig", WC, JIG_PLUG_R, x0 - 0.01, -MOTOR_L, n=128)      # relieved: NOT the datum
    spg = lcyl("spg", WC, JIG_SPIGOT_D / 2, -MOTOR_L - 0.01, -MOTOR_L + JIG_SPIGOT_L, n=64)   # datum: motor's Ø8 access hole
    fl = lprism("fl", hull_circles([(WC, 22.0), (vadd(WC, N_DIR, 26.0), 6.0)], 64), x0 - 4.0, x0)
    bevel(fl, EB)
    ob = csg(plug, add=[fl, spg])
    sub = [lcyl("pk", WC, 3.05, -MOTOR_L - (MAGNET_T - REAR_SHAFT_RECESS), -MOTOR_L + JIG_SPIGOT_L + 0.5, n=32),
           lcyl("vt", WC, 1.0, x0 - 5, -MOTOR_L + 1, n=12),
           lcyl("gr", vadd(WC, N_DIR, 26.0), 3.0, x0 - 5, x0 + 1, n=20)]
    ob = csg(ob, sub=sub)
    return finish(ob, "TOOL_encoder_jig", 'TOOL', COL_B, "PIV_tilt", stl="encoder_jig", print_rot=R_NX_DOWN, infill=40, supports="no",
                  orient="flange on the bed, plug up (magnet pocket open at the top)")


# =====================================================================================
# PURCHASED PLACEHOLDERS
# =====================================================================================


def import_stl(path, name):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=path)
    ob = [o for o in bpy.data.objects if o not in before][0]
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    tmp().objects.link(ob)
    ob.name = name
    return ob


def build_purchased():
    # MotorGo Axis (exact STL)
    mg = import_stl(os.path.join(REF, "mg_axis.stl"), "BUY_motorgo_axis")
    M = frame((MG_X0, MG_PCB_Y, MG_Z0), (-1, 0, 0), (0, 0, -1), (0, -1, 0))
    xform(mg, M)
    finish(mg, "BUY_motorgo_axis", 'BUY', COL['pcb'], None, part="MotorGo Axis (reference/mg_axis.stl)")
    # USB-C plug overmold + 25 mm straight
    y0 = MG_PCB_Y - USB_STEP[2] - 0.2
    pl = prism("BUY_usbc_plug", rrect(USB_W[0] - 3.5, USB_W[0] + 3.5, USB_W[1] - 6.25, USB_W[1] + 6.25, 2.5), y0 - 25, y0, 'Y')
    cb = cyl("cb", (USB_W[0], USB_W[1]), 2.0, -BASE_HALF - 30, y0 - 24.9, 'Y')
    finish(csg(pl, add=[cb]), "BUY_usbc_plug", 'BUY', COL['black'], None, part="USB-C cable plug (12.5 x 7 overmold)")
    # Plink encoder (exact STL), JST pointing up the lead slot toward the tilt axis
    pk = import_stl(os.path.join(REF, "plink_encoder.stl"), "BUY_plink_encoder")
    xform(pk, plink_frame())
    finish(pk, "BUY_plink_encoder", 'BUY', COL['pcb'], "PIV_tilt", part="Plink MT6701 encoder")
    # motor: lead block on the rear end, turned to point at the tilt axis
    wy, wz = W_P, T_Z + W_Q
    body = cyl("BUY_motor", (wy, wz), MOTOR_D / 2, -MOTOR_L, X_MF, 'X', n=96)
    bevel(body, 0.8)
    shaft = cyl("sh", (wy, wz), 2.5, X_MF - 0.01, X_MF + SHAFT_LEN - 14, 'X', n=24)
    rb, fl = 2.5, 1.95
    dp = [(wy + rb * math.cos(math.radians(a)), wz + rb * math.sin(math.radians(a))) for a in range(0, 360, 10) if rb * math.cos(math.radians(a)) < fl]
    dp += [(wy + fl, wz - math.sqrt(rb * rb - fl * fl)), (wy + fl, wz + math.sqrt(rb * rb - fl * fl))]
    dsh = prism("dsh", hull2d(dp), X_MF + SHAFT_LEN - 14.01, X_MF + SHAFT_LEN, 'X')
    S, N = S_DIR, N_DIR
    blkp = [vadd(vadd(WC, S, -10.0), N, 6.0), vadd(vadd(WC, S, -(MOTOR_D / 2 + 7)), N, 6.0), vadd(vadd(WC, S, -(MOTOR_D / 2 + 7)), N, -6.0), vadd(vadd(WC, S, -10.0), N, -6.0)]
    blk = lprism("blk", blkp, -MOTOR_L + 0.5, -MOTOR_L + 12.5)
    rec = cyl("rec", (wy, wz), REAR_ACCESS_D / 2, -MOTOR_L - 1, -MOTOR_L + REAR_SHAFT_RECESS + 1.5, 'X', n=24)
    rs = cyl("rs", (wy, wz), 2.5, -MOTOR_L + REAR_SHAFT_RECESS, -MOTOR_L + REAR_SHAFT_RECESS + 1.6, 'X', n=24)
    ob = csg(body, add=[shaft, dsh, blk])
    ob = csg(ob, sub=[rec])
    ob = csg(ob, add=[rs])
    finish(ob, "BUY_motor", 'BUY', COL['motor'], "PIV_tilt", part="XTEAM XTI-3674 1900KV")
    mag = cyl("BUY_magnet", (wy, wz), MAGNET_D / 2, -MOTOR_L + REAR_SHAFT_RECESS - MAGNET_T, -MOTOR_L + REAR_SHAFT_RECESS, 'X', n=24)
    finish(mag, "BUY_magnet", 'BUY', COL['magnet'], "PIV_flywheel", part="Ø6 x 2.5 diametric magnet (glued to rear shaft)")
    # battery + adapter
    b = BATT
    bat = box("BUY_battery", b[0], b[1], b[2], b[3], b[4], ADAPTER[4])
    bevel(bat, 3.0, seg=2)
    stem = box("stem", ADAPTER[0] + 10.5, ADAPTER[1] - 10.5, ADAPTER[2] + 8, ADAPTER[3] - 8, ADAPTER[4] - 0.5, b[5])   # rails, between the corner holes
    finish(csg(bat, add=[stem]), "BUY_battery", 'BUY', COL['dewalt'], None, part="DeWalt 20V battery envelope 115 x 76 x 70")
    a = ADAPTER
    ad = box("BUY_dewalt_adapter", a[0], a[1], a[2], a[3], a[4], a[5])
    bevel(ad, 2.0)
    wedge = prism("wd", [(a[1] - 18, a[4] - 1), (a[1] + 1, a[4] - 1), (a[1] + 1, a[4] + 12)], a[2] - 1, a[3] + 1, 'Y')
    holes = [cyl("adh%d" % i, h, 1.7, a[4] - 1, a[5] + 1, n=12) for i, h in enumerate(ADAPTER_HOLES)]
    # Ø6.5 x 5.5 counterbore on the battery-side face of each corner hole (drill it if the adapter has none) for the nut
    holes += [cyl("adc%d" % i, h, 3.25, a[4] - 1, a[4] + ADAPTER_CB, n=24) for i, h in enumerate(ADAPTER_HOLES)]
    finish(csg(ad, sub=[wedge] + holes), "BUY_dewalt_adapter", 'BUY', COL['dewalt'], None, part="DeWalt 20V battery adapter")
    # buck converter (finned)
    bx, by = BUCK_C
    base = box("BUY_buck", bx - 36.9, bx + 36.9, by - 32.5, by + 32.5, FLOOR_T + 4, FLOOR_T + 9)
    ears = [box("ear%d" % s, bx - 9, bx + 9, min(by + s * 32.5, by + s * 36.9), max(by + s * 32.5, by + s * 36.9), FLOOR_T + 4, FLOOR_T + 7) for s in (-1, 1)]
    fins = [box("fin%d" % k, bx - 36.9, bx + 36.9, by - 31 + k * 7.7, by - 29 + k * 7.7, FLOOR_T + 8.9, FLOOR_T + 4 + 31) for k in range(9)]
    eh = [cyl("eh%d" % s, (bx, by + s * 33.4), 1.9, 0, 20, n=12) for s in (-1, 1)]
    bk = csg(base, add=ears + fins)
    bk = csg(bk, sub=eh)
    finish(bk, "BUY_buck_12v", 'BUY', COL['metal'], None, part="12V buck converter, finned 73.8 x 73.8 x 31")
    # servo controller board
    c = CTRL
    zb = FLOOR_T + CTRL_BOSS_H
    pcb = box("BUY_servo_controller", c[0], c[1], c[2], c[3], zb, zb + 1.6)
    cx, cy = 0.5 * (c[0] + c[1]), 0.5 * (c[2] + c[3])
    holes = [cyl("ch%d%d" % (sx, sy), (cx + sx * 17.5, cy + sy * 25.5), 1.6, zb - 1, zb + 3, n=12) for sx in (-1, 1) for sy in (-1, 1)]
    pcb = csg(pcb, sub=holes)
    comps = []
    for s in (-1, 1):
        y_edge = c[3] if s > 0 else c[2]
        comps.append(box("ports%d" % s, c[0] + 7.5, c[1] - 7.5, min(y_edge - s * 6, y_edge + s * 1.5), max(y_edge - s * 6, y_edge + s * 1.5), zb + 1.6, zb + 7.5))
    comps.append(box("usba", c[0] - 0.5, c[0] + 14, cy - 18, cy - 4, zb + 1.6, zb + 8.5))
    comps.append(box("sw", c[1] - 8, c[1] + 0.5, cy - 8, cy + 6, zb + 1.6, zb + 6))
    comps.append(box("term", c[1] - 9, c[1] + 0.5, c[3] - 17, c[3] - 7, zb + 1.6, zb + 11))
    comps.append(cyl("cap", (cx, cy + 6), 4.0, zb + 1.6, zb + 14, n=20))
    comps.append(box("under", c[0] + 8, c[1] - 8, c[2] + 9, c[3] - 9, zb - 2, zb + 0.01))
    finish(join("BUY_servo_controller", [pcb] + comps), "BUY_servo_controller", 'BUY', COL['white_pcb'], None,
           part="Hiwonder bus servo controller 58 x 42")


# =====================================================================================
# FASTENERS AND CABLES
# =====================================================================================


def screw(name, pos, direction, length, pivot=None, head_d=5.5, head_h=3.0, csk=False):
    """M3 screw: head at pos, shank along `direction`. csk=True models a flush 90 deg countersunk head."""
    d = Vector(direction).normalized()
    shank = cyl(name, (0, 0), 1.5, -length, 0, n=12)
    if csk:
        head = cone(name + "h", (0, 0), 1.49, 3.0, -1.6, -0.05, n=16)
    else:
        head = cyl(name + "h", (0, 0), head_d / 2, 0.05, head_h, n=16)
    ob = csg(shank, add=[head])                     # one manifold solid (Manifold-checkable)
    rot = Vector((0, 0, 1)).rotation_difference(-d).to_matrix().to_4x4()
    xform(ob, Matrix.Translation(pos) @ rot)
    return finish(ob, name, 'FST', COL['screw'], pivot, part="M3 x %d%s" % (round(length), " countersunk" if csk else ""))


def nut(name, pos, direction, pivot=None):
    d = Vector(direction).normalized()
    ob = prism(name, hexagon((0, 0), 5.5, 0.0), 0, 2.4)
    rot = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
    xform(ob, Matrix.Translation(pos) @ rot)
    return finish(ob, name, 'FST', COL['screw'], pivot, part="M3 nut")


def lpt(x, c):
    return (x, c[0], T_Z + c[1])


def build_fasteners():
    wy, wz = W_P, T_Z + W_Q
    # motor face: heads in the counterbores inside the guard, shank through wall + nacelle plate into the motor
    for k, c in enumerate(MOTOR_SCREWS):
        screw("FST_motor_%d" % k, lpt(X_BODY_IN - 2.0, c), (-1, 0, 0), 10, "PIV_tilt", head_h=2.0)
    for k, c in enumerate(NAC_SCREWS):
        screw("FST_nacelle_%d" % k, lpt(X_BODY_IN - 2.0, c), (-1, 0, 0), 12, "PIV_tilt", head_h=2.0)
    for i, c in enumerate(COVER_SCREWS):
        screw("FST_cover_%d" % i, lpt(X_COVER_OUT, c), (-1, 0, 0), 12, "PIV_tilt", csk=True)
    for i, c in enumerate(JP_SCREWS):
        screw("FST_jplate_%d" % i, lpt(X_COVER_OUT, c), (-1, 0, 0), 12, "PIV_tilt", csk=True)
    screw("FST_hinge", lpt(X_BODY_OUT, HINGE), (1, 0, 0), 30, "PIV_tilt", csk=True)
    # compliant nip: hex-head stud (moves with the backplate), captive nut in the thumbwheel, 2 cover screws
    Uw = (0, NIP_U[0], NIP_U[1])
    NM = nip_frame()
    screw("FST_nip_stud", lpt(NIP_X, JACK_PT), Uw, STUD_L, "PIV_hood", head_d=STUD_HEAD_AF, head_h=STUD_HEAD_K)
    nut("FST_nip_nut", tuple(NM @ Vector((NIP_X, TW_NUT_U[0], 0.0))), Uw, "PIV_tilt")
    uo = SHELL_U0 + SHELL_T
    for k, x in enumerate(NIP_SCREW_X):
        screw("FST_nip_cover_%d" % k, tuple(NM @ Vector((x, uo - CBORE_D, NIP_SCREW_V))), (0, -NIP_U[0], -NIP_U[1]), 16, "PIV_tilt", head_h=2.5)
    for i, c in enumerate(ENC_SCREWS):
        screw("FST_enc_%d" % i, lpt(NAC_X0 - 4, c), (1, 0, 0), 12, "PIV_tilt", csk=True)
    # flywheel pinch bolts (point-symmetric pair)
    for s in (-1, 1):
        hy = wy + s * FW_T_HEAD
        screw("FST_fw_bolt_%d" % (s + 1), (FW_BOLT_X, hy, wz + s * FW_BOLT_OFF), (0, -s, 0), FW_BOLT_L, "PIV_flywheel", head_h=FW_HEAD_H)
        nut("FST_fw_nut_%d" % (s + 1), (FW_BOLT_X, wy - s * FW_T_NUT, wz + s * FW_BOLT_OFF), (0, -s, 0), "PIV_flywheel")
    for side, (x0, x1) in (("L", ARM_L_X), ("R", ARM_R_X)):
        for s in (-1, 1):
            screw("FST_cap_%s%d" % (side, s), (0.5 * (x0 + x1), s * CAP_SCREW_Y, PLATE_Z0 + PLATE_T), (0, 0, -1), 45, "PIV_pan", csk=True)
    for i, (x, y) in enumerate(ARM_FOOT_HOLES_L + ARM_FOOT_HOLES_R):
        screw("FST_foot_%d" % i, (x, y, TT_Z1 + FOOT_T - CBORE_D), (0, 0, -1), 10, "PIV_pan", head_h=2.5)
    vb = SERVO_W / 2 + 0.3 + 2.4 + 1.6
    xcv = TILT_CLAMP_X + 0.2 + SVC_W
    for s in (-1, 1):
        screw("FST_tilt_clamp_%d" % (s + 1), (xcv, s * vb, T_Z + CLAMP_BOSS_U), (-1, 0, 0), 16, "PIV_pan", csk=True)
    w_bot = SERVO_TOP_W - SERVO_H - 4.0 - FSH_T
    for k, s_ in enumerate((-1, 1)):
        p_ = M_FEED @ Vector((CLAMP_BOSS_U, s_ * vb, w_bot))
        screw("FST_feeder_clamp_%d" % k, tuple(p_), (0, 0, 1), 16, "PIV_pan", csk=True)
    for i, (x, y) in enumerate(B_BOSSES):
        screw("FST_floor_%d" % i, (x, y, 0), (0, 0, 1), 12, None, csk=True)
    for i, (x, y) in enumerate(ADAPTER_HOLES):
        screw("FST_adapter_%d" % i, (x, y, BASE_H), (0, 0, -1), ADAPTER_SCREW_L, None, csk=True)
        nut("FST_adapter_nut_%d" % i, (x, y, BASE_H - ADAPTER_SCREW_L + 0.3), (0, 0, 1), None)   # tip 0.3 past the nut


def cable(name, pts, r, color, pivot=None):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    ob = bpy.data.objects.new(name, cu)
    tmp().objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    mo = bpy.data.objects.new(name, me)
    tmp().objects.link(mo)
    return finish(mo, name, 'CAB', color, pivot, part="cable route")


def build_cables():
    xl = ARM_L_X[0]
    xb = xl - BONNET_DEPTH + 3.0
    S, N = S_DIR, N_DIR
    # launcher (tilt frame): three phase leads + encoder cable up the nacelle duct, into the trunnion bore, out of the journal end.
    # Motor leads are cut to ~55 mm and joined (staggered, heat-shrunk) inside the straight bore at x -60..-90.
    for k in range(3):
        off = (k - 1) * 3.6
        a = vadd(vadd(WC, S, -(MOTOR_D / 2 + 5)), N, off)
        b = vadd(vadd(WC, S, -40.0), N, off)
        c = vadd(vadd((0.0, 0.0), S, 1.0), N, off * 0.6)
        cable("CAB_phase_tilt_%d" % k, [lpt(-66, a), lpt(-68, b), lpt(-68, c), lpt(-90, c), lpt(xb, c)], 1.9, COL['cable_yel'], "PIV_tilt")
    a = vadd(vadd(WC, S, -11.0), N, 5.5)
    cable("CAB_encoder_tilt", [lpt(NAC_X0 + 3.5, a), lpt(NAC_X0 + 2.5, vadd(vadd(WC, S, -26.0), N, 5.5)), lpt(-70, vadd(vadd(WC, S, -40.0), N, 5.5)),
                               lpt(-70, vadd((0.0, 0.0), N, 5.0)), lpt(xb, vadd((0.0, 0.0), N, 5.0))], 1.3, COL['cable_wht'], "PIV_tilt")
    # pan stage, left: bonnet down to the turntable groove and the hub bore
    for k in range(4):
        y = -4.5 + 3 * k
        cable("CAB_launcher_bundle_%d" % k, [(xb, y, T_Z - 2), (xb, y, T_Z - 30), (xb, y, TT_Z1 - 3), (-30, y, TT_Z1 - 3),
                                             (-4, y * 0.5, TT_Z1 - 3), (0, y * 0.4, TT_Z0 - 10), (0, y * 0.4, 60)], 1.8 if k < 3 else 1.3,
              COL['cable_yel'] if k < 3 else COL['cable_wht'], "PIV_pan")
    # feeder servo bus: hub -> left groove -> bonnet -> cap notch -> plate underside groove -> feeder pocket channel
    g = PLATE_GROOVE
    zc = T_Z + CAP_H - 2.6          # inside the cap notch (and the bonnet), then up into the plate groove
    cable("CAB_bus_feeder", [(-2, 3, 60), (-2, 3, TT_Z1 - 3), (xb, 3, TT_Z1 - 3), (xb - 1, -7.5, TT_Z1 + 8), (xb - 1, -7.5, zc),
                             (ARM_L_X[0] + 3.0, -7.5, zc), (ARM_L_X[0] + 7.0, -7.5, PLATE_Z0 + 1.5), (g[1][0], g[1][1], PLATE_Z0 + 1.5), (g[2][0], g[2][1], PLATE_Z0 + 1.5),
                             (g[3][0], g[3][1], PLATE_Z0 + 1.5), (g[4][0], g[4][1], PLATE_Z0 - 2), (g[4][0], g[4][1] + 1.0, PLATE_Z0 - 44)], 1.4, COL['cable_wht'], "PIV_pan")
    # tilt servo bus: hub -> right groove -> right arm cover -> under the servo housing -> pocket flange notch
    xr = ARM_R_X[1] + 4
    cable("CAB_bus_tilt", [(3, 0, 60), (3, 0, TT_Z1 - 3), (xr, 0, TT_Z1 - 3), (xr, 0, COVER_R_TOP - 2), (ARM_R_X[1] + 6, 0, T_Z - 35),
                           (ARM_R_X[1] + 46, 0, T_Z - 35)], 1.4, COL['cable_wht'], "PIV_pan")
    # base: service loop to the MotorGo, bus to controller and pan servo, 12 V, UART
    cable("CAB_loop_motor", [(0, 0, 60), (0, -10, 40), (-15, -30, 40), (-40, -55, 66), (-60, -70, 72)], 2.0, COL['cable_yel'])
    cable("CAB_bus_ctrl", [(3, 0, 60), (10, 10, 45), (60, 20, 20), (85, 17, 14)], 1.4, COL['cable_wht'])
    cable("CAB_bus_pan_servo", [(85, 81, 14), (40, 90, 20), (0, 96, 40)], 1.4, COL['cable_wht'])
    cable("CAB_12v_in", [(ADAPTER[0] - 0.5, -60, 72), (-5, -60, 72), (-20, -30, 30), (BUCK_C[0] + 37.5, BUCK_C[1], 14)], 1.8, COL['cable_red'])
    cable("CAB_12v_mg", [(BUCK_C[0] + 37.5, BUCK_C[1] + 6, 14), (-36, -40, 30), (-36, -66, 57)], 1.6, COL['cable_red'])
    cable("CAB_12v_ctrl", [(BUCK_C[0] + 37.5, BUCK_C[1] - 6, 14), (20, 10, 14), (70, 60, 14), (CTRL[1] - 4, CTRL[3] - 12, 17)], 1.6, COL['cable_red'])
    # MotorGo UART header (top edge, behind the board) -> floor clips -> servo controller UART pins (~230 mm, 4-wire)
    cable("CAB_uart", [(-40, -75, 60), (-40, -60, 30), (UART_CLIPS[0][0], UART_CLIPS[0][1], FLOOR_T + 3.2),
                       (UART_CLIPS[1][0], UART_CLIPS[1][1], FLOOR_T + 3.2), (CTRL[0] + 3, 0.5 * (CTRL[2] + CTRL[3]) - 12, FLOOR_T + CTRL_BOSS_H + 4)],
          1.2, COL['cable_blk'])


# =====================================================================================
# BUILD
# =====================================================================================


def build():
    _scene_setup()
    make_pivots()
    build_base_shell()
    build_base_floor()
    build_pan_hub()
    build_pan_pinion()
    build_turntable()
    build_spine()
    for s in ("L", "R"):
        build_arm(s)
        build_cap(s)
    build_bonnet()
    build_cover_r()
    build_tilt_servo_cover()
    build_feeder_shroud()
    build_feeder_plate()
    build_feeder_disc()
    build_hopper()
    build_hopper_lid()
    build_launcher_body()
    build_journal_plate()
    build_launcher_cover()
    build_hood()
    build_thumbwheel()
    build_nip_cover()
    build_flywheel()
    build_nacelle()
    build_encoder_cap()
    build_encoder_jig()
    servo_set("pan", M_PAN, None, "PIV_pan_pinion", "pan")
    servo_set("tilt", M_TILT, "PIV_pan", "PIV_tilt")
    servo_set("feeder", M_FEED, "PIV_pan", "PIV_feeder")
    build_purchased()
    build_fasteners()
    build_cables()
    for o in list(TMP.objects):
        _kill(o)
    bpy.data.collections.remove(TMP)
    globals()["TMP"] = None
    for ob in bpy.data.objects:
        if ob.type == 'MESH':
            for p in ob.data.polygons:
                p.use_smooth = False
    jig = bpy.data.objects["TOOL_encoder_jig"]
    jig.hide_render = True
    jig.hide_viewport = True
    sc = bpy.context.scene
    sc["hood_gap_nominal"] = HOOD_GAP
    sc["hood_gap_range"] = "%.1f..%.1f mm at BDC (hinge %.2f..%.2f deg)" % (HOOD_GAP_MIN, HOOD_GAP_MAX, math.degrees(EPS_OPEN), math.degrees(EPS_CLOSE))


# =====================================================================================
# POSE, STL EXPORT
# =====================================================================================


def lkey(name, s, theta_deg, short=18.0, long=60.0, r=1.3):
    """2.5 mm L-key in pinch bolt s (+1 / -1) at home pose (world), parented to PIV_flywheel. Short leg 2 mm into the
    socket and out along the bolt axis; long leg leaves along cos(theta) X + sin(theta) (radial) from the elbow."""
    wy, wz = W_P, T_Z + W_Q
    t0 = FW_T_HEAD + FW_HEAD_H - 2.0
    z = wz + s * FW_BOLT_OFF
    a = Vector((FW_BOLT_X, wy + s * t0, z))
    e = Vector((FW_BOLT_X, wy + s * (t0 + short), z))
    th = math.radians(theta_deg)
    d = Vector((math.cos(th), 0.0, s * math.sin(th)))
    b = e + d * long

    def rod(nm, p, q):
        L = (q - p).length
        c = cyl(nm, (0, 0), r, -0.6 * r, L + 0.6 * r, 'Z', n=12)
        R = Vector((0, 0, 1)).rotation_difference((q - p).normalized()).to_matrix().to_4x4()
        xform(c, Matrix.Translation(p) @ R)
        return c
    ob = csg(rod(name, a, e), add=[rod(name + "b", e, b)])
    ob.name = name
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    bpy.context.scene.collection.objects.link(ob)
    piv = bpy.data.objects["PIV_flywheel"]
    ob.matrix_world = Matrix.Identity(4)
    ob.parent = piv
    ob.matrix_parent_inverse = piv.matrix_world.inverted()
    return ob


def set_pose(pan=0.0, tilt=0.0, wheel=0.0, feeder=0.0, hood=0.0):
    P = bpy.data.objects
    P["PIV_pan"].rotation_euler = (0, 0, math.radians(pan))
    P["PIV_tilt"].rotation_euler = (math.radians(tilt), 0, 0)
    P["PIV_flywheel"].rotation_euler = (math.radians(wheel), 0, 0)
    P["PIV_feeder"].rotation_euler = (0, 0, math.radians(feeder))
    P["PIV_pan_pinion"].rotation_euler = (0, 0, math.radians(-pan))
    P["PIV_hood"].rotation_euler = (hood, 0, 0)
    bpy.context.view_layer.update()


def write_stl(path, tris):
    with open(path, "wb") as f:
        f.write(b"mm_launcher".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            n = (b - a).cross(c - a)
            n = n.normalized() if n.length > 0 else n
            f.write(struct.pack("<12fH", n.x, n.y, n.z, a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z, 0))


def print_mesh_tris(ob):
    """World-frame (home pose) triangles rotated into print orientation, min z = 0, centred in XY."""
    R = Matrix(ob["print_rot"]) if "print_rot" in ob else Matrix.Identity(3)
    me = ob.data
    me.calc_loop_triangles()
    Mw = ob.matrix_world
    vs = [R @ (Mw @ v.co) for v in me.vertices]
    xs = [v.x for v in vs]
    ys = [v.y for v in vs]
    zs = [v.z for v in vs]
    off = Vector((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs)))
    vs = [v + off for v in vs]
    return [(vs[t.vertices[0]], vs[t.vertices[1]], vs[t.vertices[2]]) for t in me.loop_triangles]


def export_stls():
    os.makedirs(STL_DIR, exist_ok=True)
    set_pose(0, 0)
    for f in os.listdir(STL_DIR):
        if f.endswith(".stl"):
            os.remove(os.path.join(STL_DIR, f))
    done = set()
    for cname in ("Printed", "Tools"):
        for ob in bpy.data.collections[cname].objects:
            stl = ob.get("stl")
            if not stl or stl in done:
                continue
            done.add(stl)
            write_stl(os.path.join(STL_DIR, stl + ".stl"), print_mesh_tris(ob))
    return sorted(done)


def store_print_rot():
    for name, info in PARTS.items():
        ob = bpy.data.objects[name]
        if "print_rot" in info:
            R = info["print_rot"]
            ob["print_rot"] = [list(R[i]) for i in range(3)]


# =====================================================================================
# RENDERING
# =====================================================================================


def render_setup(res=(1800, 1350)):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'MATERIAL'
    sh.show_shadows = True
    sh.shadow_intensity = 0.35
    sh.show_cavity = True
    sh.cavity_type = 'BOTH'
    sh.show_object_outline = True
    sh.object_outline_color = (0.15, 0.15, 0.15)
    sh.show_specular_highlight = True
    sc.display.light_direction = (0.45, -0.45, 0.75)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("W")
    sc.world.color = (0.95, 0.95, 0.94)
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'PNG'


def camera(name, loc, target, ortho=None, lens=50):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.clip_start = 5
    cam.data.clip_end = 5000
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = 'PERSP'
        cam.data.lens = lens
    bpy.context.scene.camera = cam
    return cam


def shot(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    render_setup()
    for o in bpy.data.objects:
        if o.type == 'EMPTY':
            o.hide_render = True
    set_pose(0, 0)
    camera("CAM", (520, -610, 470), (0, 0, 175), lens=58); shot(os.path.join(outdir, "iso.png"))
    camera("CAM", (-480, 560, 430), (0, 0, 175), lens=58); shot(os.path.join(outdir, "iso_front_left.png"))
    zc, osc = 152, ORTHO_SCALE
    camera("CAM", (0, 1200, zc), (0, 0, zc), ortho=osc); shot(os.path.join(outdir, "front.png"))
    camera("CAM", (1200, 0, zc), (0, -20, zc), ortho=osc); shot(os.path.join(outdir, "side.png"))
    camera("CAM", (-1200, 0, zc), (0, -20, zc), ortho=osc); shot(os.path.join(outdir, "side_left.png"))
    camera("CAM", (0, 0, 1400), (0, 0.01, 0), ortho=310); shot(os.path.join(outdir, "top.png"))
    camera("CAM", (-330, -560, 230), (-10, 0, 140), lens=45); shot(os.path.join(outdir, "rear_cable_side.png"))
    camera("CAM", (0, -1200, zc), (0, 0, zc), ortho=osc); shot(os.path.join(outdir, "rear.png"))
    camera("CAM", (-260, -330, 120), (12, -20, 140), lens=70); shot(os.path.join(outdir, "pod_underside_nip_cover.png"))
    for pan in (-90, 90):
        for tilt in (0, 45):
            set_pose(pan, tilt)
            camera("CAM", (520, -610, 470), (0, 0, 175), lens=58)
            shot(os.path.join(outdir, "pan%+d_tilt%d.png" % (pan, tilt)))
    set_pose(0, 45)
    camera("CAM", (1200, 0, 180), (0, 0, 180), ortho=340); shot(os.path.join(outdir, "side_tilt45.png"))
    # service view: tilt 45, cover off, wheel visible
    cv = bpy.data.objects["PRT_launcher_cover"]
    hidden = [cv] + [o for o in bpy.data.objects if o.name.startswith("FST_cover_")]
    for o in hidden:
        o.hide_render = True
    camera("CAM", (620, 420, 330), (20, 40, 215), lens=70); shot(os.path.join(outdir, "service_cover_off_tilt45.png"))
    # pinch-bolt access: both L-keys drawn at theta 0 (long leg straight out +X through the open cover side)
    set_pose(0, 0)
    keys = [lkey("LKEY_%d" % (s_ + 1), s_, 0.0) for s_ in (-1, 1)]
    for k in keys:
        k.data.materials.clear()
        k.data.materials.append(mat((0.85, 0.12, 0.10, 1)))
        for pl in k.data.polygons:
            pl.material_index = 0
    set_pose(0, 45)
    Mt = bpy.data.objects["PIV_flywheel"].matrix_world.translation
    camera("CAM", (Mt.x + 330, Mt.y + 160, Mt.z + 120), (Mt.x + 10, Mt.y, Mt.z), lens=60)
    shot(os.path.join(outdir, "flywheel_lkey_access_tilt45.png"))
    for k in keys:
        me = k.data
        bpy.data.objects.remove(k)
        bpy.data.meshes.remove(me)
    for o in hidden:
        o.hide_render = False
    # feeder index: park (solid disc over the outlet) and fire (+30), hopper and lid hidden
    hid = [bpy.data.objects[n] for n in ("PRT_hopper", "PRT_hopper_lid")]
    for o in hid:
        o.hide_render = True
    set_pose(0, 0)
    for f, tag in ((0.0, "park0"), (FEED_FIRE, "fire+30"), (-FEED_FIRE, "fire-30")):
        set_pose(0, 0, feeder=f)
        camera("CAM", (FEED_XY[0], FEED_XY[1], 900), (FEED_XY[0], FEED_XY[1] + 0.01, 0), ortho=150)
        shot(os.path.join(outdir, "feeder_index_%s.png" % tag))
    for o in hid:
        o.hide_render = False
    set_pose(0, 0)
    render_section(outdir, "x", WHEEL_XW, "section_launcher_wheel_plane.png", (900, 25, 175), (0, 25, 175), 175, only_cut=True)
    render_section(outdir, "x", WHEEL_XW, "section_full_wheel_plane.png", (900, 0, 160), (0, 0, 160), 340, only_cut=False)
    set_pose(0, 45)
    render_section(outdir, "x", WHEEL_XW, "section_launcher_tilt45.png", (900, 40, 205), (0, 40, 205), 190, only_cut=True)
    set_pose(0, 0)
    render_section(outdir, "y", W_P, "section_motor_encoder_axis.png", (-40, 900, T_Z + W_Q + 25), (-40, 0, T_Z + W_Q + 25), 190,
                   only_cut=False, scope={"PIV_tilt"}, keep_cables=True)
    render_section(outdir, "x", -68.0, "section_nacelle_duct.png", (900, 15, T_Z - 30), (0, 15, T_Z - 30), 150,
                   only_cut=True, scope={"PIV_tilt"}, keep_cables=True)
    render_section(outdir, "z", 60.0, "section_base_plan_z60.png", (0, 0, 900), (0, 0.01, 0), 280, only_cut=False, keep_cables=True)
    render_section(outdir, "x", NIP_X, "section_nip_stud_thumbwheel.png", (900, -12, 132), (0, -12, 132), 75,
                   only_cut=True, scope={"PIV_tilt"}, keep_cables=True)
    render_section(outdir, "x", FW_BOLT_X, "section_flywheel_pinch_bolts.png", (900, W_P, T_Z + W_Q), (0, W_P, T_Z + W_Q), 90,
                   only_cut=True, scope={"PIV_tilt"}, keep_cables=True)
    render_exploded(outdir)
    set_pose(0, 0)


def _root_pivot(ob):
    p = ob.parent
    names = set()
    while p is not None:
        names.add(p.name)
        p = p.parent
    return names


def render_section(outdir, axis, val, fname, cam_loc, cam_tgt, ortho, only_cut=True, scope=None, keep_cables=False):
    """Cut every solid at axis = val, removing the side toward the camera; cut faces are coloured section-yellow."""
    k = "xyz".index(axis)
    lo = [-600, -600, -100]
    hi = [600, 600, 700]
    lo[k] = val
    cutter = box("SECTION_CUT", lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    cutter.data.materials.append(mat((0.98, 0.83, 0.25, 1)))
    hidden, mods = [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.name == "SECTION_CUT" or ob.hide_render:
            continue
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        mn = min(v[k] for v in bb)
        mx = max(v[k] for v in bb)
        if mn >= val or (scope and not (_root_pivot(ob) & scope)):
            ob.hide_render = True
            hidden.append(ob)
        elif mx > val:
            if ob.name.startswith("PRT_") or ob.name in ("BUY_motor", "BUY_magnet", "BUY_battery", "BUY_dewalt_adapter", "BUY_buck_12v"):
                m = ob.modifiers.new("sec", 'BOOLEAN')
                m.operation = 'DIFFERENCE'
                m.solver = 'MANIFOLD'
                if hasattr(m, "material_mode"):
                    m.material_mode = 'TRANSFER'
                m.object = cutter
                mods.append((ob, m))
            elif (ob.name.startswith("FST_") or ob.name.startswith("CAB_")) and keep_cables:
                pass
            else:
                ob.hide_render = True
                hidden.append(ob)
        elif only_cut:
            ob.hide_render = True
            hidden.append(ob)
    cutter.hide_render = True
    camera("CAM", cam_loc, cam_tgt, ortho=ortho)
    shot(os.path.join(outdir, fname))
    for ob, m in mods:
        ob.modifiers.remove(m)
    for ob in hidden:
        ob.hide_render = False
    me = cutter.data
    bpy.data.objects.remove(cutter)
    bpy.data.meshes.remove(me)


ORTHO_SCALE = 440.0

EXPLODE = {
    "PRT_base_floor": (0, 0, -120), "PRT_base_shell": (0, 0, -40), "BUY_battery": (160, 0, -60), "BUY_dewalt_adapter": (110, 0, -40),
    "BUY_buck_12v": (-40, 0, -110), "BUY_servo_controller": (60, 0, -110), "BUY_motorgo_axis": (-40, -60, -40), "BUY_usbc_plug": (-40, -110, -40),
    "PRT_pan_hub": (0, 0, -15), "PRT_pan_pinion": (0, 30, -60), "PRT_servo_pocket_pan": (0, 30, -90), "PRT_servo_clamp_pan": (0, 30, -130),
    "BUY_servo_pan": (0, 30, -110), "BUY_horn_pan": (0, 30, -75), "PRT_horn_adapter_pan": (0, 30, -68),
    "PRT_turntable": (0, 0, 30), "PRT_turntable_spine": (0, 0, 50),
    "PRT_yoke_arm_L": (-70, 0, 60), "PRT_arm_cap_L": (-70, 0, 120), "PRT_arm_cover_L": (-110, 0, 60),
    "PRT_yoke_arm_R": (90, 0, 60), "PRT_arm_cap_R": (90, 0, 120), "PRT_arm_cover_R": (130, 0, 60),
    "PRT_servo_pocket_tilt": (150, 0, 80), "PRT_servo_clamp_tilt": (205, 0, 80), "BUY_servo_tilt": (175, 0, 80),
    "BUY_horn_tilt": (120, 0, 80), "PRT_horn_adapter_tilt": (110, 0, 80), "PRT_tilt_servo_cover": (250, 0, 80),
    "PRT_feeder_plate": (0, 0, 170), "PRT_feeder_disc": (0, 0, 195), "PRT_hopper": (0, 0, 225), "PRT_hopper_lid": (0, 0, 255),
    "PRT_servo_pocket_feeder": (0, -40, 140), "PRT_servo_clamp_feeder": (0, -40, 100), "BUY_servo_feeder": (0, -40, 120),
    "BUY_horn_feeder": (0, -40, 160), "PRT_horn_adapter_feeder": (0, -40, 168),
    "PRT_feeder_shroud": (0, -40, 95), "PRT_nip_cover": (0, -60, -30), "PRT_nip_wheel": (0, -40, -20),
    "PRT_launcher_cover": (80, 50, 40), "PRT_journal_plate": (60, 10, 60), "PRT_hood": (20, 60, -30),
    "PRT_flywheel": (40, 50, 40), "PRT_launcher_body": (0, 50, 40), "PRT_nacelle": (-60, 40, 40), "BUY_motor": (-110, 40, 40),
    "BUY_magnet": (-150, 40, 40), "BUY_plink_encoder": (-165, 40, 40), "PRT_encoder_cap": (-185, 40, 40),
}


def render_exploded(outdir):
    set_pose(0, 0)
    saved = {}
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        if ob.name.startswith("FST_") or ob.name.startswith("CAB_"):
            ob.hide_render = True
            saved[ob.name] = None
            continue
        off = EXPLODE.get(ob.name)
        if off is None:
            continue
        saved[ob.name] = ob.matrix_world.copy()
        ob.matrix_world = Matrix.Translation(Vector(off)) @ ob.matrix_world
    bpy.context.view_layer.update()
    camera("CAM", (820, -950, 600), (0, 0, 200), lens=40)
    shot(os.path.join(outdir, "exploded.png"))
    for name, mw in saved.items():
        ob = bpy.data.objects[name]
        if mw is None:
            ob.hide_render = False
        else:
            ob.matrix_world = mw
    bpy.context.view_layer.update()


# =====================================================================================
if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build()
    store_print_rot()
    set_pose(0, 0)
    names = export_stls()
    print("STL exported:", len(names), names)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    if "--render" in argv:
        render_all(argv[argv.index("--render") + 1])
        bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("BUILD_DONE")
