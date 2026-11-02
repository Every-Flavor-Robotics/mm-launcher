"""Pan stage (PIV_pan): thrust ring, R108 turntable with the integral hollow hub (bore R14) and a cable groove under a
cap, 36T hub gear screwed up into the hub from below, two posts that are slices of the R108 drum (U-bores open at the
top, cable channels), the beam (closes both U-slots with tongues, carries the feeder), the tilt servo inside the right
post (spline -X on the tilt axis) behind a cover on the outer arc, and the tilt horn adapter (PIV_tilt).

Cable route: launcher bundle on-axis out of the left journal -> end-wall hole -> cavity -> left channel -> groove ->
hub bore; tilt bus from the servo foot -> notch -> right channel -> groove -> hub bore. The feeder bus drops through the
beam at IF_FEED_BUS_XY into the left channel (upper part x -104..-97.8) and follows the bundle (feeder work item).
Every screw: features.screw_hole(at, into, ...) and asm.fastener(name, at, into, ...) share at/into (screw()).

Assembly step 7 (v2-A1-06): the pod goes into the post U-slots nose-up about 20 deg (PIV_tilt 20), lowered straight
down -Z; at tilt 20 the reversed slide (+Z out) passes with 0.2 to PRT_post_L (slide_out "v2-A1-06 step 7 reversed").
Feeder mount (v2-A1-05): the beam csk holes are cut at every IF_FEED_BOLTS entry, so the -X pair follows the params
move to (-36, +/-21) and keeps 3.5 to the feeder pinion.
"""
import math
from cadlib import geom as G, features as F, asm as A
import placeholders as PH

C = PH.C
UP, DOWN, PX, NX = (0.0, 0.0, 1.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)


def screw(name, at, into, length, spec, host, step, joint="PIV_pan", cut=()):
    for kind, kw, lst in cut:
        lst += F.screw_hole(at, into, length, kind=kind, name=name, **kw)
    A.fastener(name, at, into, length, spec=spec, joint=joint, host=host, step=step)


def arc_x(R, y):
    return math.sqrt(R * R - y * y)


# ------------------------------------------------------------------ plan outlines

def rounded_plan(R, hy, cr, n=240):
    """Circle R cut to |y| <= hy with the four corners rounded cr, sampled at n polar angles (same count for any
    inset, so two of them loft into a chamfer)."""
    yc = hy - cr
    xc = math.sqrt((R - cr) ** 2 - yc ** 2)
    phi = math.atan2(yc, xc)
    dense = []
    for t in [(-phi + 2 * phi * i / 40) for i in range(41)]:
        dense.append((R * math.cos(t), R * math.sin(t)))
    for cx, cy, a0, a1, b0, b1 in ((xc, yc, phi, math.pi / 2, None, None), (-xc, yc, math.pi / 2, math.pi - phi, None, None)):
        for i in range(13):
            t = a0 + (a1 - a0) * i / 12
            dense.append((cx + cr * math.cos(t), cy + cr * math.sin(t)))
        if cx < 0:
            for t in [(math.pi - phi + 2 * phi * i / 40) for i in range(41)]:
                dense.append((R * math.cos(t), R * math.sin(t)))
    for cx, cy, a0, a1 in ((-xc, -yc, math.pi + phi, 1.5 * math.pi), (xc, -yc, 1.5 * math.pi, 2 * math.pi - phi)):
        for i in range(13):
            t = a0 + (a1 - a0) * i / 12
            dense.append((cx + cr * math.cos(t), cy + cr * math.sin(t)))
    out = []
    m = len(dense)
    for k in range(n):
        th = 2 * math.pi * k / n
        d = (math.cos(th), math.sin(th))
        best = None
        for i in range(m):
            p, q = dense[i], dense[(i + 1) % m]
            ex, ey = q[0] - p[0], q[1] - p[1]
            den = d[0] * ey - d[1] * ex
            if abs(den) < 1e-12:
                continue
            s = (p[0] * ey - p[1] * ex) / den          # ray parameter
            u = (p[0] * d[1] - p[1] * d[0]) / den      # segment parameter
            if s > 0 and -1e-9 <= u <= 1 + 1e-9 and (best is None or s < best):
                best = s
        out.append((best * d[0], best * d[1]))
    return out


def sector(c, r0, r1, a0, a1, n=10):
    """Annular sector in a profile plane, angles in degrees from +u toward +v."""
    pts = [(c[0] + r1 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r1 * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
           for i in range(n + 1)]
    pts += [(c[0] + r0 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), c[1] + r0 * math.sin(math.radians(a1 - (a1 - a0) * i / n)))
            for i in range(n + 1)]
    return pts


# ------------------------------------------------------------------ printed parts

def build_turntable(P, cuts):
    R, z0, z1 = P.IF_TT_R, P.IF_TT_Z0, P.IF_TT_Z1
    # one revolved profile (a cone unioned onto a cylinder leaves an internal face where their sides coincide)
    tt = G.revolve("tt", [(10.0, z0), (R - P.CH, z0), (R, z0 + P.CH), (R, z1), (10.0, z1)],
                   (P.IF_PAN_XY[0], P.IF_PAN_XY[1], 0.0), n=256)       # the drum's one chamfer at its foot
    G.bevel(tt, P.EB)
    hub = G.cyl("hub", P.IF_PAN_XY, P.IF_HUB_R, P.IF_GEAR_Z[1], z0 + 0.5)
    tt = G.csg(tt, add=[hub])
    gx0, gx1, gy0, gy1, gz = P.TT_GROOVE
    t = P.GCAP_T
    sub = list(cuts)
    sub.append(G.cyl("bore", P.IF_PAN_XY, P.IF_HUB_BORE_R, P.IF_GEAR_Z[1] - 1, z1 + 1))
    sub.append(G.box("grv", gx0, gx1, gy0, gy1, gz, z1 + 1))          # open top: post feet / the cap close it
    sub.append(G.box("grvc", -10.0, 10.0, gy0 + 6.0, -6.0, gz, z1 + 1))     # groove -> bore without a sliver
    tt = G.csg(tt, sub=sub)
    A.part(tt, "PRT_turntable", 'PRT', "pla_a", joint="PIV_pan", stl="turntable", print_rot=A.R_FLIP,
           orient="top face on the bed, hub up (groove and cap rebate open to the bed)", supports="no", infill=15)


def build_groove_cap(P, cuts):
    z1, t, c = P.IF_TT_Z1, P.GCAP_T, 0.2
    strip = G.box("gc", P.IF_ARM_L_IN + c, P.IF_ARM_R_IN - c, P.GCAP_Y[0], P.GCAP_Y[1], z1, z1 + t)
    disc = G.cyl("gcd", P.IF_PAN_XY, P.GCAP_DISC_R, z1, z1 + t)
    cap = G.csg(strip, add=[disc])
    G.bevel(cap, 0.6)
    cap = G.csg(cap, sub=list(cuts))
    A.part(cap, "PRT_groove_cap", 'PRT', "pla_a", joint="PIV_pan", stl="groove_cap", print_rot=A.R_ID,
           orient="flat, countersinks up", supports="no", infill=40)


def build_thrust_ring(P):
    r0, r1 = P.RING_R
    ring = G.cyl("tr", P.IF_PAN_XY, r1, P.IF_DECK_Z, P.IF_TT_Z0)
    G.bevel(ring, 0.4)
    ring = G.csg(ring, sub=[G.cyl("tri", P.IF_PAN_XY, r0, P.IF_DECK_Z - 1, P.IF_TT_Z0 + 1)])
    A.part(ring, "PRT_thrust_ring", 'PRT', "pla_b", joint="PIV_pan", stl="thrust_ring", print_rot=A.R_ID,
           orient="flat", supports="no", infill=100)


def build_hub_gear(P, cuts):
    z0, z1 = P.IF_GEAR_Z
    g = G.prism("hg", G.gear_poly(P.IF_GEAR_M, P.IF_GEAR_N, c=P.IF_PAN_XY, backlash=P.GEAR_BACKLASH, phase=0.0), z0, z1, 'Z')
    # n=256: the R13 bore sits 1.0 off the bus splice envelope (v2-A5-03); the default facets put the flats 0.03 inside R13
    g = G.csg(g, sub=[G.cyl("hgb", P.IF_PAN_XY, P.HUB_GEAR_BORE_R, z0 - 1, z1 + 1, n=256)] + list(cuts))
    A.part(g, "PRT_hub_gear", 'PRT', "pla_b", joint="PIV_pan", stl="hub_gear", print_rot=A.R_ID,
           orient="flat, screw heads' face down", supports="no", infill=40)


def post_blank(P, name, x0, x1):
    """Slice of the R108 drum between x0 and x1 over IF_POST_Y, inner vertical corners CR."""
    y0, y1 = P.IF_POST_Y
    left = x1 < 0
    xa, xb = (-130.0, x1) if left else (x0, 130.0)
    pl = G.prism(name, G.rrect(xa, xb, y0, y1, P.CR, 8), P.IF_TT_Z1, P.IF_BEAM_Z0, 'Z')
    d = G.cyl(name + "d", P.IF_PAN_XY, P.IF_TT_R, P.IF_TT_Z1 - 1, P.IF_BEAM_Z0 + 1, n=256)
    ob = G.csg(pl, inter=[d])
    G.bevel(ob, P.EB)
    return ob


def inner_top_chamfer(P, name, x_in, s):
    """45 x CH reveal along the inner face's top edge (s = +1 if the post lies at +x of its inner face)."""
    z = P.IF_BEAM_Z0
    h = P.CH
    tri = [(x_in - s * 1.0, z - h - 1.0), (x_in - s * 1.0, z + 1.0), (x_in + s * (h + 1.0), z + 1.0)]
    if s < 0:
        tri.reverse()
    return G.prism(name, tri, P.IF_POST_Y[0] - 1, P.IF_POST_Y[1] + 1, 'Y')


def u_bore(P, name, x0, x1):
    r, zt = P.IF_BORE_R, P.IF_TILT_Z
    b = G.cyl(name, (P.IF_TILT_Y, zt), r, x0, x1, 'X')
    return [b, G.box(name + "u", x0, x1, -r, r, zt, P.IF_BEAM_Z0 + 1)]


def build_post_L(P, cuts):
    x_in = P.IF_ARM_L_IN
    ob = post_blank(P, "PRT_post_L", -P.IF_TT_R - 1, x_in)
    cx0, cx1, cy0, cy1 = P.IF_POST_L_CHANNEL
    kx0, kx1, ky0, ky1, kz0, kz1 = P.POST_L_CAVITY
    z0 = P.IF_TT_Z1
    sub = list(cuts)
    sub += u_bore(P, "lb", P.POST_L_BORE_X0, x_in + 1)
    sub.append(G.prism("lwh", G.teardrop((P.IF_TILT_Y, P.IF_TILT_Z), 7.0, up=(0, 1)), P.POST_L_WALL_X - 1, P.POST_L_BORE_X0 + 0.5, 'X'))
    sub.append(G.box("lch_o", cx0, kx1, cy0, cy1, z0 - 1, P.IF_BEAM_Z0 + 1))        # outer channel strip, full height
    sub.append(G.box("lch_i", kx1 - 0.01, cx1, cy0, cy1, z0 - 1, 209.0))           # full IF width below the bore
    sub.append(G.box("lcav", kx0, kx1, ky0, ky1, kz0, kz1))
    fx, fy = P.IF_FEED_BUS_XY
    sub.append(G.box("lfb", fx - 2.5, P.POST_L_BORE_X0 + 0.1, fy - 2.6, fy + 2.6, P.IF_BEAM_Z0 - 6, P.IF_BEAM_Z0 + 1))  # bus drop-in
    sub.append(inner_top_chamfer(P, "lcf", x_in, -1))
    ob = G.csg(ob, sub=sub)
    A.part(ob, "PRT_post_L", 'PRT', "pla_a", joint="PIV_pan", stl="post_L", print_rot=A.R_ID,
           orient="upright, foot on the bed (U-bore opens to the top; channel cavity roofs bridge 6 mm)",
           supports="no", infill=25)


def stop_lug(P, name, a0, a1):
    """Right-post hard stop on the inner face: radial contact faces, outer arc drafted 45 deg (prints upright)."""
    r0, r1 = P.IF_STOP_R
    xt, xr = P.IF_STOP_POST_X
    c = (P.IF_TILT_Y, P.IF_TILT_Z)
    tip = sector(c, r0, r1, a0, a1)
    root = sector(c, r0, r1 + (xr - xt), a0, a1)
    return G.loft(name, root, tip, xr + 0.5, xt, 'X')


def stop_angles(P):
    a, hw = P.IF_STOP_JP_A, P.IF_STOP_JP_HW
    hi = (a + hw + P.TILT_STOP_HI, a + hw + P.TILT_STOP_HI + 12.0)     # touched by the jp lug's upper face at +46
    lo = (a - hw + P.TILT_STOP_LO - 12.0, a - hw + P.TILT_STOP_LO)     # touched by its lower face at -3
    return hi, lo


def build_post_R(P, cuts_post, cuts_cover):
    x_in = P.IF_ARM_R_IN
    ob = post_blank(P, "PRT_post_R", x_in, P.IF_TT_R + 1)
    hi, lo = stop_angles(P)
    ob = G.csg(ob, add=[stop_lug(P, "sth", *hi), stop_lug(P, "stl", *lo)])
    g = Servo(P)
    cx0, cx1, cy0, cy1 = P.IF_POST_R_CHANNEL
    cl = P.SERVO_POCKET_CLR
    xc = P.POST_R_COVER_X
    sub = list(cuts_post)
    sub += u_bore(P, "rb", x_in - 1, P.POST_R_BORE_X1)
    sub.append(G.prism("rtd", G.teardrop((P.IF_TILT_Y, P.IF_TILT_Z), P.POST_R_TEAR_R, up=(0, 1)), P.POST_R_BORE_X1 - 0.01, xc + 1, 'X'))
    sub.append(G.box("rpk", g.x0 - cl, xc + 1, g.y0 - cl, g.y1 + cl, g.z0 - cl, g.z1 + cl))
    sub.append(G.box("rnt", 84.0, 94.5, -18.0, -6.0, 182.0, g.z0 - cl + 0.3))           # lead notch: pocket -> channel
    sub.append(G.box("rch", cx0, cx1, cy0, cy1, P.IF_TT_Z1 - 1, P.POST_R_CHANNEL_Z1))
    sub.append(inner_top_chamfer(P, "rcf", x_in, 1))
    ob = G.csg(ob, sub=sub)
    # split the outer-arc cover off: the servo slides out +X through it
    zc0, zc1 = P.POST_R_COVER_Z
    band = G.box("cvb", xc, P.IF_TT_R + 2, P.IF_POST_Y[0] - 2, P.IF_POST_Y[1] + 2, zc0, zc1)
    band2 = G.box("cvb2", xc, P.IF_TT_R + 2, P.IF_POST_Y[0] - 2, P.IF_POST_Y[1] + 2, zc0, zc1)
    cover = G.csg(G.cyl("cvd", P.IF_PAN_XY, P.IF_TT_R, zc0 - 1, zc1 + 1, n=256), inter=[band2])
    y0, y1 = P.IF_POST_Y
    cover = G.csg(cover, inter=[G.box("cvy", xc - 1, P.IF_TT_R + 2, y0, y1, zc0 - 1, zc1 + 1)])
    G.bevel(cover, 0.6)
    idler = G.cyl("cvi", (P.IF_TILT_Y, P.IF_TILT_Z), 3.0 + P.SERVO_POCKET_CLR + 0.2, xc - 1, g.x1 + C["hiwonder_bus_servo"]["idler_boss"]["protrudes"] + 0.5, 'X')
    cover = G.csg(cover, sub=list(cuts_cover) + [idler])        # servo idler boss locates in the cover
    ob = G.csg(ob, sub=[band])
    A.part(ob, "PRT_post_R", 'PRT', "pla_a", joint="PIV_pan", stl="post_R", print_rot=A.R_ID,
           orient="upright, foot on the bed (servo pocket roof bridges 21 mm, teardrop passage, stop lugs drafted)",
           supports="no", infill=25)
    A.part(cover, "PRT_post_R_cover", 'PRT', "pla_a", joint="PIV_pan", stl="post_R_cover", print_rot=A.R_NX_DOWN,
           orient="flat inner face on the bed, arc face up", supports="no", infill=25)


def build_beam(P, cuts):
    R, (b0, b1) = P.IF_TT_R, P.IF_BEAM_Y
    z0, z1 = P.IF_BEAM_Z0, P.IF_BEAM_Z1
    hy = 0.5 * (b1 - b0)
    p0 = rounded_plan(R, hy, P.CR)
    # chamfer by intersecting with a frustum whose side crosses the plan at z1 - CH (no coincident side faces)
    beam = G.prism("beam", p0, z0, z1, 'Z')
    q0 = rounded_plan(R + 1.0, hy + 1.0, P.CR + 1.0)
    q1 = rounded_plan(R - P.CH - 1.0, hy - P.CH - 1.0, P.CR - P.CH - 1.0)
    fr = G.loft("beamf", q0, q1, z1 - P.CH - 1.0, z1 + 1.0, 'Z')
    fr = G.csg(fr, add=[G.box("beamfb", -200, 200, -200, 200, z0 - 2.0, z1 - P.CH - 0.5)])
    beam = G.csg(beam, inter=[fr])
    G.bevel(beam, P.EB)
    # tongues close both U-slots: 0.2 radial to the journals (bore radius), 0.1 to the slot walls
    add = []
    r = P.IF_BORE_R
    for nm, x0, x1 in (("tgL", P.POST_L_BORE_X0 + 0.1, P.IF_ARM_L_IN - 0.1), ("tgR", P.IF_ARM_R_IN + 0.1, P.POST_R_BORE_X1 - 0.1)):
        t = G.box(nm, x0, x1, -r + 0.1, r - 0.1, P.IF_TILT_Z + 9.0, z0 + 0.5)     # flat foot: no slivers
        t = G.csg(t, sub=[G.cyl(nm + "j", (P.IF_TILT_Y, P.IF_TILT_Z), r, x0 - 1, x1 + 1, 'X')])
        add.append(t)
    beam = G.csg(beam, add=add)
    sub = list(cuts)
    sub.append(G.cyl("bh", P.IF_DROP_XY, P.IF_BEAM_HOLE_D / 2, z0 - 1, z1 + 1))
    for i, (x, y) in enumerate(P.IF_FEED_BOLTS):          # feeder housing screws: csk from the beam underside, up
        sub += F.screw_hole((x, y, z0), UP, P.IF_BEAM_T, kind="clearance", head="csk", name="fb%d" % i)
    fx, fy = P.IF_FEED_BUS_XY
    sub.append(G.cyl("bfb", (fx, fy), 2.5, z0 - 1, z1 + 1))
    beam = G.csg(beam, sub=sub)
    A.part(beam, "PRT_beam", 'PRT', "pla_a", joint="PIV_pan", stl="beam", print_rot=A.R_FLIP,
           orient="top face on the bed, tongues up", supports="no", infill=30)


# ------------------------------------------------------------------ tilt drive

class Servo:
    """Tilt servo in the right post: spline -X on the tilt axis, tip at IF_TILT_SPLINE_X, length vertical."""

    def __init__(self, P):
        s = C["hiwonder_bus_servo"]
        L, W, H = s["body"]
        self.face = P.IF_TILT_SPLINE_X + s["spline"]["protrudes"]          # 55.9
        self.x0, self.x1 = self.face, self.face + H
        self.y0, self.y1 = P.IF_TILT_Y - W / 2, P.IF_TILT_Y + W / 2
        zc = P.IF_TILT_Z - s["spline"]["offset_from_body_centre"]
        self.z0, self.z1 = zc - L / 2, zc + L / 2
        hc = C["servo_horn_disc"]
        self.horn_x0 = self.face - P.HORN_LIFT                              # hub underside
        self.disc_in = self.horn_x0 - hc["hub"]["h"]                        # disc face toward the servo
        self.disc_out = self.disc_in - hc["disc"]["t"]                      # disc face toward the adapter


def build_tilt_drive(P):
    g = Servo(P)
    zt, yt = P.IF_TILT_Z, P.IF_TILT_Y
    M = G.frame((g.face, yt, zt), (0, 0, 1), (0, 1, 0), (-1, 0, 0))
    sv = PH.servo("BUY_servo_tilt")
    sv = G.csg(sv, sub=[G.cyl("svb", (0, 0), 3.1, -4.1, 10)])               # spline belongs to the horn (PIV_tilt)
    G.xform(sv, M)
    A.part(sv, "BUY_servo_tilt", 'BUY', "buy", joint="PIV_pan", mass_g=C["hiwonder_bus_servo"]["mass_g"], src="components.json")
    hn = PH.horn("BUY_horn_tilt")
    spl = G.cyl("spl", (0, 0), C["hiwonder_bus_servo"]["spline"]["boss_d"] / 2, -P.HORN_LIFT - 4.0,
                C["hiwonder_bus_servo"]["spline"]["protrudes"] - P.HORN_LIFT)
    hn = G.csg(hn, add=[spl])
    G.xform(hn, G.frame((g.horn_x0, yt, zt), (0, 0, 1), (0, 1, 0), (-1, 0, 0)))
    A.part(hn, "BUY_horn_tilt", 'BUY', "buy_metal", joint="PIV_tilt", mass_g=C["servo_horn_disc"]["mass_g"],
           src="components.json servo_horn_disc (+ the servo output spline)")
    # adapter: disc in the journal counterbore, 1.0 horn recess on +X, 12 AF key into the journal-plate socket
    ar, ax0, ax1 = P.IF_TILT_ADAPTER
    kx0, kx1 = P.IF_TILT_KEY_X
    d = G.cyl("tha", (yt, zt), ar, ax0, ax1, 'X')
    G.bevel(d, 0.6)
    key = G.prism("thak", G.hexagon((yt, zt), P.IF_TILT_KEY_AF), kx0, kx1 + 1.0, 'X')
    G.bevel(key, 0.5)
    hd = C["servo_horn_disc"]
    cuts = F.horn_recess((ax1, yt, zt), NX, disc_d=hd["disc"]["d"], depth=P.HORN_RECESS,
                         bolt_circle_d=hd["holes"]["bolt_circle_d"], n_holes=hd["holes"]["n"],
                         centre_hole_d=P.IF_TILT_KEY_HOLE_D, name="tha")
    ad = G.csg(d, add=[key])
    ad = G.csg(ad, sub=cuts)
    A.part(ad, "PRT_tilt_horn_adapter", 'PRT', "pla_b", joint="PIV_tilt", stl="tilt_horn_adapter", print_rot=A.R_PX_DOWN,
           orient="horn recess face on the bed, hex key up", supports="no", infill=60)
    # horn -> adapter on the bench (M2 through 4 horn holes, drill the dimples with the horn as template), then the
    # centre screw through the key's 6.5 hole into the spline
    bc = hd["holes"]["bolt_circle_d"] / 2
    for i in range(4):
        a = math.radians(90 * i)
        A.fastener("FST_tilt_horn_%d" % i, (g.disc_in, yt + bc * math.sin(a), zt + bc * math.cos(a)), NX, 8,
                   spec="M2_pan", joint="PIV_tilt", host="PRT_tilt_horn_adapter", step="8a")
    A.fastener("FST_tilt_horn_ctr", (g.disc_out, yt, zt), PX, 6, spec="M3_cap", joint="PIV_tilt", host="BUY_horn_tilt",
               step="8b")


# ------------------------------------------------------------------ cables

def build_cables(P):
    zt = P.IF_TILT_Z
    gz = 0.5 * (P.TT_GROOVE[4] + P.IF_TT_Z1)
    gy = 0.5 * (P.TT_GROOVE[2] + P.TT_GROOVE[3])
    kx = 0.5 * (P.POST_L_CAVITY[0] + P.POST_L_CAVITY[1])
    # v2-A5-03: the bundle ends off the axis at BUS_LB_JCT (az 235, r 4, z 70, under the splice); the tilt bus ends on the splice top face
    A.cable("CAB_launcher_bundle", [(P.IF_JOURNAL_L_X1 + 0.5, P.IF_TILT_Y, zt), (kx, P.IF_TILT_Y, zt), (kx, -8.0, zt - 1),
                                    (kx, gy, zt - 6), (kx, gy, 200.0), (-98.0, gy, 185.0), (-98.0, gy, 106.0),
                                    (-95.0, gy, gz), (-8.0, gy, gz)] + P.LB_HUB, P.BUNDLE_R, "cable_blk", joint="PIV_pan",
            lead_len=P.CABLE_LEADS["CAB_launcher_bundle"])
    A.cable("CAB_bus_tilt", [(88.0, -8.0, 190.2), (92.0, -15.0, 186.0), (95.0, gy, 178.0), (95.0, gy, 106.0),
                             (92.0, gy, gz), (8.0, gy, gz)] + P.BUS_HUB, P.BUS_R, "cable_wht", joint="PIV_pan",
            lead_len=P.CABLE_LEADS["CAB_bus_tilt"])
    # v2-A6-02: the pan bus lead's PIV_pan tail, from the static loop's end on the pan axis (BUS_PAN_AX, z 63) out to the
    # splice axis (az 35) and up to its bottom face centre (BUS_JCT_BOT, z 74). Coaxial with the static end, so the joint never
    # opens over pan. No lead_len: the cable_chains row "pan bus lead" (350) sums CAB_bus_pan + this tail.
    ca, sa = math.cos(math.radians(P.BUS_JCT["az"])), math.sin(math.radians(P.BUS_JCT["az"]))
    vb = lambda r, z: (P.IF_PAN_XY[0] + r * ca, P.IF_PAN_XY[1] + r * sa, z)
    A.cable("CAB_bus_pan_tail", [P.BUS_PAN_AX, vb(3.5, 66.0), vb(7.0, 68.0), P.BUS_JCT_BOT], P.BUS_R, "cable_wht",
            joint="PIV_pan", step="11a")


def build_bus_junction(P):
    """v2-A5-03: BOM 14a, the 3-way Hiwonder bus splice in the hub bore (envelope only; PIV_pan, axis Z)"""
    j = P.BUS_JCT
    ob = G.cyl("bjc", P.BUS_JCT_XY, j["d"] / 2, j["z0"], j["z0"] + j["l"], n=128)
    G.bevel(ob, 1.0)
    A.part(ob, "BUY_bus_junction", 'BUY', "cable_wht", joint="PIV_pan", mass_g=8,
           src="3 x 3-to-1 solder splices under heat shrink, sleeved (BOM 14a): servo bus V+/GND/signal of CAB_bus_pan, "
               "CAB_bus_tilt and CAB_bus_feeder; Ø10 x 25 envelope")


# ------------------------------------------------------------------ build

def build(P):
    tt, gc, hg, pl, pr, cv, bm = [], [], [], [], [], [], []
    z1 = P.IF_TT_Z1
    # groove cap (2 mm strip + disc on the flat turntable top): csk M3 x 8 self-tappers into the lands each side of
    # the groove and 2 in the disc (step 11a, pod at tilt 45, after every bus lead is in the groove; v2-A6-01)
    gpts = [(-60.0, -25.2), (-60.0, -9.0), (22.0, -25.2), (22.0, -9.0), (-10.0, 16.2), (10.0, 16.2)]
    for i, (x, y) in enumerate(gpts):
        screw("FST_gcap_%d" % i, (x, y, z1 + P.GCAP_T), DOWN, 10, "M3_csk", "PRT_turntable", "11a",
              cut=[("clamp", dict(clamp=P.GCAP_T, head="csk"), gc), ("clamp", dict(clamp=P.GCAP_T, head="csk"), tt)])
    # posts: csk M3 x 16 from the turntable underside into the post feet (bench 2c, before the turntable goes on)
    ppts_L = [(-97.0, 2.0), (-97.0, 15.0), (-101.0, -6.0)]
    ppts_R = [(50.0, 16.0), (50.0, -5.0), (80.0, 16.0), (80.0, -5.0)]
    for i, (x, y) in enumerate(ppts_L + ppts_R):
        host = "PRT_post_L" if x < 0 else "PRT_post_R"
        screw("FST_post_%d" % i, (x, y, P.IF_TT_Z0), UP, 16, "M3_csk", host, "2c",
              cut=[("clamp", dict(clamp=10.0, head="csk"), tt), ("clamp", dict(clamp=10.0, head="csk"), pl if x < 0 else pr)])
    # hub gear: 3 x M3 x 12 cap up through the gear into the hub wall (floor still off, step 2d)
    for i, a in enumerate((90.0, 210.0, 330.0)):
        x, y = P.HUB_SCREW_R * math.cos(math.radians(a)), P.HUB_SCREW_R * math.sin(math.radians(a))
        screw("FST_hub_%d" % i, (x, y, P.IF_GEAR_Z[0]), UP, 12, "M3_cap", "PRT_turntable", "2d",
              cut=[("clamp", dict(clamp=P.IF_GEAR_Z[1] - P.IF_GEAR_Z[0]), hg), ("clamp", dict(clamp=P.IF_GEAR_Z[1] - P.IF_GEAR_Z[0]), tt)])
    # beam: csk M3 x 16 from the top into the post tops
    bpts = [(-102.5, 10.0), (-101.5, -5.0), (-95.0, 19.0), (56.0, 19.0), (56.0, -21.0), (90.0, 16.0), (90.0, -19.0)]
    for i, (x, y) in enumerate(bpts):
        host = "PRT_post_L" if x < 0 else "PRT_post_R"
        screw("FST_beam_%d" % i, (x, y, P.IF_BEAM_Z1), DOWN, 16, "M3_csk", host, "9",
              cut=[("clamp", dict(clamp=P.IF_BEAM_T, head="csk"), bm), ("clamp", dict(clamp=P.IF_BEAM_T, head="csk"), pl if x < 0 else pr)])
    # right-post cover: 4 csk M3 x 16 in -X through the cover into the post
    xc = P.POST_R_COVER_X
    for i, (y, z) in enumerate(((17.0, 196.0), (-17.0, 196.0), (17.0, 238.0), (-17.0, 238.0))):
        sk = 3.2
        xa = arc_x(P.IF_TT_R, y) - sk
        screw("FST_postcover_%d" % i, (xa, y, z), NX, 14, "M3_cap", "PRT_post_R", "8c",
              cut=[("clamp", dict(clamp=xa - xc, head="cap", sink=sk), cv), ("clamp", dict(clamp=xa - xc, head="cap", sink=sk), pr)])

    build_thrust_ring(P)
    build_turntable(P, tt)
    build_groove_cap(P, gc)
    build_hub_gear(P, hg)
    build_post_L(P, pl)
    build_post_R(P, pr, cv)
    build_beam(P, bm)
    build_tilt_drive(P)
    build_cables(P)
    build_bus_junction(P)
