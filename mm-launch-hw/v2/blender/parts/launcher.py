"""Launcher pod (PIV_tilt) = the launch test rig, ported from v1 attempt-3 (../blender/build_assembly.py) onto params.py.

Parts: nacelle (motor bore R18.15 + crush ribs, hollow left journal R15 / Ø12 bore, encoder end), guard body (left wall +
perimeter, chute, wheel cavity, nip, muzzle, backplate bay, flat nip land), journal plate (right journal, 12 AF socket,
stop lug, hinge nut trap), wheel-side cover (4 csk screws in front of the right post at tilt 45), encoder cap (Plink on
pegs, ENC_GAP 1.0 by construction), backplate PRT_hood on PIV_hood (hinged, stud pocket), thumbwheel stop on the land,
flat-printed leaf spring PRT_nip_leaf under PRT_nip_cover, flywheel on PIV_flywheel (web on the motor side, 2 pinch bolts
through nuts). 2D profiles live in launcher_geom.py (pure Python). Every screw: F.screw_hole and A.fastener share at/into.

Modelling notes: the thumbwheel and its nut are drawn static on PIV_tilt at the 6.5 mm setting (they ride the stud; the
stud swings through them). The leaf is drawn in its FREE (as-printed, flat) state: its pads stand LEAF_PRE 1.2 into the
thumbwheel top, which is the assembly preload (checks.json allow row).
"""
import math, os
from mathutils import Vector, Matrix
from cadlib import geom as G, features as F, asm as A, export as E
import placeholders as PH
from parts.launcher_geom import Geo, lin, vadd, sector

C = PH.C
PX, NX = (1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ = 222.0
g = None
P_ = None
PSI_RELIEF = 62.0               # v2-A4: flange relief ends at psi 62 (A4 92). Above it the lift-matched profile keeps >= 4.6
                                # to the flange 1 deg past the stop, and a groove there held the x 29 drop rays 1.5 off the
                                # flange (5/31 stalls at the static max, tilt 22.5..46)


def lpt(x, c):
    return (x, c[0], TZ + c[1])


def wyz(pts):
    return [(p, TZ + q) for p, q in pts]


def lprism(name, pts, x0, x1):
    return G.prism(name, wyz(pts), x0, x1, 'X')


def lcyl(name, c, r, x0, x1, n=None):
    return G.cyl(name, (c[0], TZ + c[1]), r, x0, x1, 'X', n=n)


def screw(name, at, into, length, spec, host, step, joint="PIV_tilt", cut=()):
    for kind, kw, lst in cut:
        lst += F.screw_hole(at, into, length, kind=kind, name=name, **kw)
    A.fastener(name, at, into, length, spec=spec, joint=joint, host=host, step=step)


def td_bore(at, into, print_up, r0, z0, z1, name, r1=None, cap=1.0):
    """teardrop counterbore (r1 None) or countersink cone (r0 at z0 -> r1 at z1) along `into` from `at`, point toward
    print_up: F.screw_hole teardrops only the shank holes, so a horizontal head bore's roof was a flat overhang"""
    F3 = F._frame((0, 0, 0), into).to_3x3()
    up = F3.inverted() @ Vector(print_up)
    a = math.atan2(up.y, up.x)

    def ring(r):                                   # teardrop with its point flattened at cap * r: at 1.0 the bore reaches
        pts, k = G.teardrop((0.0, 0.0), r, (up.x, up.y)), cap * r      # no further than the round one (the full point came
        out = []                                                       # within 0.9 of the next bore), 0.83 r bridge on top
        for i in range(len(pts)):
            p, q = pts[i - 1], pts[i]
            dp = p[0] * math.cos(a) + p[1] * math.sin(a) - k
            dq = q[0] * math.cos(a) + q[1] * math.sin(a) - k
            if (dp > 0) != (dq > 0):
                t = dp / (dp - dq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
            if dq <= 0:
                out.append(q)
        return out
    t0 = ring(r0)
    t1 = t0 if r1 is None else ring(r1)
    ob = G.loft(name, t0, t1, z0, z1, 'Z')
    return [F._place(ob, at, into)]


def along(name, poly, x, a, b):
    """prism of a 2D polygon (s = world-x offset, t = in-plane normal) from launcher point a to b at world x"""
    Av = Vector((x, a[0], TZ + a[1]))
    Bv = Vector((x, b[0], TZ + b[1]))
    w = (Bv - Av).normalized()
    u = Vector((1, 0, 0))
    ob = G.prism(name, poly, 0.0, (Bv - Av).length, 'Z')
    return G.xform(ob, G.frame(Av, u, w.cross(u), w))


def nip_frame():
    """local (x, u, v) -> world"""
    return G.frame((0.0, g.NIP_E[0], TZ + g.NIP_E[1]), (1, 0, 0), (0, g.NIP_U[0], g.NIP_U[1]), (0, g.NIP_V[0], g.NIP_V[1]))


def to_nip(ob):
    """bake the nip frame; it is left-handed (x, U, V with V toward the hinge), so flip the winding back"""
    G.xform(ob, nip_frame())
    ob.data.flip_normals()
    return ob


def nip_world(x, u, v):
    p = g.nip_pq(u, v)
    return (x, p[0], TZ + p[1])


def rot_to_down(d):
    """print_rot that turns world direction d to -Z (that face onto the bed)"""
    return Vector(d).rotation_difference(Vector((0, 0, -1))).to_matrix()


def top_chamfer(P, x_face, side, ch=None):
    """45 deg x CH chamfer cutter on the pod's top edge at the side face x_face (material on the `side` of it):
    profile ring inset CH at the face lofted to the full ring CH further in, kept above the top zone line."""
    ch = ch or P.CH
    prof = g.PROFILE
    big = G.offset_convex(prof, 3.0)
    inset = G.offset_convex(prof, -ch - 0.95)        # a hair under 45 deg: the left face prints on the bed
    grow = G.offset_convex(prof, 1.0)
    xa, xb = x_face - side * 1.0, x_face + side * (ch + 1.0)
    cut = lprism("tcb", big, min(xa, xb), max(xa, xb))
    keep = G.loft("tck", wyz(inset), wyz(grow), x_face - side * 1.0, x_face + side * (ch + 1.0), 'X')   # 45 deg, both sides of the face
    cut = G.csg(cut, sub=[keep])
    a, b = (-24.0, 0.0), (P.MUZZLE_FRONT + 8.0, P.MUZZLE_ROOF + 2.0)      # zone: above the line a-b
    d = (b[0] - a[0], b[1] - a[1])
    n = (-d[1], d[0])
    zone = [vadd(a, d, -1.0), vadd(b, d, 1.0), vadd(vadd(b, d, 1.0), n, 2.0), vadd(vadd(a, d, -1.0), n, 2.0)]
    return G.csg(cut, inter=[lprism("tcz", zone, min(xa, xb) - 1, max(xa, xb) + 1)])


# ------------------------------------------------------------------ guard body

def ccw(poly):
    a = sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))
    return poly if a > 0 else poly[::-1]


def finger_scallop(P):
    """v2-A2-03 finger scallop: an R8.5 cylinder along x about the R8 fingertip centre (resting on the thumbwheel rim crest),
    cut from the guard shelf (the land's -v corner), so the fingertip reaches the rim instead of the shelf. Built in the nip
    frame (x, u, v). Edge breaks: 1.0 x 45 deg chamfers where the scallop meets the land top (u 0) and front (v -12) faces,
    along the scallop (section triangles) and at its two ends (45 deg wedges clipped to the cylinder)."""
    uc, vc, R, L, eb = P.FINGER_SCALLOP
    x0, x1 = P.NIP_X - 0.5 - L / 2, P.NIP_X - 0.5 + L / 2      # 9.0..29.0 (+eb: 8.0..30.0): keeps a 2.5 lid under x 31.5
    vf = P.LAND_V[0]
    out = [G.cyl("fsc", (uc, vc), R, x0, x1, 'X', n=96)]
    # long edges: top face (u 0) and front face (v vf) meet the arc
    v1 = vc + math.sqrt(R * R - uc * uc)
    t1 = (-(v1 - vc) / R, -uc / R)                             # unit tangent into the solid (toward -u)
    if t1[0] > 0:
        t1 = (-t1[0], -t1[1])
    u2 = uc - math.sqrt(R * R - (vf - vc) ** 2)
    t2 = ((vf - vc) / R, -(u2 - uc) / R)
    if t2[1] < 0:
        t2 = (-t2[0], -t2[1])
    rin = 0.3                                                  # arc vertex 0.3 inside R: the 96-gon's chords left 0.02 slivers
    tri1 = [(0.0, v1 + eb), (eb, v1 - 0.2), (t1[0] * eb - rin * (0.0 - uc) / R, v1 + t1[1] * eb - rin * (v1 - vc) / R)]
    tri2 = [(u2 - eb, vf), (u2 + t2[0] * eb - rin * (u2 - uc) / R, vf + t2[1] * eb - rin * (vf - vc) / R), (u2 + 0.3, vf - eb)]
    out += [G.prism("fst1", ccw(tri1), x0, x1, 'X'), G.prism("fst2", ccw(tri2), x0, x1, 'X')]
    # ends: 45 deg wedges, clipped to the cylinder
    for k, (xe, s) in enumerate(((x0, -1), (x1, 1))):
        xa = xe + s * eb                                       # surface end of the chamfer
        top = ccw([(xa, 0.0), (xe - s * 0.5, -eb - 0.5), (xe - s * 0.5, 4.0), (xa + s * 4.0, 4.0)])
        frt = ccw([(xa, vf), (xe - s * 0.5, vf + eb + 0.5), (xe - s * 0.5, vf - 4.0), (xa + s * 4.0, vf - 4.0)])
        for j, w in enumerate((G.prism("fwt%d" % k, top, vc - R - 1, vc + R + 1, 'Z'),
                               G.prism("fwf%d" % k, frt, uc - R - 1, uc + R + 1, 'Y'))):
            out.append(G.csg(w, inter=[G.cyl("fwc%d%d" % (k, j), (uc, vc), R, min(xe, xa) - 0.5, max(xe, xa) + 0.5, 'X', n=96)]))
    return [to_nip(o) for o in out]


def build_body(P, cuts):
    xo, xi, xc = P.X_BODY_OUT, P.X_BODY_IN, P.X_COVER_IN
    body = lprism("body", g.PROFILE, xo, xc)
    v0, v1 = P.LAND_V
    land = lprism("land", [g.nip_pq(P.LAND_U0, v0), g.nip_pq(0.0, v0), g.nip_pq(0.0, v1), g.nip_pq(P.LAND_U0, v1)], xo, xc)
    body = G.csg(body, add=[land])
    G.bevel(body, P.EB)
    body = G.csg(body, sub=[top_chamfer(P, xo, 1)])
    sub = [lprism("wc", g.wheel_cavity_poly(), xi, xc + 1), lprism("nip", g.nip_poly(), xi, xc + 1),
           lprism("mz", g.muzzle_poly(), xi, xc + 1), lprism("ch", g.chute_poly(), P.CH_X0, xc + 1)]
    for k, poly in enumerate(g.BAY_POLYS):
        sub.append(lprism("bay%d" % k, poly, xi, xc + 1))
    sub.append(lprism("bayb", g.BAY_BOSS, xi, xc + 1))
    sub.append(lprism("nsp", g.nip_stop_pocket(), nip_stop_x()[0], xc + 1))     # v2-A1-01 pocket for PRT_nip_stop
    slab = to_nip(G.box("lsl", xo - 1, xc + 1, 0.0, 40.0, v0, v1))                 # nothing of the guard past the land face
    sub.append(slab)
    body = G.csg(body, sub=sub)
    ot = math.radians(2.6)                                   # cadcheck overtravel 2.5 deg
    td = G.teardrop((0.0, 0.0), P.STUD_HOLE_R, up=(1, 0))    # roof pointed +X (print up): no flat ceiling
    sub = []
    for k, e in enumerate(lin(g.EPS_OPEN - ot, g.EPS_CLOSE + ot, 13)):   # stud slot over the hinge range (head passes in)
        p0, d = g.stud_line(e)
        sub.append(along("stud%d" % k, td, P.NIP_X, vadd(p0, d, -1.0), vadd(p0, d, g.stud_d(e) + 2.0)))
    sub.append(lcyl("sh", g.WC, 6.0, xo - 1, xi + 1))
    sub += finger_scallop(P)
    body = G.csg(body, sub=sub + list(cuts))
    A.part(body, "PRT_launcher_body", 'PRT', "pla_b", joint="PIV_tilt", stl="launcher_body", print_rot=A.R_NX_DOWN,
           orient="left (motor) wall outer face on the bed; profile extruded so every wall is vertical", supports="no",
           infill=25)


# ------------------------------------------------------------------ journal plate + cover

def jp_region(kind, name):
    """journal-plate region solid: a 2 mm layer at the parting arc, then a 45 deg lap (v2-A1-08: the A1 flat lap step was a
    2 x 48 mm ceiling with the plate printed inner face down). The cover subtracts the same solid grown 0.3."""
    P = g.P
    k = 0.0 if kind == "jp" else 0.3
    xa, xe = P.X_COVER_IN - 0.01, P.X_COVER_OUT + 0.01
    xb, xc = P.X_COVER_IN + 1.6, P.X_COVER_OUT - 1.6         # 1.6 vertical lands either side: no knife edge on either part
    lay = lprism(name + "a", g.jp_union(P.JP_R, k), xa, xb)
    lap = G.loft(name + "b", wyz(g.jp_union(P.JP_R, k)), wyz(g.jp_union(P.JP_R, k + 0.75)), xb, xc, 'X')   # 43 deg off vertical
    top = lprism(name + "c", g.jp_union(P.JP_R, k + 0.75), xc, xe)
    return G.csg(lay, add=[lap, top])


def build_journal_plate(P, cuts):
    ob = G.csg(lprism("jpl", g.PROFILE, P.X_COVER_IN, P.X_COVER_OUT), inter=[jp_region("jp", "jpr")])
    G.bevel(ob, P.EB)
    ob = G.csg(ob, sub=[top_chamfer(P, P.X_COVER_OUT, -1, P.CH - 1.6)])     # 4 mm plate: CH - 1.6 keeps a 1.6 mm land
    # journal on after the chamfer, its base grown from the bed inside the plate region: the chamfer cutter's 1 mm overshoot
    # notched the journal base at the chute-entry chord (r 16.2), a 31 mm ceiling at x 36.5 (v2-A1-08)
    jr = lcyl("jr", (0, 0), P.IF_JOURNAL_R, P.X_COVER_OUT - 0.5, P.IF_JOURNAL_R_X1)
    G.bevel(jr, 0.6)
    jb = G.csg(lcyl("jrb", (0, 0), P.IF_JOURNAL_R, P.X_COVER_IN, P.X_COVER_OUT), inter=[jp_region("jp", "jrr")])
    a, hw = P.IF_STOP_JP_A, P.IF_STOP_JP_HW
    lug = lprism("lug", sector(P.IF_STOP_R[0], P.IF_STOP_R[1], a - hw, a + hw, 8), P.IF_STOP_JP_X[0] - 0.5, P.IF_STOP_JP_X[1])
    ob = G.csg(ob, add=[jr, jb, lug])
    kx1 = P.IF_TILT_KEY_X[1] - 0.3
    sub = [G.prism("hex", G.hexagon((0.0, TZ), P.IF_TILT_KEY_AF + 0.3), kx1 - 7.5, kx1 + 0.01, 'X'),
           G.cyl("cbr", (0.0, TZ), P.IF_TILT_ADAPTER[0] + 0.3, kx1, P.IF_JOURNAL_R_X1 + 1, 'X')]
    ob = G.csg(ob, sub=sub + list(cuts))
    A.part(ob, "PRT_journal_plate", 'PRT', "pla_b", joint="PIV_tilt", stl="journal_plate", print_rot=A.R_NX_DOWN,
           orient="inner face on the bed; lap step, journal, socket and stop lug grow up", supports="no", infill=30)


def build_cover(P, cuts):
    ob = G.csg(lprism("cvl", g.PROFILE, P.X_COVER_IN, P.X_COVER_OUT), sub=[jp_region("cover", "cvr")])
    G.bevel(ob, P.EB)
    ob = G.csg(ob, sub=[top_chamfer(P, P.X_COVER_OUT, -1, P.CH - 1.6)] + list(cuts))
    A.part(ob, "PRT_launcher_cover", 'PRT', "pla_b", joint="PIV_tilt", stl="launcher_cover", print_rot=A.R_NX_DOWN,
           orient="inner face on the bed; rebated edge steps in toward the top", supports="no", infill=25)


# ------------------------------------------------------------------ backplate, nip stop, leaf, nip cover

def relief_cuts(P, x0, x1):
    """v2-A1-01 hood relief over the flywheel's R36 tracks (web + left flange x <= WEB_X1; right flange x >= WHEEL_X1 - 1.6).
    1 deg past the stop (hood +2.315) the bare face sits h = 3.23 above the flange top (psi ~20). Over each flange the face
    is cut 1.5 deep; beside it the cut follows a circle of radius HOOD_FLANGE_RELIEF[0] about the flange corner (depth
    sqrt(Rc^2 - s^2) - h), so no hood point is nearer than Rc, and a candy anywhere on the face stays within 7 of the wheel
    (a step-sided groove left 5/31 drop rays stalling in it). Lofts between depth stations; 45 deg into the deep part."""
    Rc, h, D = P.HOOD_FLANGE_RELIEF
    psis = lin(P.BP_PSI0 - 3.0, PSI_RELIEF, 48)

    def rel(d):
        return [P.pw(P.WHEEL_R + P.gap_at(ps) - 1.0, ps) for ps in psis] + \
               [P.pw(P.WHEEL_R + P.gap_at(ps) + d, ps) for ps in psis[::-1]]
    s_end = math.sqrt(Rc * Rc - h * h)
    st = [(-1.0, D)] + [(s_, math.sqrt(Rc * Rc - s_ * s_) - h) for s_ in lin(0.0, s_end, 7)[:-1]]
    k = (st[-1][1] - 0.0) / (s_end - st[-1][0])                  # last segment runs on through the face to depth -0.3
    st.append((s_end + 0.3 / k, -0.3))
    out = []
    for side, xe, xf in ((1, P.WEB_X1, x0 - 1.0), (-1, P.WHEEL_X1 - 1.6, x1 + 1.0)):
        xs = [xe + side * s_ for s_, _ in st]
        a, b = sorted((xf, xs[0]))
        out.append(lprism("hrd%d" % side, rel(D), a, b))
        for k in range(len(st) - 1):
            wa, wb = xs[k], xs[k + 1]
            pa, pb = rel(st[k][1]), rel(st[k + 1][1])
            if wa > wb:
                wa, wb, pa, pb = wb, wa, pb, pa
            out.append(G.loft("hrl%d_%d" % (side, k), wyz(pa), wyz(pb), wa, wb, 'X'))
    return out


def build_hood(P, cuts):
    x0, x1 = P.X_BODY_IN + 0.55, P.X_COVER_IN - 0.5     # 0.55: the left wall clearance read 0.500 exactly
    h = lprism("hood", g.bp_band(0.0, 0.0), x0, x1)
    h = G.csg(h, add=[lcyl("hb", g.HINGE, P.HINGE_BOSS_R, x0, x1, n=32), lprism("hlug", g.hood_lug(0.0, 0.0), x0, x1)])
    G.bevel(h, 0.8)
    cuts = list(cuts) + relief_cuts(P, x0, x1)
    pocket = along("hsp", G.hexagon((0, 0), C["m3_hardware"]["nut_trap_af"], 0.0), P.NIP_X,
                   vadd(g.JACK_PT, g.NIP_U, 1.0), vadd(g.JACK_PT, g.NIP_U, -P.STUD_POCKET_D))
    # spot face square to the stud, STUD_SPOT_D below the head's bearing face (A4 1.6 for the cap head): on the 26 deg back face it leaves a
    # flat floor round the hex instead of a 0.9 mm lip (v2-A1-08); the R3.8 stop sleeve stands in it on the head
    spot = along("hsf", G.circle((0, 0), 4.2, 32), P.NIP_X, vadd(g.JACK_PT, g.NIP_U, -P.STUD_SPOT_D),
                 vadd(g.JACK_PT, g.NIP_U, 4.0))
    # the back face runs 26 deg off square to the stud, so the pocket's -v flat ran out through it as a 0.9 mm lip (A1-08 "hood
    # nip edge"): the pocket's -v half becomes a U-slot out through the back face (the +v half's three flats key the head; the
    # R4.4 guard slot round the R3.8 sleeve keeps the stud within 0.6 of its line)
    hr = C["m3_hardware"]["nut_trap_af"] / math.sqrt(3.0)            # hex corner radius (corners on +-x)
    lip = along("hsl", [(-hr, -7.0), (hr, -7.0), (hr, 0.0), (-hr, 0.0)], P.NIP_X,
                vadd(g.JACK_PT, g.NIP_U, -P.STUD_POCKET_D), vadd(g.JACK_PT, g.NIP_U, 4.0))
    h = G.csg(h, sub=[pocket, spot, lip] + list(cuts))           # spot face square to the stud (back face is 26 deg off)
    A.part(h, "PRT_hood", 'PRT', "pla_a", joint="PIV_hood", stl="hood", print_rot=A.R_NX_DOWN,
           orient="on its side face (profile extruded, all walls vertical; stud pocket has a vertex up)", supports="no",
           infill=40)


def build_thumbwheel(P):
    w = G.cyl("tw", (P.NIP_X, 0.0), P.TW_R, 0.0, P.TW_T, 'Y', n=64)
    G.bevel(w, 0.6)
    af = C["m3_hardware"]["nut_trap_af"]
    sub = [G.cyl("twh", (P.NIP_X, 0.0), 1.7, -1, P.TW_T + 1, 'Y', n=16),
           G.prism("twn", G.hexagon((P.NIP_X, 0.0), af), -1.0, P.TW_NUT_U[1] + 0.3, 'Y')]
    for k in range(12):
        a = 2 * math.pi * k / 12
        sub.append(G.cyl("kn%d" % k, (P.NIP_X + P.TW_R * math.cos(a), P.TW_R * math.sin(a)), 0.9, -1, P.TW_T + 1, 'Y', n=12))
    ob = G.csg(w, sub=sub)
    to_nip(ob)
    A.part(ob, "PRT_nip_wheel", 'PRT', "pla_b", joint="PIV_nip_lift", stl="nip_wheel",
           print_rot=rot_to_down((0, g.NIP_U[0], g.NIP_U[1])), orient="outer face on the bed, nut trap up (press the nut in)",
           supports="no", infill=50)
    A.nut("FST_tw_nut", nip_world(P.NIP_X, P.TW_NUT_U[0], 0.0), (0, g.NIP_U[0], g.NIP_U[1]), joint="PIV_nip_lift", step="6e")


def nip_stop_x():
    xc = 0.5 * (P_.X_BODY_IN + 0.5 + P_.X_COVER_IN - 0.5)
    return xc - P_.NIP_STOP_W / 2, xc + P_.NIP_STOP_W / 2


def build_nip_stop(P, cuts):
    """v2-A1-01 printed min-gap stop: a pad in a pocket under the muzzle floor, its face on the plane of the hood's free-end
    face at HOOD_HI. The hood lug lands on it over a 3.4 x 20 land at gap 5.3; the pocket's front wall takes the load,
    the one M3 only retains it."""
    x0, x1 = nip_stop_x()
    ob = lprism("nstop", g.nip_stop_poly(0.0), x0, x1)
    G.bevel(ob, 0.4)
    ob = G.csg(ob, sub=list(cuts))
    o, f, n = g.nip_stop_frame()
    A.part(ob, "PRT_nip_stop", 'PRT', "pla_a", joint="PIV_tilt", stl="nip_stop", print_rot=rot_to_down((0, -f[0], -f[1])),
           orient="bottom (screw) face on the bed: pilot vertical, contact face a vertical wall", supports="no", infill=100,
           notes="gap-5.3 hard stop; print thicker/thinner along the face normal to move the stop")


def stop_sleeve_len(P):
    """sleeve from the stud head's bearing face to the thumbwheel underside (seat plane u = 0) at the gap-7.0 setting; the
    sleeve end tilts with the stud, so its high edge (R * sin eps) is what touches"""
    e = math.radians(P.HOOD_STATIC_LO)
    p0, d = g.stud_line(e)
    U = g.NIP_U
    du = d[0] * U[0] + d[1] * U[1]
    return ((g.NIP_E[0] - p0[0]) * U[0] + (g.NIP_E[1] - p0[1]) * U[1] - P.SLEEVE_R[1] * abs(math.sin(e))) / du


def build_stop_sleeve(P):
    """v2-A1-01 static max-gap stop: a tube on the stud between the head's bearing face and the thumbwheel underside. The
    thumbwheel bottoms on it at gap 7.0 (stud tension through head, sleeve and nut); the leaf lift beyond stays free."""
    L = stop_sleeve_len(P)
    a, b = g.JACK_PT, vadd(g.JACK_PT, g.NIP_U, L)
    ri, ro = P.SLEEVE_R
    ob = along("slv", G.circle((0, 0), ro, 48), P.NIP_X, a, b)
    ob = G.csg(ob, sub=[along("slvi", G.circle((0, 0), ri, 24), P.NIP_X, vadd(a, g.NIP_U, -1.0), vadd(b, g.NIP_U, 1.0))])
    A.part(ob, "PRT_nip_stop_sleeve", 'PRT', "pla_a", joint="PIV_hood", stl="nip_stop_sleeve",
           print_rot=rot_to_down((0, -g.NIP_U[0], -g.NIP_U[1])), orient="end on the bed (tube upright)", supports="no",
           infill=100, notes="length %.2f = stud_d at gap %.1f; shorten it to raise the max gap" % (L, P.NIP_SET[1]))


def build_leaf(P, cuts):
    """Flat strip, printed with its +U face on the bed (bending stress in the layer plane). Root block under the strip
    carries the two FST_leaf_* threads; R2 fillet where the strip leaves the block; two pads over the thumbwheel."""
    u0, t = g.LEAF_U0, P.LEAF_T
    vr, bl, bh = P.LEAF_L, P.LEAF_BLOCK_L, P.LEAF_BLOCK_H
    r = P.LEAF_ROOT_R
    tc = P.LEAF_TIP_CH
    prof = [(u0 + t, P.NIP_V_TIP + tc), (u0 + t, vr + bl), (u0 - bh, vr + bl), (u0 - bh, vr)]
    prof += [(u0 - r + r * math.cos(math.radians(a)), vr - r + r * math.sin(math.radians(a))) for a in range(90, -1, -15)]
    prof += [(u0, P.NIP_V_TIP), (u0 + t - tc, P.NIP_V_TIP)]
    x0, x1 = g.LEAF_X
    leaf = G.prism("leaf", prof, x0, x1, 'X')              # local (x, u, v); nip frame below
    pads = [G.box("pad%d" % s, P.NIP_X + s * 6.0 - 1.5, P.NIP_X + s * 6.0 + 1.5, u0 - P.LEAF_PAD_H, u0 + 0.01, -2.0, 2.0)
            for s in (-1, 1)]
    leaf = G.csg(leaf, add=pads)
    # stud swing (open fork). v2-A3-A2-01: half width 2.6 -> nut corner + 0.7 (4.0, pads from 4.5): at full lift the captive
    # nut's top (TW_NUT_U 3.2 + 2.2) came 0.35 under the free-state strip (u 5.8) across the 2.6 slot edge
    sw = C["m3_hardware"]["nut_trap_af"] / math.sqrt(3.0) + 0.7
    slot = G.box("ls", P.NIP_X - sw, P.NIP_X + sw, u0 - P.LEAF_PAD_H - 1, u0 + t + 1, P.NIP_V_TIP - 1.0, 5.0)
    leaf = G.csg(leaf, sub=[slot])
    to_nip(leaf)
    leaf = G.csg(leaf, sub=list(cuts))
    A.part(leaf, "PRT_nip_leaf", 'PRT', "pla_b", joint="PIV_tilt", stl="nip_leaf",
           print_rot=rot_to_down((0, g.NIP_U[0], g.NIP_U[1])),
           orient="flat: strip's outer face on the bed, root block and pads up (bending stress in the layer plane)",
           supports="no", infill=100, notes=str(g.leaf_numbers()))


def build_nip_cover(P, cuts):
    x0, x1 = g.NIP_XC
    v0, v1 = P.NIP_COVER_V0, P.LAND_V[1]          # v2-A1-02: the -v end wall stands 2.0 inside the thumbwheel rim
    uo, ui = g.SHELL_UO, g.SHELL_U0
    cr, ce = P.CR, 2.0
    prof = [(0.0, v0)]
    prof += [(uo - cr + cr * math.sin(math.radians(a)), v0 + cr - cr * math.cos(math.radians(a))) for a in range(0, 91, 10)]
    prof += [(uo - ce + ce * math.cos(math.radians(a)), v1 - ce + ce * math.sin(math.radians(a))) for a in range(0, 91, 15)]
    prof += [(0.0, v1)]
    ob = G.prism("nc", prof, x0, x1, 'X')
    G.bevel(ob, P.EB)
    xa, xb = x0 + P.NIP_END_T, x1 - P.NIP_END_T
    sk = v0 + P.NIP_SHELL_T
    rc = (uo - cr, v0 + cr)
    # v2-A2 launcher step: the inner corner over the slot end is a 45 deg chamfer (print up = -v; 1.025 steep so facets never
    # tip past 45), not the R4 arc whose first 35 deg printed as a near-flat overhang (A2 overhang warn). The arc also cut
    # into the leaf tip's path (the tip rises to the roof at v -3.5); the chamfer stays outside it, so the roof over the
    # slot end is a 2.8 x 22 bridge between the end walls instead
    # the leaf tip rises to the roof (u ui); its outer edge is chamfered LEAF_TIP_CH, so the cavity's chamfer runs 0.3 outside
    # the line u - v = ui - (NIP_V_TIP + LEAF_TIP_CH) (the A2 R4 arc cut into that path)
    vc = ui - (ui - P.NIP_V_TIP - P.LEAF_TIP_CH + 0.3 * math.sqrt(2.0))
    cprof = [(-1.0, sk), (ui - (vc - sk) / 1.025, sk)]
    vr = P.LEAF_L
    vs = vr - 0.4                                   # roof step 0.4 before the strip root: 1.7 (A2 1.3) under the FST_leaf bores
    cprof += [(ui, vc), (ui, vs), (g.LEAF_U0 + P.LEAF_T, vs), (g.LEAF_U0 + P.LEAF_T, vr + P.LEAF_BLOCK_L + 0.5),
              (-1.0, vr + P.LEAF_BLOCK_L + 0.5)]
    cav = G.prism("ncc", cprof, xa, xb, 'X')
    win = G.prism("ncw", G.hull_circles([((P.NIP_X, 1.0), P.STUD_WINDOW_R - 1.0), ((P.NIP_X, 2.5), P.STUD_WINDOW_R - 1.0)]),
                  rc[0], uo + 1, 'Y')                     # stud tip window, long along v for the stud's swing (from u 7: the
    # 45 deg corner chamfer passes u 9.8 at the window's -v end, so the A2 start at ui - 1 left a 0.15 skin)
    sl, sh = P.FINGER_SLOT                          # v2-A1-02 finger slot: the rim passes 2.0 proud through the -v end wall
    xs1 = xb - 0.3                                  # slot ends 0.3 inside the cavity end: the +x end wall keeps 1.6 past EB
    fslot = G.box("ncf", xs1 - sl, xs1, -1.0, sh, v0 - 1.0, v0 + P.NIP_SHELL_T + 1.0)
    # the rim's top edge comes within 0.83 of the slot top at full leaf lift: open the slot 0.3 over the rim's width only
    flift = G.box("ncfl", P.NIP_X - P.TW_R - 0.5, P.NIP_X + P.TW_R + 0.5, sh - 0.1, sh + P.FINGER_SLOT_LIFT,
                  v0 - 1.0, v0 + P.NIP_SHELL_T + 1.0)
    ob = G.csg(ob, sub=[cav, win, fslot, flift])
    to_nip(ob)
    ob = G.csg(ob, sub=list(cuts))
    A.part(ob, "PRT_nip_cover", 'PRT', "pla_b", joint="PIV_tilt", stl="nip_cover",
           print_rot=rot_to_down((0, g.NIP_V[0], g.NIP_V[1])),
           orient="screw-block end on the bed; shell and end walls grow up as vertical walls; skirt bridges at the top; "
                  "finger slot %g x %g in the -v end wall over the thumbwheel rim (v2-A1-02)" % P.FINGER_SLOT,
           supports="no", infill=30)


# ------------------------------------------------------------------ flywheel

def build_flywheel(P):
    wy, wz = P.W_P, TZ + P.W_Q
    hh = C["m3_hardware"]["cap_head"][1]
    t_surf = math.sqrt(P.FW_HUB_R ** 2 - P.FW_BOLT_OFF ** 2)
    t_head = t_surf - hh - 0.3                      # head seat 0.3 below flush; the nut seat is point-symmetric
    web = G.cyl("fw", (wy, wz), P.WHEEL_FLANGE_R, P.HUB_X0, P.WEB_X1, 'X', n=160)
    rim = G.cyl("fwr", (wy, wz), P.WHEEL_R, P.WEB_X1 - 0.01, P.WHEEL_X1, 'X', n=160)
    flr = G.cyl("fwf", (wy, wz), P.WHEEL_FLANGE_R, P.WHEEL_X1 - 1.6, P.WHEEL_X1, 'X', n=160)
    flc = G.loft("fwc", G.circle((wy, wz), P.WHEEL_R - 0.01, 160), G.circle((wy, wz), P.WHEEL_FLANGE_R, 160),
                 P.WHEEL_X1 - 2.6, P.WHEEL_X1 - 1.59, 'X')
    ob = G.csg(web, add=[rim, flr, flc])
    ob = G.csg(ob, sub=[G.cyl("fwi", (wy, wz), P.WHEEL_R - P.FW_RIM_T, P.WEB_X1, P.WHEEL_X1 + 1, 'X', n=128)])
    hub = G.cyl("fwh", (wy, wz), P.FW_HUB_R, P.HUB_X0, P.FW_HUB_X1, 'X')
    G.bevel(hub, 0.6)
    ob = G.csg(ob, add=[hub])
    rb, flat = 2.55, 2.0
    dp = [(wy + rb * math.cos(math.radians(a)), wz + rb * math.sin(math.radians(a))) for a in range(0, 360, 10)
          if rb * math.sin(math.radians(a)) < flat]
    dp += [(wy - math.sqrt(rb * rb - flat * flat), wz + flat), (wy + math.sqrt(rb * rb - flat * flat), wz + flat)]
    sub = [G.prism("fwb", G.hull2d(dp), P.HUB_X0 - 1, P.FW_HUB_X1 + 1, 'X'),
           G.cone("fwbc", (wy, wz), 3.3, 2.0, P.HUB_X0 - 0.01, P.HUB_X0 + 1.3, 'X', n=32)]
    af = C["m3_hardware"]["nut_trap_af"]
    sx0, sx1 = P.WEB_X1, P.FW_HUB_X1 + 1.0
    bx = P.FW_BOLT_X
    for s in (-1, 1):
        sub.append(G.box("sl%d" % s, sx0, sx1, wy - 0.8, wy + 0.8, min(wz, wz + s * (P.FW_HUB_R + 1)), max(wz, wz + s * (P.FW_HUB_R + 1))))
        bz = wz + s * P.FW_BOLT_OFF
        sub.append(G.cyl("bh%d" % s, (bx, bz), 1.7, wy - P.FW_HUB_R - 1, wy + P.FW_HUB_R + 1, 'Y', n=16))
        yh, ych = wy + s * (P.FW_HUB_R + 1), wy + s * t_head
        sub.append(G.cyl("cb%d" % s, (bx, bz), 3.1, min(yh, ych), max(yh, ych), 'Y', n=20))
        sub.append(G.box("cbu%d" % s, bx - 3.1, bx + 3.1, min(yh, ych), max(yh, ych), min(bz, bz + s * 10), max(bz, bz + s * 10)))
        ynt, ynt2 = wy - s * t_head, wy - s * (P.FW_HUB_R + 1)
        sub.append(G.prism("nt%d" % s, G.hexagon((bx, bz), af), min(ynt, ynt2), max(ynt, ynt2), 'Y'))
        sub.append(G.box("ntu%d" % s, bx - af / 2, bx + af / 2, min(ynt, ynt2), max(ynt, ynt2), min(bz, bz + s * 10), max(bz, bz + s * 10)))
    for k in range(6):
        a = math.radians(21.0 + 60 * k)
        sub.append(G.cyl("lw%d" % k, (wy + 21.5 * math.cos(a), wz + 21.5 * math.sin(a)), 4.5, P.HUB_X0 - 1, P.WEB_X1 + 1, 'X'))
    ob = G.csg(ob, sub=sub)
    A.part(ob, "PRT_flywheel", 'PRT', "pla_a", joint="PIV_flywheel", stl="flywheel", print_rot=A.R_NX_DOWN,
           orient="motor-side web face on the bed; rim and hub grow up (top flange has a 45 deg underside)", supports="no",
           infill=100, notes="wrap 12-15 mm hockey tape on the 14 mm land. The 72 mm 'bridge' cadcheck reports is the 1 mm "
           "R36 flange ring over the rim's 45 deg underside (33 mm2 ceiling): it prints as perimeter loops on the cone, declared "
           "benign (v2-A1-08)")
    # v2-A4 launcher step: the hockey tape on the land, TAPE_T thick between the flanges. It is the surface a candy meets
    # (NIP_PASS and the nip rows already count it), so the drop rows target it; A1-A4 rows ended on the bare R35 land
    tape = G.cyl("tape", (wy, wz), P.WHEEL_R + P.TAPE_T, P.WEB_X1, P.WHEEL_X1 - 1.6, 'X', n=160)
    tape = G.csg(tape, sub=[G.cyl("tapei", (wy, wz), P.WHEEL_R, P.WEB_X1 - 1, P.WHEEL_X1, 'X', n=160)])
    A.part(tape, "BUY_tape", 'BUY', "buy", joint="PIV_flywheel", mass_g=2,
           src="BOM item 12: 1/2 in hockey tape, one wrap on the 14 mm land (TAPE_T %.1f)" % P.TAPE_T)
    for i, s in enumerate((-1, 1)):
        bz = wz + s * P.FW_BOLT_OFF
        A.fastener("FST_fw_bolt_%d" % i, (bx, wy + s * t_head, bz), (0, -s, 0), P.FW_BOLT_L, spec="M3_cap",
                   joint="PIV_flywheel", step="6f")
        A.nut("FST_fw_nut_%d" % i, (bx, wy - s * t_head, bz), (0, -s, 0), joint="PIV_flywheel", step="6f")


# ------------------------------------------------------------------ nacelle, encoder cap, jig

def crush_rib(r0, r1, ang_from_s, w=1.6):
    a = math.atan2(g.S[1], g.S[0]) + math.radians(ang_from_s)
    c, s_ = math.cos(a), math.sin(a)
    t = (-s_, c)
    return [(g.WC[0] + r * c + h * t[0], g.WC[1] + r * s_ + h * t[1]) for (r, h) in ((r0, -w / 2), (r1, -w / 2), (r1, w / 2), (r0, w / 2))]


def build_nacelle(P, cuts):
    x0, x1 = g.NAC_X0, P.X_MF + P.NAC_PLATE_T
    ob = lprism("nac", G.hull_circles([(g.WC, P.NAC_RW), ((0.0, 0.0), P.NAC_RT)], 128), x0, x1)
    G.bevel(ob, P.EB)
    col = lcyl("ncol", (0, 0), P.NAC_COLLAR_R, P.POD_X[0], x0 + 0.5)
    jr = lcyl("njr", (0, 0), P.IF_JOURNAL_R, P.IF_JOURNAL_L_X1, P.POD_X[0] + 0.01)
    G.bevel(jr, 0.6)
    ob = G.csg(ob, add=[col, jr])
    rr = P.MOTOR_D / 2 + P.BORE_CLR
    S, N, WC = g.S, g.N, g.WC
    slot = [vadd(WC, N, 7.0), vadd(vadd(WC, S, -27.0), N, 7.0), vadd(vadd(WC, S, -27.0), N, -7.0), vadd(WC, N, -7.0)]
    jb = P.IF_JOURNAL_BORE_R
    sub = [lcyl("nbore", WC, rr, x0 - 1, P.X_MF, n=128), lcyl("nsh", WC, 6.0, P.X_MF - 1, x1 + 1),
           lprism("nslot", slot, x0 - 1, -56.0),
           lprism("nduct", G.hull_circles([(vadd(WC, S, -20.0), 7.5), (vadd((0, 0), S, 2.0), 7.5)], 32), -76.0, -56.0),
           lcyl("ntb", (0, 0), jb, P.IF_JOURNAL_L_X1 - 1, -56.0),
           G.loft("ntbc", wyz(G.circle((0, 0), jb + 1.5, 48)), wyz(G.circle((0, 0), jb - 0.01, 48)),
                  P.IF_JOURNAL_L_X1 - 0.01, P.IF_JOURNAL_L_X1 + 1.5, 'X')]
    for xc in (-16.0, -34.0, -52.0):       # diamond vents under the can (45 deg edges in print)
        sub.append(G.prism("nv%d" % int(-xc), [(xc - 7, P.W_P), (xc, P.W_P - 6), (xc + 7, P.W_P), (xc, P.W_P + 6)],
                           TZ + P.W_Q - P.NAC_RW - 2, TZ + P.W_Q - 8, 'Z'))
    ob = G.csg(ob, sub=sub + list(cuts))
    ribs = [lprism("ncr%d" % k, crush_rib(P.MOTOR_D / 2, rr + 0.4, 120.0 * k), -P.MOTOR_L + 1.0, -P.MOTOR_L + 13.0) for k in range(3)]
    ob = G.csg(ob, add=ribs)
    A.part(ob, "PRT_nacelle", 'PRT', "pla_b", joint="PIV_tilt", stl="nacelle", print_rot=A.R_PX_DOWN,
           orient="front plate on the bed, journal up (duct roof bridges 15 mm)", supports="no", infill=25)


def plink_frame():
    S = g.S
    return G.frame((g.NAC_X0, g.WC[0], TZ + g.WC[1]), (0, S[1], -S[0]), (0, S[0], S[1]), (1, 0, 0))


def build_encoder_cap(P, cuts):
    x0 = g.NAC_X0
    rr = P.MOTOR_D / 2 + P.BORE_CLR
    cap = lprism("ecap", G.hull_circles([(g.WC, P.NAC_RW), (vadd(g.WC, g.S, -26.0), 8.0)], 96), x0 - 4, x0)
    G.bevel(cap, P.EB)
    spo = lcyl("espo", g.WC, rr - 0.25, x0 - 0.01, x0 + 4.5, n=128)
    spo = G.csg(spo, add=[lprism("erb%d" % k, crush_rib(rr - 0.5, rr, 120.0 * k), x0 + 0.5, x0 + 4.5) for k in range(3)])
    spig = G.csg(spo, sub=[lcyl("espi", g.WC, 16.0, x0 - 1, x0 + 5, n=96)])
    M = plink_frame()
    hs = C["plink_mt6701"]["holes"]["square"] / 2
    pegs = []
    for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        h = M @ Vector((sx * hs, sy * hs, 0.0))
        pegs.append(G.cyl("epg%d" % i, (h.y, h.z), C["plink_mt6701"]["holes"]["d"] / 2 - 0.1, x0 - 0.01, x0 + 1.5, 'X', n=16))
    ob = G.csg(cap, add=[spig] + pegs)
    S, N, WC = g.S, g.N, g.WC
    cut = [vadd(vadd(WC, S, -12.0), N, 7.0), vadd(vadd(WC, S, -30.0), N, 7.0), vadd(vadd(WC, S, -30.0), N, -7.0), vadd(vadd(WC, S, -12.0), N, -7.0)]
    ob = G.csg(ob, sub=[lprism("eslot", cut, x0 - 0.5, x0 + 6)] + list(cuts))
    A.part(ob, "PRT_encoder_cap", 'PRT', "pla_b", joint="PIV_tilt", stl="encoder_cap", print_rot=A.R_NX_DOWN,
           orient="back face on the bed, spigot and pegs up", supports="no", infill=40)


def write_jig(P):
    """Magnet glue jig (tool STL only, not in the assembly): plugs into the nacelle bore from the rear, its Ø7.8 spigot
    locates in the motor's Ø8 rear access hole (concentric with the bearing), magnet in a Ø6.1 pocket."""
    x0 = g.NAC_X0
    ml = P.MOTOR_L
    plug = lcyl("jig", g.WC, P.JIG_PLUG_R, x0 - 0.01, -ml, n=128)
    spg = lcyl("jsp", g.WC, P.JIG_SPIGOT_D / 2, -ml - 0.01, -ml + P.JIG_SPIGOT_L, n=64)
    fl = lprism("jfl", G.hull_circles([(g.WC, 22.0), (vadd(g.WC, g.N, 26.0), 6.0)], 64), x0 - 4.0, x0)
    G.bevel(fl, P.EB)
    ob = G.csg(plug, add=[fl, spg])
    ob = G.csg(ob, sub=[lcyl("jpk", g.WC, P.MAGNET_D / 2 + 0.05, -ml - (P.MAGNET_T - P.REAR_SHAFT_RECESS), -ml + P.JIG_SPIGOT_L + 0.5, n=32),
                        lcyl("jvt", g.WC, 1.0, x0 - 5, -ml + 1, n=12), lcyl("jgr", vadd(g.WC, g.N, 26.0), 3.0, x0 - 5, x0 + 1, n=20)])
    ob["print_rot"] = [list(r) for r in A.R_NX_DOWN]
    d = os.path.join(os.path.dirname(HERE), "stl", "tools")
    os.makedirs(d, exist_ok=True)
    E.write_stl(os.path.join(d, "encoder_jig.stl"), E.print_tris(ob))
    G.kill(ob)


# ------------------------------------------------------------------ purchased parts, cables

def build_purchased(P):
    wy, wz = P.W_P, TZ + P.W_Q
    m = PH.motor_3674("BUY_motor")
    G.xform(m, G.frame((P.X_MF, wy, wz), (1, 0, 0), (0, 1, 0), (0, 0, 1)))
    A.part(m, "BUY_motor", 'BUY', "buy_metal", joint="PIV_tilt", mass_g=C["xteam_3674"]["mass_g"], src="components.json xteam_3674")
    mg = PH.magnet("BUY_magnet")
    G.xform(mg, G.frame((-P.MOTOR_L + P.REAR_SHAFT_RECESS, wy, wz), (0, 1, 0), (0, 0, 1), (1, 0, 0)))
    A.part(mg, "BUY_magnet", 'BUY', "buy_metal", joint="PIV_flywheel", mass_g=1, src="components.json plink_mt6701.magnet")
    pk = PH.plink("BUY_plink_encoder")
    G.xform(pk, plink_frame())
    A.part(pk, "BUY_plink_encoder", 'BUY', "pcb", joint="PIV_tilt", mass_g=C["plink_mt6701"]["mass_g"], src="components.json plink_mt6701")


def build_cables(P):
    S, N, WC = g.S, g.N, g.WC
    lead_len = P.CABLE_LEADS["CAB_phase_*"]          # = components.json xteam_3674 leads.len (80)
    xe = P.POD_X[0] - 3.0          # joints to the bundle inside the straight journal bore
    for k in range(3):
        off = (k - 1) * 3.6
        a = vadd(vadd(WC, S, -(P.MOTOR_D / 2 + 4)), N, off)
        b = vadd(vadd(WC, S, -40.0), N, off)
        c = vadd(vadd((0.0, 0.0), S, 0.5), N, off * 0.55)
        A.cable("CAB_phase_%d" % k, [lpt(-67, a), lpt(-68, b), lpt(-68, c), lpt(xe, c)], 1.9, "cable_yel", joint="PIV_tilt",
                lead_len=lead_len)
    a = vadd(vadd(WC, S, -11.0), N, 5.5)
    A.cable("CAB_encoder", [lpt(g.NAC_X0 + 3.5, a), lpt(g.NAC_X0 + 2.5, vadd(vadd(WC, S, -24.0), N, 5.0)),
                            lpt(-72, vadd(vadd(WC, S, -24.0), N, 4.0)), lpt(-70, vadd(vadd(WC, S, -40.0), N, 4.0)), lpt(-70, vadd((0.0, 0.0), N, 2.5)),
                            lpt(P.IF_JOURNAL_L_X1 + 0.5, vadd((0.0, 0.0), N, 2.5))], 1.3, "cable_wht", joint="PIV_tilt",
            lead_len=P.CABLE_LEADS["CAB_encoder"])


# ------------------------------------------------------------------ build

def build(P):
    global g, TZ, P_
    TZ = P.IF_TILT_Z
    P_ = P
    g = Geo(P)
    body, jp, cv, hood, nac, ecap, ncov, leaf, nstop = [], [], [], [], [], [], [], [], []
    xo, xi, xc, xco = P.X_BODY_OUT, P.X_BODY_IN, P.X_COVER_IN, P.X_COVER_OUT
    rb = C["m3_hardware"]
    # motor + nacelle screws: pan heads counterbored into the left wall from inside the guard (bench 6a)
    hp = rb["pan_head"][1]
    for k, c in enumerate(g.MOTOR_SCREWS):
        screw("FST_motor_%d" % k, lpt(xi - hp, c), NX, 10, "M3_pan", "BUY_motor", "6a",
              cut=[("clearance", dict(head="pan", sink=hp), body), ("clearance", dict(), nac)])
    for k, c in enumerate(g.NAC_SCREWS):
        screw("FST_nacelle_%d" % k, lpt(xi - hp, c), NX, 12, "M3_pan", "PRT_nacelle", "6a",
              cut=[("clamp", dict(head="pan", sink=hp, clamp=xi - hp - P.X_MF), body), ("clamp", dict(clamp=xi - hp - P.X_MF), nac)])
    # encoder cap: 2 csk from its back face into the nacelle (6b)
    for k, c in enumerate(g.ENC_SCREWS):
        screw("FST_enc_%d" % k, lpt(g.NAC_X0 - 4, c), PX, 12, "M3_csk", "PRT_nacelle", "6b",
              cut=[("clamp", dict(head="csk", clamp=4.0), ecap), ("clamp", dict(clamp=4.0), nac)])
    # journal plate (3) and cover (4): csk from the outer face into the body (6d / 6g)
    for k, c in enumerate(g.JP_SCREWS):
        screw("FST_jp_%d" % k, lpt(xco, c), NX, 12, "M3_csk", "PRT_launcher_body", "6d",
              cut=[("clamp", dict(head="csk", clamp=xco - xc), jp), ("clamp", dict(clamp=xco - xc), body)])
    for k, c in enumerate(g.COVER_SCREWS):
        screw("FST_cover_%d" % k, lpt(xco, c), NX, 12, "M3_csk", "PRT_launcher_body", "6g",
              cut=[("clamp", dict(head="csk", clamp=xco - xc), cv), ("clamp", dict(clamp=xco - xc), body)])
    # hinge axle: M3 x 35 csk from the left wall, through the backplate boss, nut in a trap on the journal plate (6d)
    hz = lpt(xo, g.HINGE)
    screw("FST_hinge", hz, PX, P.HINGE_AXLE_L, "M3_csk", None, "6d",
          cut=[("clearance", dict(head="csk"), body), ("clearance", dict(), hood), ("clearance", dict(), jp)])
    nh = rb["nut_h"]
    nf = (xco - nh - 0.3, hz[1], hz[2])
    jp += F.nut_trap(nf, PX, depth=nh + 0.3 + 0.6, name="hgn")
    A.nut("FST_hinge_nut", nf, PX, joint="PIV_tilt", step="6d")
    # nip stud: hex head in the backplate pocket (dropped in before the backplate goes into its bay)
    # v2-A4 (A3-02 deferral closed): ISO 4017 M3 x 16 hex head, AF 5.5 x 2.0 (cadlib M3_hex), same at/into
    A.fastener("FST_nip_stud", lpt(P.NIP_X, g.JACK_PT), (0, g.NIP_U[0], g.NIP_U[1]), P.STUD_L, spec="M3_hex",
               joint="PIV_hood", step="6c")
    # v2-A1-01 nip stop: 1 x M3 x 10 cap from the pod's outer skin (counterbored), up the face plane into the pad (bench 6c)
    o, f, n = g.nip_stop_frame()
    xs = 0.5 * sum(nip_stop_x())
    mid = vadd(vadd(o, f, -P.NIP_STOP_H), n, P.NIP_STOP_T / 2)
    skin = g._surface_along(mid, (-f[0], -f[1]), g.PROFILE, step=0.1)
    sk = rb["cap_head"][1] + 0.3
    at2 = vadd(skin, f, sk)
    clamp = math.hypot(mid[0] - at2[0], mid[1] - at2[1])
    screw("FST_nipstop", lpt(xs, at2), (0, f[0], f[1]), P.NIP_STOP_SCREW_L, "M3_cap", "PRT_nip_stop", "6c",
          cut=[("clamp", dict(head="cap", sink=sk, clamp=clamp), body)])
    nstop += F.screw_hole(lpt(xs, at2), (0, f[0], f[1]), P.NIP_STOP_SCREW_L - 1.0, kind="clamp", clamp=clamp, name="nsph")   # pilot
    # ends at the screw tip (the default +1 left 0.9 under the muzzle floor)
    # nip cover: 2 csk through the cover into the land; leaf: 2 csk through the cover into the leaf root block (6e)
    Uin = (0, -g.NIP_U[0], -g.NIP_U[1])
    uo = g.SHELL_UO
    pup = (0, -g.NIP_V[0], -g.NIP_V[1])            # the nip cover prints with -v up: its screw bores lie horizontal
    for k, x in enumerate(P.NIP_SCREW_X):
        # v2-A3-A2-01: the roof rose 0.5, so the counterbore deepens with it: the head keeps bearing at u 9.8 (as in A3) and
        # the M3 x 14 keeps >= 4.2 of thread in the land (cap head + 0.2 alone gave 3.5, cadcheck warn)
        sk = max(rb["cap_head"][1] + 0.2, uo - (14.0 - 4.2))
        at = nip_world(x, uo - sk, P.NIPCOVER_SCREW_V)
        # cover bores are teardrops only (td_bore): a round cutter on top left tangent faces that fooled the inside test
        screw("FST_nipcover_%d" % k, at, Uin, 14, "M3_cap", "PRT_launcher_body", "6e", cut=[])
        ncov += td_bore(at, Uin, pup, F.RULES["m3_clear_d"] / 2, -0.6, uo - sk + 0.01, "ncc%d" % k)
        # pilot ends NIPCOVER_PILOT_OVER past the tip (screw_hole's default 1.0 left 1.12 over the hood bay)
        body += F.screw_hole(at, Uin, 14 - 1.0 + P.NIPCOVER_PILOT_OVER, kind="clamp", clamp=uo - sk, name="FST_nipcover_%d" % k)
        ncov += td_bore(at, Uin, pup, F.RULES["counterbore_d"] / 2, -sk - 0.6, 0.01, "ncb%d" % k)
        at = nip_world(P.NIP_X + (k - 0.5) * 13.0, uo, P.LEAF_SCREW_V)
        cl = uo - (g.LEAF_U0 + P.LEAF_T)
        screw("FST_leaf_%d" % k, at, Uin, 10, "M3_csk", "PRT_nip_leaf", "6e")
        # pilot runs through the root block (the +0.5 roof left a 0.3 floor at the default tip + 1.0)
        leaf += F.screw_hole(at, Uin, uo - g.LEAF_U0 + P.LEAF_BLOCK_H, kind="clamp", clamp=cl, name="FST_leaf_%d" % k)
        ncov += td_bore(at, Uin, pup, F.RULES["m3_clear_d"] / 2, -0.6, cl + 0.01, "nlc%d" % k)
        rk = F.RULES["m3_csk_head_d"] / 2 + 0.2
        ncov += td_bore(at, Uin, pup, rk + 0.6, -0.6, rk - F.RULES["m3_clear_d"] / 2, "ncs%d" % k,
                        r1=F.RULES["m3_clear_d"] / 2)

    build_nacelle(P, nac)
    build_body(P, body)
    build_journal_plate(P, jp)
    build_cover(P, cv)
    build_hood(P, hood)
    build_nip_stop(P, nstop)
    build_stop_sleeve(P)
    build_thumbwheel(P)
    build_leaf(P, leaf)
    build_nip_cover(P, ncov)
    build_flywheel(P)
    build_encoder_cap(P, ecap)
    build_purchased(P)
    build_cables(P)
    write_jig(P)
