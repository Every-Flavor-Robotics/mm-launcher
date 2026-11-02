# Export one binary STL per moving group of the v2 assembly, in world
# coordinates at the rest pose (all joints 0), plus a pivots manifest.
# Read-only on the .blend: nothing is saved.
#
#   Blender -b model.blend --python export_model.py -- <out dir>
#
# Groups follow the CAD pivots (base, PIV_pan, PIV_pan_pinion, PIV_tilt,
# PIV_flywheel, PIV_feeder, PIV_feeder_pinion); Printed + Purchased only
# (fasteners and cables are left out). Each group is decimated to about 25k
# triangles so the panel loads in a second or two.
import bpy, json, os, sys
argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
os.makedirs(out, exist_ok=True)

KEEP = {"Printed", "Purchased"}
GROUP_PIVOTS = ["PIV_flywheel", "PIV_tilt", "PIV_feeder", "PIV_feeder_pinion", "PIV_pan_pinion", "PIV_pan"]
def group_of(o):
    p = o
    while p is not None:
        if p.name in GROUP_PIVOTS:
            return p.name
        p = p.parent
    return "base"

def in_keep(o):
    return any(c.name in KEEP for c in o.users_collection)

groups = {}
for o in bpy.data.objects:
    if o.type != "MESH" or not in_keep(o) or o.hide_get() or o.hide_render:
        continue
    groups.setdefault(group_of(o), []).append(o)

manifest = {"units": "mm", "up": "Z", "groups": {}, "pivots": {}}
for name in GROUP_PIVOTS:
    p = bpy.data.objects.get(name)
    if p:
        manifest["pivots"][name] = {"loc": [round(v, 3) for v in p.matrix_world.translation],
                                    "parent": p.parent.name if p.parent else None}

deps = bpy.context.evaluated_depsgraph_get()
import bmesh
for g, objs in groups.items():
    bm = bmesh.new()
    for o in objs:
        ev = o.evaluated_get(deps)
        me = ev.to_mesh()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        ev.to_mesh_clear()
    bmesh.ops.triangulate(bm, faces=bm.faces)
    me = bpy.data.meshes.new(g)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("EXP_" + g, me)
    bpy.context.scene.collection.objects.link(ob)
    tris0 = len(me.polygons)
    target = 25000
    if tris0 > target:
        mod = ob.modifiers.new("dec", "DECIMATE"); mod.ratio = target / tris0
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    fn = os.path.join(out, g.replace("PIV_", "") + ".stl")
    bpy.ops.wm.stl_export(filepath=fn, export_selected_objects=True, apply_modifiers=True,
                          ascii_format=False, forward_axis="Y", up_axis="Z")
    manifest["groups"][g.replace("PIV_", "")] = {"file": os.path.basename(fn), "objects": len(objs), "tris": tris0}
    print("EXPORTED", g, len(objs), "objs", tris0, "tris ->", os.path.getsize(fn), "bytes")

with open(os.path.join(out, "pivots.json"), "w") as f:
    json.dump(manifest, f, indent=1)
print("MANIFEST", json.dumps(manifest["pivots"]))
