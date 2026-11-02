"""Supplementary CG/tip-angle grid over pan x tilt (cadcheck stability evaluates only 1 pose on this blend).
Same mass model as cadcheck.check_stability: PLA 1.24e-3 g/mm3 * (0.45 + 0.55 infill), BUY mass_g / masses_g."""
import bpy, bmesh, math, json, fnmatch, sys
from mathutils import Vector

cfg = json.load(open(sys.argv[sys.argv.index("--") + 1]))
masses = cfg.get("masses_g", {})
O = bpy.data.objects
J = {e.name: e for e in O if e.name.startswith("PIV_")}
base = {n: tuple(e.rotation_euler) for n, e in J.items()}
SOL = [o for o in O if o.type == 'MESH' and o.name[:4] in ("PRT_", "BUY_", "FST_")]


def body(o):
    p = o.parent
    while p is not None:
        if p.name.startswith("PIV_"):
            return p.name
        p = p.parent
    return "static"


def pose(vals):
    for n, e in J.items():
        ax = e.get("joint_axis")
        if ax not in ("X", "Y", "Z"):
            continue
        r = list(base[n])
        r["XYZ".index(ax)] = math.radians(vals.get(n, e.get("joint_home", 0.0) or 0.0))
        e.rotation_euler = r
    bpy.context.view_layer.update()


def cv(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    v6, c = 0.0, Vector()
    for f in bm.faces:
        a, b, d = (l.vert.co for l in f.loops)
        v = a.dot(b.cross(d)); v6 += v; c += v * (a + b + d) / 4.0
    bm.free()
    return (c / v6 if abs(v6) > 1e-9 else Vector()), abs(v6) / 6


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


pose({})
st = [o for o in SOL if body(o) == "static"]
zmin = min(min((o.matrix_world @ v.co).z for v in o.data.vertices) for o in st)
H = hull([((o.matrix_world @ v.co).x, (o.matrix_world @ v.co).y) for o in st for v in o.data.vertices if (o.matrix_world @ v.co).z < zmin + 0.6])
rows = []
for jar in (0, 30):
    for tilt in (-3, 0, 22.5, 46):
        for pan in (0, 45, 90, 135, 180, 225, 270, 315):
            pose({"PIV_pan": pan, "PIV_tilt": tilt, "PIV_jar": jar})
            M, S = 0.0, Vector()
            for o in SOL:
                c, v = cv(o)
                if o.name.startswith("PRT_"):
                    m = v * 1.24e-3 * (0.45 + 0.55 * float(o.get("infill", 20)) / 100)
                else:
                    m = float(o.get("mass_g", next((x for k, x in masses.items() if fnmatch.fnmatch(o.name, k)), 0.0)))
                M += m; S += c * m
            g = S / M
            d = 1e9
            for i in range(len(H)):
                (x1, y1), (x2, y2) = H[i], H[(i + 1) % len(H)]
                L = math.hypot(x2 - x1, y2 - y1) or 1e-9
                d = min(d, -((g.x - x1) * (y2 - y1) - (g.y - y1) * (x2 - x1)) / L)
            rows.append((jar, tilt, pan, round(M), round(g.x, 1), round(g.y, 1), round(g.z, 1), round(d, 1), round(math.degrees(math.atan2(d, g.z - zmin)), 1)))
for r in rows:
    print("CGGRID jar=%g tilt=%g pan=%g mass_g=%d cg=(%.1f,%.1f,%.1f) edge=%.1f tip=%.1f" % r)
w = min(rows, key=lambda r: r[-1])
print("CGGRID_WORST jar=%g tilt=%g pan=%g mass_g=%d cg=(%.1f,%.1f,%.1f) edge=%.1f tip=%.1f (of %d poses)" % (w + (len(rows),)))
