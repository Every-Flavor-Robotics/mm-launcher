"""Base (static): shell with deck, removable floor, battery bay (+X slide-out), DeWalt adapter, buck, MotorGo
behind the rear partition (vertical USB-C into the rear niche), servo controller, pan servo + pinion.

Port of v1 attempt 3 (../../blender/build_assembly.py build_base_*) onto the IF_* values, with the review deltas:
  - adapter: 4 x M3 x 20 self-tappers from the deck top into its corner holes, countersunk flush, no nuts (A3-M2)
  - +X window = pack outline + 2, two finger scallops (A3-A3, A3-M2)
  - pan servo spline-up in a clamp pocket under the 36T pinion; horn in a 1.0 recess, centre screw through the pinion
Every screw: features.screw_hole(at, into, ...) and asm.fastener(name, at, into, ...) share at/into (screw()).
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


def screw(name, at, into, length, spec, host, step, joint=None, cut=()):
    """One fastener: the same at/into for every part it passes and for asm.fastener.
    cut = [(kind, kwargs, sink_list)]: features.screw_hole cutters appended to each list."""
    for kind, kw, lst in cut:
        lst += F.screw_hole(at, into, length, kind=kind, name=name, **kw)
    A.fastener(name, at, into, length, spec=spec, joint=joint, host=host, step=step)


# ------------------------------------------------------------------ printed parts

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
    # adapter locating fence on the deck underside (+0.4 all round)
    a = P.ADAPTER
    fo = G.prism("af_o", G.rrect(a[0] - 2.4, a[1] + 2.4, a[2] - 2.4, a[3] + 2.4, 2), g.zd0 - 3.5, g.zd0 + 0.5)
    fi = G.prism("af_i", G.rrect(a[0] - 0.4, a[1] + 0.4, a[2] - 0.4, a[3] + 0.4, 1), g.zd0 - 5, g.zd0 + 1)
    add.append(G.csg(fo, sub=[fi]))
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
    # floor-plate screw columns
    for i, (x, y) in enumerate(P.FLOOR_SCREWS):
        add.append(G.cyl("col%d" % i, (x, y), P.FLOOR_COL_R, g.z0, g.zd0 + 0.5))
    # deck posts for the pan servo mount plate
    for i, (x, y) in enumerate(P.PAN_POSTS):
        add.append(G.cyl("dp%d" % i, (x, y), 4.5, g.S + P.PAN_PLATE_T, g.zd0 + 0.5))
    ob = G.csg(ob, add=add)

    sub = list(cuts_from_screws)
    sub.append(G.cyl("dh", P.IF_PAN_XY, P.IF_DECK_HOLE_R, g.zd0 - 1, g.zd1 + 1))
    # bay void + the +X window = pack outline + 2 (A3-A3), with a 1 mm x 45 deg lead-in
    sub.append(G.box("bay", g.bay_x0, h + 2, g.bay_y0, g.bay_y1, g.z0 - 1, P.BAY_WINDOW_Z1))
    # end the rear wall where the corner arc would leave it thinner than 1.6 (pack corner passes here)
    xr = (h - r) + math.sqrt(r * r - (r - W + 1.8) ** 2)     # 98.4: rear-wall strip >= 1.6 thick up to here
    sub.append(G.box("bay_r", xr, h + 2, -h - 1, g.bay_y0 + 0.01, g.z0 - 1, P.BAY_WINDOW_Z1))
    y0, y1, zt = g.bay_y0, g.bay_y1, P.BAY_WINDOW_Z1
    sub.append(G.loft("bay_ch", [(y0 - 1, g.z0 - 1), (y1 + 1, g.z0 - 1), (y1 + 1, zt + 1), (y0 - 1, zt + 1)],
                      [(y0, g.z0 - 1), (y1, g.z0 - 1), (y1, zt), (y0, zt)], h + 0.01, h - 1.0, 'X'))
    # top finger scallop (the bottom one is in the floor plate); its crown stops at the deck underside
    rs = P.BAY_SCALLOP_D / 2
    sub.append(G.cyl("sc_t", (g.bay_ym, g.zd0 - rs), rs, h - W - 1, h + 1, 'X'))
    # adapter lead through the bay end wall
    sub.append(G.box("bay_wire", g.bay_x0 - 4, g.bay_x0 + 1, -86, -70, 64, 78))
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
        x = 68 + 6 * kk                                     # clear of the floor column, straight wall only
        sub.append(G.prism("fv%d" % kk, G.rrect(x - 1.5, x + 1.5, 30, 70, 1.4), h - W - 1, h + 1, 'Y'))
    # servo controller (v2-A1-11): switch and terminal windows only, framed by a printed bezel on the +X face.
    # The wall stays closed over the rest of the board (no PCB in the side view).
    zw0, zw1 = P.CTRL_WIN_Z
    bw, bp = P.CTRL_BEZEL
    wins = (P.CTRL_WIN_SW, P.CTRL_WIN_TB)
    def win(y0, y1, z0, z1, r, n=6):
        # square corners at the world-bottom edge: printed deck-down that edge is a flat 16 mm bridge, not an arc overhang
        pts = [(y0, z0), (y1, z0)]
        for cy, a in ((y1 - r, 0), (y0 + r, 90)):
            pts += [(cy + r * math.cos(math.radians(a + 90 * i / n)), z1 - r + r * math.sin(math.radians(a + 90 * i / n)))
                    for i in range(n + 1)]
        return pts
    for k, (y0, y1) in enumerate(wins):
        sub.append(G.prism("ctrl_w%d" % k, win(y0, y1, zw0, zw1, 1.5), h - W - 1, h + bp + 1, 'X'))
        # 0.8 x 45 deg lead-in on the bezel face (sides and top; the world-bottom edge stays square for the bridge)
        sub.append(G.loft("ctrl_wc%d" % k, win(y0, y1, zw0, zw1, 1.5), win(y0 - 0.8, y1 + 0.8, zw0, zw1 + 0.8, 2.3),
                          h + bp - 0.6, h + bp + 0.2, 'X'))
    by0, by1 = wins[0][0] - bw, wins[-1][1] + bw
    bz0, bz1 = zw0 - bw, zw1 + bw
    # world-top side insets 1.6 x bp (printed deck-down it is the overhang side: 32 deg from vertical); the
    # world-bottom side only 0.5 x bp, so the 2.5 rail under the windows keeps >= 1.6 at the face
    bez = G.loft("ctrl_bz", G.rrect(by0, by1, bz0, bz1, 3.0), G.rrect(by0 + bp, by1 - bp, bz0 + 0.5 * bp, bz1 - 1.6 * bp, 3.0 - bp),
                 h - 0.5, h + bp, 'X')
    ob = G.csg(ob, add=[bez])
    ob = G.csg(ob, sub=sub)
    # zip-tie anchor on the niche's left wall (vertical tunnel, no bridge)
    blk = G.box("anc", xc - hw - 0.5, xc - hw + 6, -112, -104, ztv + 1, ztv + 11)
    tun = G.box("anc_t", xc - hw + 2, xc - hw + 4, -110, -106, ztv, ztv + 12)
    ob = G.csg(ob, add=[blk])
    ob = G.csg(ob, sub=[tun])
    A.part(ob, "PRT_base_shell", 'PRT', "pla_a", stl="base_shell", print_rot=A.R_FLIP,
           orient="upside down: deck face on the bed, walls up", supports="no", infill=15)


def build_floor(P, g, cuts_from_screws):
    h = g.h
    pl = G.prism("floor", G.rrect(-h, h, -h, h, P.BASE_CORNER_R, 12), 0, P.FLOOR_T, 'Z')
    G.bevel(pl, P.EB)
    add, sub = [], list(cuts_from_screws)
    for i, (x, y) in enumerate(g.buck_holes):
        add.append(G.cyl("bk%d" % i, (x, y), 4.0, g.z0 - 0.5, g.buck_z0))
    # servo controller: drill-to-fit bosses (holes unconfirmed) with centre-punch dimples, +0.4 corner fences
    for i, (x, y) in enumerate(g.ctrl_holes):
        top = (x, y, g.ctrl_z)
        add.append(G.cyl("cb%d" % i, (x, y), P.CTRL_BOSS_D / 2, g.z0 - 0.5, g.ctrl_z))
        sub.append(G.cone("cd%d" % i, (x, y), 0.05, 0.6, g.ctrl_z - 0.6, g.ctrl_z + 0.01, n=12))
        F._log("drill_to_fit_boss", top, DOWN, od=P.CTRL_BOSS_D, height=P.CTRL_BOSS_H)
    c = P.CTRL
    zt = g.ctrl_z + 3
    for sx in (-1, 1):
        for sy in (-1, 1):
            xc = c[1] + 0.4 if sx > 0 else c[0] - 0.4
            yc = c[3] + 0.4 if sy > 0 else c[2] - 0.4
            add.append(G.box("fx%d%d" % (sx, sy), min(xc, xc + sx * 1.6), max(xc, xc + sx * 1.6),
                             min(yc - sy * 5, yc + sy * 1.6), max(yc - sy * 5, yc + sy * 1.6), g.z0 - 0.5, zt))
            add.append(G.box("fy%d%d" % (sx, sy), min(xc - sx * 5, xc + sx * 1.6), max(xc - sx * 5, xc + sx * 1.6),
                             min(yc, yc + sy * 1.6), max(yc, yc + sy * 1.6), g.z0 - 0.5, zt))
    F._log("pcb_pocket", (g.ctrl_c[0], g.ctrl_c[1], g.ctrl_z), DOWN, w=c[1] - c[0], h=c[3] - c[2], depth=3, clear=0.4)
    # UART lead clips: the lead presses into the slot (dab of hot glue)
    for i, (x, y) in enumerate(P.UART_CLIPS):
        add.append(G.box("uc%d" % i, x - 4, x + 4, y - 4, y + 4, g.z0 - 0.5, g.z0 + 7.6))
        sub.append(G.box("ucs%d" % i, x - 5, x + 5, y - 1.6, y + 1.6, g.z0 + 1.0, g.z0 + 5.5))
    # rubber-foot recesses and the bottom finger scallop under the battery opening
    for sx in (-1, 1):
        for sy in (-1, 1):
            sub.append(G.cyl("ft%d%d" % (sx, sy), (sx * 100, sy * 100), 7.0, -1, 1.0))
    sub.append(G.cyl("sc_b", (h, g.bay_ym), P.BAY_SCALLOP_D / 2, -1, P.FLOOR_T + 1))
    ob = G.csg(pl, add=add)
    ob = G.csg(ob, sub=sub)
    A.part(ob, "PRT_base_floor", 'PRT', "pla_a", stl="base_floor", print_rot=A.R_ID, orient="flat, bosses up",
           supports="no", infill=15)


def build_partition(P, g, cuts_from_screws):
    x0, x1 = P.MG_PART_X
    yw = P.MG_WALL_Y
    pl = G.box("part", x0, x1, yw - 3, yw, g.z0, g.zd0 - 0.5)
    G.bevel(pl, P.EB)
    add = [G.box("pf%d" % i, xf - 5, xf + 5, yw - 3, yw + 5, g.z0, g.z0 + 8) for i, xf in enumerate((x0 + 8, x1 - 8))]
    add += [G.cyl("so%d" % i, (hx, hz), 3.0, yw - 0.5, yw + P.MG_STANDOFF, 'Y') for i, (hx, hz) in enumerate(g.mg_holes)]
    ux, uz = g.usb
    sub = list(cuts_from_screws)
    sub.append(G.prism("usb", G.rrect(ux - 4.5, ux + 4.5, uz - 7.25, uz + 7.25, 3), yw - 4, yw + 1, 'Y'))
    ob = G.csg(pl, add=add)
    ob = G.csg(ob, sub=sub)
    A.part(ob, "PRT_base_partition", 'PRT', "pla_a", stl="base_partition", print_rot=A.R_NY_DOWN,
           orient="rear face on the bed, standoffs up", supports="no", infill=25)


def build_pan_mount(P, g, cuts_plate, cuts_clamp):
    """Clamp pocket hung from the four deck posts: plate (servo top bears on its underside) + walls + clamp."""
    px, py = g.pin
    S, T = g.S, P.PAN_PLATE_T
    c, wall = P.SERVO_POCKET_CLR, 2.4
    hw = g.sv_W / 2
    x0p, x1p, y0p, y1p = P.PAN_PLATE
    plate = G.prism("pm", G.rrect(x0p, x1p, y0p, y1p, P.CR), S, S + T, 'Z')
    G.bevel(plate, P.EB)
    wz0 = g.sv_z0 + 0.3                                   # walls stop 0.3 short: the clamp bears on the servo
    walls = G.prism("pmw", G.rrect(px - hw - c - wall, px + hw + c + wall, g.sv_y0 - c - wall, g.sv_y1 + c + wall, 2),
                    wz0, S + 0.01, 'Z')
    vb = hw + c + wall + 1.6
    bosses = [G.cyl("pmb%d" % i, (bx, by), 3.6, wz0, S + 0.01) for i, (bx, by) in enumerate(clamp_pts(P, g))]
    inner = G.prism("pmi", G.rrect(px - hw - c, px + hw + c, g.sv_y0 - c, g.sv_y1 + c, 1), wz0 - 1, S + 1, 'Z')
    hole = G.cyl("pmh", (px, py), P.PAN_PLATE_HOLE_R, S - 1, S + T + 1)
    lead = G.box("pml", px - 3, px + 3, g.sv_y1 - 1, g.sv_y1 + c + wall + 1, wz0 - 1, wz0 + 9)   # servo lead exit
    walls = G.csg(walls, add=bosses)
    walls = G.csg(walls, sub=[inner, lead])               # pocket tube first, so the plate hole never slivers it
    plate = G.csg(plate, sub=[hole])
    ob = G.csg(plate, add=[walls])
    ob = G.csg(ob, sub=cuts_plate)
    A.part(ob, "PRT_pan_servo_mount", 'PRT', "pla_a", stl="pan_servo_mount", print_rot=A.R_FLIP,
           orient="plate top on the bed, pocket walls up", supports="no", infill=30)
    # clamp plate under the servo (idler boss passes through)
    cp = clamp_pts(P, g)
    cl = G.prism("pc", G.hull_circles([(p, 5.0) for p in cp] + [((px - hw - c - wall, g.sv_y0 - c - wall), 1.0),
                                                                  ((px + hw + c + wall, g.sv_y1 + c + wall), 1.0),
                                                                  ((px - hw - c - wall, g.sv_y1 + c + wall), 1.0),
                                                                  ((px + hw + c + wall, g.sv_y0 - c - wall), 1.0)]),
                 g.sv_z0 - 4, g.sv_z0, 'Z')
    G.bevel(cl, 0.8)
    idl = G.cyl("pci", (px, py), 4.5, g.sv_z0 - 5, g.sv_z0 + 1)
    cl = G.csg(cl, sub=[idl] + cuts_clamp)
    A.part(cl, "PRT_pan_servo_clamp", 'PRT', "pla_a", stl="pan_servo_clamp", print_rot=A.R_ID, orient="flat",
           supports="no", infill=30)


def clamp_pts(P, g):
    px, py = g.pin
    vb = g.sv_W / 2 + P.SERVO_POCKET_CLR + 2.4 + 1.6
    return [(px + vb, g.sv_y1 - 5), (px - vb, g.sv_y0 + 5)]


def build_pinion(P, g):
    px, py = g.pin
    z0, z1 = P.IF_GEAR_Z
    gear = G.prism("pp", G.gear_poly(P.IF_GEAR_M, P.IF_GEAR_N, c=(px, py), backlash=P.GEAR_BACKLASH,
                                      phase=math.radians(180.0 / P.IF_GEAR_N)), z0, z1, 'Z')
    hub = G.cyl("pph", (px, py), P.PINION_HUB_R, g.pin_z0, z0 + 0.01)
    hd = C["servo_horn_disc"]
    cuts = F.horn_recess((px, py, g.pin_z0), UP, disc_d=hd["disc"]["d"], depth=P.HORN_RECESS,
                         bolt_circle_d=hd["holes"]["bolt_circle_d"], n_holes=hd["holes"]["n"], centre_hole_d=6.5, name="pph")
    ob = G.csg(gear, add=[hub])
    ob = G.csg(ob, sub=cuts)
    A.part(ob, "PRT_pan_pinion", 'PRT', "pla_b", joint="PIV_pan_pinion", stl="pan_pinion", print_rot=A.R_FLIP,
           orient="gear top on the bed, horn recess up", supports="no", infill=40)


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
    sh, fl, pa, pm, pc, pn = [], [], [], [], [], []
    # adapter: M3 x 20 self-tap from the deck top, countersunk flush; tip 3+ above the battery face, no nuts (A3-M2)
    for i, (x, y) in enumerate(g.adapter_holes):
        screw("FST_adapter_%d" % i, (x, y, g.zd1), DOWN, P.ADAPTER_SCREW_L, "M3_csk", "BUY_dewalt_adapter", "1",
              cut=[("clamp", dict(clamp=P.DECK_T, head="csk"), sh)])
    # floor plate into the shell columns, countersunk from below
    for i, (x, y) in enumerate(P.FLOOR_SCREWS):
        screw("FST_floor_%d" % i, (x, y, 0.0), UP, 12, "M3_csk", "PRT_base_shell", "3",
              cut=[("clamp", dict(clamp=P.FLOOR_T, head="csk"), sh), ("clamp", dict(clamp=P.FLOOR_T, head="csk"), fl)])
    # partition onto the floor plate, from below
    x0, x1 = P.MG_PART_X
    for i, xf in enumerate((x0 + 8, x1 - 8)):
        at = (xf, P.MG_WALL_Y + 1, 0.0)
        screw("FST_partition_%d" % i, at, UP, 10, "M3_csk", "PRT_base_partition", "2a",
              cut=[("clamp", dict(clamp=P.FLOOR_T, head="csk"), fl),
                   ("clamp", dict(clamp=P.FLOOR_T, head="csk", print_up=(0, 1, 0)), pa)])
    # MotorGo onto the partition standoffs (cap heads on the PCB back face)
    A.FASTENER_SPECS.setdefault(P.MG_SCREW, P.MG_SCREW_SPEC)    # M2.5 is not in cadlib's table
    for i, (hx, hz) in enumerate(g.mg_holes):
        screw("FST_mg_%d" % i, (hx, g.mg_pcb_y, hz), (0, -1, 0), 10, P.MG_SCREW, "PRT_base_partition", "2a")
        pa.append(G.cyl("mgp%d" % i, (hx, hz), P.MG_PILOT_D / 2, g.mg_pcb_y - 11.0, g.mg_pcb_y - P.MG_PCB_T + 0.6, 'Y', n=16))
    # buck flange onto the floor bosses
    for i, (x, y) in enumerate(g.buck_holes):
        screw("FST_buck_%d" % i, (x, y, g.buck_z0 + P.BUCK_FLANGE_T), DOWN, 8, "M3_pan", "PRT_base_floor", "2b",
              cut=[("clamp", dict(clamp=P.BUCK_FLANGE_T, head="pan"), fl)])
    # pan servo mount plate onto the deck posts, clamp onto the pocket bosses
    for i, (x, y) in enumerate(P.PAN_POSTS):
        screw("FST_panservo_%d" % i, (x, y, g.S), UP, 12, "M3_cap", "PRT_base_shell", "1c",
              cut=[("clamp", dict(clamp=P.PAN_PLATE_T), sh), ("clamp", dict(clamp=P.PAN_PLATE_T), pm)])
    for i, (x, y) in enumerate(clamp_pts(P, g)):
        screw("FST_panclamp_%d" % i, (x, y, g.sv_z0 - 4), UP, 12, "M3_cap", "PRT_pan_servo_mount", "1b",
              cut=[("clamp", dict(clamp=4.0), pm), ("clamp", dict(clamp=4.0), pc)])
    # horn to pinion (M2 through 4 of the 8 horn holes; pinion has pilot dimples, drill with the horn as template),
    # centre screw through the pinion's Ø6.5 hole into the spline
    px, py = g.pin
    bc = C["servo_horn_disc"]["holes"]["bolt_circle_d"] / 2
    for i in range(4):
        ang = math.radians(90 * i)
        A.fastener("FST_pinion_%d" % i, (px + bc * math.cos(ang), py + bc * math.sin(ang), g.horn_disc0), UP, 8,
                   spec="M2_pan", joint="PIV_pan_pinion", host="PRT_pan_pinion", step="1a")
    A.fastener("FST_pinion_ctr", (px, py, g.horn_disc1), DOWN, 6, spec="M3_cap", joint="PIV_pan_pinion",
               host="BUY_horn_pan", step="1b")

    build_shell(P, g, sh)
    build_floor(P, g, fl)
    build_partition(P, g, pa)
    build_pan_mount(P, g, pm, pc)
    build_pinion(P, g)
    build_purchased(P, g)
    build_cables(P, g)
