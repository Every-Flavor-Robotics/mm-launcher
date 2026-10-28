"""Launcher 2D geometry (launcher frame p = world Y, q = world Z - IF_TILT_Z, at tilt 0), ported from v1 attempt-3
../blender/build_assembly.py (gap_at, bp_band, chute_poly, wheel_cavity_poly, nip_poly, muzzle_poly, guard_profile,
jp_union, the nip frame, pick_screws). Pure Python (no bpy), so the numbers can be checked outside Blender:

    python3 -c "import sys; sys.path[:0]=['blender','blender/parts']; import launcher_geom as L; L.report()"

Every value comes from params.py; v2 deltas live there (G_IN 13, NIP_SET, STUD_L, HINGE_AXLE_L, LEAF_*).
"""
import math


def lin(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


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


def circle(c, r, n):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def hull2d(pts):
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in pts))

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


def spread_pick(cands, n, seeds=()):
    picked, out, pool = list(seeds), [], list(cands)
    while len(out) < n and pool:
        best = pool[0] if not picked else max(pool, key=lambda c: min(math.hypot(c[0] - q[0], c[1] - q[1]) for q in picked))
        out.append(best)
        picked.append(best)
        pool.remove(best)
    return out


def sector(r0, r1, a0, a1, n=12, c=(0.0, 0.0)):
    """annular sector, angles in deg from +p toward +q"""
    o = [(c[0] + r1 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r1 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    i_ = [(c[0] + r0 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), c[1] + r0 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return o + i_


def _isect(Pp, a_deg, Q, b_deg):
    d1 = (math.cos(math.radians(a_deg)), math.sin(math.radians(a_deg)))
    d2 = (math.cos(math.radians(b_deg)), math.sin(math.radians(b_deg)))
    den = d1[0] * (-d2[1]) - d1[1] * (-d2[0])
    rx, ry = Q[0] - Pp[0], Q[1] - Pp[1]
    t = (rx * (-d2[1]) - ry * (-d2[0])) / den
    return (Pp[0] + t * d1[0], Pp[1] + t * d1[1])


class Geo:
    """All launcher-frame profiles and derived points for one params module P."""

    def __init__(self, P):
        self.P = P
        g = self
        g.WC = (P.W_P, P.W_Q)
        sn = math.hypot(P.W_P, P.W_Q)
        g.S = (P.W_P / sn, P.W_Q / sn)              # tilt axis -> wheel axis (nacelle spine)
        g.N = (-g.S[1], g.S[0])
        g.OUTLET_R = P.IF_OUTLET_D / 2
        g.HINGE = P.HINGE
        g.EPS_OPEN, g.EPS_CLOSE = math.radians(P.HOOD_LO), math.radians(P.HOOD_HI)
        g.EPS_BAY = g.EPS_CLOSE + math.radians(P.BAY_OVER)     # v2-A1-01: bay + tongue envelope run past the stop
        g.FLOOR_Q = P.W_Q - P.WHEEL_R - P.HOOD_GAP
        g.BAY_EPS = lin(g.EPS_OPEN, g.EPS_BAY, 25)
        g.BAY_POLYS = [g.bp_band(e, 0.55) for e in g.BAY_EPS] + [g.hood_lug(e, 0.55) for e in g.BAY_EPS]   # 0.05 over CLR for facets
        g.BAY_BOSS = circle(g.HINGE, P.HINGE_BOSS_R + 0.55, 48)   # 48-gon: the 24-gon apothem left 0.46 to the boss
        g.JACK_PT = g.pw(P.WHEEL_R + P.HOOD_GAP + P.HOOD_T, P.JACK_PSI)
        jv = (g.JACK_PT[0] - g.HINGE[0], g.JACK_PT[1] - g.HINGE[1])
        jl = math.hypot(*jv)
        g.JACK_DIR = (-jv[1] / jl, jv[0] / jl)      # closing direction at the stud
        # feed chute
        orr = g.OUTLET_R + P.COL_MARGIN + 0.5
        g.E_FRONT = (orr, -math.sqrt(P.DRUM_R ** 2 - orr ** 2))
        g.FIN_TAN = tangent_point(g.E_FRONT, g.WC, P.FIN_R1, -1)
        g.PSI_TAN = g.psi_of(g.FIN_TAN)
        g.P1_REAR = g.pt(P.DRUM_R, P.FAN_A0)
        g.TONGUE_PSI0, g.TONGUE_PSI1 = P.PSI_TOP + P.TONGUE_DPSI[0], P.PSI_TOP + P.TONGUE_DPSI[1]
        g.TONGUE_IN = g._tongue_in()
        g.J_REAR = g.pw(g.r_tongue(g.TONGUE_PSI1), g.TONGUE_PSI1)
        g.P1_IN = g.pt(P.DRUM_R - 2.0, P.FAN_A0)
        g.K_REAR = _isect(g.J_REAR, 180.0 - P.REAR_WALL_ANG, g.P1_IN, -104.0)
        g.A_CH = 45.0 + math.degrees(math.asin((g.OUTLET_R + P.COL_MARGIN) / P.DRUM_R))
        g.FIN_PSI_END = g.PSI_TAN + math.degrees(math.atan(math.sqrt((P.WC_R + 1.6) ** 2 - P.FIN_R1 ** 2) / P.FIN_R1)) + 1.0
        g.FLOOR_FIX = g.FLOOR_Q - (P.HOOD_GAP_MAX - P.HOOD_GAP) - 0.6
        g.PROFILE = g.guard_profile()
        g.CAVITIES = [g.chute_poly(), g.wheel_cavity_poly(), g.nip_poly(), g.muzzle_poly()] + g.BAY_POLYS + [g.BAY_BOSS]
        g.CAVITIES.append(g.nip_stop_poly(0.0))
        tp = tangent_point(g.pt(P.DRUM_R, 0.0), g.WC, P.WC_R + P.GUARD_WALL, 1)
        d = (tp[0], tp[1] - P.DRUM_R)
        L = math.hypot(*d)
        g.TOP_DIR = (d[0] / L, d[1] / L)
        g.TOP_N = (-g.TOP_DIR[1], g.TOP_DIR[0])
        g.JP_DIAG = (-math.sqrt(0.5), -math.sqrt(0.5))
        g.JP_REGION = g.jp_union(P.JP_R, 0.0)
        # compliant nip frame: x = world x, U = outward along the stud, V = along the guard toward the hinge
        g.NIP_U = (-g.JACK_DIR[0], -g.JACK_DIR[1])
        g.NIP_V = (-g.JACK_DIR[1], g.JACK_DIR[0])
        g.JACK_SURF = g._surface_along(g.JACK_PT, g.NIP_U, g.PROFILE)
        g.NIP_E = vadd(g.JACK_SURF, g.NIP_U, P.SEAT_H)
        g.NIP_XC = (P.X_BODY_OUT, P.X_COVER_IN)
        g.LEAF_X = (g.NIP_XC[0] + P.NIP_END_T + P.NIP_SLIT, g.NIP_XC[1] - P.NIP_END_T - P.NIP_SLIT)
        g.LEAF_U0 = P.TW_T - P.LEAF_PRE + P.LEAF_PAD_H          # free-state strip underside
        g.SHELL_U0 = g.LEAF_U0 + P.LEAF_T + P.LEAF_PRE + P.LEAF_TRAVEL
        g.SHELL_UO = g.SHELL_U0 + P.NIP_SHELL_T
        g.JP_SCREWS, g.COVER_SCREWS = g.pick_screws()
        g.NAC_SCREWS = [vadd(g.WC, g.S, -33.0), vadd(g.WC, g.S, 22.0)]
        rot = math.degrees(math.atan2(-g.S[1], -g.S[0]))
        g.MOTOR_SCREWS = [vadd(g.WC, (math.cos(math.radians(rot + 45 + 90 * k)), math.sin(math.radians(rot + 45 + 90 * k))), 12.5)
                          for k in range(4)]
        g.ENC_SCREWS = [vadd(g.WC, g.N, 21.5), vadd(g.WC, g.N, -21.5)]
        g.PCB_BACK_X = -P.MOTOR_L + P.REAR_SHAFT_RECESS - P.MAGNET_T - P.ENC_GAP - P.PLINK_IC_TOP
        g.NAC_X0 = g.PCB_BACK_X

    # ---------------------------------------------------------------- frames
    def pw(self, r, psi):
        return self.P.pw(r, psi)

    @staticmethod
    def pt(r, a):
        """(p, q) at radius r about the tilt axis, a deg from launcher-up toward the muzzle"""
        a = math.radians(a)
        return (r * math.sin(a), r * math.cos(a))

    def psi_of(self, p):
        return math.degrees(math.atan2(-(p[0] - self.P.W_P), -(p[1] - self.P.W_Q)))

    def rot2(self, p, ang, c=(0.0, 0.0)):
        return self.P.rot2(p, ang, c)

    # ---------------------------------------------------------------- backplate
    def bp_band(self, eps=0.0, grow=0.0, n=56):
        """backplate band rotated by eps (rad, + closes the gap) about the hinge"""
        P = self.P
        a0 = P.BP_PSI0 - math.degrees(grow / (P.WHEEL_R + P.HOOD_GAP))
        a1 = P.PSI_TOP + math.degrees(grow / (P.WHEEL_R + P.G_IN))
        def gr(ps, r):
            """radial grow that gives a normal offset of `grow` on the funnel slope (A1 bay: 0.46 normal there)"""
            k = (P.gap_at(ps + 0.05) - P.gap_at(ps - 0.05)) / 0.1 / (r * math.pi / 180.0)
            return grow * math.sqrt(1.0 + k * k)
        inner = [self.pw(P.WHEEL_R + P.gap_at(ps) - gr(ps, P.WHEEL_R + P.gap_at(ps)), ps) for ps in lin(a1, a0, n)]
        outer = [self.pw(P.WHEEL_R + P.gap_at(ps) + P.HOOD_T + gr(ps, P.WHEEL_R + P.gap_at(ps) + P.HOOD_T), ps)
                 for ps in lin(a0, a1, n)]
        return [self.rot2(p, eps, self.HINGE) for p in inner + outer]

    def hood_lug(self, eps=0.0, grow=0.0, n=8):
        """v2-A1-01 stop lug on the hood's free (front) end: psi BP_PSI0 .. +HOOD_LUG[0], from 1 mm inside the back face to
        HOOD_LUG[1] past it, so the end face lands on PRT_nip_stop over a 3 mm tall land below the muzzle floor"""
        P = self.P
        r0 = P.WHEEL_R + P.HOOD_GAP + P.HOOD_T - 1.0
        r1 = P.WHEEL_R + P.HOOD_GAP + P.HOOD_T + P.HOOD_LUG[1] + grow
        a0 = P.BP_PSI0 - math.degrees(grow / r1)
        a1 = P.BP_PSI0 + P.HOOD_LUG[0] + math.degrees(grow / r0)
        pts = [self.pw(r1, a) for a in lin(a0, a1, n)] + [self.pw(r0, a) for a in lin(a1, a0, n)]
        return [self.rot2(p, eps, self.HINGE) for p in pts]

    def nip_stop_frame(self):
        """hood end face at the min-gap stop: (origin on the face at the muzzle floor, f up the face, n away from the hood)"""
        P = self.P
        ai = self.rot2(self.pw(P.WHEEL_R + P.HOOD_GAP, P.BP_PSI0), self.EPS_CLOSE, self.HINGE)
        ao = self.rot2(self.pw(P.WHEEL_R + P.HOOD_GAP + P.HOOD_T + P.HOOD_LUG[1], P.BP_PSI0), self.EPS_CLOSE, self.HINGE)
        L = math.hypot(ai[0] - ao[0], ai[1] - ao[1])
        f = ((ai[0] - ao[0]) / L, (ai[1] - ao[1]) / L)
        n = (f[1], -f[0])
        if n[0] < 0:
            n = (-n[0], -n[1])
        t = (self.FLOOR_FIX - ao[1]) / f[1]
        return (ao[0] + t * f[0], ao[1] + t * f[1]), f, n

    def nip_stop_poly(self, grow=0.0):
        """PRT_nip_stop section: face on the hood end-face plane at the stop, top on the muzzle floor line"""
        P = self.P
        o, f, n = self.nip_stop_frame()
        T, H = P.NIP_STOP_T + grow, P.NIP_STOP_H + grow
        a = vadd(o, f, -H)
        b = vadd(a, n, T)
        c = (b[0] + (self.FLOOR_FIX - b[1]) / f[1] * f[0], self.FLOOR_FIX + grow)
        return [vadd(o, f, grow), a, b, c]

    def nip_stop_pocket(self, back=3.0):
        """pad section plus a floor cut 3 mm behind the face down to the pad bottom: the hood lug's swept envelope then
        meets a flat floor at an obtuse angle instead of leaving a 0.2 mm sliver against the pad face"""
        o, a, b, c = self.nip_stop_poly(0.0)
        _, f, n = self.nip_stop_frame()
        a2 = (a[0] - back, a[1])
        o2 = (o[0] - back, self.FLOOR_FIX + 0.5)
        return [o2, a2, a, b, c, o]

    # ---------------------------------------------------------------- chute
    def _tongue_in(self):
        """bay grow (0.5) + the deepest intrusion of the swinging plate surface under the tongue (envelope over every
        hinge angle, compared at equal psi) + 0.3"""
        P = self.P
        worst = 0.0
        src = [(ps, P.WHEEL_R + P.gap_at(ps)) for ps in lin(80.0, P.PSI_TOP, 160)]
        for e in lin(self.EPS_OPEN, self.EPS_BAY, 41):
            moved = []
            for ps, r0 in src:
                q = self.rot2(self.pw(r0, ps), e, self.HINGE)
                moved.append((self.psi_of(q), math.hypot(q[0] - P.W_P, q[1] - P.W_Q)))
            for k in range(len(moved) - 1):
                (pa, ra), (pb, rb) = moved[k], moved[k + 1]
                if self.TONGUE_PSI0 - 1.0 <= pa <= P.PSI_TOP and pb != pa:
                    worst = max(worst, P.WHEEL_R + P.gap_at(pa) - ra)
        return 0.5 + worst + 0.3

    def r_tongue(self, ps):
        P = self.P
        return P.WHEEL_R + P.gap_at(ps) - self.TONGUE_IN - P.TONGUE_T

    def chute_poly(self):
        P = self.P
        pts = [self.pt(30.0, a) for a in lin(P.FAN_A1, P.FAN_A0, 14)]
        pts += [self.P1_REAR, self.P1_IN, self.K_REAR]
        pts += [self.pw(self.r_tongue(ps), ps) for ps in lin(self.TONGUE_PSI1, self.TONGUE_PSI0, 8)]
        f0 = self.pw(self.r_tongue(self.TONGUE_PSI0), self.TONGUE_PSI0)
        f1 = self.pw(self.r_tongue(self.TONGUE_PSI0 + 0.5), self.TONGUE_PSI0 + 0.5)
        tx, ty = f1[0] - f0[0], f1[1] - f0[1]
        tl = math.hypot(tx, ty)
        nx, ny = ty / tl, -tx / tl
        if (f0[0] + nx - P.W_P) ** 2 + (f0[1] + ny - P.W_Q) ** 2 < (f0[0] - P.W_P) ** 2 + (f0[1] - P.W_Q) ** 2:
            nx, ny = -nx, -ny
        k = P.TONGUE_T + self.TONGUE_IN + 0.8
        # v1 had a vertex at pw(WHEEL_R + 8, 104): inside the G_IN 21 funnel, but with G_IN 13 it left a ledge 2 mm
        # off the plate where every drop stalled (tilt 15..46); run the tip step straight to the fin lip instead
        pts += [(f0[0] + nx * k, f0[1] + ny * k)]
        pts += [self.pw(P.FIN_R1, ps) for ps in lin(P.LIP_PSI, self.PSI_TAN, 8)]
        pts += [self.E_FRONT, self.pt(P.DRUM_R, P.FAN_A1)]
        return pts

    def wheel_cavity_poly(self):
        P = self.P
        return [self.pw(P.FIN_R0 if P.LIP_PSI - 0.5 <= ps <= self.FIN_PSI_END else P.WC_R, ps)
                for ps in (-180 + 2 * i for i in range(180))]

    def nip_poly(self):
        P = self.P
        return [self.WC] + [self.pw(P.WHEEL_R + P.gap_at(ps) + 0.6, ps) for ps in lin(-8.0, self.TONGUE_PSI0 - 2.0, 60)]

    def muzzle_poly(self):
        P = self.P
        f, r, mf, rp = self.FLOOR_FIX, P.MUZZLE_ROOF, P.MUZZLE_FRONT, P.ROOF_P0
        fl = P.MUZZLE_FLARE
        return [(P.W_P, f), (mf - fl, f), (mf + 1, f - fl - 1), (mf + 1, r + fl + 1), (mf - fl, r), (rp, r), (rp - 12, r + 12),
                (P.W_P, r + 12)]

    def guard_profile(self, grow=0.0):
        P = self.P
        g = grow
        circs = [((0, 0), g)]
        for i in range(72):
            a = self.A_CH + (360.0 - self.A_CH) * i / 71
            circs.append((self.pt(P.DRUM_R, a), g))
        circs += [(self.K_REAR, 3.5 + g), (self.J_REAR, 3.5 + g), (self.WC, P.WC_R + P.GUARD_WALL + g),
                  (self.HINGE, P.HINGE_BOSS_R + 0.5 + 3.5 + g)]
        for poly in self.BAY_POLYS:
            circs += [(p, 3.5 + g) for p in poly[::3]]
        mf, cr = P.MUZZLE_FRONT, P.CR
        circs += [((mf - cr, P.MUZZLE_ROOF + 7 - cr), cr + g), ((mf - cr, self.FLOOR_FIX - 7 + cr), cr + g)]
        return hull_circles(circs, 64)

    # ---------------------------------------------------------------- journal plate / cover split
    def jp_union(self, r, off):
        R = r + off
        a = off * math.sqrt(0.5)
        b = math.sqrt(2.0) * r
        c = a * a + (r + a) ** 2 - R * R
        t = (-b + math.sqrt(b * b - 4 * c)) / 2
        s0 = (a - math.sqrt(0.5) * t, -r - a - math.sqrt(0.5) * t)
        a_start = math.atan2(s0[1], s0[0])
        a_end = math.atan2(-self.TOP_N[0], self.TOP_N[1])
        arc = [(R * math.cos(a_start + (a_end - a_start) * i / 64), R * math.sin(a_start + (a_end - a_start) * i / 64)) for i in range(65)]
        e = arc[-1]
        far_top = (e[0] + 120 * self.TOP_N[0], e[1] + 120 * self.TOP_N[1])
        far_bot = (s0[0] + 160 * self.JP_DIAG[0], s0[1] + 160 * self.JP_DIAG[1])
        return [far_bot] + arc + [far_top, (-300.0, 300.0), (-300.0, -300.0)]

    # ---------------------------------------------------------------- nip
    def _surface_along(self, p, d, poly, step=0.25):
        q = p
        for _ in range(800):
            nq = vadd(q, d, step)
            if not pip(nq, poly):
                return q
            q = nq
        return q

    def nip_pq(self, u, v):
        E, U, V = self.NIP_E, self.NIP_U, self.NIP_V
        return (E[0] + u * U[0] + v * V[0], E[1] + u * U[1] + v * V[1])

    def stud_line(self, eps):
        return self.rot2(self.JACK_PT, eps, self.HINGE), self.rot2(self.NIP_U, eps)

    def stud_d(self, eps):
        """distance along the stud from the plate's back face to the seat plane"""
        p0, d = self.stud_line(eps)
        return (self.NIP_E[0] - p0[0]) * d[0] + (self.NIP_E[1] - p0[1]) * d[1]

    def leaf_numbers(self):
        P = self.P
        E, b, L, t = 3500.0, self.LEAF_X[1] - self.LEAF_X[0], P.LEAF_L, P.LEAF_T
        k = 3 * E * (b * t ** 3 / 12.0) / L ** 3
        sig = lambda F: 6 * F * L / (b * t * t)
        F0, F1 = k * P.LEAF_PRE, k * (P.LEAF_PRE + P.LEAF_TRAVEL)
        out = {"width_mm": round(b, 2), "length_mm": L, "thickness_mm": t, "rate_N_per_mm": round(k, 2),
               "preload_N": round(F0, 1), "root_stress_preload_MPa": round(sig(F0), 1),
               "force_at_stop_N": round(F1, 1), "root_stress_at_stop_MPa": round(sig(F1), 1)}
        # v2-A4-02: operating stress at the lift each candy needs over the whole entry arc (gap_arc), not at BDC only:
        # the fraction of LEAF_TRAVEL that opens the arc minimum to candy + tape, at each thumbwheel setting
        op = {}
        for nm, gap in (("min_stop", P.HOOD_GAP_MIN), ("home", P.HOOD_GAP), ("max_stop", P.NIP_SET[1])):
            e0 = P.solve_eps(gap)
            for cn, mm in (("nominal", P.MM_T_NOM), ("thickest", P.MM_T[1])):
                f = self.lift_fraction(e0, mm + P.TAPE_T)
                op["%s_%s" % (nm, cn)] = {"lift_frac": round(f, 2), "stress_MPa": round(sig(k * (P.LEAF_PRE + f * P.LEAF_TRAVEL)), 1)}
        out["operating"] = op
        return out

    def lift_fraction(self, e0, need):
        """fraction of LEAF_TRAVEL (0..1, >1 = never) at which the entry-arc minimum gap_arc reaches `need` from setting e0"""
        P = self.P
        lev = P.LEAF_TRAVEL / P.jack_r()
        if P.gap_arc(e0) >= need:
            return 0.0
        if P.gap_arc(e0 - lev) < need:
            return 9.99
        lo, hi = 0.0, 1.0
        for _ in range(40):
            m = 0.5 * (lo + hi)
            if P.gap_arc(e0 - m * lev) >= need:
                hi = m
            else:
                lo = m
        return hi

    def arc_minima(self):
        """entry-arc minimum (gap_arc) at rest and at full leaf lift, at each thumbwheel setting"""
        P = self.P
        lev = P.LEAF_TRAVEL / P.jack_r()
        return {nm: (round(P.gap_arc(P.solve_eps(gap)), 3), round(P.gap_arc(P.solve_eps(gap) - lev), 3))
                for nm, gap in (("min_stop", P.HOOD_GAP_MIN), ("home", P.HOOD_GAP), ("max_stop", P.NIP_SET[1]))}

    # ---------------------------------------------------------------- screws
    def pick_screws(self):
        """journal-plate and cover screw positions: solid body behind them, clear of every cavity. Cover screws sit
        in front of the right post at tilt 45 (world y = 0.707 (p - q) >= 40) so the cover comes off there."""
        P = self.P
        a, hw = P.IF_STOP_JP_A, P.IF_STOP_JP_HW
        r0, r1 = P.IF_STOP_R
        lugpoly = sector(r0 - 2, r1 + 2, a - hw - 6, a + hw + 6, 8)
        jack = (self.JACK_PT, vadd(self.JACK_SURF, self.NIP_U, 6))
        prof = self.PROFILE
        cavs = []
        for cav in self.CAVITIES:
            xs, ys = [p[0] for p in cav], [p[1] for p in cav]
            cavs.append((cav, min(xs) - 4, max(xs) + 4, min(ys) - 4, max(ys) + 4))
        xs, ys = [p[0] for p in prof], [p[1] for p in prof]
        jp_c, cv_c = [], []
        for i in range(int(min(xs)), int(max(xs)) + 1):
            for j in range(int(min(ys)), int(max(ys)) + 1):
                c = (float(i), float(j))
                if not pip(c, prof) or poly_dist(c, prof) < 5.2:
                    continue
                bad = False
                for cav, x0, x1, y0, y1 in cavs:
                    if x0 <= c[0] <= x1 and y0 <= c[1] <= y1 and (pip(c, cav) or poly_dist(c, cav) < 3.4):
                        bad = True
                        break
                if bad or seg_dist(c, *jack) < 6.0 or math.hypot(c[0] - self.HINGE[0], c[1] - self.HINGE[1]) < 8:
                    continue
                in_jp = pip(c, self.JP_REGION)
                dj = poly_dist(c, self.JP_REGION)
                if in_jp and dj > 5.2 and math.hypot(*c) > P.NAC_COLLAR_R + 3.6 and not pip(c, lugpoly):
                    jp_c.append(c)
                elif (not in_jp) and dj > 5.5 and 0.7071 * (c[0] - c[1]) >= 40.0:
                    cv_c.append(c)
        return spread_pick(jp_c, 3, seeds=[(0.0, 0.0)]), spread_pick(cv_c, 4, seeds=[(0.0, 0.0)])


def report():
    import params as P
    g = Geo(P)
    print("HINGE", [round(v, 2) for v in g.HINGE], "hood deg", round(P.HOOD_LO, 3), round(P.HOOD_HI, 3))
    print("hood LO = static max %.3f (gap %.1f) - leaf lift %.3f deg (%.1f at the stud, arm %.2f) = %.3f, gap %.2f; "
          "HI gap %.1f" % (P.HOOD_STATIC_LO, P.NIP_SET[1], P.HOOD_LEAF_LIFT, P.LEAF_TRAVEL, P.jack_r(), P.HOOD_LO,
                           P.HOOD_GAP_MAX, P.HOOD_GAP_MIN))
    print("HI %+.3f deg gap %.1f; full leaf lift at HI: gap %.3f >= NIP_PASS %.2f (%s)" % (
        P.HOOD_HI, P.HOOD_GAP_MIN, P.HOOD_GAP_LIFT, P.NIP_PASS, "ok" if P.HOOD_GAP_LIFT >= P.NIP_PASS else "FAIL"))
    print("TONGUE_IN", round(g.TONGUE_IN, 2), "K_REAR", [round(v, 2) for v in g.K_REAR], "J_REAR", [round(v, 2) for v in g.J_REAR])
    print("JACK_PT", [round(v, 2) for v in g.JACK_PT], "NIP_E", [round(v, 2) for v in g.NIP_E], "U", [round(v, 3) for v in g.NIP_U])
    for gap in (P.NIP_SET[0], P.HOOD_GAP, P.NIP_SET[1], P.HOOD_GAP_MAX):
        e = P.solve_eps(gap)
        print("gap %.1f eps %.2f deg stud_d %.2f tip u %.2f" % (gap, math.degrees(e), g.stud_d(e), P.STUD_L - g.stud_d(e)))
    for nm, (rest, lift) in g.arc_minima().items():
        print("entry arc (gap_arc, psi %.0f..%.0f) at %s: rest %.3f, full leaf lift %.3f (NIP_PASS %.2f)" % (
            P.BP_PSI0, P.PSI_TOP, nm, rest, lift, P.NIP_PASS))
    print("leaf", g.leaf_numbers(), "LEAF_U0", g.LEAF_U0, "SHELL_U0", g.SHELL_U0)
    print("JP", g.JP_SCREWS, "COVER", g.COVER_SCREWS)
    for nm, (u, v) in (("land0", (P.LAND_U0, P.LAND_V[0])), ("land1", (P.LAND_U0, P.LAND_V[1])), ("land1o", (0, P.LAND_V[1]))):
        print(nm, [round(c, 2) for c in g.nip_pq(u, v)], pip(g.nip_pq(u, v), g.PROFILE))
