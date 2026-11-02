# M&M launcher v2: print plan

Everything printed for the turret: 36 machine parts (37 prints: the nip leaf is printed twice, one fitted and one spare)
and 3 tools, on 9 plates for a Bambu H2D (325 x 320) and a P1S (256 x 256). The model is frozen at attempt 7 (review 7:
9/8/9, no blockers). `cad check` gives 0 fails and 37 accepted warns (`../blender/cadcheck.json`).

**Times and grams are estimates from the geometry. No slicer was run.** They come from the launch rig's layer-by-layer model
(Bambu 0.20 mm Standard P1S speeds, capped at 21 mm³/s, 80 % motion efficiency, 1.5 s per layer, 6 min per plate start),
reused unchanged from `../../test-prints/launch-rig/build.py` (it reproduces the rig's published numbers exactly), with 3 walls
instead of 2. Script: `../blender/tools/print_estimate.py`; numbers: `print_estimate.json`. Slice the plates yourself for the
real figures. cadcheck's flat 12 mm³/s model gives 31.6 h and 1500 g for the 36 machine parts, for comparison.

`plates/<plate>/` holds copies of the STLs for each plate, already in print orientation. They are **not arranged**: load the
folder into your slicer and lay the parts out yourself. The footprint check below only packs bounding rectangles 6 mm apart
to show each plate fits its bed.

## Totals

| | Plates | Time (estimate) | Filament (estimate) |
|---|---|---|---|
| H2D queue | 2, 3, 5, 7 | 14.9 h | 944 g |
| P1S queue | 1, 4, 6, 8, 9 | 13.1 h | 761 g |
| **All plates** | 9 | **27.9 h of printing**, about 15 h wall clock with both printers running | **1705 g**: colour A 1477 g, colour B 228 g |

Have about 1.5 kg of colour A on hand (two 1 kg spools) and about 0.25 kg of colour B.

## Colours (the two-colour scheme, `params.COLOUR_B`)

- **A, warm grey:** static structure and drivetrain: base, turntable, posts, beam, crown, covers, nacelle, journal plate,
  encoder cap, gears, pinions, stops, leaf, detent clip.
- **B, terracotta:** the candy path and the touch points: jar adapter, valve, gate, feeder housing and disc, launcher body
  (chute and muzzle), hood, flywheel, thumbwheel.
- Tools: any colour. They are put on plates of whichever colour has room (the pocket coupon goes on a B plate because it must
  print like the B feeder disc).

Every plate is a single colour, so neither printer swaps filament mid-plate.

## Settings for every plate

- PLA, 0.4 nozzle, 0.20 mm layers, **3 walls**, 5 top and 3 bottom layers, grid or gyroid infill at the per-part value below.
- **Supports: none, on every part.** Each STL is already in its print orientation. cadcheck's parts check confirms this for all
  36 machine parts: manifold, they fit both beds, they have a flat bed face, and the only overhang warning is 205 mm² of
  loft-seam facets on the beam's corner chamfers (accepted). The longest bridge is 16.6 mm, on the feeder crown.
- **Brim (5 mm) on:**
  - `post_L` (150 tall on a 649 mm² foot);
  - `post_R` (150 tall);
  - `nip_cover` (56 tall on 268 mm²).
  `gate_detent` and `nip_stop_sleeve` are tiny; add a brim if your bed is marginal.
- **100 % infill:**
  - flywheel: as on the rig; it keeps the wheel's inertia and the pinch-hub strength;
  - nip leaf: a spring, printed flat so it bends in the layer plane;
  - stops, thrust ring, jar gate, gate detent.
- Self-tap pilots are Ø2.5 (M3) and Ø2.1 (M2.5). 3 walls keep solid plastic round them. If your printer prints holes
  undersize, run a Ø2.5 drill through each pilot rather than forcing the screw.

## Print order

1. **Launcher pod first** (plates 1 and 2, one on each printer, about 3.5 h).
   - The pod uses the launch rig's parameters, so you can check it against the rig you already printed (see "Validate the pod"
     below) before committing about 25 h to the rest.
   - Plate 2 also carries the **pocket test coupon**. Do the M&M calipering and the coupon test (`MEASURE_FIRST.md` item 2)
     while plates 3-9 wait: the feeder disc on plate 3 depends on it.
2. **Feeder and jar** (plates 3 and 4). Before plate 3: caliper the jar and band (`MEASURE_FIRST.md` item 1) and settle
   `POCKET_D` from the coupon.
3. **Pan stage** (plates 5 and 6). Before them: check the servo horn's bolt circle (`MEASURE_FIRST.md` item 4). It sets the
   tilt horn adapter on plate 5; the feeder pinion on plate 4 has the same interface.
4. **Base** (plates 7, 8, 9). Before them, check:
   - the DeWalt adapter holes (base shell, plate 7);
   - the buck flange and the servo controller holes (floor, plate 8);
   - the MotorGo holes (partition, plate 9).

| Step | H2D | P1S |
|---|---|---|
| 1 | Plate 2, pod terracotta, 2.3 h | Plate 1, pod grey, 3.5 h |
| (validate the pod; calipering and coupon) | | |
| 2 | Plate 3, feeder and jar terracotta, 1.6 h | Plate 4, feeder grey, 1.6 h |
| 3 | Plate 5, turntable and beam, 3.6 h | Plate 6, posts, 4.8 h |
| 4 | Plate 7, base shell, 7.4 h | Plate 8, floor, 2.2 h, then plate 9, mounts, 1.0 h |

If a change from `MEASURE_FIRST.md` alters a part, rebuild before printing that plate:
`cd ../blender && cad build build_assembly.py && cad check model.blend checks.json`. Then re-copy the changed STLs from `../stl/`
into the plate folder.

## Validate the pod against the rig (after plates 1 and 2)

The pod shares the rig's parameters, but it is **not a copy of the rig's parts**. The same:

- the wheel: R35 land between R36 flanges, wheel plane x 21, D-shaft pinch hub, M3 x 20 pinch bolts;
- the motor face and the crush ribs;
- the rear-shaft magnet and the Plink pegs;
- the thumbwheel's Ø17 x 5 envelope.

Different (compared STL to STL):

- **Flywheel web:** 4.5 thick here, 5.1 on the rig. `HUB_X0` 9.0 -> 9.6 moves the hub 0.6 off the motor-side wall, for the
  brief's 1.5 mm rotating clearance. The land and both flanges are unchanged. Volume 33.2 vs 35.4 cm³.
- **Thumbwheel nut trap:** 0.3 deeper, so the nut seats below the face.
- **Hood (backplate):** v2 uses the lift-matched profile (`GAP_PROFILE` "lift"); the rig uses the attempt-3 quadratic. The
  printed gap window is 6.2..7.0 here (rig 5..12), set by two printed stops.
- **Leaf:** v2 has a separate 21.9 x 2.3 leaf (7.1 N preload); the rig has one built into its guard (28 x 1.84, 9.0 N).

What to check on the bench (BOM step 6):

- the wheel slides onto the motor's D-shaft and clamps;
- the motor face screws (M3 x 10 pan) sit below the web with daylight to the spinning wheel;
- the encoder cap seats the Plink at the rig's air gap;
- the thumbwheel turns through the finger slot between the two stops;
- a thick candy pushed into the nip by hand lifts the leaf and passes.

If the rig has given you `NIP_SET`, `G_IN`, leaf preload or tape-thickness numbers, put them into `params.py` and rebuild
**before** printing plate 2 (hood, body). BOM section 0 lists which numbers the rig should feed back.

## Plates

### Plate 1-pod-grey  (P1S, colour A warm grey)

Estimate: **3.5 h, 205 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `nacelle` | 1 | front plate on the bed, journal up (duct roof bridges 15 mm) | 25 % | 3 | 95.5 x 80.5 x 99.7 | 128 | 137.6 |
| `launcher_cover` | 1 | inner face on the bed; rebated edge steps in toward the top | 25 % | 3 | 109.9 x 119 x 4 | 23 | 24.6 |
| `journal_plate` | 1 | inner face on the bed; lap step, journal, socket and stop lug grow up | 30 % | 3 | 64.6 x 52.5 x 20.2 | 13 | 10.8 |
| `encoder_cap` | 1 | back face on the bed, spigot and pegs up | 40 % | 3 | 55.7 x 53 x 8.5 | 9 | 8.7 |
| `nip_cover` | 1 | screw-block end on the bed; shell and end walls grow up as vertical walls; skirt bridges at the top; finger slot 22 x 8.3 in the -v end wall over the thumbwheel rim (v2-A1-02) | 30 % | 3 | 27.5 x 13.5 x 56 | 16 | 8.6 |
| `nip_leaf` | 2 | flat: strip's outer face on the bed, root block and pads up (bending stress in the layer plane) | 100 % | 3 | 21.9 x 42.6 x 5.9 | 7 | 6.2 |
| `nip_stop` | 1 | bottom (screw) face on the bed: pilot vertical, contact face a vertical wall | 100 % | 3 | 20 x 7 x 6.5 | 2 | 1.1 |
| `nip_stop_sleeve` | 1 | end on the bed (tube upright) | 100 % | 3 | 7.6 x 7.6 x 9.4 | 2 | 0.4 |
| `tools/encoder_jig` | 1 | as exported: flat face on the bed (magnet glue jig, BOM 6b) | 20 % | 3 | 44 x 49.1 x 11.2 | 8 | 7.4 |

### Plate 2-pod-terracotta  (H2D, colour B terracotta)

Estimate: **2.3 h, 140 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `launcher_body` | 1 | left (motor) wall outer face on the bed; profile extruded so every wall is vertical | 25 % | 3 | 128.5 x 122.2 x 27.5 | 70 | 77.0 |
| `flywheel` | 1 | motor-side web face on the bed; rim and hub grow up (top flange has a 45 deg underside) | 100 % | 3 | 72 x 72 x 19.9 | 38 | 41.2 |
| `hood` | 1 | on its side face (profile extruded, all walls vertical; stud pocket has a vertex up) | 40 % | 3 | 75.3 x 58.8 x 22.5 | 13 | 11.8 |
| `nip_wheel` | 1 | outer face on the bed, nut trap up (press the nut in) | 50 % | 3 | 16.9 x 16.9 x 5 | 2 | 1.0 |
| `tools/test_pocket_coupon` | 1 | flat, chamfered pocket rims up (print it like the feeder disc) | 40 % | 3 | 51.1 x 51.1 x 8 | 9 | 9.5 |

### Plate 3-feeder-jar-terracotta  (H2D, colour B terracotta)

Estimate: **1.6 h, 87 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `feeder_housing` | 1 | disc running face on the bed, spout up | 30 % | 3 | 151.4 x 96 x 18 | 27 | 26.9 |
| `feeder_disc` | 1 | gear band on the bed, fins up | 40 % | 3 | 69 x 69 x 14 | 17 | 17.6 |
| `jar_adapter` | 1 | lid disc (glass side) on the bed, spout up | 40 % | 3 | 69 x 69 x 11.9 | 10 | 9.4 |
| `jar_valve` | 1 | skirt + baffle bottom on the bed (lug undersides bridge 5.5 mm) | 40 % | 3 | 71 x 69.5 x 27.1 | 24 | 24.3 |
| `jar_gate` | 1 | flat, chamfer, tab, stop lug and detent notches up | 100 % | 3 | 61.5 x 56 x 8.6 | 9 | 9.0 |

### Plate 4-feeder-grey  (P1S, colour A warm grey)

Estimate: **1.6 h, 89 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `feeder_crown` | 1 | top (z 286) on the bed: lip, socket cone, slot ceilings and pocket floors all print as floors | 25 % | 3 | 151.4 x 96 x 23 | 52 | 57.5 |
| `feeder_cover` | 1 | chamfered top on the bed, ears up | 20 % | 3 | 47 x 49.1 x 36.3 | 21 | 18.6 |
| `feeder_pinion` | 1 | gear face on the bed, horn recess up | 60 % | 3 | 47.8 x 48 x 9 | 11 | 11.7 |
| `gate_detent` | 1 | flat +Y back face (screw-head face) on the bed: the beam along x and its bending lie in the layer plane | 100 % | 3 | 28 x 11.1 x 15.9 | 4 | 1.5 |

### Plate 5-pan-turntable-beam  (H2D, colour A warm grey)

Estimate: **3.6 h, 231 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S no.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `turntable` | 1 | top face on the bed, hub up (groove and cap rebate open to the bed) | 15 % | 3 | 216 x 216 x 17 | 125 | 140.4 |
| `beam` | 1 | top face on the bed, tongues up | 30 % | 3 | 216 x 60 x 29 | 58 | 63.9 |
| `hub_gear` | 1 | flat, screw heads' face down | 40 % | 3 | 57 x 57 x 7.5 | 11 | 11.0 |
| `thrust_ring` | 1 | flat | 100 % | 3 | 88 x 88 x 2 | 11 | 11.9 |
| `tilt_horn_adapter` | 1 | horn recess face on the bed, hex key up | 60 % | 3 | 26 x 25.9 x 13.3 | 5 | 3.6 |

### Plate 6-pan-posts  (P1S, colour A warm grey)

Estimate: **4.8 h, 283 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `post_L` | 1 | upright, foot on the bed (U-bore opens to the top; channel cavity roofs bridge 6 mm) | 25 % | 3 | 20 x 48 x 150 | 75 | 66.4 |
| `post_R` | 1 | upright, foot on the bed (servo pocket roof bridges 21 mm, teardrop passage, stop lugs drafted) | 25 % | 3 | 71.1 x 48 x 150 | 164 | 175.4 |
| `post_R_cover` | 1 | flat inner face on the bed, arc face up | 25 % | 3 | 58 x 48 x 11.8 | 16 | 16.5 |
| `groove_cap` | 1 | flat, countersinks up | 40 % | 3 | 127.6 x 54 x 3 | 12 | 12.2 |
| `tools/tilt45_prop` | 1 | base (turntable face) on the bed; the sloped pad top and the foot grow up | 15 % | 3 | 49 x 30.7 x 50.9 | 17 | 12.4 |

### Plate 7-base-shell  (H2D, colour A warm grey)

Estimate: **7.4 h, 486 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S no.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `base_shell` | 1 | upside down: deck face on the bed, walls up | 15 % | 3 | 241.2 x 240 x 87 | 421 | 467.5 |
| `pan_pinion` | 1 | gear top on the bed, horn recess up | 40 % | 3 | 56.9 x 56.9 x 9.1 | 13 | 13.5 |
| `pan_servo_clamp` | 1 | flat | 30 % | 3 | 38.7 x 47.4 x 4 | 5 | 4.8 |

### Plate 8-base-floor  (P1S, colour A warm grey)

Estimate: **2.1 h, 132 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `base_floor` | 1 | flat, bosses up | 15 % | 3 | 240 x 240 x 11 | 123 | 131.5 |

### Plate 9-base-mounts  (P1S, colour A warm grey)

Estimate: **1.0 h, 52 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `base_partition` | 1 | rear face on the bed, standoffs up | 25 % | 3 | 80 x 82.5 x 15.5 | 19 | 18.6 |
| `pan_servo_mount` | 1 | plate top on the bed, pocket walls up | 30 % | 3 | 84 x 66 x 43.7 | 35 | 33.1 |

## Plate folders

`plates/1-pod-grey/` has `nip_leaf.stl` and `nip_leaf_spare.stl`, the same part twice (one fitted, one kept unloaded as the
creep reference, BOM section 0). Every other part is printed once. The three tools are `encoder_jig` (magnet glue jig, step 6b),
`test_pocket_coupon` (sets `POCKET_D`) and `tilt45_prop` (holds the pod at 45 for step 11a, new after review 7).
