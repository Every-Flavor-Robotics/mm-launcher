"""Export the frozen v2 assembly to GLB for the assembly guide (BUILD/guide/assembly_guide.html).

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup ../../blender/model.blend \
        --python export_glb.py -- [--out assembly.glb] [--prop-blend /tmp/mm_prop_model.blend]

Read-only on the design: it opens model.blend, changes materials and adds decimate modifiers in memory, exports, and
never saves. Nothing in blender/, stl/ or the skills repo is written.

- Object names (PRT_/BUY_/FST_/CAB_) and the PIV_* empties are kept as glTF nodes, so the viewer can turn PIV_pan,
  PIV_tilt, PIV_flywheel, PIV_feeder (and the coupled pinions) about their own origins. Joint ranges ride along as
  node extras (joint_axis, joint_lo, joint_hi, couple_to, couple_ratio).
- Materials are baked from the cadlib palette (asm.PALETTE): pla_a warm grey and pla_b terracotta for printed parts
  (params.COLOUR_B decides which), neutral greys for purchased parts, steel for fasteners, the cable colours, and
  transmissive-looking glass (alpha blend) for the jar. The palette values are display (sRGB) colours, so they are
  linearised for glTF's linear baseColorFactor.
- Purchased meshes over DECIMATE_OVER vertices get a collapse decimate (applied at export) on a copied mesh. Printed
  parts are exported at full resolution (the largest, jar_valve, is 11k vertices).
- The 45 deg prop (tools/tilt45_prop.py) is not in the model. If its scratch blend exists, its placed mesh is copied in
  as TOOL_tilt45_prop on PIV_pan, drawn blue like the step renders. The viewer shows it only at step 11a.
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(argv[argv.index("--out") + 1]) if "--out" in argv else os.path.join(HERE, "assembly.glb")
PROP_BLEND = argv[argv.index("--prop-blend") + 1] if "--prop-blend" in argv else "/tmp/mm_prop_model.blend"

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
    "tool_blue": (0.6, 0.0, 1.0),
}
TOOL_BLUE = (0.184, 0.384, 0.910)   # alex-style dark s1 #2f62e8, the step renders' prop colour


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


def add_prop():
    if not os.path.exists(PROP_BLEND):
        print("GUIDE: no prop scratch blend at %s; step 11a.0 will have no prop" % PROP_BLEND)
        return None
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(PROP_BLEND, link=False) as (src, dst):
        if "PRT_tilt45_prop" not in src.objects:
            print("GUIDE: %s has no PRT_tilt45_prop" % PROP_BLEND)
            return None
        dst.objects = ["PRT_tilt45_prop"]
    lib_ob = dst.objects[0]
    mw = lib_ob.matrix_world.copy()
    me = lib_ob.data.copy()
    me.transform(mw)                       # world coordinates at the home pose, like every other part
    me.name = "TOOL_tilt45_prop"
    for o in set(bpy.data.objects) - before:   # the appended object and any parent it dragged in
        bpy.data.objects.remove(o, do_unlink=True)
    ob = bpy.data.objects.new("TOOL_tilt45_prop", me)
    bpy.data.collections["Purchased"].objects.link(ob)   # any collection; the viewer keys on the name
    piv = bpy.data.objects["PIV_pan"]
    ob.parent = piv
    ob.matrix_parent_inverse = piv.matrix_world.inverted()
    me.materials.clear()
    me.materials.append(baked("tool_blue", TOOL_BLUE))
    ob["kind"] = "TOOL"
    ob["note"] = "printed tool, not a machine part (tools/tilt45_prop.py); placed for step 11a.0"
    lo = [min((ob.matrix_world @ v.co)[i] for v in me.vertices) for i in range(3)]
    hi = [max((ob.matrix_world @ v.co)[i] for v in me.vertices) for i in range(3)]
    print("GUIDE: prop added, world bbox %s .. %s" % ([round(x, 1) for x in lo], [round(x, 1) for x in hi]))
    return ob


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
    home_pose()
    remap = bake_materials()
    dec = decimate()
    add_prop()
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
