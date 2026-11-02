"""Feeder (PIV_pan) + jar group (PIV_jar).

Static (PIV_pan):
  PRT_feeder_housing  floor plate 260-263 + outlet Ø16 at IF_DROP_XY + spout OD 22 down through the beam hole to 245.
                      Printed top face down, spout up. Clamped to the beam by FST_feedmount_* (csk M3 x 16 up from the
                      beam underside, through the plate, threading into the crown).
  PRT_feeder_crown    everything above the floor: gear-band cavity R35, lip + land journal R31.3 (no candy reaches the
                      mesh), pinion chamber, bayonet socket ID 68.6 with 3 L-slots (entry at +30, 30 deg twist, end
                      stops), servo pocket (servo #3 spline down at FEED_PINION_XY), bus channel to IF_FEED_BUS_XY.
                      Printed upside down (top on the bed): every downward face in the assembly prints as a floor.
  PRT_feeder_cover    shroud over the servo (the crown's left lobe), CH chamfer, FST_fcover_* csk.
  BUY_servo_feeder, CAB_bus_feeder.
Moving:
  PRT_feeder_disc     PIV_feeder: 44T m1.5 band (bottom) + R31 land (journal) + 3 x Ø13.75 pockets with a 1 x 45 top rim
                      chamfer at r 21 (60/180/300 deg from the outlet) + agitator fins on the hub.
  PRT_feeder_pinion   PIV_feeder_pinion: 30T, horn recess on top, BUY_horn_feeder held by the 4 FST_fhorn_* only (no centre
                      screw: servo #3 lifts +Z off the spline with the lobe cover off, v2-A1-04).
Jar group (PIV_jar, 0 locked .. 30 free): BUY_jar, BUY_mm_fill, BUY_jar_band, PRT_jar_adapter (lid disc + spout),
  PRT_jar_valve (skirt in the chamber, baffle over the outlet sector, bayonet lugs, three cheeks that clamp the spout
  with FST_valve_* and guide the gate), PRT_jar_gate (guillotine on PIV_gate, a +X slide under PIV_jar 0..52: home 0 =
  closed, 52 = open notch under the detent; R6 tab flush with the valve OD; a lug on top of its -X end rides in two
  notches in the adapter spout tip and meets the +X notch shoulder at +52.35),
  PRT_gate_detent + FST_detent_0 (v2-A2-A1-09: clip on the +Y cheek, R1 bump in a blade notch at x 29.5 closed / -22.5 open;
  v2-A3-A3-01: tab EB 1.0, plate EB 0.6 with an R3 plan end, M3 x 10 pan self-tap in a Ø6.6 counterbore;
  v2-A4-01: back face 39.9 and counterbore 2.4 so the pan head sits flush; v2-A5-01: flat tab top at 299.5, 1.0 under
  the jar band lip (z 300.5), EB 1.0 on every tab edge, replacing A4's 45 deg top chamfer).
  v2-A1-10: EB 1.0 on the adapter, valve, gate tab, crown, disc land, housing and cover (0.6 on the 2 mm blade and the 1.6 flange).

Index: park 0 (pockets at +/-60 and 180, outlet covered by 5.5 mm of disc). Fire A: +60 (the -60 pocket crosses the
outlet) then back to 0. Fire B: -60 (the +60 pocket) then 0. Servo = -1.467 x disc (-/+88). checks.json index_tests.
"""
import math
from cadlib import geom as G, features as F, asm as A
import placeholders as PH

C = PH.C
UP, DOWN = (0.0, 0.0, 1.0), (0.0, 0.0, -1.0)
D2R = math.pi / 180.0


def screw(name, at, into, length, spec, host, step, joint="PIV_pan", cut=()):
    for kind, kw, lst in cut:
        lst += F.screw_hole(at, into, length, kind=kind, name=name, **kw)
    A.fastener(name, at, into, length, spec=spec, joint=joint, host=host, step=step)


def sector(name, r0, r1, z0, z1, a0, a1, c=(0.0, 0.0), n=720):
    """annular sector solid between angles a0..a1 (deg)"""
    return G.revolve(name, [(r0, z0), (r1, z0), (r1, z1), (r0, z1)], center=(c[0], c[1], 0.0), n=n,
                     a0=a0 * D2R, a1=a1 * D2R)


def edge_halfspace(name, th, z0, slope, below, r=(4.0, 45.0), foot=None):
    """Cutter bounded by the plane that contains the radial line at angle th (deg) and height z0 and slopes at
    `slope` deg toward the inside of a sector centred on 0 deg. below=True removes the region under the plane
    (underside ramp), False the region over it (roof). `foot` (below only): the ramp stops where the plane reaches
    this height, leaving a vertical flat down to the part's bottom instead of a feathered edge."""
    t = th * D2R
    e1 = (math.cos(t), math.sin(t), 0.0)
    sg = 1.0 if th > 0 else -1.0
    e2 = (sg * math.sin(t), -sg * math.cos(t), 0.0)          # horizontal, toward the sector centre
    e3 = (0.0, 0.0, 1.0)
    wv = (e2[1] * e3[2] - e2[2] * e3[1], e2[2] * e3[0] - e2[0] * e3[2], e2[0] * e3[1] - e2[1] * e3[0])
    k = math.tan(slope * D2R)
    S = 40.0
    if below and foot is not None:
        uf = (z0 - foot) / k
        poly = [(-2.0, 2.0 * k), (-2.0, -30.0), (uf, -30.0), (uf, -uf * k)]
    elif below:
        poly = [(-2.0, 2.0 * k), (-2.0, -30.0), (S, -30.0), (S, -S * k)]
    else:
        poly = [(-2.0, -2.0 * k), (S, S * k), (S, 40.0), (-2.0, 40.0)]
    w0, w1 = (r[0], r[1]) if wv[0] * e1[0] + wv[1] * e1[1] > 0 else (-r[1], -r[0])
    ob = G.prism(name, poly, w0, w1, 'Z')
    return G.xform(ob, G.frame((0.0, 0.0, z0), e2, e3, wv))


def plan_outline(P):
    """crown / floor-plate footprint pieces (prisms are unioned): collar disc, servo lobe, bus tab"""
    px = P.FEED_PINION_XY
    lobe = G.hull_circles([(px, P.PINION_CH_R + 3.0), ((-84.0, 10.0), 6.0), ((-84.0, -10.0), 6.0)] +
                          [(c, P.CR) for c in P.COVER_SCREWS], n=96)     # v2-A1-10 plan corners R6
    tab = G.hull_circles([(c, 5.5) for c in P.BUS_TAB])
    return lobe, tab


# ------------------------------------------------------------------ fasteners (shared at/into with their holes)

def fasteners(P, crown, plate, cover, valve, adapter, detent):
    t_plate = P.FEED_FLOOR_T
    for i, (x, y) in enumerate(P.IF_FEED_BOLTS):     # csk up from the beam underside (beam has the csk), into the crown
        screw("FST_feedmount_%d" % i, (x, y, P.IF_BEAM_Z0), UP, 16, "M3_csk", "PRT_feeder_crown", "11",
              cut=[("clamp", dict(clamp=P.IF_BEAM_T + t_plate, head="none"), plate),
                   ("clamp", dict(clamp=P.IF_BEAM_T + t_plate, head="none"), crown)])
    for i, (x, y) in enumerate(P.PLATE_SCREWS):      # bench: plate to crown, csk flush in the plate underside
        screw("FST_fplate_%d" % i, (x, y, P.IF_BEAM_Z1), UP, 8, "M3_csk", "PRT_feeder_crown", "10c",
              cut=[("clamp", dict(clamp=t_plate, head="csk"), plate), ("clamp", dict(clamp=t_plate, head="csk"), crown)])
    z0 = P.COVER_BOX[3]
    for i, (x, y) in enumerate(P.COVER_SCREWS):      # cover ears, csk down into the crown lobe
        screw("FST_fcover_%d" % i, (x, y, z0 + 4.0), DOWN, 12, "M3_csk", "PRT_feeder_crown", "10d",
              cut=[("clamp", dict(clamp=4.0, head="csk"), cover), ("clamp", dict(clamp=4.0, head="csk"), crown)])
    # valve cheeks -> pads inside the adapter spout (radial, head counterbored flush with the OD 68)
    r_at = P.VALVE_OD / 2 - 3.0
    for i, a in enumerate(P.VALVE_SCREW_A):
        u = (math.cos(a * D2R), math.sin(a * D2R))
        at = (r_at * u[0], r_at * u[1], P.VALVE_SCREW_Z)
        into = (-u[0], -u[1], 0.0)
        cl = r_at - P.ADAPTER_SPOUT_OD / 2
        valve += F.screw_hole(at, into, 10, kind="clamp", clamp=cl, head="cap", sink=3.0, print_up=UP, name="vs%d" % i)
        adapter += F.screw_hole(at, into, 10, kind="clamp", clamp=cl, head="cap", sink=3.0, print_up=DOWN, name="vsa%d" % i)
        A.fastener("FST_valve_%d" % i, at, into, 10, spec="M3_cap", joint="PIV_jar", host="PRT_jar_adapter", step="12")
    # v2-A2-A1-09 detent clip: M3 self-tap -Y through its tab into the +Y cheek (pilot breaks out in the gate slot).
    # v2-A3-A3-01: pan head on the floor of a 1.0 counterbore in the tab back face (stock x 10, tip at y 27.5)
    D = P.GATE_DETENT
    sx, sz, sl = D["screw"]
    sink = D["cbore"][1]
    at, into = (sx, D["plate_y"][1] - sink, sz), (0.0, -1.0, 0.0)
    cl = at[1] - math.sqrt(D["tab_r"] ** 2 - sx * sx)                       # tab inner face on the axis: valve pilot from here
    cl_t = at[1] - math.sqrt(D["tab_r"] ** 2 - (sx + 1.7) ** 2)            # ... and at the Ø3.4 hole's +X edge: the tab's
    valve += F.screw_hole(at, into, sl, kind="clamp", clamp=cl, head="none", print_up=UP, name="dts")  # clearance runs out
    detent += F.screw_hole(at, into, sl, kind="clamp", clamp=cl_t, head="pan", sink=sink, name="dtd")  # through its curved face
    A.fastener("FST_detent_0", at, into, sl, spec="M3_selftap_pan", joint="PIV_jar", host="PRT_jar_valve", step="12")


# ------------------------------------------------------------------ static parts

def build_housing(P, cuts):
    lobe, tab = plan_outline(P)
    z0, z1 = P.IF_BEAM_Z1, P.FEED_FLOOR_Z
    h = G.cyl("fh", P.IF_JAR_XY, P.CROWN_R[0], z0, z1, n=256)
    h = G.csg(h, add=[G.prism("fhl", lobe, z0, z1), G.prism("fht", tab, z0, z1),
                      G.cyl("fhs", P.IF_DROP_XY, P.IF_SPOUT_OD / 2, P.IF_SPOUT_Z0, z0 + 0.5)])
    G.bevel(h, P.EB)                                # v2-A1-10 edge break before the cuts
    sub = list(cuts)
    sub.append(G.cyl("fho", P.IF_DROP_XY, P.IF_OUTLET_D / 2, P.IF_SPOUT_Z0 - 1, z1 + 1))
    sub.append(G.cyl("fhb", P.IF_FEED_BUS_XY, 2.6, z0 - 1, z1 + 1))
    h = G.csg(h, sub=sub)
    A.part(h, "PRT_feeder_housing", 'PRT', "pla_b", joint="PIV_pan", stl="feeder_housing", print_rot=A.R_FLIP,
           orient="disc running face on the bed, spout up", supports="no", infill=30)


def build_crown(P, cuts):
    c, px = P.IF_JAR_XY, P.FEED_PINION_XY
    zb, zt = P.FEED_FLOOR_Z, P.IF_SOCKET_Z[1]
    lobe, tab = plan_outline(P)
    r0, r1 = P.CROWN_R
    s0, s1 = P.CROWN_STEP_Z
    col = G.revolve("crc", [(0.0, zb), (r0, zb), (r0, s0), (r1, s1), (r1, zt - P.CH), (r1 - P.CH, zt), (0.0, zt)],
                    center=(c[0], c[1], 0.0), n=256)
    cr = G.csg(col, add=[G.prism("crl", lobe, zb, zt), G.prism("crt", tab, zb, zt)])
    G.bevel(cr, P.EB)                               # v2-A1-10 edge break before the cuts
    sub = list(cuts)
    sub.append(G.cyl("crd", c, P.FEED_CAV_R, zb - 1, P.FEED_LIP_Z, n=256))                       # gear band
    sub.append(G.cyl("crj", c, P.LAND_BORE_R, zb - 1, P.IF_SOCKET_Z[0] + 0.05, n=512))          # land journal + chamber
    sz0 = P.IF_SOCKET_Z[0]
    rs = P.IF_SOCKET_ID / 2
    sub.append(G.revolve("crs", [(0.0, sz0), (P.LAND_BORE_R, sz0), (rs, sz0 + (rs - P.LAND_BORE_R) * P.SOCKET_CONE),
                                 (rs, zt + 1), (0.0, zt + 1)], center=(c[0], c[1], 0.0), n=768))
    lz0, lz1 = P.IF_BAYO_LUG_Z[0], P.BAYO_LEG_Z1
    ro = P.IF_BAYO_LUG_R + 0.4
    for k in range(P.IF_BAYO_N):
        a = 360.0 * k / P.IF_BAYO_N
        sub.append(sector("crg%d" % k, P.LAND_BORE_R - 0.3, ro, lz0, lz1, a + P.BAYO_LEG[0], a + P.BAYO_LEG[1]))
        sub.append(sector("cre%d" % k, rs - 0.3, ro, lz1 - 0.4, zt + 1, a + P.BAYO_ENTRY[0], a + P.BAYO_ENTRY[1]))
    sub.append(G.cyl("crp", px, P.PINION_CH_R, zb - 1, P.DISC_Z[1] + 1.35, n=256))               # pinion + hub
    # blunt the knife-edge cusps where the pinion chamber meets the band cavity and the land bore
    # the fin between the land bore and the pinion chamber is < 1.6 for |y| < 7.2: remove it there (the journal gap
    # widens from +/-5.4 to +/-7.3, about 27 deg of the 360 deg land); its ends are 1.75 thick
    sub.append(G.box("crwf", px[0] + P.PINION_CH_R - 2.0, c[0] - P.LAND_BORE_R + 1.0, -7.3, 7.3, zb - 1,
                     P.DISC_Z[1] + 1.35))
    for nm, R, z0_, z1_ in (("crq", P.FEED_CAV_R, zb - 1, P.FEED_LIP_Z),):
        d = abs(px[0] - c[0])
        xq = (R * R - P.PINION_CH_R ** 2 + d * d) / (2 * d)
        yq = math.sqrt(max(0.0, R * R - xq * xq))
        for sgn in (1, -1):
            sub.append(G.cyl(nm + ("p" if sgn > 0 else "n"), (c[0] - xq, c[1] + sgn * yq), 3.0, z0_, z1_))
    sub.append(G.cyl("crh", px, P.HORN_CAV_R, P.DISC_Z[1] + 0.7, P.FEED_SERVO_FACE_Z + 0.1))     # horn + M2 heads
    x0, x1, hy = P.SERVO_POCKET
    sub.append(G.box("crv", x0, x1, -hy, hy, P.FEED_SERVO_FACE_Z, zt + 1))
    # bus: servo foot -> channel under the pocket floor -> down at IF_FEED_BUS_XY
    fx, fy = P.IF_FEED_BUS_XY
    cz0, cz1 = P.DISC_Z[1] + 1.5, P.FEED_SERVO_FACE_Z + 0.1
    sub.append(G.box("crb1", -86.0, -81.5, fy + 2.6, -3.0, cz0, cz1))
    sub.append(G.box("crb2", fx - 2.3, -81.5, fy - 2.6, fy + 2.6, cz0, cz1))
    sub.append(G.cyl("crb3", (fx, fy), 2.6, zb - 1, cz1))
    cr = G.csg(cr, sub=sub)
    A.part(cr, "PRT_feeder_crown", 'PRT', "pla_b", joint="PIV_pan", stl="feeder_crown", print_rot=A.R_FLIP,
           orient="top (z 286) on the bed: lip, socket cone, slot ceilings and pocket floors all print as floors",
           supports="no", infill=25)


def build_cover(P, cuts):
    x0, x1, hy, z0, z1 = P.COVER_BOX
    r = P.CR                                        # v2-A1-10 plan corners R6 (A1 R4); the frustum keeps the CH 45 deg
    body = G.prism("cvb", G.rrect(x0, x1, -hy, hy, r), z0, z1)
    e = 1.0                                         # chamfer by intersection with a 45 deg frustum (no coplanar seam)
    fr = G.loft("cvc", G.rrect(x0 - e, x1 + e, -hy - e, hy + e, r + e),
                G.rrect(x0 + P.CH + e, x1 - P.CH - e, -hy + P.CH + e, hy - P.CH - e, r - P.CH - e), z1 - P.CH - e, z1 + e)
    fr = G.csg(fr, add=[G.box("cvcb", x0 - 5, x1 + 5, -hy - 5, hy + 5, z0 - 1, z1 - P.CH - e + 0.5)])
    body = G.csg(body, inter=[fr])
    cap = None
    ears = [G.prism("cve%d" % i, G.hull_circles([((x, y), P.CR), ((x, 0.6 * y), P.CR)]), z0, z0 + 4.0)
            for i, (x, y) in enumerate(P.COVER_SCREWS)]
    cv = G.csg(body, add=ears)
    G.bevel(cv, P.EB)                               # v2-A1-10 edge break before the cuts
    sx0, sx1, shy = P.SERVO_POCKET
    s = C["hiwonder_bus_servo"]
    top = P.FEED_SERVO_FACE_Z + s["body"][2] + 0.4
    idl = G.cyl("cvid", P.FEED_PINION_XY, 3.6, top - 1.0, top + s["idler_boss"]["protrudes"] + 0.4)   # idler boss
    cv = G.csg(cv, sub=list(cuts) + [G.box("cvi", sx0 - 0.4, sx1 + 0.1, -shy - 0.2, shy + 0.2, z0 - 1, top), idl])
    A.part(cv, "PRT_feeder_cover", 'PRT', "pla_b", joint="PIV_pan", stl="feeder_cover", print_rot=A.R_FLIP,
           orient="chamfered top on the bed, ears up", supports="no", infill=20)


def build_drive(P):
    """servo #3 spline down over the pinion; horn screwed into the pinion recess (4 x M2); no centre screw, the lobe
    cover holds the servo down on its pocket floor"""
    px, py = P.FEED_PINION_XY
    s, hc = C["hiwonder_bus_servo"], C["servo_horn_disc"]
    face = P.FEED_SERVO_FACE_Z
    M = G.frame((px, py, face), (1, 0, 0), (0, -1, 0), (0, 0, -1))       # spline down, body toward -X
    sv = PH.servo("BUY_servo_feeder")
    sv = G.csg(sv, sub=[G.cyl("fsvb", (0, 0), 3.1, -4.1, 10)])          # spline belongs to the horn (pinion joint)
    G.xform(sv, M)
    A.part(sv, "BUY_servo_feeder", 'BUY', "buy", joint="PIV_pan", mass_g=s["mass_g"], src="components.json")
    hz0 = face - P.HORN_LIFT                                             # horn hub underside (toward the servo)
    hn = PH.horn("BUY_horn_feeder")
    hn = G.csg(hn, add=[G.cyl("fspl", (0, 0), s["spline"]["boss_d"] / 2, -P.HORN_LIFT - 4.0,
                               s["spline"]["protrudes"] - P.HORN_LIFT)])
    G.xform(hn, G.frame((px, py, hz0), (1, 0, 0), (0, -1, 0), (0, 0, -1)))
    A.part(hn, "BUY_horn_feeder", 'BUY', "buy_metal", joint="PIV_feeder_pinion", mass_g=hc["mass_g"],
           src="components.json servo_horn_disc (+ the servo output spline)")
    disc0 = hz0 - hc["hub"]["h"]                     # horn disc face toward the servo (273.8)
    disc1 = disc0 - hc["disc"]["t"]                  # horn disc face toward the pinion (271.3)
    ptop = disc1 + P.HORN_RECESS                     # pinion hub top (272.3)
    z0, z1 = P.DISC_Z
    gear = G.prism("fpg", G.gear_poly(P.FEED_GEAR_M, P.PINION_N, c=(px, py), backlash=P.GEAR_BACKLASH,
                                      phase=math.pi / P.PINION_N), z0, z1)
    hub = G.cyl("fph", (px, py), 12.0, z1 - 0.01, ptop)
    cuts = F.horn_recess((px, py, ptop), DOWN, disc_d=hc["disc"]["d"], depth=P.HORN_RECESS,
                         bolt_circle_d=hc["holes"]["bolt_circle_d"], n_holes=hc["holes"]["n"], centre_hole_d=6.5,
                         name="fph")
    pn = G.csg(gear, add=[hub])
    pn = G.csg(pn, sub=cuts)
    A.part(pn, "PRT_feeder_pinion", 'PRT', "pla_a", joint="PIV_feeder_pinion", stl="feeder_pinion", print_rot=A.R_ID,
           orient="gear face on the bed, horn recess up", supports="no", infill=60)
    bc = hc["holes"]["bolt_circle_d"] / 2
    for i in range(4):
        a = math.radians(90 * i)
        A.fastener("FST_fhorn_%d" % i, (px + bc * math.cos(a), py + bc * math.sin(a), disc0), DOWN, 8,
                   spec="M2_pan", joint="PIV_feeder_pinion", host="PRT_feeder_pinion", step="10a")
    # v2-A1-04: no centre screw. The 4 M2 FST_fhorn_* hold the horn in the pinion recess; the servo is held by the
    # lobe cover and lifts +Z off the spline (A1's FST_fhorn_ctr was only reachable with the housing off the beam).


def build_disc(P):
    c = P.IF_JAR_XY
    z0, z1 = P.DISC_Z
    zb = z0 + P.DISC_BAND_H
    band = G.prism("fdg", G.gear_poly(P.FEED_GEAR_M, P.DISC_GEAR_N, c=c, backlash=P.GEAR_BACKLASH, phase=0.0), z0, zb)
    eb = P.EB                                                       # v2-A1-10 edge break on the land top rim
    land = G.revolve("fdl", [(0.0, zb - 0.01), (P.DISC_LAND_R, zb - 0.01), (P.DISC_LAND_R, z1 - eb),
                             (P.DISC_LAND_R - eb, z1), (0.0, z1)], center=(c[0], c[1], 0.0), n=256)
    top = z1 + P.AGITATOR_H
    fins = [G.cyl("fdh", c, 3.5, z1 - 0.01, top)]
    for k, a in enumerate((0.0, 120.0, 240.0)):                    # between the pockets
        f = G.box("fdf%d" % k, 0.0, P.FIN_R, -P.FIN_T / 2, P.FIN_T / 2, z1 - 0.01, top)
        tri = [(P.FIN_R - 3.0, top + 0.5), (P.FIN_R + 1.0, top - 3.5), (P.FIN_R + 1.0, top + 0.5)]
        f = G.csg(f, sub=[G.prism("fdc%d" % k, tri, -3.0, 3.0, 'Y')])      # 45 deg outer top corner
        G.xform(f, G.frame((c[0], c[1], 0.0), (math.cos(a * D2R), math.sin(a * D2R), 0), (-math.sin(a * D2R), math.cos(a * D2R), 0),
                           (0, 0, 1)))
        fins.append(f)
    d = G.csg(band, add=[land] + fins)
    rp, ch = P.POCKET_D / 2, P.POCKET_CH         # v2-A3-A1-03 Ø13.75 (A2 13.9, A1 14.4) + 1 x 45 lead-in on the top rim
    pk = [G.revolve("fdp%d" % k, [(0.0, z0 - 1), (rp, z0 - 1), (rp, z1 - ch), (rp + ch + 1.0, z1 + 1.0), (0.0, z1 + 1.0)],
                    center=(c[0] + P.FEED_RP * math.cos(a * D2R), c[1] + P.FEED_RP * math.sin(a * D2R), 0.0), n=128)
          for k, a in enumerate((60.0, 180.0, 300.0))]
    d = G.csg(d, sub=pk)
    A.part(d, "PRT_feeder_disc", 'PRT', "pla_a", joint="PIV_feeder", stl="feeder_disc", print_rot=A.R_ID,
           orient="gear band on the bed, fins up", supports="no", infill=40)


def build_bus(P):
    fx, fy = P.IF_FEED_BUS_XY
    zc = P.DISC_Z[1] + 3.3
    gz = 0.5 * (P.TT_GROOVE[4] + P.IF_TT_Z1)
    gy = 0.5 * (P.TT_GROOVE[2] + P.TT_GROOVE[3])
    kx = 0.5 * (P.POST_L_CAVITY[0] + P.POST_L_CAVITY[1])
    pts = [(-83.7, -5.5, zc), (-83.7, fy, zc), (fx, fy, zc), (fx, fy, P.IF_BEAM_Z0 - 4.0), (kx, gy, P.IF_BEAM_Z0 - 10.0),
           (kx, gy, 200.0), (-98.0, gy, 185.0), (-98.0, gy, 106.0), (-95.0, gy, gz), (-8.0, gy, gz)] + P.BUS_HUB  # v2-A5-03: ends on the splice top
    A.cable("CAB_bus_feeder", pts, P.BUS_R, "cable_wht", joint="PIV_pan", lead_len=P.CABLE_LEADS["CAB_bus_feeder"])


# ------------------------------------------------------------------ jar group (PIV_jar)

def build_jar(P, valve_cuts, adapter_cuts):
    c = P.IF_JAR_XY
    rim, top = P.IF_GLASS_RIM_Z, P.IF_GLASS_RIM_Z + P.JAR_H
    ro, t = P.JAR_D / 2, P.JAR_GLASS_T
    prof = [(P.JAR_MOUTH_ID / 2, rim), (P.JAR_THREAD_OD / 2, rim), (P.JAR_THREAD_OD / 2, rim + 16), (ro, rim + 28),
            (ro, top), (0.01, top), (0.01, top - t), (ro - t, top - t), (ro - t, rim + 30), (P.JAR_MOUTH_ID / 2, rim + 20)]
    jar = G.revolve("jar", prof, center=(c[0], c[1], 0), n=128)
    A.part(jar, "BUY_jar", 'BUY', (0.80, 0.88, 0.92, 1.0), joint="PIV_jar", mass_g=P.JAR_MASS_GLASS,
           src="DESIGN_BRIEF v2 table (Ball/Kerr regular-mouth pint, nominal, confirm with calipers)")
    fill = G.cyl("fill", c, ro - t - 1.0, rim + 32, top - t - 8)
    A.part(fill, "BUY_mm_fill", 'BUY', (0.75, 0.20, 0.15, 1.0), joint="PIV_jar", mass_g=P.JAR_MASS_FILL,
           src="400 g of M&Ms (mass carrier for the tip check)")
    b0 = P.IF_BAND_Z0
    band = G.cyl("band", c, P.JAR_BAND_OD / 2, b0, b0 + P.JAR_BAND_H, n=192)
    band = G.csg(band, sub=[G.cyl("bi", c, P.JAR_BAND_OD / 2 - 0.6, b0 + P.JAR_BAND_LIP_T, b0 + P.JAR_BAND_H + 1, n=192),
                            G.cyl("bl", c, P.JAR_BAND_LIP_ID / 2, b0 - 1, b0 + 1, n=192)])
    A.part(band, "BUY_jar_band", 'BUY', "buy_metal", joint="PIV_jar", mass_g=P.JAR_MASS_BAND, src="user's jar band")
    # adapter: Ø69 x 1.6 lid disc + spout 55/50 through the band lip, 3 screw pads inside the spout (sloped tops)
    ri, rso = P.ADAPTER_SPOUT_ID / 2, P.ADAPTER_SPOUT_OD / 2
    d0 = b0 + P.JAR_BAND_LIP_T
    eb, sz0, ra, zr = P.EB, P.ADAPTER_SPOUT_Z0, P.ADAPTER_D / 2, P.IF_GLASS_RIM_Z     # v2-A1-10 EB 1.0 in the profile
    ef = 0.6                                        # the 1.6 flange (brief limit) gets 0.6, so it keeps 1.6 of wall
    ad = G.revolve("ad", [(ri + 0.5, sz0), (rso - eb, sz0), (rso, sz0 + eb), (rso, d0 + 0.01), (ra - ef, d0 + 0.01),
                          (ra, d0 + 0.01 + ef), (ra, zr), (ri + eb, zr), (ri, zr - eb), (ri, sz0 + 0.5)],
                    center=(c[0], c[1], 0), n=256)
    pads = []
    for i, a in enumerate(P.VALVE_SCREW_A):
        pads.append(G.revolve("adp%d" % i, [(P.SPOUT_PAD_R, P.VALVE_SCREW_Z - 3.5), (ri + 0.05, P.VALVE_SCREW_Z - 3.5),
                                           (ri + 0.05, d0 + 0.4), (P.SPOUT_PAD_R, P.VALVE_SCREW_Z + 1.0)],
                              center=(c[0], c[1], 0), n=720, a0=(a - 11.5) * D2R, a1=(a + 11.5) * D2R))
    # v2-A1-09 gate open stop in the spout tip: boss on the OD behind the +X shoulder (45 deg back so it prints spout-up)
    lx, lhy, lh = P.GATE_STOP_LUG
    gc = P.GATE_STOP_CLR
    br, bhy, bh = P.SPOUT_STOP_BOSS
    boss = G.prism("adsb", [(rso - 1.0, sz0), (br, sz0), (br, sz0 + bh), (rso - 1.0, sz0 + bh + br - rso + 1.0)],
                   -bhy, bhy, 'Y')
    ad = G.csg(ad, add=pads + [boss])
    nz1 = P.GATE_Z[1] + lh + gc                                     # notch roof
    xs = P.GATE_X0 + lx + P.GATE_TRAVEL + gc                        # +X shoulder (26.55)
    ad = G.csg(ad, sub=list(adapter_cuts) + [
        G.box("adn0", P.GATE_X0 - 3.0, -ri + 0.5, -lhy - gc, lhy + gc, sz0 - 1.0, nz1),
        G.box("adn1", ri - 2.0, xs, -lhy - gc, lhy + gc, sz0 - 1.0, nz1)])
    A.part(ad, "PRT_jar_adapter", 'PRT', "pla_b", joint="PIV_jar", stl="jar_adapter", print_rot=A.R_FLIP,
           orient="lid disc (glass side) on the bed, spout up", supports="no", infill=40)
    # valve
    rv = P.VALVE_OD / 2
    z0 = P.VALVE_Z0
    li0, li1, liz = P.VALVE_LEADIN
    rk = P.VALVE_SKIRT_R
    zc0 = P.IF_SOCKET_Z[0] + 0.5 + (rk - P.LAND_BORE_R) * P.SOCKET_CONE + 0.3 * P.SOCKET_CONE    # chamfer start
    eb, vz1 = P.EB, P.VALVE_BODY_Z1                                 # v2-A1-10 edge breaks in the profile (skirt foot 0.6)
    v = G.revolve("val", [(li0, z0), (rk - 0.6, z0), (rk, z0 + 0.6), (rk, zc0), (rv, zc0 + (rv - rk) * P.SOCKET_CONE),
                          (rv, vz1 - eb), (rv - eb, vz1), (li1 + eb, vz1), (li1, vz1 - eb), (li1, liz)],
                    center=(c[0], c[1], 0), n=768)
    add = []
    zc1, zc2 = P.VALVE_BODY_Z1 - 1.0, P.IF_VALVE_Z1                 # three cheeks above the gate floor (ends >= 2 thick);
                                                                    # rooted 1 mm into the body so their EB stays hidden there
    for nm, bx in (("vchp", (-15.0, 15.0, P.CHEEK_Y, 40.0)), ("vchn", (-15.0, 15.0, -40.0, -P.CHEEK_Y)),
                   ("vchx", (-40.0, P.GATE_SLOT_X0, -16.0, 16.0))):
        ch = G.cyl(nm, c, rv, zc1, zc2, n=768)
        ch = G.csg(ch, inter=[G.box(nm + "i", bx[0], bx[1], bx[2], bx[3], zc1 - 1, zc2 + 1)],
                   sub=[G.cyl(nm + "b", c, P.ADAPTER_SPOUT_OD / 2 + 0.15, zc1 - 1, zc2 + 1, n=256)])
        G.bevel(ch, P.EB)
        add.append(ch)
    for k in range(P.IF_BAYO_N):
        a = 360.0 * k / P.IF_BAYO_N
        add.append(sector("vlug%d" % k, rk + 0.5, P.IF_BAYO_LUG_R, P.IF_BAYO_LUG_Z[0], P.IF_BAYO_LUG_Z[1],
                          a - P.BAYO_LUG_HW, a + P.BAYO_LUG_HW))
    # baffle over the outlet sector (+X at PIV_jar 0): underside ramps on both edges, roof shedding to both sides
    bf = sector("vbf", P.BAFFLE_R[0], P.BAFFLE_R[1], z0, P.BAFFLE_TOP, -P.BAFFLE_HALF, P.BAFFLE_HALF)
    bf = G.csg(bf, sub=[edge_halfspace("vbr%d" % i, s * P.BAFFLE_HALF, P.BAFFLE_RAMP_TOP, P.BAFFLE_RAMP, True,
                                       foot=z0 + P.BAFFLE_FLAT) for i, s in enumerate((1, -1))] +
               [edge_halfspace("vbt%d" % i, s * P.BAFFLE_HALF, P.BAFFLE_EDGE_TOP, P.BAFFLE_ROOF, False)
                for i, s in enumerate((1, -1))])
    add.append(bf)
    v = G.csg(v, add=add)
    v = G.csg(v, sub=valve_cuts)
    A.part(v, "PRT_jar_valve", 'PRT', "pla_b", joint="PIV_jar", stl="jar_valve", print_rot=A.R_ID,
           orient="skirt + baffle bottom on the bed (lug undersides bridge 5.5 mm)", supports="no", infill=40)
    # gate: guillotine blade, 30 deg leading edge on the column side, pull tab at +X
    # v2-A1-08/09: blade +X plan corners R6 and EB 0.6, 0.8 flat on the leading edge, R6 EB 1.0 tab flush with the
    # valve OD, stop lug under the -X end
    g0, g1 = P.GATE_Z
    x0, x1, R = P.GATE_X0, P.GATE_X1, P.GATE_TAB_R
    hw = P.GATE_W / 2
    bl = G.prism("gate", G.rrect(x0 - 1.0 - R, x1, -hw, hw, R, n=12), g0, g1)
    G.bevel(bl, P.GATE_BLADE_EB)
    sl = math.tan(P.GATE_CHAMFER * D2R)
    zf = g0 + P.GATE_KNIFE_FLAT
    wedge = G.prism("gch", [(x0 - 2.0, zf - 2.0 * sl), (x0 + (g1 + 1.0 - zf) / sl, g1 + 1.0), (x0 - 2.0, g1 + 1.0)],
                    -hw - 1, hw + 1, 'Y')
    bl = G.csg(bl, sub=[wedge, G.box("gend", x0 - 10.0, x0, -hw - 1, hw + 1, g0 - 1, g1 + 1)])
    tx0, tx1, thy, tz = P.GATE_TAB
    tab = G.prism("gtab", G.rrect(-thy, thy, tz - 2 * R - 2.0, tz, R, n=12), tx0, tx1, 'X')
    tab = G.csg(tab, inter=[G.box("gtabi", tx0 - 1, tx1 + 1, -thy - 1, thy + 1, g0 + 0.3, tz + 1)])
    G.bevel(tab, P.GATE_EB)
    lx, lhy, ld = P.GATE_STOP_LUG
    lug = G.box("glug", x0, x0 + lx, -lhy, lhy, zf - 0.01, g1 + ld)
    bl = G.csg(bl, add=[tab, lug])
    # v2-A2-A1-09 detent notches on the blade top: closed (under the bump) and closed - GATE_TRAVEL (under it when open)
    nr, nd, dy = P.GATE_DETENT_NOTCH_R, P.GATE_DETENT_NOTCH_D, P.GATE_DETENT["y"]
    bl = G.csg(bl, sub=[G.cyl("gdn%d" % k, (nx, dy), nr, g1 - nd, g1 + 1.0, n=48)
                        for k, nx in enumerate(P.GATE_DETENT_NOTCH_X)])
    A.part(bl, "PRT_jar_gate", 'PRT', "pla_a", joint="PIV_gate", stl="jar_gate", print_rot=A.R_ID,
           orient="flat, chamfer, tab, stop lug and detent notches up", supports="no", infill=100)


def build_detent(P, cuts):
    """v2-A2-A1-09 PRT_gate_detent: tab on the +Y cheek's outside face (FST_detent_0 radial) + a 1.2 plate at blade-top
    level reaching +X past the cheek end; the R1 x 0.5 spherical-cap bump under its free end sits in the blade's closed
    notch. Pulling the gate lifts the beam 0.4 until the open notch (52 along -X on the blade) comes under the bump."""
    D = P.GATE_DETENT
    c = P.IF_JAR_XY
    g1 = P.GATE_Z[1]
    z0 = g1 + D["gap"]                              # plate underside 290.45
    z1 = z0 + D["clip"][2]                          # plate top 291.65
    px0, px1 = D["plate_x"]
    py0, py1 = D["plate_y"]
    tx0, tx1 = D["tab_x"]
    # v2-A3-A3-01: plate EB 0.6 (like the 2.0 blade) with R3 plan corners on its free +X end; tab EB 1.0 (form language)
    re = D["plate_end_r"]
    pl = [(px0, py0)]
    for cx, cy, a0 in ((px1 - re, py0 + re, -90.0), (px1 - re, py1 - re, 0.0)):
        pl += [(cx + re * math.cos((a0 + 90.0 * i / 8) * D2R), cy + re * math.sin((a0 + 90.0 * i / 8) * D2R))
               for i in range(9)]
    pl.append((px0, py1))
    plate = G.prism("dtp", pl, z0, z1, 'Z')
    G.bevel(plate, D["plate_eb"])
    tz0, tz1 = D["tab_z0"], D["tab_z1"]
    # v2-A5-01: flat top at tab_z1 299.5, 1.0 under the band lip (A5's planar chamfer cutter is gone). The tab is one
    # plan prism whose inner face is 6 chords circumscribing R tab_r (>= 0.05 off the R34 cheek). A5 cut it with an n=768
    # cylinder: its 0.28 facet edges made the bevel's overlap clamp shrink every tab EB to about 0.1 (cad q ray).
    th0, th1 = math.asin((tx0 - c[0]) / D["tab_r"]), math.asin((tx1 - c[0]) / D["tab_r"])
    ns = 6
    rv = D["tab_r"] / math.cos((th1 - th0) / (2 * ns))     # chord vertices, chord midpoints on R tab_r
    arc = [(c[0] + rv * math.sin(t), c[1] + rv * math.cos(t))
           for t in [th0 + (th1 - th0) * i / ns for i in range(ns + 1)]]
    arc[0] = (tx0, c[1] + math.sqrt(rv ** 2 - (tx0 - c[0]) ** 2))
    arc[-1] = (tx1, c[1] + math.sqrt(rv ** 2 - (tx1 - c[0]) ** 2))
    tab = G.prism("dtt", arc + [(tx1, py1), (tx0, py1)], tz0, tz1, 'Z')
    G.bevel(tab, D["tab_eb"])                       # EB 1.0 on every tab edge
    clip = G.csg(plate, add=[tab])
    r, h = D["bump_r"], D["bump_h"]
    zc = z0 - h + r                                 # sphere centre: cap stands h under the plate
    arc = [(r * math.cos(t * D2R), zc + r * math.sin(t * D2R)) for t in range(-90, -9, 8)]
    arc[0] = (0.0, arc[0][1])
    bump = G.revolve("dtb", arc + [(0.0, arc[-1][1])], center=(D["x"], D["y"], 0.0), n=48)
    clip = G.csg(clip, add=[bump])
    clip = G.csg(clip, sub=list(cuts))
    A.part(clip, "PRT_gate_detent", 'PRT', "pla_a", joint="PIV_jar", stl="gate_detent", print_rot=A.R_PY_DOWN,
           orient="flat +Y back face (screw-head face) on the bed: the beam along x and its bending lie in the layer plane",
           supports="no", infill=100)


def build(P):
    crown, plate, cover, valve, adapter, detent = [], [], [], [], [], []
    fasteners(P, crown, plate, cover, valve, adapter, detent)
    build_housing(P, plate)
    build_crown(P, crown)
    build_cover(P, cover)
    build_drive(P)
    build_disc(P)
    build_bus(P)
    build_jar(P, valve, adapter)
    build_detent(P, detent)
