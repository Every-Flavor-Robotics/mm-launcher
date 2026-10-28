"""section render with some objects hidden: -- axis val out camx,camy,camz ortho keep hide1,hide2 [lentil cx,cy,cz:nx,ny,nz]"""
import bpy, sys, os
from mathutils import Vector
S = "/Users/alxchunlin/code-stuff/alex-3d-skills-pin/skills/print-cad-blender/scripts"
sys.path.insert(0, S)
from cadlib import render as R
a = sys.argv[sys.argv.index("--") + 1:]
axis, val, out, cam, ortho, keep, hide = a[0], float(a[1]), a[2], Vector([float(x) for x in a[3].split(",")]), float(a[4]), a[5], a[6]
R.setup(final=False)
from cadlib import geom as G
for n in [h for h in hide.split(",") if h]:      # pre-cut with the Manifold solver (the EXACT boolean in render.section inverts these)
    o = bpy.data.objects[n]
    lo, hi = [-5000] * 3, [5000] * 3
    k0 = "xyz".index(axis)
    if keep == "-": lo[k0] = val
    else: hi[k0] = val
    G.csg(o, sub=[G.box("precut_" + n, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])], check=False)
if len(a) > 7:
    c, nn = a[7].split(":")
    R.marker_lentil("MM_0", Vector([float(x) for x in c.split(",")]), Vector([float(x) for x in nn.split(",")]))
k = "xyz".index(axis); tgt = cam.copy(); tgt[k] = val
print("SEC", R.section(os.path.dirname(os.path.abspath(out)), os.path.basename(out), axis, val, cam, tgt, ortho, keep_side=keep))
