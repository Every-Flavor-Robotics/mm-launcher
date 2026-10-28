"""Base (static): shell with deck, removable floor, battery bay (+X slide-out), DeWalt adapter, buck, MotorGo
behind the rear partition (vertical USB-C into the rear niche), servo controller, pan servo + pinion.

v3 attempt 1 (min-hardware, DESIGN_LOG "Attempt 1: plan" joint table): the only base screws left are FST_adapter_0/1
(M3 pan x 10, diagonal corners, counterbored flush) and the pan servo centre screw FST_pinion_ctr.
  - PRT_base_partition is merged into PRT_base_floor (the wall grows up from the plate)
  - MotorGo: card guides on that wall + deck ribs over its top edge (CAPT)
  - buck: flange strips under 45 deg hook rails on the floor, -X end held by shell wall ribs (CAPT)
  - servo controller: +0.4 fences + 2 in-plane hold-down tongues in the floor (SNAP-IP)
  - floor: 2 in-plane latches (+Y, finger pads) + 2 in-plane detents (-Y) into keeper pockets on the shell wall feet
  - pan drive: mount plate pressed onto the 4 deck-post pins (crush ribs), servo backed by a floor column, pinion on
    the horn by 8 printed pins in a horn pocket
"""
import math
from cadlib import geom as G, features as F, asm as A
import placeholders as PH

C = PH.C
UP, DOWN = (0.0, 0.0, 1.0), (0.0, 0.0, -1.0)


class Geo:
    """Derived numbers (one place, from params)."""

    def __init__(self, P):
        self.h = P.BASE_HALF
        self.z0 = P.FLOOR_T                                  # shell bottom = floor top
        self.zd0 = P.IF_DECK_Z - P.DECK_T                    # deck underside 86
        self.zd1 = P.IF_DECK_Z                               # deck top 90
        b = P.BATT
        self.bay_x0 = b[0] - P.BAY_CLR                       # 8
        self.bay_y0 = b[2] - P.BAY_CLR                       # -117 (rear wall inner face)
        self.bay_y1 = b[3] + P.BAY_CLR                       # -37
        self.bay_z0 = b[4] - P.BAY_CLR                       # 2.6
        self.bay_ym = 0.5 * (b[2] + b[3])                    # -77
        a = P.ADAPTER
        i = P.ADAPTER_HOLE_INSET
        # 0, 1 on the +X side (A3-M2: those are the ones the pack slides past)
        self.adapter_holes = [(a[1] - i, a[3] - i), (a[1] - i, a[2] + i), (a[0] + i, a[3] - i), (a[0] + i, a[2] + i)]
        self.mg_pcb_y = P.MG_WALL_Y + P.MG_STANDOFF + P.MG_PCB_T          # world y of the STEP z = 0 plane
        self.usb = (P.MG_X0 - P.USB_STEP[0], P.MG_Z0 - P.USB_STEP[1])     # world x, z of the USB-C axis
        self.usb_y0 = self.mg_pcb_y - P.USB_STEP[2] - 0.2                 # plug face
        self.mg_holes = [(P.MG_X0 - sx, P.MG_Z0 - sy) for sx, sy in ((0, 0), (58, 0), (0, -49), (58, -49))]
        self.S = P.PAN_SERVO_TOP_Z
        px, py = P.IF_PINION_XY
        self.pin = (px, py)
        self.horn_z0 = self.S + P.HORN_LIFT                               # horn hub underside
        hc = C["servo_horn_disc"]
        self.horn_disc0 = self.horn_z0 + hc["hub"]["h"]
        self.horn_disc1 = self.horn_disc0 + hc["disc"]["t"]
        self.pin_z0 = self.horn_disc1 - P.HORN_RECESS                     # pinion hub bottom
        sv = C["hiwonder_bus_servo"]
        self.sv_L, self.sv_W, self.sv_H = sv["body"]
        self.sv_off = sv["spline"]["offset_from_body_centre"]
        # servo body along world -Y from the spline axis (u = -Y): y from py - (off - L/2) .. py + off + L/2
        self.sv_y0, self.sv_y1 = py + self.sv_off - self.sv_L / 2, py + self.sv_off + self.sv_L / 2
        self.sv_z0 = self.S - self.sv_H
        bc = P.BUCK_C
        self.buck_z0 = self.z0 + P.BUCK_BOSS_H
        self.buck_holes = [(bc[0], bc[1] + s * P.BUCK_HOLE_Y) for s in (1, -1)]
        c = P.CTRL
        self.ctrl_c = (0.5 * (c[0] + c[1]), 0.5 * (c[2] + c[3]))
        self.ctrl_z = self.z0 + P.CTRL_BOSS_H
        hr = C["hiwonder_servo_controller"]["holes"]["rect"]
        self.ctrl_holes = [(self.ctrl_c[0] + sx * hr[1] / 2, self.ctrl_c[1] + sy * hr[0] / 2) for sx in (-1, 1) for sy in (-1, 1)]
        # ---- v3-A1
        self.pin_z0 = self.horn_disc1 - P.PAN_HORN_POCKET               # pinion hub bottom (horn pocket mouth)
        self.mg_face = self.mg_pcb_y - P.MG_PCB_T                         # MotorGo component face (-Y)
        st = C["motorgo_axis"]
        self.mg_x0, self.mg_x1 = P.MG_X0 - st["stl_bbox_max"][0], P.MG_X0 - st["stl_bbox_min"][0]   # PCB vertical edges
        self.mg_top = P.MG_Z0 - st["stl_bbox_min"][1]                     # PCB top edge (70.25)
        self.buck_x0 = P.BUCK_C[0] - C["buck_12v_finned"]["body"][0] / 2
        self.col_top = self.sv_z0 - sv["idler_boss"]["protrudes"] - P.PAN_COLUMN_GAP   # 27.8
        self.q_keep = P.BASE_HALF - P.WALL - 2.2                          # keeper face |y| 114.8
        qf = self.q_keep - 0.3                                            # post face |y| 114.5
        zb = P.FLOOR_BARB_Z
        self.arms, self.keepers, self.flex = [], [], []
        w, eng, rel = P.FLOOR_LATCH_WD
        for i, (xr, xt) in enumerate(P.FLOOR_LATCH):
            self.arms.append(("fl_l%d" % i, xr, xt, 1, (qf - w, qf), rel + 0.5, (14.0, 100.0, qf), (zb, 0.3, eng, False, (0.0, 6.0)),
                              (8.0, 106.0, 4.5)))
        w, eng, rel = P.FLOOR_DETENT_WD
        for i, (xr, xt) in enumerate(P.FLOOR_DETENT):
            self.arms.append(("fl_d%d" % i, xr, xt, -1, (qf - w, qf), rel + 0.5, (6.0, qf - w, qf), (zb, 0.3, eng, True, (0.0, 6.0)),
                              None))
        for nm, xr, xt, sd, aq, rl, hd, bb, ho in self.arms:
            d = 1.0 if xt > xr else -1.0
            xs = sorted((xt + d * bb[4][0], xt + d * bb[4][1]))
            qt = hd[2] + bb[1] + bb[2]
            self.keepers.append((sd, xs[0] - 0.5, xs[1] + 0.5, _pocket(hd[2], bb[0], qt, bb[3])))
        w, eng, rel = P.CTRL_TONGUE_WD
        xr, xt = P.CTRL_TONGUE_X
        zc = self.ctrl_z + C["hiwonder_servo_controller"]["pcb"][2] + 0.2      # lip underside 0.2 over the PCB
        for i, (yc, sd) in enumerate(zip(P.CTRL_TONGUE_Y, (1, -1))):
            qc = sd * yc
            qe = (c[2] - 0.4) if sd > 0 else -(c[3] + 0.4)               # post face 0.4 off the PCB edge
            self.arms.append(("ct%d" % i, xr, xt, sd, (qc - w / 2, qc + w / 2), rel + 0.5, (6.0, qc - w / 2, qe),
                              (zc, 0.4, eng, False, (0.0, 6.0)), None))


def screw(name, at, into, length, spec, host, step, joint=None, cut=()):
    """One fastener: the same at/into for every part it passes and for asm.fastener.
    cut = [(kind, kwargs, sink_list)]: features.screw_hole cutters appended to each list."""
    for kind, kw, lst in cut:
        lst += F.screw_hole(at, into, length, kind=kind, name=name, **kw)
    A.fastener(name, at, into, length, spec=spec, joint=joint, host=host, step=step)


# ------------------------------------------------------------------ printed parts

def _qpoly(pts, s):
    """(q, z) profile with q = s * world y -> (y, z) points, counter-clockwise for prism(..., 'X')"""
    out = [(s * q, z) for q, z in pts]
    return out if s > 0 else out[::-1]


def inplane_arm(name, xr, xt, s, arm_q, relief, head, gap=0.8, T=3.0):
    """SNAP-IP arm cut through the flat floor plate (z 0..T): beam along X from root xr to tip xt, in the layer plane.
    q = s * world y. The beam spans q arm_q = (qa0, qa1) and deflects toward -q into a relief `relief` wide; the head
    (hl along X beyond the tip, q hq0..hq1) carries the post. Returns (cuts, adds, d) with d = sign(xt - xr)."""
    d = 1.0 if xt > xr else -1.0
    qa0, qa1 = arm_q
    hl, hq0, hq1 = head
    def ys(q0, q1):
        return sorted((s * q0, s * q1))
    xs = sorted((xr, xt))
    cut = [G.box(name + "_ca", xs[0], xs[1], *ys(qa0 - relief, qa1 + gap), -1, T + 1)]
    xh = sorted((xt - d * gap, xt + d * (hl + gap)))
    cut.append(G.box(name + "_ch", xh[0], xh[1], *ys(hq0 - relief, hq1 + gap), -1, T + 1))
    xa = sorted((xr - d * 0.5, xt + d * 0.01))
    add = [G.box(name + "_a", xa[0], xa[1], *ys(qa0, qa1), 0, T)]
    xh2 = sorted((xt, xt + d * hl))
    add.append(G.box(name + "_h", xh2[0], xh2[1], *ys(hq0, hq1), 0, T))
    return cut, add, d


def build_shell(P, g, cuts_from_screws):
    h, r, W = g.h, P.BASE_CORNER_R, P.WALL
    outer = G.prism("shell", G.rrect(-h, h, -h, h, r, 12), g.z0, g.zd1, 'Z')
    G.bevel(outer, P.EB)
    inner = G.prism("cav", G.rrect(-h + W, h - W, -h + W, h - W, r - W, 12), g.z0 - 1, g.zd0, 'Z')
    ob = G.csg(outer, sub=[inner])
    add = []
    # battery bay: front partition and inner end wall (2.0 to the pack each side)
    add.append(G.box("bay_f", g.bay_x0 - 3, h - 1, g.bay_y1, g.bay_y1 + 3, g.z0, g.zd0 + 0.5))
    add.append(G.box("bay_e", g.bay_x0 - 3, g.bay_x0, -h + 1, g.bay_y1 + 3, g.z0, g.zd0 + 0.5))
    # v3-A1 adapter: 4 printed fences (2 thick, +0.4) round its full-width body take the shear; 2 screws take the hang.
    # The +X fence stops at ADAPTER_FENCE[3] so the battery's rail stem (top 74.6) slides out under it; the -X fence
    # has a notch for the adapter lead (open at the fence tip in the deck-down print: no bridge)
    a = P.ADAPTER
    ft, fc, fz0, fz0x = P.ADAPTER_FENCE
    zt = g.zd0 + 0.5
    add.append(G.box("af_mx", a[0] - fc - ft, a[0] - fc, a[2] - fc - ft, a[3] + fc + ft, fz0, zt))
    add.append(G.box("af_px", a[1] + fc, a[1] + fc + ft, a[2] - fc - ft, a[3] + fc + ft, fz0x, zt))
    for k, (y0, y1) in enumerate(((a[2] - fc - ft, a[2] - fc), (a[3] + fc, a[3] + fc + ft))):
        add.append(G.box("af_y%d" % k, a[0] - fc - ft, a[1] + fc + ft, y0, y1, fz0, zt))
    # USB niche: two side walls + a V floor (print: deck on the bed, so the V points up and needs no support)
    xc, k, hw = g.usb[0], P.NICHE_V_SLOPE, P.NICHE_W / 2
    zv = g.usb[1] - 14.5                                   # V apex under the cable
    ztv = zv + k * hw
    dz = W * math.sqrt(1 + k * k)
    ny0, ny1 = -h + 1, P.MG_WALL_Y - 3 - 0.5               # rear wall .. 0.5 short of the partition
    zt_o = ztv + k * W - dz
    band = G.prism("n_v", [(xc - hw - W, zt_o), (xc, zv - dz), (xc + hw + W, zt_o)], ny0, ny1, 'Y')
    band = G.csg(band, sub=[G.prism("n_vi", [(xc - hw, ztv), (xc, zv), (xc + hw, ztv), (xc + hw, zt_o + 5), (xc - hw, zt_o + 5)],
                                    ny0 - 1, ny1 + 1, 'Y')])
    add.append(band)
    for s in (-1, 1):
        xa, xb = (xc - hw - W, xc - hw) if s < 0 else (xc + hw, xc + hw + W)
        add.append(G.box("n_s%d" % s, xa, xb, ny0, ny1, ztv - 1.5, g.zd0 + 0.5))
    # v3-A1: the 8 floor-screw columns are gone (FST_floor x8 -> latches). Deck posts for the pan servo mount: the
    # post shoulder (z S + T) is the seat, a pin below it presses into the plate's crush-rib hole
    pr, pl = P.PAN_POST_PIN
    for i, (x, y) in enumerate(P.PAN_POSTS):
        add.append(G.cyl("dp%d" % i, (x, y), 4.5, g.S + P.PAN_PLATE_T, g.zd0 + 0.5))
        add.append(G.cyl("dpp%d" % i, (x, y), pr, g.S + P.PAN_PLATE_T - pl, g.S + P.PAN_PLATE_T + 0.01, n=32))
    # v3-A1 MotorGo: ribs from the deck underside end 0.5 over the board's top edge (CAPT in its card guides)
    for i, (x0, x1) in enumerate(P.MG_RIB_X):
        add.append(G.box("mgr%d" % i, x0, x1, g.mg_face - 1.5, g.mg_pcb_y + 1.5, g.mg_top + 0.5, g.zd0 + 0.5))
    # v3-A1 buck: ribs on the -X wall, 0.3 off the buck's -X end (it slides -X out of its floor rails); full height
    # so the deck-down print has no overhang
    for i, yb in enumerate(P.BUCK_STOP_Y):
        add.append(G.box("bks%d" % i, -h + W - 0.01, g.buck_x0 - 0.3, yb - 2.0, yb + 2.0, g.z0, g.zd0 + 0.5))
    # v3-A1 floor keepers: a block on each wall foot with a pocket the floor barb snaps into. The pocket's retaining
    # face is a 7 mm bridge between the block cheeks in the deck-down print; the block top slopes 45 deg into the wall
    for i, (sd, xk0, xk1, poly) in enumerate(g.keepers):
        qk, qw = g.q_keep, h - W
        blk = G.prism("kp%d" % i, _qpoly([(qk, g.z0), (qw + 0.01, g.z0), (qw + 0.01, 13.0 + (qw - qk)), (qk, 13.0)], sd),
                      xk0 - 2.5, xk1 + 2.5, 'X')
        blk = G.csg(blk, sub=[G.prism("kpp%d" % i, _qpoly(poly, sd), xk0, xk1, 'X')])
        add.append(blk)
    ob = G.csg(ob, add=add)

    sub = list(cuts_from_screws)
    sub.append(G.cyl("dh", P.IF_PAN_XY, P.IF_DECK_HOLE_R, g.zd0 - 1, g.zd1 + 1))
    # bay void + the +X window = pack outline + 2 (A3-A3), with a 1 mm x 45 deg lead-in
    sub.append(G.box("bay", g.bay_x0, h + 2, g.bay_y0, g.bay_y1, g.z0 - 1, P.BAY_WINDOW_Z1))
    # end the rear wall where the corner arc would leave it thinner than 1.6 (pack corner passes here)
    xr = (h - r) + math.sqrt(r * r - (r - W + 1.8) ** 2)     # 98.4: rear-wall strip >= 1.6 thick up to here
    sub.append(G.box("bay_r", xr, h + 2, -h - 1, g.bay_y0 + 0.01, g.z0 - 1, P.BAY_WINDOW_Z1))
    y0, y1, ztw = g.bay_y0, g.bay_y1, P.BAY_WINDOW_Z1
    sub.append(G.loft("bay_ch", [(y0 - 1, g.z0 - 1), (y1 + 1, g.z0 - 1), (y1 + 1, ztw + 1), (y0 - 1, ztw + 1)],
                      [(y0, g.z0 - 1), (y1, g.z0 - 1), (y1, ztw), (y0, ztw)], h + 0.01, h - 1.0, 'X'))
    # top finger scallop (the bottom one is in the floor plate); its crown stops at the deck underside
    rs = P.BAY_SCALLOP_D / 2
    sub.append(G.cyl("sc_t", (g.bay_ym, g.zd0 - rs), rs, h - W - 1, h + 1, 'X'))
    # adapter lead through the bay end wall, and its notch at the -X fence tip
    sub.append(G.box("bay_wire", g.bay_x0 - 4, g.bay_x0 + 1, -86, -70, 64, 78))
    sub.append(G.box("af_wire", a[0] - fc - ft - 1, a[0] - fc + 0.5, -83, -73, fz0 - 1, 79.5))
    # USB niche opening in the rear wall (same V profile)
    sub.append(G.prism("n_open", [(xc - hw, P.NICHE_TOP_Z), (xc - hw, ztv), (xc, zv), (xc + hw, ztv), (xc + hw, P.NICHE_TOP_Z)],
                       -h - 1, -h + W + 0.5, 'Y'))
    # buck intake louvres (left wall, low) and exhaust louvres (left wall, high)
    bx, by = P.BUCK_C
    for kk in range(9):
        y = by - 32 + 8 * kk
        sub.append(G.prism("lv%d" % kk, G.rrect(y - 1.5, y + 1.5, 12, 30, 1.4), -h - 1, -h + W + 1, 'X'))
        sub.append(G.prism("hv%d" % kk, G.rrect(y - 1.5, y + 1.5, 52, 76, 1.4), -h - 1, -h + W + 1, 'X'))
    # front wall vents (cross flow past the servo controller)
    for kk in range(4):
        x = 68 + 6 * kk                                     # straight wall only
        sub.append(G.prism("fv%d" % kk, G.rrect(x - 1.5, x + 1.5, 30, 70, 1.4), h - W - 1, h + 1, 'Y'))
    # servo controller (v2-A1-11): switch and terminal windows only, framed by a printed bezel on the +X face.
    # The wall stays closed over the rest of the board (no PCB in the side view).
    zw0, zw1 = P.CTRL_WIN_Z
    bw, bp = P.CTRL_BEZEL
    wins = (P.CTRL_WIN_SW, P.CTRL_WIN_TB)
    def win(y0, y1, z0, z1, r, n=6):
        # square corners at the world-bottom edge: printed deck-down that edge is a flat 16 mm bridge, not an arc overhang
        pts = [(y0, z0), (y1, z0)]
        for cy, a_ in ((y1 - r, 0), (y0 + r, 90)):
            pts += [(cy + r * math.cos(math.radians(a_ + 90 * i / n)), z1 - r + r * math.sin(math.radians(a_ + 90 * i / n)))
                    for i in range(n + 1)]
        return pts
    for kw, (y0, y1) in enumerate(wins):
        sub.append(G.prism("ctrl_w%d" % kw, win(y0, y1, zw0, zw1, 1.5), h - W - 1, h + bp + 1, 'X'))
        # 0.8 x 45 deg lead-in on the bezel face (sides and top; the world-bottom edge stays square for the bridge)
        sub.append(G.loft("ctrl_wc%d" % kw, win(y0, y1, zw0, zw1, 1.5), win(y0 - 0.8, y1 + 0.8, zw0, zw1 + 0.8, 2.3),
                          h + bp - 0.6, h + bp + 0.2, 'X'))
    by0, by1 = wins[0][0] - bw, wins[-1][1] + bw
    bz0, bz1 = zw0 - bw, zw1 + bw
    # world-top side insets 1.6 x bp (printed deck-down it is the overhang side: 32 deg from vertical); the
    # world-bottom side only 0.5 x bp, so the 2.5 rail under the windows keeps >= 1.6 at the face
    bez = G.loft("ctrl_bz", G.rrect(by0, by1, bz0, bz1, 3.0), G.rrect(by0 + bp, by1 - bp, bz0 + 0.5 * bp, bz1 - 1.6 * bp, 3.0 - bp),
                 h - 0.5, h + bp, 'X')
    ob = G.csg(ob, add=[bez])
    ob = G.csg(ob, sub=sub)
    # zip-tie anchor on the niche's left wall (vertical tunnel, no bridge). v3-A1: its world top slopes 45 deg up into
    # the niche wall (printed deck-down that face was a 6.0 mm cantilever, the baseline printcheck fail)
    xw = xc - hw
    blk = G.prism("anc", [(xw - 0.5, ztv + 1), (xw + 6, ztv + 1), (xw + 6, ztv + 11), (xw - 0.5, ztv + 17.5)], -112, -104, 'Y')
    tun = G.box("anc_t", xw + 2, xw + 4, -110, -106, ztv, ztv + 18)
    ob = G.csg(ob, add=[blk])
    ob = G.csg(ob, sub=[tun])
    A.part(ob, "PRT_base_shell", 'PRT', "pla_a", stl="base_shell", print_rot=A.R_FLIP,
           orient="upside down: deck face on the bed, walls up", supports="no", infill=15)


TIP = 1.2     # barb / lip tip land (wall probe >= 1.6 across the lead-in)


def _barb(q0, q1, zb, gap, eng, detent):
    """post + barb profile (q, z) from the arm head (q0..q1) up; barb tip q1 + gap + eng; 45 deg lead-in on top;
    detent=True: 45 deg underside too (pops on a firm pull), else a flat retaining face"""
    qt = q1 + gap + eng
    run = qt - q1
    lo = [(q1, zb - run), (qt, zb)] if detent else [(q1, zb), (qt, zb)]
    return [(q0, 0.0), (q1, 0.0)] + lo + [(qt, zb + TIP), (q1, zb + TIP + run), (q0, zb + TIP + run)], qt, run


def _pocket(q1, zb, qt, detent):
    """keeper pocket (q, z): the barb profile grown 0.15 (bottom 0.1), open past the keeper face"""
    o = 0.15
    qa = q1 - 0.6
    top = [(qt + o, zb + TIP + o), (qa, zb + TIP + o + (qt + o - qa))]
    if detent:
        return [(qa, zb - o - (qt + o - qa)), (qt + o, zb - o)] + top
    return [(qa, zb - 0.1), (qt + o, zb - 0.1)] + top


def build_floor(P, g):
    """v3-A1: floor plate + the merged MotorGo partition wall (card guides), buck hook rails, servo controller fences
    and hold-down tongues, the pan servo column, and the 4 in-plane latches that replace FST_floor x8."""
    h, T = g.h, P.FLOOR_T
    pl = G.prism("floor", G.rrect(-h, h, -h, h, P.BASE_CORNER_R, 12), 0, T, 'Z')
    G.bevel(pl, P.EB)
    add, sub, add2, sub2 = [], [], [], []
    # ---- MotorGo partition wall (was PRT_base_partition + FST_partition x2), USB-C opening, foot gussets
    x0, x1 = P.MG_PART_X
    yw = P.MG_WALL_Y
    add.append(G.box("part", x0, x1, yw - 3, yw, T - 0.01, g.zd0 - 0.5))
    add += [G.box("pf%d" % i, xf - 5, xf + 5, yw - 0.01, yw + 5, T - 0.01, T + 8) for i, xf in enumerate((x0 + 8, x1 - 8))]
    ux, uz = g.usb
    # USB-C plug opening (plug 7 x 12.5 + 1 all round); the wall prints upright, so the top is a 45 deg gable
    sub2.append(G.prism("usb", [(ux - 4.5, uz - 7.25), (ux + 4.5, uz - 7.25), (ux + 4.5, uz + 6.75), (ux, uz + 11.25),
                                (ux - 4.5, uz + 6.75)], yw - 4, yw + 1, 'Y'))
    # ---- MotorGo card guides (CAPT, replaces FST_mg x4 + standoffs): 2 vertical slotted rails take the PCB's
    # vertical edges (slot = PCB + 2 x MG_GUIDE clearance... 1.77 + 0.3); the slot bottom at the board's bottom edge is
    # the floor stop. Each rail: a slot block round the edge + a web back to the wall, kept off the USB plug.
    cl, eng, zs, eng_c = P.MG_GUIDE
    yp0, yp1 = g.mg_face, g.mg_pcb_y
    ztop = g.mg_top - 2.0
    for i, (xe, kk) in enumerate(((g.mg_x0, 1.0), (g.mg_x1, -1.0))):
        bx0, bx1 = sorted((xe - kk * (cl + 2.5), xe + kk * eng))
        add.append(G.box("mgg%d" % i, bx0, bx1, yp0 - cl / 2 - 2.0, yp1 + cl / 2 + 2.0, T - 0.01, ztop))
        wx0, wx1 = sorted((xe - kk * (cl + 2.5), xe - kk * (cl + 0.3)))
        add.append(G.box("mgw%d" % i, wx0, wx1, yw - 0.01, yp0 - cl / 2 - 1.99, T - 0.01, ztop))
        sx0, sx1 = sorted((xe - kk * cl, xe + kk * (eng + 0.1)))
        sub2.append(G.box("mgs%d" % i, sx0, sx1, yp0 - cl / 2, yp1 + cl / 2, zs, ztop + 1))
        rx0, rx1 = sorted((xe + kk * eng_c, xe + kk * (eng + 0.1)))      # component-face wall only eng_c over the PCB
        sub2.append(G.box("mgc%d" % i, rx0, rx1, yp0 - cl / 2 - 2.1, yp0 - cl / 2 + 0.01, zs, ztop + 1))
        # lead-in at the slot mouth (45 deg, 1 mm)
        sub2.append(G.loft("mgl%d" % i, G.rrect(sx0, sx1, yp0 - cl / 2, yp1 + cl / 2, 0.01),
                           G.rrect(sx0 - 1, sx1 + 1, yp0 - cl / 2 - 1, yp1 + cl / 2 + 1, 0.01), ztop - 1.0, ztop + 0.01, 'Z'))
    # ---- buck hook rails (CAPT, replaces FST_buck x2): the flange's two fin-free strips slide +X under 45 deg
    # undercut lips to an end stop; the shell's -X wall ribs hold it there once the floor is in
    bx, by = P.BUCK_C
    Lx, Ly, H = C["buck_12v_finned"]["body"]
    rc, lov, lg = P.BUCK_RAIL
    fz0, fz1 = g.buck_z0, g.buck_z0 + P.BUCK_FLANGE_T
    qe = Ly / 2
    qw, ql = qe + rc, qe - lov
    zl = fz1 + lg + (qw - ql) + 0.5                        # lip top
    xb0, xb1 = bx - Lx / 2, bx + Lx / 2
    for t in (1, -1):
        def yq(q):
            return by + t * q
        add.append(G.box("bkr%d" % t, xb0, xb1, *sorted((yq(qe - 6.0), yq(qe + 0.01))), T - 0.01, fz0))
        prof = [(ql, fz1 + lg + (qw - ql)), (qw, fz1 + lg), (qw + 3.0, fz1 + lg), (qw + 3.0, zl), (ql, zl)]
        prof = [(yq(q), z) for q, z in prof]
        prof = prof if t > 0 else prof[::-1]
        add.append(G.prism("bkl%d" % t, prof, xb0, xb1 + rc + 3.0, 'X'))
        add.append(G.box("bkw%d" % t, xb0, xb1 + rc + 3.0, *sorted((yq(qw), yq(qw + 3.0))), T - 0.01, zl))
        add.append(G.box("bke%d" % t, xb1 + rc, xb1 + rc + 3.0, *sorted((yq(qe - 6.0), yq(qw + 3.0))), T - 0.01, zl))
    # ---- servo controller: drill-to-fit bosses (holes unconfirmed) with centre-punch dimples, +0.4 corner fences
    for i, (x, y) in enumerate(g.ctrl_holes):
        top = (x, y, g.ctrl_z)
        add.append(G.cyl("cb%d" % i, (x, y), P.CTRL_BOSS_D / 2, T - 0.5, g.ctrl_z))
        sub2.append(G.cone("cd%d" % i, (x, y), 0.05, 0.6, g.ctrl_z - 0.6, g.ctrl_z + 0.01, n=12))
        F._log("drill_to_fit_boss", top, DOWN, od=P.CTRL_BOSS_D, height=P.CTRL_BOSS_H)
    c = P.CTRL
    zt = g.ctrl_z + 3
    for sx in (-1, 1):
        for sy in (-1, 1):
            xc = c[1] + 0.4 if sx > 0 else c[0] - 0.4
            yc = c[3] + 0.4 if sy > 0 else c[2] - 0.4
            add.append(G.box("fx%d%d" % (sx, sy), min(xc, xc + sx * 1.6), max(xc, xc + sx * 1.6),
                             min(yc - sy * 5, yc + sy * 1.6), max(yc - sy * 5, yc + sy * 1.6), T - 0.5, zt))
            add.append(G.box("fy%d%d" % (sx, sy), min(xc - sx * 5, xc + sx * 1.6), max(xc - sx * 5, xc + sx * 1.6),
                             min(yc, yc + sy * 1.6), max(yc, yc + sy * 1.6), T - 0.5, zt))
    F._log("pcb_pocket", (g.ctrl_c[0], g.ctrl_c[1], g.ctrl_z), DOWN, w=c[1] - c[0], h=c[3] - c[2], depth=3, clear=0.4)
    # ---- pan servo column (replaces PRT_pan_servo_clamp + FST_panclamp x2): top PAN_COLUMN_GAP under the idler boss;
    # kept +X of the bus lead that runs along x = -4 under the servo
    px, py = g.pin
    add.append(G.box("pcol", px - 1.8, px + 7.0, py - 6.0, py + 6.0, T - 0.01, g.col_top))
    # UART lead clips: the lead presses into the slot (dab of hot glue)
    for i, (x, y) in enumerate(P.UART_CLIPS):
        add.append(G.box("uc%d" % i, x - 4, x + 4, y - 4, y + 4, T - 0.5, T + 7.6))
        sub2.append(G.box("ucs%d" % i, x - 5, x + 5, y - 1.6, y + 1.6, T + 1.0, T + 5.5))
    # rubber-foot recesses and the bottom finger scallop under the battery opening
    for sx in (-1, 1):
        for sy in (-1, 1):
            sub2.append(G.cyl("ft%d%d" % (sx, sy), (sx * 100, sy * 100), 7.0, -1, 1.0))
    sub2.append(G.cyl("sc_b", (h, g.bay_ym), P.BAY_SCALLOP_D / 2, -1, P.FLOOR_T + 1))
    # ---- in-plane arms (SNAP-IP, beam in the floor plane): 2 floor latches (+Y, finger pad), 2 floor detents (-Y),
    # 2 controller hold-down tongues. The post + barb rises from the arm's head.
    for nm, xr, xt, sd, arm_q, relief, head, barb, hole in g.arms:
        cut, ad, d = inplane_arm(nm, xr, xt, sd, arm_q, relief, head, T=T)
        sub += cut
        add2 += ad
        zb, gp, eng, det, xp = barb
        q1 = head[2]
        prof, qt, run = _barb(q1 - 2.2, q1, zb, gp, eng, det)
        xs = sorted((xt + d * xp[0], xt + d * xp[1]))
        add2.append(G.prism(nm + "_b", _qpoly(prof, sd), xs[0], xs[1], 'X'))
        if hole:
            sub2.append(G.cyl(nm + "_fh", (xt + d * hole[0], sd * hole[1]), hole[2], -1, T + 1))
    ob = G.csg(pl, add=add)
    ob = G.csg(ob, sub=sub)
    ob = G.csg(ob, add=add2)
    ob = G.csg(ob, sub=sub2)
    A.part(ob, "PRT_base_floor", 'PRT', "pla_a", stl="base_floor", print_rot=A.R_ID,
           orient="flat, partition wall and bosses up (the v2 partition printed upright too: rear face was its bed)",
           supports="no", infill=15)


def build_pan_mount(P, g):
    """Pocket hung from the four deck posts: plate (servo top bears on its underside) + walls. v3-A1: no screws, no
    clamp: the plate presses up onto the post pins (3 crush ribs per hole), the post shoulders are the seat, and the
    floor's servo column backs the servo from below."""
    px, py = g.pin
    S, T = g.S, P.PAN_PLATE_T
    c, wall = P.SERVO_POCKET_CLR, 2.4
    hw = g.sv_W / 2
    x0p, x1p, y0p, y1p = P.PAN_PLATE
    plate = G.prism("pm", G.rrect(x0p, x1p, y0p, y1p, P.CR), S, S + T, 'Z')
    G.bevel(plate, P.EB)
    wz0 = g.sv_z0 + 0.3                                   # walls stop 0.3 above the case bottom
    walls = G.prism("pmw", G.rrect(px - hw - c - wall, px + hw + c + wall, g.sv_y0 - c - wall, g.sv_y1 + c + wall, 2),
                    wz0, S + 0.01, 'Z')
    inner = G.prism("pmi", G.rrect(px - hw - c, px + hw + c, g.sv_y0 - c, g.sv_y1 + c, 1), wz0 - 1, S + 1, 'Z')
    hole = G.cyl("pmh", (px, py), P.PAN_PLATE_HOLE_R, S - 1, S + T + 1)
    lead = G.box("pml", px - 3, px + 3, g.sv_y1 - 1, g.sv_y1 + c + wall + 1, wz0 - 1, wz0 + 9)   # servo lead exit
    walls = G.csg(walls, sub=[inner, lead])               # pocket tube first, so the plate hole never slivers it
    pr, pl_ = P.PAN_POST_PIN
    rr, ri = P.PAN_POST_RIB
    hr = pr + 0.15                                        # hole radius; ribs reach pr - ri
    sub = [hole]
    for i, (x, y) in enumerate(P.PAN_POSTS):
        hc = G.cyl("pmp%d" % i, (x, y), hr, S - 1, S + T + 1, n=40)
        ribs = [G.cyl("pmr%d%d" % (i, k), (x + (pr - ri + rr) * math.cos(math.radians(90 + 120 * k)),
                                            y + (pr - ri + rr) * math.sin(math.radians(90 + 120 * k))), rr, S - 2, S + T + 2, n=16)
                for k in range(3)]
        sub.append(G.csg(hc, sub=ribs))
        # 0.5 x 45 deg lead-in at the hole mouth (plate top)
        sub.append(G.cone("pmc%d" % i, (x, y), hr, hr + 0.6, S + T - 0.6, S + T + 0.01, n=40))
    plate = G.csg(plate, sub=sub)
    ob = G.csg(plate, add=[walls])
    A.part(ob, "PRT_pan_servo_mount", 'PRT', "pla_a", stl="pan_servo_mount", print_rot=A.R_FLIP,
           orient="plate top on the bed, pocket walls up", supports="no", infill=30)


def build_pinion(P, g):
    """v3-A1 HORN: the horn sits in a 2.7-deep pocket (disc + 0.2) with 8 printed O2.0 pins in its 8 holes (replaces
    FST_pinion x4 M2); the centre screw clamps the horn on the spline through the O6.5 hole, the pinion is held on the
    horn by the pins and trapped axially between the mount plate and the deck."""
    px, py = g.pin
    z0, z1 = P.IF_GEAR_Z
    gear = G.prism("pp", G.gear_poly(P.IF_GEAR_M, P.IF_GEAR_N, c=(px, py), backlash=P.GEAR_BACKLASH,
                                      phase=math.radians(180.0 / P.IF_GEAR_N)), z0, z1, 'Z')
    hub = G.cyl("pph", (px, py), P.PINION_HUB_R, g.pin_z0, z0 + 0.01)
    hd = C["servo_horn_disc"]
    pocket = G.cyl("ppk", (px, py), hd["disc"]["d"] / 2 + 0.1, g.pin_z0 - 1, g.horn_disc1, n=96)
    ctr = G.cyl("ppc", (px, py), 3.25, g.horn_disc1 - 0.01, z1 + 1, n=40)
    ob = G.csg(gear, add=[hub])
    ob = G.csg(ob, sub=[pocket, ctr])
    bc = hd["holes"]["bolt_circle_d"] / 2
    rp, lp = P.PAN_HORN_PIN
    pins = [G.cyl("ppn%d" % k, (px + bc * math.cos(k * math.pi / 4), py + bc * math.sin(k * math.pi / 4)), rp,
                  g.horn_disc1 - lp, g.horn_disc1 + 0.01, n=16) for k in range(hd["holes"]["n"])]
    ob = G.csg(ob, add=pins)
    A.part(ob, "PRT_pan_pinion", 'PRT', "pla_b", joint="PIV_pan_pinion", stl="pan_pinion", print_rot=A.R_FLIP,
           orient="gear top on the bed, horn pocket up (the 8 pins grow up from its floor)", supports="no", infill=40)


# ------------------------------------------------------------------ purchased placeholders

def build_purchased(P, g):
    # battery: envelope body below the adapter face + the rail stem that runs inside the adapter (ESTIMATED width)
    b, a = P.BATT, P.ADAPTER
    body = G.box("bat", b[0], b[1], b[2], b[3], b[4], a[4])
    G.bevel(body, 3.0, seg=2)
    sx, sy = P.BATT_STEM_INSET
    stem = G.box("stem", a[0] + sx, a[1] - sx, a[2] + sy, a[3] - sy, a[4] - 0.5, b[5])
    bat = G.csg(body, add=[stem])
    A.part(bat, "BUY_battery", 'BUY', "buy", mass_g=C["dewalt_20v_battery"]["mass_g"],
           src="components.json dewalt_20v_battery envelope; rail stem width estimated (BATT_STEM_INSET)")
    ad = PH.dewalt_adapter("BUY_dewalt_adapter")
    G.xform(ad, G.frame(((a[0] + a[1]) / 2, (a[2] + a[3]) / 2, a[5]), (1, 0, 0), (0, 1, 0), (0, 0, 1)))
    A.part(ad, "BUY_dewalt_adapter", 'BUY', "buy", mass_g=C["dewalt_20v_adapter"]["mass_g"], src="components.json")
    # buck: flange plate with the two holes on fin-free strips, fins along X (airflow), core block
    Lx, Ly, H = C["buck_12v_finned"]["body"]
    bx, by = P.BUCK_C
    z0, ft = g.buck_z0, P.BUCK_FLANGE_T
    fl = G.box("bk", bx - Lx / 2, bx + Lx / 2, by - Ly / 2, by + Ly / 2, z0, z0 + ft)
    yf = P.BUCK_HOLE_Y - 4.0                                # fins stay clear of the screw heads
    core = G.box("bkc", bx - Lx / 2, bx + Lx / 2, by - yf, by + yf, z0 + ft - 0.01, z0 + ft + 5)
    nf = 8
    fins = [G.box("bkf%d" % kk, bx - Lx / 2, bx + Lx / 2, by - yf + kk * (2 * yf - 2) / (nf - 1),
                  by - yf + kk * (2 * yf - 2) / (nf - 1) + 2, z0 + ft + 4.9, z0 + H) for kk in range(nf)]
    eh = [G.cyl("bkh%d" % i, p, 1.9, z0 - 1, z0 + ft + 1, n=16) for i, p in enumerate(g.buck_holes)]
    bk = G.csg(fl, add=[core] + fins)
    bk = G.csg(bk, sub=eh)
    A.part(bk, "BUY_buck_12v", 'BUY', "buy_metal", mass_g=C["buck_12v_finned"]["mass_g"],
           src="components.json buck_12v_finned (73.8 x 73.8 x 31, holes +/-33.4)")
    # MotorGo: exact STL; STEP X -> world -X, STEP Y -> world -Z, STEP Z (components) -> world -Y (toward the partition)
    mg = PH.motorgo_axis("BUY_motorgo_axis")
    G.xform(mg, G.frame((P.MG_X0, g.mg_pcb_y, P.MG_Z0), (-1, 0, 0), (0, 0, -1), (0, -1, 0)))
    # the STL's mounting holes measure ~Ø2.5-2.6 (v2 brief finding); open them to the M2.5 clearance MG_HOLE_D
    # (components.json still says Ø3.4: unconfirmed on the real board)
    hd = P.MG_HOLE_D
    mg = G.csg(mg, sub=[G.cyl("mgh%d" % i, (hx, hz), hd / 2, g.mg_pcb_y - 3, g.mg_pcb_y + 1, 'Y', n=24)
                        for i, (hx, hz) in enumerate(g.mg_holes)], check=False)
    A.part(mg, "BUY_motorgo_axis", 'BUY', "pcb", mass_g=C["motorgo_axis"]["mass_g"], src="REF/mg_axis.stl")
    ux, uz = g.usb
    u = C["motorgo_axis"]["usb_c"]
    ow, oh = u["plug_overmold"]
    plug = G.prism("BUY_usbc_plug", G.rrect(ux - oh / 2, ux + oh / 2, uz - ow / 2, uz + ow / 2, 2.5),
                   g.usb_y0 - u["straight_run"], g.usb_y0, 'Y')
    A.part(plug, "BUY_usbc_plug", 'BUY', "buy", mass_g=10, src="components.json motorgo_axis.usb_c (plug 12.5 x 7, 25 straight)")
    # servo controller: long edge along world Y
    sc = PH.servo_controller("BUY_servo_controller")
    G.xform(sc, G.frame((g.ctrl_c[0], g.ctrl_c[1], g.ctrl_z), (0, 1, 0), (-1, 0, 0), (0, 0, 1)))
    # bottom-edge parts from the REF photo (v2-A1-11): slide switch (lever at OFF) and 2-pole terminal, edge at world +X
    xe, zt = P.CTRL[1], g.ctrl_z + C["hiwonder_servo_controller"]["pcb"][2]
    sy0, sy1, sd, sh, lw, lh = P.CTRL_SW
    ly = 0.5 * (sy0 + sy1) - 2.0
    ty0, ty1, td, th = P.CTRL_TB
    sc = G.csg(sc, add=[G.box("sc_sw", xe - sd, xe, sy0, sy1, zt - 0.01, zt + sh),
                        G.box("sc_lv", xe - sd / 2 - 1.5, xe - sd / 2 + 1.5, ly - lw / 2, ly + lw / 2, zt + sh - 0.01, zt + sh + lh),
                        G.box("sc_tb", xe - td + 0.5, xe + 0.5, ty0, ty1, zt - 0.01, zt + th)], check=False)
    A.part(sc, "BUY_servo_controller", 'BUY', "pcb", mass_g=C["hiwonder_servo_controller"]["mass_g"],
           src="components.json; switch + terminal positions from REF/servo_controller_board_photo.png (CTRL_SW, CTRL_TB)")
    # pan servo: case static; the output spline belongs to the pinion joint (it lives in the horn object)
    px, py = g.pin
    sv = PH.servo("BUY_servo_pan")
    sv = G.csg(sv, sub=[G.cyl("svb", (0, 0), 3.1, -4.1, 10)])
    G.xform(sv, G.frame((px, py, g.S), (0, -1, 0), (1, 0, 0), (0, 0, 1)))
    A.part(sv, "BUY_servo_pan", 'BUY', "buy", mass_g=C["hiwonder_bus_servo"]["mass_g"], src="components.json")
    hn = PH.horn("BUY_horn_pan")
    spl = G.cyl("spl", (0, 0), C["hiwonder_bus_servo"]["spline"]["boss_d"] / 2, -P.HORN_LIFT - 4.0,
                C["hiwonder_bus_servo"]["spline"]["protrudes"] - P.HORN_LIFT)
    hn = G.csg(hn, add=[spl])
    G.xform(hn, G.frame((px, py, g.horn_z0), (1, 0, 0), (0, 1, 0), (0, 0, 1)))
    A.part(hn, "BUY_horn_pan", 'BUY', "buy_metal", joint="PIV_pan_pinion", mass_g=C["servo_horn_disc"]["mass_g"],
           src="components.json servo_horn_disc (+ the servo output spline)")


# ------------------------------------------------------------------ cables

def _plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def _vplane(P, az):
    """(r, z) in the vertical half-plane through the pan axis at azimuth az (deg) -> world point"""
    ca, sa = math.cos(math.radians(az)), math.sin(math.radians(az))
    ax, ay = P.IF_PAN_XY
    return lambda r, z: (ax + r * ca, ay + r * sa, z)


def _arc(pt, rc, zc, R, a0, a1, n=8):
    """points on a circle of radius R about (rc, zc) in a vertical plane, angles a0 -> a1 (deg, 0 = +r, 90 = +z), ends included"""
    return [pt(rc + R * math.cos(math.radians(a0 + (a1 - a0) * k / n)), zc + R * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


def _note_loop(P, name, pts, i0, i1):
    """v2-A2-02: record the loop segment pts[i0..i1] in the manifest and assert it adds >= PAN_LOOP_ADD over its chord"""
    seg = pts[i0:i1 + 1]
    L, S = _plen(seg), math.dist(seg[0], seg[-1])
    assert L - S >= P.PAN_LOOP_ADD, "%s loop adds %.1f < %.1f" % (name, L - S, P.PAN_LOOP_ADD)
    A.PARTS[name]["loop"] = {"from": [round(c, 2) for c in seg[0]], "to": [round(c, 2) for c in seg[-1]],
                             "path_len": round(L, 1), "straight": round(S, 1), "added": round(L - S, 1),
                             "min_added": P.PAN_LOOP_ADD}


def build_cables(P, g):
    lead = P.CABLE_LEADS
    ux, uz = g.usb
    A.cable("CAB_usb", [(ux, g.usb_y0 - 25, uz), (ux, -g.h - 8, uz), (ux, -g.h - 20, 6), (ux, -g.h - 60, 2)], 2.0, "cable_blk",
            lead_len=lead["CAB_usb"])
    bx, by = P.BUCK_C
    bxe = bx + C["buck_12v_finned"]["body"][0] / 2 + 2
    a = P.ADAPTER
    A.cable("CAB_12v_in", [(a[0] - 1.5, -78, 75), (g.bay_x0 - 1.5, -78, 75), (-4, -58, 76), (-12, -50, 50), (-25, -35, 22), (bxe, by - 4, g.buck_z0 + 8)],
            1.8, "cable_red", lead_len=lead["CAB_12v_in"])
    A.cable("CAB_12v_mg", [(bxe, by - 10, g.buck_z0 + 8), (-30, -45, 30), (-36, -62, 44)], 1.6, "cable_red",
            lead_len=lead["CAB_12v_mg"])
    c = P.CTRL
    A.cable("CAB_12v_ctrl", [(bxe, by + 4, g.buck_z0 + 8), (-30, 12, 7), (60, 12, 7), (c[1] - 6, c[2] - 3, g.ctrl_z + 4)],
            1.6, "cable_red", lead_len=lead["CAB_12v_ctrl"])
    cl = P.UART_CLIPS
    zc = P.FLOOR_T + 3.2
    A.cable("CAB_uart", [(-24, -63, 60), (-24, -45, 25), (cl[0][0] - 10, cl[0][1], zc), (cl[0][0], cl[0][1], zc),
                         (cl[1][0], cl[1][1], zc), (cl[1][0] + 15, cl[1][1], zc), (c[0] - 3, g.ctrl_c[1] - 12, g.ctrl_z + 3)],
            1.2, "cable_blk", lead_len=lead["CAB_uart"])
    jz = P.HUB_JCT_Z
    # bus: controller -X port -> pan servo lead (pocket end notch) -> under the pocket -> v2-A2-02 loop -> BUY_bus_junction
    # (v2-A5-03, the splice with CAB_bus_tilt / CAB_bus_feeder). The loop (az 35, the +X+Y quadrant, clear of the launcher loop
    # at az 235): riser at r 14 to z 60, an arch over to r 9, down to the U at PAN_LOOP_ZC (legs r 9 / r 3), up at r 3 to z 59,
    # then onto the pan axis at BUS_PAN_AX (z 63). v2-A6-02: the static lead ends on the axis; the PIV_pan tail
    # (pan_stage CAB_bus_pan_tail) carries it on to the splice's bottom face, so no static end sits under the orbiting splice.
    px, py = g.pin
    ye = g.sv_y1 + 5
    vb = _vplane(P, 35.0)
    zl = P.PAN_LOOP_ZC
    bus = [(c[0] - 3.5, g.ctrl_c[1] + 8, g.ctrl_z + 4), (40, ye, 18), (px + 4, ye, 24), (px, ye, g.sv_z0 + 3),
           (px - 4, ye, 24), (px - 4, 30, 16)]
    i0 = len(bus) - 1                                      # loop starts at the pocket exit (last fixed point)
    bus += [vb(14.0, 18.0)] + _arc(vb, 11.5, 60.0, 2.5, 0, 180, 6) + _arc(vb, 6.0, zl, 3.0, 0, -180, 8) + [vb(3.0, 59.0), P.BUS_PAN_AX]
    A.cable("CAB_bus_pan", bus, P.BUS_R, "cable_wht", lead_len=lead["CAB_bus_pan"])
    _note_loop(P, "CAB_bus_pan", bus, i0, len(bus) - 1)
    # v2-A2-02 launcher lead, static side (3 phases + encoder JST in one sleeve, BUNDLE_R): from the pan-axis junction with
    # CAB_launcher_bundle (BUS_LB_JCT, az 235 r 4 z 70), a hanging U under the hub gear (az 235: down at LB_LEG_R 6.5, U r 11.25 R 4.75 at LB_LOOP_ZC 46.5 (v2-A6-02: the inner leg clears the PIV_pan bus tail near the axis), riser at r 16 to z 68, 3 under the FST_hub_* heads' swept band at z 74; the bus legs at az 35 stay 6 apart), across the
    # base at z 77 (deck underside 86) into the 12.5 slot between the partition and the MotorGo component face, over encoder
    # JST 1 (0.5 above its top) to the J6/J8 phase pads (0.2 off the PCB).
    vl = _vplane(P, 235.0)
    jx, jzz = P.MG_X0 - P.MG_ENC_JST_STEP[0], P.MG_Z0 - P.MG_ENC_JST_STEP[1]
    qx, qz = P.MG_X0 - P.MG_PHASE_PAD_STEP[0], P.MG_Z0 - P.MG_PHASE_PAD_STEP[1]
    face = g.mg_pcb_y - P.MG_PCB_T                         # component face (-Y)
    ys = 0.5 * (face + P.MG_WALL_Y)                        # slot centre between the face and the partition
    r = P.BUNDLE_R
    # v2-A5-03: the meeting point with the bundle is off the axis and under the splice (BUS_LB_JCT, az 235 r 4, z 70)
    lb = [P.BUS_LB_JCT, vl(P.LB_LEG_R, P.BUS_LB_JCT[2] - 4.0)] + _arc(vl, P.LB_U_RC, P.LB_LOOP_ZC, P.LB_U_R, 180, 360, 10) + [vl(16.0, 68.0)]
    i1 = len(lb) - 1
    lb += [(jx + 10.0, -60.0, 77.0), (jx + 10.0, ys, 77.0), (jx, ys, jzz + 1.2 + 0.5 + r), (jx - 6.5, ys + 0.7, jzz + 1.7 + r),
           (qx, face - r - 0.2, qz)]
    A.cable("CAB_launcher_base", lb, r, "cable_blk", lead_len=lead["CAB_launcher_base"], step="3")
    _note_loop(P, "CAB_launcher_base", lb, 0, i1)
    A.PARTS["CAB_launcher_base"]["ends"] = {"junction": [round(v, 2) for v in lb[0]], "encoder_jst": [jx, round(ys, 2), jzz],
                                            "phase_pads": [qx, round(face, 2), qz], "route_len": round(_plen(lb), 1),
                                            "straight": round(math.dist(lb[0], lb[-1]), 1)}


# ------------------------------------------------------------------ fasteners

def build(P):
    g = Geo(P)
    sh = []
    # adapter (v3-A1): 2 diagonal corners, M3 pan x 10 (FST_motor's spec), counterbored flush in the deck, into the
    # adapter's own holes; tip >= 3 above the battery (distances FST_adapter_0/1). 4 deck fences take the shear.
    cb = P.ADAPTER_CBORE
    for j, i in enumerate(P.ADAPTER_SCREWS):
        x, y = g.adapter_holes[i]
        screw("FST_adapter_%d" % j, (x, y, g.zd1 - cb), DOWN, P.ADAPTER_SCREW_L3, "M3_pan", "BUY_dewalt_adapter", "1",
              cut=[("clamp", dict(clamp=P.DECK_T - cb, head="pan", sink=cb), sh)])
    # pan servo centre screw (allowed metal): through the pinion's O6.5 hole, head on the horn disc, into the spline
    px, py = g.pin
    A.fastener("FST_pinion_ctr", (px, py, g.horn_disc1), DOWN, 6, spec="M3_cap", joint="PIV_pan_pinion",
               host="BUY_horn_pan", step="1a")

    build_shell(P, g, sh)
    build_floor(P, g)
    build_pan_mount(P, g)
    build_pinion(P, g)
    build_purchased(P, g)
    build_cables(P, g)
