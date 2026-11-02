"""Export the v3 assembly (attempt 1 + the attempt-2 hotfix) to GLB for the assembly guide (BUILD/guide/assembly_guide.html).

    cp ../../blender/model.blend /tmp/mmv3guide/model.blend
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup /tmp/mmv3guide/model.blend \
        --python export_glb.py -- [--out assembly.glb]

Ported from the v2 guide (../../../v2/BUILD/guide/export_glb.py). Run it on a copy of model.blend: it changes materials
and adds decimate modifiers in memory, exports, and never saves. Nothing in blender/, stl/ or the skills repo is written.

- Object names (PRT_/BUY_/FST_/CAB_) and the PIV_* empties are kept as glTF nodes, so the viewer can turn PIV_pan,
  PIV_tilt, PIV_flywheel, PIV_feeder, PIV_jar (and the coupled pinions) about their own origins. Joint ranges ride
  along as node extras (joint_axis, joint_lo, joint_hi, couple_to, couple_ratio). Before export, every PIV_* empty is
  compared with ../../blender/manifest.json "joints" (axis, lo, hi, couple_to, couple_ratio, parent); a mismatch stops
  the export.
- Materials are baked from the cadlib palette (asm.PALETTE): pla_a warm grey and pla_b terracotta for printed parts
  (params.COLOUR_B decides which), neutral greys for purchased parts, steel for fasteners, the cable colours, and
  transmissive-looking glass (alpha blend) for the jar. The palette values are display (sRGB) colours, so they are
  linearised for glTF's linear baseColorFactor.
- Purchased meshes over DECIMATE_OVER vertices get a collapse decimate (applied at export) on a copied mesh: in v3 that
  is only BUY_motorgo_axis (129k). Printed parts are exported at full resolution (the largest, jar_valve, is 11.5k).
- v2 copied in a 45 deg tilt prop for its step 11a. v3 has no tilt pose (checks.json assembly.held_poses is []) and no
  prop, so that path is gone.
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(argv[argv.index("--out") + 1]) if "--out" in argv else os.path.join(HERE, "assembly.glb")
MANIFEST = os.path.join(os.path.dirname(os.path.dirname(HERE)), "blender", "manifest.json")

DECIMATE_OVER = 6000        # purchased meshes above this many vertices are decimated
DECIMATE_TARGET = 6000      # ... to about this many

# cadlib asm.PALETTE (display colours) and the two extra materials parts/finish.py makes
PALETTE = {
    "pla_a": (0.82, 0.80, 0.76),
    "pla_b": (0.77, 0.33, 0.17),
    "buy": (0.22, 0.23, 0.25),
    "buy_metal": (0.62, 0.63, 0.65),
    "pcb": (0.10, 0.32, 0.20),
    "screw": (0.55, 0.56, 0.58),
    "cable_red": (0.70, 0.12, 0.10),
    "cable_blk": (0.08, 0.08, 0.08),
    "cable_wht": (0.90, 0.90, 0.88),
    "cable_yel": (0.85, 0.70, 0.15),
    "mm_fill": (0.75, 0.20, 0.15),
    "glass": (0.80, 0.90, 0.95),
}
LOOK = {  # roughness, metallic, alpha
    "pla_a": (0.65, 0.0, 1.0), "pla_b": (0.6, 0.0, 1.0), "buy": (0.55, 0.1, 1.0), "buy_metal": (0.35, 0.8, 1.0),
    "pcb": (0.5, 0.0, 1.0), "screw": (0.35, 0.85, 1.0), "mm_fill": (0.5, 0.0, 1.0), "glass": (0.05, 0.0, 0.22),
}


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def palette_key(rgba):
    """which palette entry a design material is (match on the viewport colour cadlib set)"""
    if abs(rgba[3] - 1.0) > 1e-3:
        return "glass"
    best = min(PALETTE, key=lambda k: sum((a - b) ** 2 for a, b in zip(PALETTE[k], rgba[:3])))
    assert sum((a - b) ** 2 for a, b in zip(PALETTE[best], rgba[:3])) < 1e-4, "unknown design colour %r" % (rgba,)
    return best


def baked(key, rgb):
    name = "GUIDE_" + key
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    rough, metal, alpha = LOOK.get(key, (0.6, 0.0, 1.0))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    lin = [srgb_to_linear(c) for c in rgb]
    bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*rgb, alpha)
    if alpha < 1.0:
        for attr, val in (("surface_render_method", 'BLENDED'), ("blend_method", 'BLEND')):
            if hasattr(m, attr):
                try:
                    setattr(m, attr, val)
                except (TypeError, AttributeError):
                    pass
    return m


def home_pose():
    for o in bpy.data.objects:
        if o.type == 'EMPTY' and o.name.startswith("PIV_"):
            o.rotation_euler = (0.0, 0.0, 0.0)
            if o.get("joint_kind") == "prismatic" and "joint_base_loc" in o.keys():
                o.location = tuple(o["joint_base_loc"])
    bpy.context.view_layer.update()


def bake_materials():
    remap = {}
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        for slot in ob.material_slots:
            src = slot.material
            if src is None:
                continue
            if src.name not in remap:
                key = palette_key(tuple(src.diffuse_color))
                remap[src.name] = baked(key, PALETTE[key])
            slot.material = remap[src.name]
    return {k: v.name for k, v in remap.items()}


def decimate():
    done = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.name.startswith("BUY_"):
            continue
        n = len(ob.data.vertices)
        if n <= DECIMATE_OVER:
            continue
        ob.data = ob.data.copy()          # work on a copy of the mesh data; model.blend is never saved anyway
        mod = ob.modifiers.new("guide_decimate", 'DECIMATE')
        mod.decimate_type = 'COLLAPSE'
        mod.ratio = DECIMATE_TARGET / n
        mod.use_collapse_triangulate = True
        done.append((ob.name, n, round(mod.ratio, 4)))
    return done


def check_joints():
    """every PIV_* empty must match manifest.json joints (names, axes, ranges, couplings, parents), both ways"""
    import json
    want = json.load(open(MANIFEST))["joints"]
    have = {o.name: o for o in bpy.data.objects if o.type == 'EMPTY' and o.name.startswith("PIV_")}
    bad = []
    if set(want) != set(have):
        bad.append("names differ: only in manifest %s, only in model %s" % (sorted(set(want) - set(have)),
                                                                           sorted(set(have) - set(want))))
    for n in sorted(set(want) & set(have)):
        w, o = want[n], have[n]
        for key, prop in (("axis", "joint_axis"), ("lo", "joint_lo"), ("hi", "joint_hi"), ("couple_to", "couple_to"),
                          ("couple_ratio", "couple_ratio"), ("kind", "joint_kind")):
            a, b = w.get(key), o.get(prop)
            if isinstance(a, float) or isinstance(b, float):
                ok = a is not None and b is not None and abs(a - b) < 1e-6
            else:
                ok = a == b
            if not ok:
                bad.append("%s %s: manifest %r, model %r" % (n, key, a, b))
        parent = o.parent.name if o.parent else None
        if parent != w.get("parent"):
            bad.append("%s parent: manifest %r, model %r" % (n, w.get("parent"), parent))
    assert not bad, "GUIDE: PIV_* joints don't match manifest.json: " + "; ".join(bad)
    print("GUIDE: %d joints match manifest.json: %s" % (len(have), ", ".join(
        "%s %s %s..%s" % (n, have[n].get("joint_axis"), have[n].get("joint_lo"), have[n].get("joint_hi"))
        for n in sorted(have))))


def clean_props():
    """drop custom properties the exporter can't serialise cleanly (nested id-property arrays like print_rot)"""
    for ob in bpy.data.objects:
        for k in list(ob.keys()):
            v = ob[k]
            if not isinstance(v, (int, float, str)):
                try:
                    flat = list(v)
                    if any(not isinstance(x, (int, float)) for x in flat):
                        del ob[k]
                    else:
                        ob[k] = [float(x) for x in flat]
                except TypeError:
                    del ob[k]


def main():
    check_joints()
    home_pose()
    remap = bake_materials()
    dec = decimate()
    clean_props()
    for ob in bpy.data.objects:
        ob.hide_set(False)
        ob.hide_render = False
        ob.hide_viewport = False
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=OUT, export_format='GLB', use_selection=False, export_apply=True, export_yup=True,
        export_extras=True, export_materials='EXPORT', export_normals=True, export_texcoords=False,
        export_cameras=False, export_lights=False, export_animations=False, export_skins=False, export_morph=False)
    print("GUIDE: materials %s" % remap)
    print("GUIDE: decimated %s" % dec)
    print("GUIDE: wrote %s (%.2f MB)" % (OUT, os.path.getsize(OUT) / 1e6))


main()
