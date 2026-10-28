"""Pan stage (PIV_pan), v3 attempt 1 (min-hardware): thrust ring, PRT_turntable (R108 drum + both posts, one print,
bottom-down), PRT_hub_gear (36T + the R20 hub tube, snapped up into the turntable socket), PRT_beam (beam + the v2 feeder
housing: feed floor at z 263, spout; 4 snap hooks into the post tops), the tilt servo top-loaded into the right post, and
the tilt horn adapter (PIV_tilt, HORN pocket + 8 printed pins, double-D key in the journal plate's top-open fork).

Joints (DESIGN_LOG "Attempt 1: plan" joint table):
  FST_post x7     MERGE: posts are part of PRT_turntable (printed bottom-down, posts upright as v2 printed them).
  FST_hub x3      SNAP-V: 3 fingers in the hub tube wall click their barbs over a ledge in the turntable socket; 3 torque
                  dogs on the tube top sit in turntable pockets. Permanent.
  FST_gcap x6     eliminated with the groove cap: the groove is 2 closed tunnels (roof bridged), the hub bore has a printed
                  roof (45 deg cone to an R11.5 flat), the bus splice is soldered below the deck and pushed up the bore.
  FST_postcover x4 eliminated with the cover: the servo pocket, its idler slot and the passage open to the post top; the
                  tilt drive drops in -Z at tilt 0; the beam tongue closes the pocket 0.43 over the servo.
  FST_beam x7     SNAP-V: 4 hooks on the beam (L 20, t 1.4) into slots in the post tops; release with a flat screwdriver
                  through slots in the posts' inner faces.
  FST_tilt_horn x4 HORN: 2.7 pocket + 8 O2.0 pins; FST_tilt_horn_ctr (servo centre screw) kept.

Cables: each lead has its own route (V2R7 A7-02): bundle (inner) and feeder bus (outer) down the left post channel, the
tilt bus down the right one, R15 into the tunnels, then to the bore: the bundle drops to BUS_LB_JCT, the two bus leads run
side by side (+/-1.5) onto the splice top (params hub_bus / fillet_path).
"""
import math
from cadlib import geom as G, features as F, asm as A
import placeholders as PH

C = PH.C
UP, DOWN, PX, NX = (0.0, 0.0, 1.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)


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



def plan_box(name, az, r0, r1, t0, t1, z0, z1, c=(0.0, 0.0)):
    """box in the hub's polar frame: radial r0..r1 along az, tangential t0..t1, z0..z1"""
    er = (math.cos(math.radians(az)), math.sin(math.radians(az)))
    et = (-er[1], er[0])
    pts = [(c[0] + r * er[0] + t * et[0], c[1] + r * er[1] + t * et[1]) for r, t in ((r0, t0), (r1, t0), (r1, t1), (r0, t1))]
    return G.prism(name, pts, z0, z1, 'Z')


def polar_prism(name, az, prof, t0, t1, c=(0.0, 0.0)):
    """(r, z) profile swept straight over tangential t0..t1 at azimuth az"""
    ob = G.prism(name, prof, t0, t1, 'Y')            # (u, v, w) = (r, z, t) -> world (x, z, y) before the turn
    er = (math.cos(math.radians(az)), math.sin(math.radians(az)), 0.0)
    G.xform(ob, G.frame((c[0], c[1], 0.0), er, (-er[1], er[0], 0.0), (0.0, 0.0, 1.0)))
    return ob


# ------------------------------------------------------------------ printed parts

def build_thrust_ring(P):
    r0, r1 = P.RING_R
    ring = G.cyl("tr", P.IF_PAN_XY, r1, P.IF_DECK_Z, P.IF_TT_Z0)
    G.bevel(ring, 0.4)
    ring = G.csg(ring, sub=[G.cyl("tri", P.IF_PAN_XY, r0, P.IF_DECK_Z - 1, P.IF_TT_Z0 + 1, n=256)])
    A.part(ring, "PRT_thrust_ring", 'PRT', "pla_b", joint="PIV_pan", stl="thrust_ring", print_rot=A.R_ID,
           orient="flat", supports="no", infill=100)


def tunnel_cuts(P):
    """2 closed tunnels (left post channel -> hub, right post channel -> hub) with R15 centreline bends, and the hub pocket"""
    x0, x1, y0, y1, zf = P.TT_GROOVE
    zc, zr, R = P.TT_TUNNEL_ZC, P.TT_TUNNEL_Z1, P.TT_TUNNEL_BEND_R
    h = zc - zf                                        # 3.3: half band
    xl, xr = -98.0 + R, 95.0 - R                        # bend centres (channel centrelines x -98 / 95)
    zh = P.TT_HUB_Z1                                   # lower ceiling over the hub zone: its bridge stays apart from the roof
    xh = P.TT_HUB_X
    cut = [G.box("tunL", xl, -xh, y0, y1, zf, zr), G.box("tunR", xh, xr, y0, y1, zf, zr), G.box("tunH", -xh - 0.01, xh + 0.01, y0, y1, zf, zh)]
    cut.append(G.prism("tbl", sector((xl, zc + R), R - h, R + h, 180.0, 270.0, 24), y0, y1, 'Y'))
    cut.append(G.prism("tbr", sector((xr, zc + R), R - h, R + h, 270.0, 360.0, 24), y0, y1, 'Y'))
    px0, px1, py0, py1 = P.TT_HUB_POCKET
    cut.append(G.box("thp", px0, px1, py0, py1, zf, zh))
    return cut


def hub_socket_cuts(P):
    """turntable side of the hub joint: 45 deg cone cavity (bed to the flat roof), 3 dog pockets, 3 finger slots with
    their barb pockets (the material under a barb pocket is the ledge)"""
    z0 = P.IF_TT_Z0
    rc, zc0 = P.HUB_CONE
    zr = P.HUB_ROOF_Z
    c = P.IF_PAN_XY
    cut = [G.cone("hcn", c, rc + (zc0 - (z0 - 1)), rc - (zr - zc0), z0 - 1, zr, n=128)]
    d = P.HUB_DOG
    for i, az in enumerate(d["az"]):
        hw = d["w"] / 2 + d["clr"]
        cut.append(plan_box("hdp%d" % i, az, P.HUB_TUBE_R[0] - 2.0, P.HUB_TUBE_R[1] + 0.2, -hw, hw, z0 - 1, d["top"] + 0.2))
    f = P.HUB_FINGER
    for i, az in enumerate(f["az"]):
        hw = f["w"] / 2 + 0.3
        ro = P.HUB_TUBE_R[1]
        cut.append(plan_box("hfp%d" % i, az, ro - f["t"] - 0.2, P.HUB_SOCKET_R, -hw, hw, z0 - 1, f["tip_z"] + 0.3))
        cut.append(plan_box("hfb%d" % i, az, ro - 0.05, ro + f["barb"] + 0.05 + 0.25, -hw, hw, f["ledge_z"], f["tip_z"] + 0.3))
    return cut


def hook_slot_cuts(P):
    """post-top slots for the 4 beam hooks + the screwdriver release slots through the posts' inner faces"""
    hk = P.BEAM_HOOK
    zt = P.IF_BEAM_Z0 - hk["L"]
    zc = zt + 1.8                                       # barb catch face (ledge underside 0.05 above)
    cut = []
    for i, (xb, y, s) in enumerate(hk["pos"]):
        hw = hk["w"] / 2 + 0.3
        xa, xf = xb - s * (hk["t"] + 1.0), xb + s * 0.1       # back gap 1.0 (release 0.7), front 0.1
        cut.append(G.box("hks%d" % i, min(xa, xf), max(xa, xf), y - hw, y + hw, zt - 1.5, P.IF_BEAM_Z0 + 1))
        x_in = P.IF_ARM_L_IN if s > 0 else P.IF_ARM_R_IN
        rw = hk["slot_hw"]
        cut.append(G.box("hkr%d" % i, min(xb - s * 0.01, x_in + s), max(xb - s * 0.01, x_in + s), y - rw, y + rw, zt - 1.5, zc + 0.05))
    return cut


def build_turntable(P):
    """turntable drum + both posts, one print (bottom-down). Posts: slices of the R108 drum over IF_POST_Y."""
    R, z0, z1, zb = P.IF_TT_R, P.IF_TT_Z0, P.IF_TT_Z1, P.IF_BEAM_Z0
    y0, y1 = P.IF_POST_Y
    drum = G.revolve("tt", [(10.0, z0), (R - P.CH, z0), (R, z0 + P.CH), (R, zb), (10.0, zb)],
                     (P.IF_PAN_XY[0], P.IF_PAN_XY[1], 0.0), n=256)
    keep = G.box("ttk", -200, 200, -200, 200, z0 - 1, z1)
    keep = G.csg(keep, add=[G.prism("pLk", G.rrect(-130.0, P.IF_ARM_L_IN, y0, y1, P.CR, 8), z1 - 1, zb + 1, 'Z'),
                            G.prism("pRk", G.rrect(P.IF_ARM_R_IN, 130.0, y0, y1, P.CR, 8), z1 - 1, zb + 1, 'Z')])
    tt = G.csg(drum, inter=[keep])
    G.bevel(tt, P.EB)
    tt = G.csg(tt, add=[G.cyl("ttc", P.IF_PAN_XY, 12.0, z0 + 2.0, z1)])  # bore roof material (drum ID is 10)
    hi, lo = stop_angles(P)
    tt = G.csg(tt, add=[stop_lug(P, "sth", *hi), stop_lug(P, "stl", *lo)])
    sub = tunnel_cuts(P) + hub_socket_cuts(P) + hook_slot_cuts(P)
    # ---- left post (v2 build_post_L cuts)
    x_in = P.IF_ARM_L_IN
    cx0, cx1, cy0, cy1 = P.IF_POST_L_CHANNEL
    kx0, kx1, ky0, ky1, kz0, kz1 = P.POST_L_CAVITY
    sub += u_bore(P, "lb", P.POST_L_BORE_X0, x_in + 1)
    sub.append(G.prism("lwh", G.teardrop((P.IF_TILT_Y, P.IF_TILT_Z), 7.0, up=(0, 1)), P.POST_L_WALL_X - 1, P.POST_L_BORE_X0 + 0.5, 'X'))
    sub.append(G.box("lch_o", cx0, kx1, cy0, cy1, z1 - 1, zb + 1))
    sub.append(G.box("lch_i", kx1 - 0.01, cx1, cy0, cy1, z1 - 1, 209.0))
    sub.append(G.box("lcav", kx0, kx1, ky0, ky1, kz0, kz1))
    fx, fy = P.IF_FEED_BUS_XY
    sub.append(G.box("lfb", fx - 2.5, P.POST_L_BORE_X0 + 0.1, fy - 2.6, fy + 2.6, zb - 6, zb + 1))
    sub.append(inner_top_chamfer(P, "lcf", x_in, -1))
    # ---- right post: top-loaded tilt servo (pocket, idler slot and adapter passage open to the post top)
    x_in = P.IF_ARM_R_IN
    g = Servo(P)
    zt, yt = P.IF_TILT_Z, P.IF_TILT_Y
    cl, xc = P.SERVO_POCKET_CLR, P.POST_R_COVER_X
    rx0, rx1, ry0, ry1 = P.IF_POST_R_CHANNEL
    sub += u_bore(P, "rb", x_in - 1, P.POST_R_BORE_X1)
    rp = P.POST_R_TEAR_R
    sub.append(G.cyl("rps", (yt, zt), rp, P.POST_R_BORE_X1 - 0.01, g.x0 - cl + 0.1, 'X'))
    sub.append(G.box("rpu", P.POST_R_BORE_X1 - 0.01, g.x0 - cl + 0.1, yt - rp, yt + rp, zt, zb + 1))
    sub.append(G.box("rpk", g.x0 - cl, xc, g.y0 - cl, g.y1 + cl, g.z0 - cl, zb + 1))
    ir, ix1 = P.POST_R_IDLER_R, g.x1 + C["hiwonder_bus_servo"]["idler_boss"]["protrudes"] + 0.5
    sub.append(G.cyl("rid", (yt, zt), ir, xc - 0.5, ix1, 'X'))
    sub.append(G.box("riu", xc - 0.5, ix1, yt - ir, yt + ir, zt, zb + 1))
    sub.append(G.box("rnt", 84.0, 94.5, -18.0, -6.0, 182.0, g.z0 - cl + 0.3))           # lead notch: pocket -> channel
    sub.append(G.box("rch", rx0, rx1, ry0, ry1, z1 - 1, P.POST_R_CHANNEL_Z1))
    sub.append(inner_top_chamfer(P, "rcf", x_in, 1))
    tt = G.csg(tt, sub=sub)
    A.part(tt, "PRT_turntable", 'PRT', "pla_a", joint="PIV_pan", stl="turntable", print_rot=A.R_ID,
           orient="bottom face on the bed, posts upright (tunnel roofs and the hub roof bridge <= 23 mm; servo pocket, "
                  "idler slot and U-slots open to the top; release-slot roofs bridge 4.2)", supports="no", infill=20)


def build_hub_gear(P):
    z0, z1 = P.IF_GEAR_Z
    c = P.IF_PAN_XY
    ri, ro = P.HUB_TUBE_R
    g = G.prism("hg", G.gear_poly(P.IF_GEAR_M, P.IF_GEAR_N, c=c, backlash=P.GEAR_BACKLASH, phase=0.0), z0, z1, 'Z')
    zc = P.HUB_CONE[1]
    tube = G.cyl("hgt", c, ro, z1 - 0.5, zc + 0.01, n=256)
    tube = G.csg(tube, add=[G.cone("hgtc", c, ro, ro - (P.HUB_TUBE_Z1 - zc), zc, P.HUB_TUBE_Z1, n=256)])
    add = [tube]
    d = P.HUB_DOG
    for i, az in enumerate(d["az"]):
        add.append(plan_box("hgd%d" % i, az, ri + 0.05, ro - 0.05, -d["w"] / 2, d["w"] / 2, zc - 1.0, d["top"]))
    g = G.csg(g, add=add)
    f = P.HUB_FINGER
    sub = [G.cyl("hgb", c, P.HUB_GEAR_BORE_R, z0 - 1, z1 + 0.01, n=256),
           G.cyl("hgtb", c, ri, z1, P.HUB_TUBE_Z1 + 5, n=128)]
    for i, az in enumerate(f["az"]):
        hw, sw = f["w"] / 2, f["w"] / 2 + f["slot"]
        sub.append(plan_box("hgfg%d" % i, az, ro - f["t"] - f["gap"], ro - f["t"], -sw, sw, z1, P.HUB_TUBE_Z1 + 1))
        sub.append(plan_box("hgfs%d" % i, az, ro - f["t"] - f["gap"] - 0.1, ro + 0.5, hw, sw, z1, P.HUB_TUBE_Z1 + 1))
        sub.append(plan_box("hgft%d" % i, az, ro - f["t"] - f["gap"] - 0.1, ro + 0.5, -sw, -hw, z1, P.HUB_TUBE_Z1 + 1))
    # tunnels + hub pocket pass over the tube top: notch the tube wall there (0.3 clear of the cables' cut)
    x0, x1, y0, y1, zf = P.TT_GROOVE
    px0, px1, py0, py1 = P.TT_HUB_POCKET
    sub.append(G.box("hgn1", -30, 30, y0 - 0.3, y1 + 0.3, zf - 0.3, P.HUB_TUBE_Z1 + 5))
    sub.append(G.box("hgn2", px0 - 0.3, px1 + 0.3, -30, py1 + 0.3, zf - 0.3, P.HUB_TUBE_Z1 + 5))
    g = G.csg(g, sub=sub)
    add = []
    for i, az in enumerate(f["az"]):
        hw = f["w"] / 2
        add.append(plan_box("hgfx%d" % i, az, ro - f["t"], ro, -hw, hw, zc - 0.5, f["tip_z"]))
        prof = [(ro - 0.01, f["catch_z"]), (ro + f["barb"] + 0.05, f["catch_z"]), (ro + f["barb"] + 0.05, f["catch_z"] + 0.5),
                (ro - 0.01, f["tip_z"] - 0.05)]
        add.append(polar_prism("hgfb%d" % i, az, prof, -hw, hw))
    g = G.csg(g, add=add)
    A.part(g, "PRT_hub_gear", 'PRT', "pla_b", joint="PIV_pan", stl="hub_gear", print_rot=A.R_ID,
           orient="gear face on the bed, hub tube up (3 snap fingers and 3 dogs grow up; barb catch faces 0.5 ledges)",
           supports="no", infill=40)


def build_beam(P):
    from parts import feeder as FD
    R, (b0, b1) = P.IF_TT_R, P.IF_BEAM_Y
    z0, z1 = P.IF_BEAM_Z0, P.FEED_FLOOR_Z               # v3-A1: the top is the feed floor (263) everywhere
    hy = 0.5 * (b1 - b0)
    p0 = rounded_plan(R, hy, P.CR)
    beam = G.prism("beam", p0, z0, z1, 'Z')
    q0 = rounded_plan(R + 1.0, hy + 1.0, P.CR + 1.0)
    q1 = rounded_plan(R - P.CH - 1.0, hy - P.CH - 1.0, P.CR - P.CH - 1.0)
    fr = G.loft("beamf", q0, q1, z1 - P.CH - 1.0, z1 + 1.0, 'Z')
    fr = G.csg(fr, add=[G.box("beamfb", -200, 200, -200, 200, z0 - 2.0, z1 - P.CH - 0.5)])
    beam = G.csg(beam, inter=[fr])
    h_add, h_sub = FD.housing_geom(P)                  # feeder item's feed floor plate + spout
    beam = G.csg(beam, add=h_add)
    G.bevel(beam, P.EB)
    add = []
    r = P.IF_BORE_R
    for nm, x0, x1 in (("tgL", P.POST_L_BORE_X0 + 0.1, P.IF_ARM_L_IN - 0.1), ("tgR", P.IF_ARM_R_IN + 0.1, P.POST_R_BORE_X1 - 0.1)):
        t = G.box(nm, x0, x1, -r + 0.1, r - 0.1, P.IF_TILT_Z + 9.0, z0 + 0.5)
        t = G.csg(t, sub=[G.cyl(nm + "j", (P.IF_TILT_Y, P.IF_TILT_Z), r, x0 - 1, x1 + 1, 'X')])
        add.append(t)
    # tongue over the tilt servo (0.43 over its top) and in the idler slot over the boss
    g = Servo(P)
    cl, xc, yt, zt = P.SERVO_POCKET_CLR, P.POST_R_COVER_X, P.IF_TILT_Y, P.IF_TILT_Z
    add.append(G.box("tgS", g.x0 - cl + 0.1, xc - 0.1, g.y0 - cl + 0.1, g.y1 + cl - 0.1, P.TILT_TONGUE_Z0, z0 + 0.5))
    ir, ix1 = P.POST_R_IDLER_R, g.x1 + C["hiwonder_bus_servo"]["idler_boss"]["protrudes"] + 0.5
    add.append(G.box("tgI", g.x1 + 0.1, ix1 - 0.1, yt - ir + 0.1, yt + ir - 0.1, zt + 3.0 + 0.5, z0 + 0.5))
    # 4 snap hooks (SNAP-V) into the post tops
    hk = P.BEAM_HOOK
    zh = z0 - hk["L"]
    for i, (xb, y, s) in enumerate(hk["pos"]):
        hw = hk["w"] / 2
        xa = xb - s * hk["t"]
        add.append(G.box("bhk%d" % i, min(xa, xb), max(xa, xb), y - hw, y + hw, zh, z0 + 0.5))
        b = hk["barb"] + 0.1                           # 0.6 barb, 0.1 slot clearance: 0.5 engage
        prof = [(xb - s * 0.01, zh), (xb + s * b, zh + 0.8), (xb + s * b, zh + 1.8), (xb - s * 0.01, zh + 1.8)]
        add.append(G.prism("bhb%d" % i, prof, y - hw, y + hw, 'Y'))
    beam = G.csg(beam, add=add)
    sub = list(h_sub)
    for i, (x, y) in enumerate(P.IF_FEED_BOLTS):      # feeder item's FST_feedmount (until the crown hooks replace them)
        sub.append(G.cyl("fb%d" % i, (x, y), 1.7, z0 - 1, z1 + 1, n=24))
    tw, rd, ph, pr = P.IF_CROWN_HOOK_SLOT
    for i, (x, y) in enumerate(P.IF_CROWN_HOOKS):      # crown hook slots + the barb pockets in the beam underside
        az = math.degrees(math.atan2(y, x))
        rc = math.hypot(x, y)
        sub.append(plan_box("chs%d" % i, az, rc - rd / 2, rc + rd / 2, -tw / 2, tw / 2, z0 - 1, z1 + 1))
        sub.append(plan_box("chp%d" % i, az, rc - rd / 2, rc - rd / 2 + pr, -tw / 2, tw / 2, z0 - 1, z0 + ph))
    beam = G.csg(beam, sub=sub)
    A.part(beam, "PRT_beam", 'PRT', "pla_a", joint="PIV_pan", stl="beam", print_rot=A.R_FLIP,
           orient="top face (feed floor, z 263) on the bed; spout, tongues and the 4 snap hooks grow up", supports="no",
           infill=30)
    flex = []
    for i, (xb, y, s) in enumerate(hk["pos"]):
        xm = xb - s * hk["t"] / 2
        flex.append(((round(xm, 2), y, z0), (round(xm, 2), y, zh)))
    return flex


# ------------------------------------------------------------------ tilt drive

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
    # v3-A1 adapter: double-D key (flats vertical at tilt 0, into the journal plate's top-open fork), 45 deg cone up to the
    # R13 disc, HORN pocket (disc + 0.2, 2.7 deep) on +X with 8 printed O2.0 pins in the horn holes (FST_tilt_horn x4 gone)
    ar, ax0, ax1 = P.IF_TILT_ADAPTER
    kx0, kx1 = P.IF_TILT_KEY_X
    kr, kf = P.IF_TILT_KEY_R, P.IF_TILT_KEY_AF / 2
    hd = C["servo_horn_disc"]
    xc1 = ax0 + (ar - kr)                              # cone reaches R13
    ad = G.cyl("tha", (yt, zt), ar, xc1 - 0.01, ax1 - 0.6, 'X', n=96)        # one solid of revolution, 0.6 chamfer at +X
    ad = G.csg(ad, add=[G.cone("thacn", (yt, zt), kr, ar, ax0, xc1, 'X', n=96),
                        G.cone("thace", (yt, zt), ar, ar - 0.6, ax1 - 0.61, ax1, 'X', n=96)])
    key = G.cyl("thak", (yt, zt), kr, kx0, kx1 + 1.0, 'X', n=64)
    key = G.csg(key, inter=[G.box("thakf", kx0 - 1, kx1 + 2, yt - kf, yt + kf, zt - kr - 1, zt + kr + 1)])
    G.bevel(key, 0.5)
    ad = G.csg(ad, add=[key])
    disc_out = g.disc_out
    pocket = G.cyl("thap", (yt, zt), hd["disc"]["d"] / 2 + 0.1, disc_out, ax1 + 1, 'X', n=96)
    ctr = G.cyl("thac", (yt, zt), P.IF_TILT_KEY_HOLE_D / 2, kx0 - 1, disc_out + 0.01, 'X', n=40)
    ad = G.csg(ad, sub=[pocket, ctr])
    bc = hd["holes"]["bolt_circle_d"] / 2
    rp, lp = P.PAN_HORN_PIN
    pins = [G.cyl("thpn%d" % k, (yt + bc * math.sin(k * math.pi / 4), zt + bc * math.cos(k * math.pi / 4)), rp,
                  disc_out - 0.01, disc_out + lp, 'X', n=16) for k in range(hd["holes"]["n"])]
    ad = G.csg(ad, add=pins)
    A.part(ad, "PRT_tilt_horn_adapter", 'PRT', "pla_b", joint="PIV_tilt", stl="tilt_horn_adapter", print_rot=A.R_NX_DOWN,
           orient="key end (-X) on the bed; 45 deg cone to the disc, horn pocket up, the 8 pins grow up from its floor",
           supports="no", infill=60)
    # centre screw through the key's 6.5 hole into the spline (bench 8a, allowed metal)
    A.fastener("FST_tilt_horn_ctr", (disc_out, yt, zt), PX, 6, spec="M3_cap", joint="PIV_tilt", host="BUY_horn_tilt",
               step="8a")


# ------------------------------------------------------------------ cables

def build_cables(P):
    zt = P.IF_TILT_Z
    kx = 0.5 * (P.POST_L_CAVITY[0] + P.POST_L_CAVITY[1])
    yb = P.LB_Y
    pts = [((P.IF_JOURNAL_L_X1 + 0.5, P.IF_TILT_Y, zt), 0), ((kx, P.IF_TILT_Y, zt), 4.5), ((kx, -8.0, zt - 1), 4.5),
           ((kx, yb, zt - 6), 4.5), ((kx, yb, 200.0), 4.5)] + P.channel_down(-98.0, yb, 185.0) + P.LB_HUB
    A.cable("CAB_launcher_bundle", P.fillet_path(pts, 4.5), P.BUNDLE_R, "cable_blk", joint="PIV_pan",
            lead_len=P.CABLE_LEADS["CAB_launcher_bundle"])
    ty = P.TB_Y
    pts = [((88.0, -8.0, 190.2), 0), ((92.0, -15.0, 186.0), 2.5), ((95.0, ty, 178.0), 3.0)] + \
        P.channel_down(95.0, ty, 170.0)[1:] + P.BUS_HUB_TILT
    A.cable("CAB_bus_tilt", P.fillet_path(pts, 3.0), P.BUS_R, "cable_wht", joint="PIV_pan",
            lead_len=P.CABLE_LEADS["CAB_bus_tilt"])
    # v2-A6-02: the pan bus lead's PIV_pan tail, from the static loop's end on the pan axis (BUS_PAN_AX, z 63) out to the
    # splice axis (az 35) and up to its bottom face centre (BUS_JCT_BOT, z 72). No lead_len: cable_chains "pan bus lead".
    ca, sa = math.cos(math.radians(P.BUS_JCT["az"])), math.sin(math.radians(P.BUS_JCT["az"]))
    vb = lambda r, z: (P.IF_PAN_XY[0] + r * ca, P.IF_PAN_XY[1] + r * sa, z)
    tail = [(P.BUS_PAN_AX, 0), (vb(3.5, 65.5), 2.5), (vb(7.0, 67.0), 2.5), (P.BUS_JCT_BOT, 0)]   # 5 straight into the splice
    A.cable("CAB_bus_pan_tail", P.fillet_path(tail, 2.5), P.BUS_R, "cable_wht", joint="PIV_pan", step="11a")


def build_bus_junction(P):
    """BOM 14a, the 3-way Hiwonder bus splice in the hub bore (envelope only; PIV_pan, axis Z). v3-A1: soldered below
    the deck with the floor off and pushed up the hub-gear bore; the bore roof keeps it from rising into the tunnels."""
    j = P.BUS_JCT
    ob = G.cyl("bjc", P.BUS_JCT_XY, j["d"] / 2, j["z0"], j["z0"] + j["l"], n=128)
    G.bevel(ob, 1.0)
    A.part(ob, "BUY_bus_junction", 'BUY', "cable_wht", joint="PIV_pan", mass_g=8,
           src="3 x 3-to-1 solder splices under heat shrink, sleeved (BOM 14a): servo bus V+/GND/signal of CAB_bus_pan, "
               "CAB_bus_tilt and CAB_bus_feeder; O%g x %g envelope" % (j["d"], j["l"]))


# ------------------------------------------------------------------ build

def build(P):
    build_thrust_ring(P)
    build_turntable(P)
    build_hub_gear(P)
    flex = build_beam(P)
    print("PAN_STAGE beam hooks (from, to): %s" % flex)
    build_tilt_drive(P)
    build_cables(P)
    build_bus_junction(P)
