"""finish: presentation pass that runs after every geometry subsystem (no geometry), plus the encoder lead budget.

- v2-A1-12 colour map: every PRT_ material comes from params.COLOUR_B (pla_b terracotta = candy path and touch points,
  pla_a warm grey = static structure and drivetrain). Modules may use any colour; this pass overrides them.
- v2-A1-11 (second half): BUY_jar gets a transmissive glass material (RGBA alpha JAR_GLASS_RGBA[3]) so the M&M fill,
  the brief's hero element, shows through in the view set. Workbench draws a material with alpha < 1 in its
  transparent pass, so this needs no render-engine change.
- v2-A3-A2-02 encoder lead: one unspliced ENC_LEAD (550) JST-SH lead runs Plink -> journal (CAB_encoder), then rides
  CAB_launcher_bundle and CAB_launcher_base to the MotorGo. Every subsystem is built by now, so the bundle and base
  path_len are final: CAB_encoder lead_len = ENC_LEAD - bundle - base - ENC_SPARE (params.enc_budget). The build asserts
  that budget covers the CAB_encoder path, and that it agrees (within 1 mm) with checks.json cable_leads CAB_encoder.
  Since v2-A4 the checks.json cable_chains row (encoder signal, lead =ENC_LEAD - 5) is the check; this budget stays as the
  CAB_encoder lead_len.
- v2-A4-02 nip numbers for the BOM: nip_numbers() re-asserts NIP_PASS over the whole entry arc (params.gap_arc, psi
  BP_PSI0..PSI_TOP, not the BDC-only gap_bdc) at all three thumbwheel settings, and writes the arc minima and the leaf
  operating-stress table (launcher_geom.leaf_numbers) to manifest parts.PRT_hood.nip / parts.PRT_nip_leaf.operating, so
  the BOM quotes one source.
"""
import json, os
import bpy
from cadlib import asm as A
from parts.launcher_geom import Geo

CHECKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "checks.json")


def encoder_budget(P):
    obs = bpy.data.objects
    bundle, base, enc = obs["CAB_launcher_bundle"], obs["CAB_launcher_base"], obs["CAB_encoder"]
    budget = P.enc_budget(bundle["path_len"], base["path_len"])
    path = enc["path_len"]
    assert budget >= path, "CAB_encoder path %.1f exceeds its lead budget %.1f (ENC_LEAD %d - bundle %.1f - base %.1f - %.0f)" % (
        path, budget, P.ENC_LEAD, bundle["path_len"], base["path_len"], P.ENC_SPARE)
    enc["lead_len"] = float(budget)
    enc["enc_lead"] = float(P.ENC_LEAD)
    A.PARTS["CAB_encoder"]["lead_len"] = float(budget)
    P.CABLE_LEADS["CAB_encoder"] = int(round(budget))
    with open(CHECKS) as f:
        ck = json.load(f).get("cable_leads", {}).get("CAB_encoder")
    assert ck is not None and abs(ck - budget) <= 1.0, "checks.json cable_leads CAB_encoder %s != built budget %.1f" % (ck, budget)
    print("FINISH CAB_encoder lead budget %.1f = %d - %.1f - %.1f - %.0f; path %.1f; spare %.1f; checks.json %s" % (
        budget, P.ENC_LEAD, bundle["path_len"], base["path_len"], P.ENC_SPARE, path, budget - path, ck))


# v2-A3 finish (A3-02, A3-01, A2-02): the purchased item behind each object, as the BOM lists it. v2-A4: FST_nip_stud is
# modelled with the cadlib M3_hex spec (ISO 4017 AF 5.5 x 2.0), so the model and the BOM name the same part.
# v3-A1 finish: FST_detent_0 and every v2 screw the merges removed are gone (bom_items asserts each named object exists);
# the bus texts follow the v3 splice (O10 x 20, z 72..92, pushed up from below at 11a, captive under the turntable's bore
# roof) and the encoder text quotes the built budget.
BOM_ITEM = {
    "FST_nip_stud": "M3 x 16 hex head ISO 4017 (AF 5.5 x 2.0), modelled as cadlib M3_hex x 16; captive in the hood's hex "
                    "pocket (three +v flats key it), never driven; FST_tw_nut is captive in the thumbwheel's side slot",
}
ENC_ITEM = ("one-piece twisted 5-wire JST-SH encoder lead >= %d (ENC_LEAD), Plink -> MotorGo encoder JST, unspliced; "
            "rides CAB_launcher_bundle (%.1f) and CAB_launcher_base (%.1f) on the far side of the sleeve from the 3 phases; "
            "Plink-to-journal share %.1f for a %.1f route")
BUS_LEAD_ITEM = ("Hiwonder 3-pin bus lead %d; moving side, hub-end plug cut off, enters BUY_bus_junction (BOM 14a) at its "
                 "top face (z %g) in the R%g hub-tube bore")
# v2-A5-03 (attempt 6): the splice text is built from params.BUS_JCT in bom_items(), so it follows the model.
# v3-A1: the splice is soldered below the deck with the floor off and pushed up the hub-gear bore at step 11a (no tilt
# pose, no groove cap); the step label is read from checks.json assembly_order (assembly_step).
BUS_JCT_ITEM = ("BOM 14a: 3-way Hiwonder bus star splice, 3 x 3-to-1 solder splices (like wires joined) each under heat "
                "shrink, the three sleeved together, %g long or less; modelled as a O%g x %g envelope on PIV_pan in the "
                "R%g hub-tube bore at r %g az %g (%.2f, %.2f), z %g..%g; %d g; soldered below the deck (shell on its side, "
                "floor off) and pushed up the bore at step %s; the turntable's printed bore roof (z %g) stops it rising")
# v2-A6-02 (attempt 7): the pan lead is split on the pan axis at params.BUS_PAN_AX: static U-loop + PIV_pan tail
BUS_PAN_ITEM = ("Hiwonder 3-pin bus lead 350 (next stock length up from 300), one wire with CAB_bus_pan_tail; static side: "
                "base pocket, riser, arch and the U-loop, ending ON the pan axis at (%g, %g, %g) (params BUS_PAN_AX), so "
                "the hand-over to the turning tail has zero chord at every pan")
BUS_PAN_TAIL_ITEM = ("the last %.1f of the CAB_bus_pan 350 lead (no separate purchase; cable_chains 'pan bus lead' 350 covers "
                     "both routes): turns with PIV_pan from the pan axis at z %g up to the splice's bottom face centre "
                     "(%.2f, %.2f, %g); hub-end plug cut off, soldered into BUY_bus_junction at step %s")


def nip_numbers(P):
    """v2-A4-02: the BOM's nip claims from the entry-arc helper (gap_arc), asserted here and written to the manifest"""
    g = Geo(P)
    arc = g.arc_minima()                      # {setting: (rest, full lift)} over psi BP_PSI0..PSI_TOP
    for nm, (rest, lift) in arc.items():
        assert lift >= P.NIP_PASS + P.NIP_PASS_MARGIN - 1e-6, "entry arc at %s opens to %.3f at full lift < NIP_PASS %.2f + %.1f" % (
            nm, lift, P.NIP_PASS, P.NIP_PASS_MARGIN)
    leaf = g.leaf_numbers()
    nip = {"helper": "params.gap_arc (psi %.0f..%.0f, 0.5 deg)" % (P.BP_PSI0, P.PSI_TOP), "NIP_PASS": P.NIP_PASS,
           "assert_min": P.NIP_PASS + P.NIP_PASS_MARGIN, "gap_profile": P.GAP_PROFILE, "LIFT_FLOOR": P.LIFT_FLOOR,
           "FUNNEL_PSI0": P.FUNNEL_PSI0, "PSI_C_reference": P.PSI_C,
           "entry_arc_rest_full_lift": {k: list(v) for k, v in arc.items()}}
    A.PARTS["PRT_hood"]["nip"] = nip
    A.PARTS["PRT_nip_leaf"]["operating"] = leaf["operating"]
    print("FINISH nip entry arc (gap_arc) rest/full lift: %s; NIP_PASS %.2f (+%.1f asserted)" % (
        ", ".join("%s %.3f/%.3f" % (k, r, l) for k, (r, l) in arc.items()), P.NIP_PASS, P.NIP_PASS_MARGIN))
    print("FINISH leaf operating (lift fraction, MPa): %s; solid %.1f MPa" % (
        ", ".join("%s %.2f/%.1f" % (k, v["lift_frac"], v["stress_MPa"]) for k, v in leaf["operating"].items()),
        leaf["root_stress_at_stop_MPa"]))


def assembly_step(name):
    """the label (first token) of the checks.json assembly_order step that lists `name`, nested bench merges included"""
    with open(CHECKS) as f:
        order = json.load(f)["assembly_order"]
    def walk(steps):
        for st in steps:
            if isinstance(st, dict):
                if name in st.get("objects", []):
                    return st["step"].split()[0]
                for v in st.values():
                    if isinstance(v, list):
                        hit = walk(v)
                        if hit:
                            return hit
        return None
    return walk(order)


def bom_items(P):
    obs = bpy.data.objects
    j = P.BUS_JCT
    items = dict(BOM_ITEM)
    jstep = assembly_step("BUY_bus_junction")
    tail = obs["CAB_bus_pan_tail"]
    assert jstep == "11a" and tail.get("step") == "11a", "splice / pan tail step %r / %r, BOM says 11a" % (jstep, tail.get("step"))
    items["BUY_bus_junction"] = BUS_JCT_ITEM % (j["l"], j["d"], j["l"], P.IF_HUB_BORE_R, j["r"], j["az"], P.BUS_JCT_XY[0],
                                                P.BUS_JCT_XY[1], j["z0"], j["z0"] + j["l"],
                                                A.PARTS["BUY_bus_junction"]["mass_g"], jstep, P.HUB_ROOF_Z)
    for nm, lead in (("CAB_bus_tilt", P.CABLE_LEADS["CAB_bus_tilt"]), ("CAB_bus_feeder", P.CABLE_LEADS["CAB_bus_feeder"])):
        items[nm] = BUS_LEAD_ITEM % (lead, P.BUS_JCT_TOP[2], P.IF_HUB_BORE_R)
    items["CAB_bus_pan"] = BUS_PAN_ITEM % tuple(P.BUS_PAN_AX)
    items["CAB_bus_pan_tail"] = BUS_PAN_TAIL_ITEM % (tail["path_len"], P.BUS_PAN_AX[2], P.BUS_JCT_BOT[0], P.BUS_JCT_BOT[1],
                                                     P.BUS_JCT_BOT[2], tail["step"])
    enc = obs["CAB_encoder"]
    items["CAB_encoder"] = ENC_ITEM % (P.ENC_LEAD, obs["CAB_launcher_bundle"]["path_len"], obs["CAB_launcher_base"]["path_len"],
                                       enc["lead_len"], enc["path_len"])
    for name, item in items.items():
        assert name in obs and name in A.PARTS, "BOM_ITEM names a missing object %s" % name
        obs[name]["bom_item"] = item
        A.PARTS[name]["bom_item"] = item


def build(P):
    encoder_budget(P)
    bom_items(P)
    nip_numbers(P)
    P.apply_colours(bpy.data.objects)
    jar = bpy.data.objects.get("BUY_jar")
    if jar is not None:
        m = A.mat(P.JAR_GLASS_RGBA)
        m.roughness = 0.1
        m.metallic = 0.0
        for attr, val in (("surface_render_method", 'BLENDED'), ("blend_method", 'BLEND')):
            if hasattr(m, attr):
                try:
                    setattr(m, attr, val)
                except (TypeError, AttributeError):
                    pass
        jar.data.materials.clear()
        jar.data.materials.append(m)
        jar.show_transparent = True
        jar["glass_alpha"] = P.JAR_GLASS_RGBA[3]


ELEV_MARGIN = 1.08      # v2-A5-05: elevation frame = the scene bounds + 8 % (render.view_set's size * 1.25 cropped the jar)


def elevations(outdir):
    """v2-A5-05 (attempt 6): re-render front.png and side.png framed on the whole machine (jar top and base bottom inside
    the frame). render.view_set uses ortho = max extent * 1.25 across the 4:3 frame's width, so its height window is
    0.94 x the 432.6 tall assembly and both elevations cropped the jar top and the base bottom. Called by
    build_assembly.py right after view_set; overwrites those two files."""
    from mathutils import Vector
    from cadlib import render as R
    R.setup()
    A.set_pose()
    lo, hi = R.scene_bounds()
    c = (lo + hi) / 2
    sc = bpy.context.scene
    aspect = sc.render.resolution_x / sc.render.resolution_y
    d = max(hi - lo) * 4.4
    out = []
    for name, axis, w in (("front", Vector((0, 1, 0)), hi.x - lo.x), ("side", Vector((1, 0, 0)), hi.y - lo.y)):
        ortho = max(w, (hi.z - lo.z) * aspect) * ELEV_MARGIN
        R.camera(c + axis * d, c, ortho=ortho, lens=55)
        out.append(R.shot(os.path.join(outdir, name + ".png")))
        print("FINISH elevation %s: z %.1f..%.1f, ortho %.1f (frame height %.1f)" % (name, lo.z, hi.z, ortho, ortho / aspect))
    return out
