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


def rot_z(ob, az):
    """turn a solid built in a local radial frame (x' radial at az deg, y' tangential) about the world Z axis"""
    t = az * D2R
    return G.xform(ob, G.frame((0.0, 0.0, 0.0), (math.cos(t), math.sin(t), 0.0), (-math.sin(t), math.cos(t), 0.0),
                               (0.0, 0.0, 1.0)))


def top_chamfer(name, poly, z0, z1, ch):
    """convex plan prism z0..z1 with a 45 deg x ch chamfer on its top edge (intersection with a frustum, no seam)"""
    e = 1.0
    body = G.prism(name, poly, z0, z1)
    fr = G.loft(name + "f", G.offset_convex(poly, e), G.offset_convex(poly, -ch - e), z1 - ch - e, z1 + e)
    fr = G.csg(fr, add=[G.prism(name + "fb", G.offset_convex(poly, 5.0), z0 - 1.0, z1 - ch - e + 0.5)])
    return G.csg(body, inter=[fr])


def crown_hooks(P):
    """v3-A1 SNAP-V crown hooks (FST_feedmount x4 deleted): one per beam slot IF_CROWN_HOOKS. Returns (hooks, reliefs,
    flexure rows). Radial frame: hook t 1.0 from rc + 0.25 to rc + 1.25 (0.05 inside the slot's outer wall), barb 0.55
    outward with a 0.8-high lead-in ramp from the tip (z 252, flush with the beam underside) and its catch face at 253.9
    under the beam's under-pocket roof (254). The crown relief round each hook (z 262 .. root 268) frees the 16 mm beam."""
    H = P.CROWN_HOOK
    tw, rd, ph, pr = P.IF_CROWN_HOOK_SLOT
    z0b = P.IF_BEAM_Z0
    hooks, rel, flex = [], [], []
    for i, (x, y) in enumerate(P.IF_CROWN_HOOKS):
        az = math.degrees(math.atan2(y, x))
        rc = math.hypot(x, y)
        ro = rc + rd / 2 - H["gap_out"]
        ri = ro - H["t"]
        hw = H["w"] / 2
        body = G.box("chk%d" % i, ri, ro, -hw, hw, z0b, H["root_z"] + 0.5)
        b = H["barb"]
        barb = G.prism("chb%d" % i, [(ro - 0.01, z0b), (ro + b, z0b + 0.8), (ro + b, z0b + ph - 0.1), (ro - 0.01, z0b + ph - 0.1)],
                       -hw, hw, 'Y')
        hooks.append(rot_z(G.csg(body, add=[barb]), az))
        r0 = min(rc - rd / 2, P.FEED_CAV_R - 0.5)              # +X hook: merge the relief into the band cavity (no 0.2 sliver)
        rel.append(rot_z(G.box("chr%d" % i, r0, ro + 0.6, -tw / 2, tw / 2, P.FEED_FLOOR_Z - 1.0, H["root_z"]), az))
        rm = 0.5 * (ri + ro)
        u = (math.cos(az * D2R), math.sin(az * D2R))
        flex.append(((round(rm * u[0], 2), round(rm * u[1], 2), H["root_z"]), (round(rm * u[0], 2), round(rm * u[1], 2), z0b + 0.8)))
    return hooks, rel, flex


# ------------------------------------------------------------------ static parts

def housing_geom(P):
    """v3-A1: the v2 PRT_feeder_housing (feed floor plate 260-263 + spout to IF_SPOUT_Z0) is merged into PRT_beam.
    pan_stage.build_beam unions `add` (before its edge break) and cuts `sub`. Owned by the feeder item: change the feed
    floor / spout here, not in pan_stage."""
    lobe, tab = plan_outline(P)
    z0, z1 = P.IF_BEAM_Z1, P.FEED_FLOOR_Z
    add = [G.cyl("fh", P.IF_JAR_XY, P.CROWN_R[0], z0, z1, n=256), G.prism("fhl", lobe, z0, z1), G.prism("fht", tab, z0, z1),
           G.cyl("fhs", P.IF_DROP_XY, P.IF_SPOUT_OD / 2, P.IF_SPOUT_Z0, P.IF_BEAM_Z0 + 0.5)]
    sub = [G.cyl("fho", P.IF_DROP_XY, P.IF_OUTLET_D / 2, P.IF_SPOUT_Z0 - 1, z1 + 1),
           G.cyl("fhb", P.IF_FEED_BUS_XY, 2.6, P.IF_BEAM_Z0 - 1, z1 + 1)]
    return add, sub


def build_crown(P):
    """v3-A1 PRT_feeder_crown = v2 crown + the lobe cover (FST_fcover x2, FST_feedmount x4 deleted). One top plane at
    z 322 (socket rim and closed lobe roof) on the bed. Servo #3 goes up into the lobe pocket from below (the pocket is
    open down to the beam face) until its top meets the roof; 4 crush ribs hold it; the pinion is pressed on its horn.
    3 SNAP-V hooks down through the beam slots. Returns the hook flexure rows."""
    c, px = P.IF_JAR_XY, P.FEED_PINION_XY
    zb, zt = P.FEED_FLOOR_Z, P.IF_SOCKET_Z[1]
    r0, r1 = P.CROWN_R
    s0, s1 = P.CROWN_STEP_Z
    col = G.revolve("crc", [(0.0, zb), (r0, zb), (r0, s0), (r1, s1), (r1, zt - P.CH), (r1 - P.CH, zt), (0.0, zt)],
                    center=(c[0], c[1], 0.0), n=256)
    circ = [(px, P.PINION_CH_R + 3.0), ((-84.0, 10.0), 6.0), ((-84.0, -10.0), 6.0)] + [(q, P.CR) for q in P.COVER_SCREWS] \
        + [(q, 5.5) for q in P.BUS_TAB]                 # lobe + bus tab in one convex hull, full height
    lobe = top_chamfer("crl", G.hull_circles(circ, n=96), zb, zt, P.CH)
    hooks, rel, flex = crown_hooks(P)
    cr = G.csg(col, add=[lobe])
    G.bevel(cr, P.EB)                               # v2-A1-10 edge break before the cuts
    sub = list(rel)
    sub.append(G.cyl("crd", c, P.FEED_CAV_R, zb - 1, P.FEED_LIP_Z, n=256))                       # gear band
    sub.append(G.cyl("crj", c, P.LAND_BORE_R, zb - 1, P.IF_SOCKET_Z[0] + 0.05, n=512))          # land journal + chamber
    sz0 = P.IF_SOCKET_Z[0]
    rs = P.IF_SOCKET_ID / 2
    sub.append(G.revolve("crs", [(0.0, sz0), (P.LAND_BORE_R, sz0), (rs, sz0 + (rs - P.LAND_BORE_R) * P.SOCKET_CONE),
                                 (rs, zt + 1), (0.0, zt + 1)], center=(c[0], c[1], 0.0), n=768))
    # L-slots: the leg floor is the lugs' 50 deg underside cone (contact), the leg ceiling 0.4 over the lug tops
    lz0, lz1 = P.IF_BAYO_LUG_Z[0], P.BAYO_LEG_Z1
    ro = P.IF_BAYO_LUG_R + 0.4
    k_ = math.tan(P.BAYO_LUG_SLOPE * D2R)
    rl0 = P.VALVE_SKIRT_R + 0.5
    ra = P.LAND_BORE_R - 0.3
    for k in range(P.IF_BAYO_N):
        a = 360.0 * k / P.IF_BAYO_N
        sub.append(G.revolve("crg%d" % k, [(ra, lz0 + (ra - rl0) * k_), (ro, lz0 + (ro - rl0) * k_), (ro, lz1), (ra, lz1)],
                             center=(c[0], c[1], 0.0), n=720, a0=(a + P.BAYO_LEG[0]) * D2R, a1=(a + P.BAYO_LEG[1]) * D2R))
        sub.append(sector("cre%d" % k, rs - 0.3, ro, lz1 - 0.4, zt + 1, a + P.BAYO_ENTRY[0], a + P.BAYO_ENTRY[1]))
    sub.append(G.cyl("crp", px, P.PINION_CH_R, zb - 1, P.DISC_Z[1] + 1.35, n=256))               # pinion + hub
    # the fin between the land bore and the pinion chamber is < 1.6 for |y| < 7.2: remove it there
    sub.append(G.box("crwf", px[0] + P.PINION_CH_R - 2.0, c[0] - P.LAND_BORE_R + 1.0, -7.3, 7.3, zb - 1,
                     P.DISC_Z[1] + 1.35))
    R = P.FEED_CAV_R
    d = abs(px[0] - c[0])
    xq = (R * R - P.PINION_CH_R ** 2 + d * d) / (2 * d)
    yq = math.sqrt(max(0.0, R * R - xq * xq))
    for sgn in (1, -1):                             # blunt the cusps where the pinion chamber meets the band cavity
        sub.append(G.cyl("crq" + ("p" if sgn > 0 else "n"), (c[0] - xq, c[1] + sgn * yq), 3.0, zb - 1, P.FEED_LIP_Z))
    sub.append(G.cyl("crh", px, P.HORN_CAV_R, P.DISC_Z[1] + 0.7, P.FEED_SERVO_FACE_Z + 0.1))     # pinion hub + horn
    x0, x1, hy = P.SERVO_POCKET
    sub.append(G.box("crv", x0, x1, -hy, hy, zb - 1, P.LOBE_ROOF_Z))           # servo pocket, open to the beam face
    ib = C["hiwonder_bus_servo"]["idler_boss"]["protrudes"]
    sub.append(G.cyl("cri", px, 3.6, P.LOBE_ROOF_Z - 0.1, P.LOBE_ROOF_Z - 0.05 + ib + 0.35))  # idler boss recess (blind)
    # bus: servo foot -> channel beside the pocket -> down at IF_FEED_BUS_XY
    fx, fy = P.IF_FEED_BUS_XY
    cz0, cz1 = P.DISC_Z[1] + 1.5, P.FEED_SERVO_FACE_Z + 0.1
    sub.append(G.box("crb1", -86.0, -81.5, fy + 2.6, -3.0, cz0, cz1))
    sub.append(G.box("crb2", fx - 2.3, -81.5, fy - 2.6, fy + 2.6, cz0, cz1))
    sub.append(G.cyl("crb3", (fx, fy), 2.6, zb - 1, cz1))
    cr = G.csg(cr, sub=sub)
    # 4 crush ribs on the +/-Y pocket walls (0.1 into the servo case, 45 deg lead-in at the bottom: servo enters from below)
    rw, ri_, rz0, rz1 = P.CRUSH_RIB
    yi = C["hiwonder_bus_servo"]["body"][1] / 2 - ri_
    ribs = []
    for xr in (-78.0, -58.0):
        for sg in (1, -1):
            pr = [(sg * (hy + 0.5), rz0 - (hy + 0.5 - yi)), (sg * yi, rz0), (sg * yi, rz1), (sg * (hy + 0.5), rz1)]
            if sg < 0:
                pr = pr[::-1]
            ribs.append(G.prism("crr%d%d" % (int(-xr), sg + 1), pr, xr - rw / 2, xr + rw / 2, 'X'))
    cr = G.csg(cr, add=ribs + hooks)
    A.part(cr, "PRT_feeder_crown", 'PRT', "pla_b", joint="PIV_pan", stl="feeder_crown", print_rot=A.R_FLIP,
           orient="top plane (z 322: socket rim + closed lobe roof) on the bed; lip, socket cone, leg cones, pocket floors "
                  "print as floors or 45-50 deg cones; the 3 snap hooks grow up", supports="no", infill=20)
    return flex


def build_drive(P):
    """servo #3 spline down over the pinion. v3-A1 HORN: the horn sits in a 2.7 pocket in the pinion hub with 8 printed
    O2.0 pins in its 8 holes (FST_fhorn x4 deleted); still no centre screw. The pinion is pressed on the horn on the
    bench; on the machine it sits 0.3 over the feed floor, so it cannot fall off the pins (2.4 long)."""
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
    disc1 = disc0 - hc["disc"]["t"]                  # horn disc face toward the pinion (271.3) = pocket floor
    z0, z1 = P.DISC_Z
    gear = G.prism("fpg", G.gear_poly(P.FEED_GEAR_M, P.PINION_N, c=(px, py), backlash=P.GEAR_BACKLASH,
                                      phase=math.pi / P.PINION_N), z0, z1)
    top = disc1 + P.FEED_HORN_POCKET                 # hub top 274.0 (0.2 past the horn disc)
    hub = G.cyl("fph", (px, py), P.FEED_HUB_R, z1 - 0.01, top)
    pocket = G.cyl("fpk", (px, py), hc["disc"]["d"] / 2 + 0.1, disc1, top + 1.0, n=96)
    pn = G.csg(gear, add=[hub], sub=[pocket])
    bc = hc["holes"]["bolt_circle_d"] / 2
    rp, lp = P.PAN_HORN_PIN
    pins = [G.cyl("fpn%d" % k, (px + bc * math.cos(k * math.pi / 4), py + bc * math.sin(k * math.pi / 4)), rp,
                  disc1 - 0.01, disc1 + lp, n=16) for k in range(hc["holes"]["n"])]
    pn = G.csg(pn, add=pins)
    A.part(pn, "PRT_feeder_pinion", 'PRT', "pla_a", joint="PIV_feeder_pinion", stl="feeder_pinion", print_rot=A.R_ID,
           orient="gear face on the bed, horn pocket up (the 8 pins grow up from its floor)", supports="no", infill=60)


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
    """v3-A1 (V2R7 A7-02): the feeder bus has its own route: outboard of the bundle in the left post channel (y P.FB_Y),
    R15 into the turntable tunnel, then side by side with the tilt bus (x -1.5 of the splice axis) onto the splice top."""
    fx, fy = P.IF_FEED_BUS_XY
    zc = P.DISC_Z[1] + 3.3
    kx = 0.5 * (P.POST_L_CAVITY[0] + P.POST_L_CAVITY[1])
    pts = [((-83.7, -5.5, zc), 0), ((-83.7, fy, zc), 3.0), ((fx, fy, zc), 3.0), ((fx, fy, P.IF_BEAM_Z0 - 4.0), 3.0),
           ((kx, P.FB_Y, P.IF_BEAM_Z0 - 10.0), 3.0), ((kx, P.FB_Y, 200.0), 3.0)] + P.channel_down(-98.0, P.FB_Y, 185.0) \
        + P.BUS_HUB_FEED
    A.cable("CAB_bus_feeder", P.fillet_path(pts, 3.0), P.BUS_R, "cable_wht", joint="PIV_pan",
            lead_len=P.CABLE_LEADS["CAB_bus_feeder"])


# ------------------------------------------------------------------ jar group (PIV_jar)

def build_jar(P):
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
    # adapter: O69 x 1.6 lid disc + spout 55/50 through the band lip. v3-A1 (FST_valve x3 deleted): spout root stepped to
    # R28.3 from the valve cheek tops to the disc (the shoulder that bears on the cheeks / pads), a groove round the spout
    # for the 2 valve snap barbs, a key groove for the +Y pad's rib (both open at the spout tip)
    ri, rso = P.ADAPTER_SPOUT_ID / 2, P.ADAPTER_SPOUT_OD / 2
    d0 = b0 + P.JAR_BAND_LIP_T
    eb, sz0, ra, zr = P.EB, P.ADAPTER_SPOUT_Z0, P.ADAPTER_D / 2, P.IF_GLASS_RIM_Z     # v2-A1-10 EB 1.0 in the profile
    ef = 0.6                                        # the 1.6 flange (brief limit) gets 0.6, so it keeps 1.6 of wall
    zsh = P.IF_VALVE_Z1 + 0.02                      # shoulder bearing face on the cheek tops
    rsh = P.SPOUT_SHOULDER_R
    ad = G.revolve("ad", [(ri + 0.5, sz0), (rso - eb, sz0), (rso, sz0 + eb), (rso, zsh), (rsh, zsh), (rsh, d0 + 0.01),
                          (ra - ef, d0 + 0.01), (ra, d0 + 0.01 + ef), (ra, zr), (ri + eb, zr), (ri, zr - eb), (ri, sz0 + 0.5)],
                    center=(c[0], c[1], 0), n=256)
    # v2-A1-09 gate open stop in the spout tip: boss on the OD behind the +X shoulder (45 deg back so it prints spout-up)
    lx, lhy, lh = P.GATE_STOP_LUG
    gc = P.GATE_STOP_CLR
    br, bhy, bh = P.SPOUT_STOP_BOSS
    boss = G.prism("adsb", [(rso - 1.0, sz0), (br, sz0), (br, sz0 + bh), (rso - 1.0, sz0 + bh + br - rso + 1.0)],
                   -bhy, bhy, 'Y')
    ad = G.csg(ad, add=[boss])
    nz1 = P.GATE_Z[1] + lh + gc                                     # notch roof
    xs = P.GATE_X0 + lx + P.GATE_TRAVEL + gc                        # +X shoulder (26.55)
    V = P.VALVE_SNAP
    zg0, zg1 = V["barb_z"] - 0.1, V["barb_z"] + 1.0
    kx, kw, kh = P.VALVE_KEY
    OD = P.GATE_OPEN_DETENT
    # A2 hotfix (v3-A1-03) open detent: bump centre (closed frame) on the lug's +Y finger, dimple in the +X notch's +Y wall
    odx = P.GATE_X0 + lx / 2
    ody = lhy + gc + OD["bump_d"] - OD["bump_r"]                    # 3.05: apex at the wall (3.35) + 0.3
    odr = OD["bump_r"] + OD["dimple_clr"]
    rk_ = rso + 0.15 - kh                                           # key rib tip radius (26.9): 0.75 off the pad face
    ka = math.degrees(math.atan2(math.sqrt(rso ** 2 - kx ** 2), kx))   # key azimuth (+Y pad)
    kd = math.degrees(math.asin((kw / 2 + 0.2) / rso))
    ad = G.csg(ad, sub=[
        G.box("adn0", P.GATE_X0 - 3.0, -ri + 0.5, -lhy - gc, ody + OD["bump_r"] + OD["closed_clr"], sz0 - 1.0, nz1),   # +Y side 4.0: the open-detent bump clears 0.35
        G.box("adn1", ri - 2.0, xs, -lhy - gc, lhy + gc, sz0 - 1.0, nz1),
        G.revolve("adg", [(V["groove_r"], zg0), (rso + 1.0, zg0), (rso + 1.0, zg1 + 1.0), (V["groove_r"], zg1)],
                  center=(c[0], c[1], 0), n=256),                   # flat catch wall (0.5 ledge), 45 deg upper flank
        sector("adk", rk_ - 0.1, rso + 1.0, sz0 - 1.0, P.IF_VALVE_Z1 + P.VALVE_KEY_GROOVE_OVER, ka - kd, ka + kd, c=c),
        G.cyl("adod0", (odx + P.GATE_TRAVEL, ody), odr, sz0 - 1.0, nz1, n=48),
        G.cyl("adod1", (odx + P.GATE_TRAVEL + gc, ody), odr, sz0 - 1.0, nz1, n=48),
        G.box("adodb", odx + P.GATE_TRAVEL, odx + P.GATE_TRAVEL + gc, ody - odr, ody + odr, sz0 - 1.0, nz1)])
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
        ch = G.csg(ch, inter=[G.box(nm + "i", bx[0], bx[1], bx[2], bx[3], zc1 - 1, zc2 + 1)])
        G.bevel(ch, P.EB)
        ch = G.csg(ch, sub=[G.cyl(nm + "b", c, rso + 0.15, zc1 - 1, zc2 + 1, n=256)])
        add.append(ch)
    # centring pads on the +/-Y cheek faces above the blade (45 deg undersides), 0.15 off the spout; key rib on the +Y pad
    yc = P.CHEEK_Y
    zp = sz0 + 0.2
    px0, px1 = P.VALVE_PAD_X
    for sg in (1, -1):
        pr = [(sg * (yc + 0.5), zp - 0.6), (sg * (yc + 0.5), zc2), (sg * 22.0, zc2), (sg * 22.0, zp + (yc - 22.0) * 1.2)]
        if sg < 0:
            pr = pr[::-1]
        pd = G.prism("vpd%d" % (sg + 1), pr, px0, px1, 'X')
        add.append(G.csg(pd, sub=[G.cyl("vpdb%d" % (sg + 1), c, rso + 0.15, zc1 - 1, zc2 + 1, n=256)]))
    kz0 = 331.0 + P.JAR_LIFT - 36.0                                 # key rib from 331 (above the pad's 50 deg underside)
    add.append(G.csg(sector("vkey", rk_, rso + 0.5, kz0, zc2, ka - math.degrees(math.asin(kw / 2 / rso)),
                            ka + math.degrees(math.asin(kw / 2 / rso)), c=c, n=1440),
                     inter=[G.box("vkeyi", kx - 3.0, kx + 3.0, 0.0, yc, kz0, zc2)]))
    # v3-A1 bayonet lugs with a 50 deg underside (v2: flat 5.5 cantilevers at 275, printcheck fail): body at 311 -> R37 tip
    k_ = math.tan(P.BAYO_LUG_SLOPE * D2R)
    rl0 = rk + 0.5
    lz0, lz1 = P.IF_BAYO_LUG_Z
    for k in range(P.IF_BAYO_N):
        a = 360.0 * k / P.IF_BAYO_N
        add.append(G.revolve("vlug%d" % k, [(rl0, lz0), (P.IF_BAYO_LUG_R, lz0 + (P.IF_BAYO_LUG_R - rl0) * k_),
                                            (P.IF_BAYO_LUG_R, lz1), (rl0 - 0.5, lz1), (rl0 - 0.5, lz0)],
                             center=(c[0], c[1], 0), n=720, a0=(a - P.BAYO_LUG_HW) * D2R, a1=(a + P.BAYO_LUG_HW) * D2R))
    # baffle over the outlet sector (+X at PIV_jar 0): underside ramps on both edges, roof shedding to both sides
    bf = sector("vbf", P.BAFFLE_R[0], P.BAFFLE_R[1], z0, P.BAFFLE_TOP, -P.BAFFLE_HALF, P.BAFFLE_HALF)
    bf = G.csg(bf, sub=[edge_halfspace("vbr%d" % i, s * P.BAFFLE_HALF, P.BAFFLE_RAMP_TOP, P.BAFFLE_RAMP, True,
                                       foot=z0 + P.BAFFLE_FLAT) for i, s in enumerate((1, -1))] +
               [edge_halfspace("vbt%d" % i, s * P.BAFFLE_HALF, P.BAFFLE_EDGE_TOP, P.BAFFLE_ROOF, False)
                for i, s in enumerate((1, -1))])
    add.append(bf)
    v = G.csg(v, add=add)
    # SNAP-V fingers in the +/-Y cheeks: relief slots (front only below the gate floor, behind, both sides) down to z_root
    fx0, fx1 = V["x"]
    t, rl, sd, zr0 = V["t"], V["relief"], V["side"], V["z_root"]
    sub = []
    for sg in (1, -1):
        def yb(y0, y1):
            return (min(sg * y0, sg * y1), max(sg * y0, sg * y1))
        ya, yb_ = yb(yc - 1.0, yc)
        sub.append(G.box("vfr%d" % (sg + 1), fx0 - sd, fx1 + sd, ya, yb_, zr0, vz1 + 0.01))          # front (under the floor)
        ya, yb_ = yb(yc + t, yc + t + rl)
        sub.append(G.box("vfb%d" % (sg + 1), fx0 - sd, fx1 + sd, ya, yb_, zr0, zc2 + 1))             # behind
        ya, yb_ = yb(yc - 1.0, yc + t + rl)
        sub.append(G.box("vfs%d" % (sg + 1), fx0 - sd, fx0, ya, yb_, zr0, zc2 + 1))                  # sides
        sub.append(G.box("vft%d" % (sg + 1), fx1, fx1 + sd, ya, yb_, zr0, zc2 + 1))
    # gate detent notch in the +Y cheek face (closed pose) and a 45 deg lead-in at the cheek's +X end inner corner
    GF = P.GATE_FINGER
    ybc = yc + GF["bump_d"] - GF["bump_r"]
    sub.append(G.cyl("vgn", (GF["x_bump"], ybc), GF["bump_r"] + GF["notch_clr"], vz1, sz0, n=48))
    sub.append(G.prism("vgl", [(14.0, yc - 0.5), (16.0, yc - 0.5), (16.0, yc + 1.5)], vz1, zc2 + 1))
    v = G.csg(v, sub=sub)
    barbs = []
    zb_ = V["barb_z"]
    for sg in (1, -1):
        bar = G.revolve("vbb%d" % (sg + 1), [(V["barb_r"], zb_), (V["barb_r"] + 0.5, zb_), (yc + 2.0, zb_ - (yc + 1.5 - V["barb_r"])),
                                             (yc + 2.0, zc2 + 2.0), (V["barb_r"], zb_ + 0.3)], center=(c[0], c[1], 0), n=720,
                        a0=(90.0 * sg - 30.0) * D2R, a1=(90.0 * sg + 30.0) * D2R)
        ya, yb_ = (0.0, yc + 0.5) if sg > 0 else (-yc - 0.5, 0.0)
        barbs.append(G.csg(bar, inter=[G.box("vbbi%d" % (sg + 1), fx0, fx1, ya, yb_, zr0, zc2)]))
    v = G.csg(v, add=barbs)
    A.part(v, "PRT_jar_valve", 'PRT', "pla_b", joint="PIV_jar", stl="jar_valve", print_rot=A.R_ID,
           orient="skirt + baffle bottom on the bed; lug undersides 50 deg, snap fingers and pads grow up", supports="no",
           infill=40)
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
    # v3-A1 SNAP-IP detent finger along the +Y edge (root at -X): relief slot on its inner side and across its free end
    xr, xf = GF["x_bump"] - GF["L"], GF["x_bump"] + GF["free"]
    yi = hw - GF["w"]
    sw = GF["slot"]
    bl = G.csg(bl, sub=[G.box("gfs", xr, xf + sw, yi - sw, yi, g0 - 1, g1 + 1),
                        G.box("gfe", xf, xf + sw, yi - sw, hw + 1, g0 - 1, g1 + 1)])
    bump = G.prism("gfb", G.circle((GF["x_bump"], ybc), GF["bump_r"], n=48), g0, g1 - 0.4)
    bl = G.csg(bl, add=[bump])
    # A2 hotfix (v3-A1-03) open detent finger: relief slots through the blade and lug on both sides of the lug's +Y
    # part (free end = the blade's -X edge), then the R0.6 bump on its +Y face, full height so it prints from the bed
    OD = P.GATE_OPEN_DETENT
    oy0, oy1 = OD["y"]
    oxr = x0 + OD["L"]
    bl = G.csg(bl, sub=[G.box("gos0", x0 - 1.0, oxr, oy0 - OD["slot_in"], oy0, g0 - 1, g1 + ld + 1),
                        G.box("gos1", x0 - 1.0, oxr, oy1, oy1 + OD["slot_out"], g0 - 1, g1 + ld + 1)])
    ody = lhy + P.GATE_STOP_CLR + OD["bump_d"] - OD["bump_r"]
    obump = G.csg(G.prism("gob", G.circle((x0 + lx / 2, ody), OD["bump_r"], n=48), g0, g1 + ld),
                  inter=[G.box("gobi", x0, x0 + lx, oy0, oy1 + 1.0, g0 - 1, g1 + ld + 1)])
    bl = G.csg(bl, add=[obump])
    A.part(bl, "PRT_jar_gate", 'PRT', "pla_a", joint="PIV_gate", stl="jar_gate", print_rot=A.R_ID,
           orient="flat, chamfer, tab and stop lug up; the detent finger bends in the layer plane", supports="no",
           infill=100)
    fl = ((round(xr, 2), round(hw - GF["w"] / 2, 2), round(0.5 * (g0 + g1), 2)),
          (round(GF["x_bump"], 2), round(hw - GF["w"] / 2, 2), round(0.5 * (g0 + g1), 2)))
    vf = [((round(0.5 * (fx0 + fx1), 2), round(sg * (yc + t / 2), 2), zr0), (round(0.5 * (fx0 + fx1), 2), round(sg * (yc + t / 2), 2),
                                                                             round(zb_ + 0.2, 2))) for sg in (1, -1)]
    ofl = ((round(x0 + OD["L"], 2), round(0.5 * (oy0 + oy1), 2), round(0.5 * (g0 + g1), 2)),
           (round(x0 + lx / 2, 2), round(0.5 * (oy0 + oy1), 2), round(0.5 * (g0 + g1), 2)))
    print("GATE_OPEN_DETENT flex", ofl, "stress %.2f" % P.GATE_OPEN_DETENT_STRESS)
    return fl, vf


def build(P):
    hook_flex = build_crown(P)
    build_drive(P)
    build_disc(P)
    build_bus(P)
    gate_flex, valve_flex = build_jar(P)
    print("FEEDER flexures: crown hooks %s; gate finger %s (%.1f MPa); valve snaps %s (%.1f MPa, L %.1f)"
          % (hook_flex, gate_flex, P.GATE_FINGER_STRESS, valve_flex, P.VALVE_SNAP_STRESS, P.VALVE_SNAP_L))
