# M&M launcher v3: print plan

Everything printed for the turret, on 8 plates for a Bambu H2D (325 x 320) and a P1S (256 x 256):

- **25 machine parts** (manifest `PRT_*`), as 26 prints: the nip leaf is printed twice, one fitted and one spare;
- **2 tools:** the encoder jig and the pocket coupon;
- **6 fit coupons** and a test hub gear (`MEASURE_FIRST.md` item 2).

The model is v3 attempt 1 plus the attempt-2 hotfix. `cad check` gives 0 fails and 69 warns: 58 accepted, 11 untriaged
(the planner-baseline set), and 1 config warn (`../renders/attempt-2/cadcheck.json`, identical to `../blender/cadcheck.json`).
`cad printcheck` passes all 25 STLs with 0 fails and 9 accepted warns (`../stl/printcheck.json`).

**Times and grams are estimates from the geometry. No slicer was run.** They come from the launch rig's layer-by-layer model:
Bambu 0.20 mm Standard P1S speeds, capped at 21 mm³/s, 80 % motion efficiency, 1.5 s per layer, 6 min per plate start. It is
reused unchanged from `../../test-prints/launch-rig/build.py`, with 3 walls instead of 2. The script is
`../blender/tools/print_estimate.py`, run as `cd ../blender && cad py tools/print_estimate.py`; it needed no path changes
for v3. Its numbers are in `print_estimate.json`. Slice the plates yourself for the real figures. For comparison,
cadcheck's flat 12 mm³/s model gives 31.2 h and 1537 g for the 25 machine parts [parts].

`plates/<plate>/` holds copies of the STLs for each plate, already in print orientation. They are **not arranged**: load the
folder into your slicer and lay the parts out yourself. The footprint check below only packs bounding rectangles 6 mm apart
to show each plate fits its bed.

## Hotfix STLs (attempt 2)

Three STLs changed in the attempt-2 hotfix and are marked **(hotfix)** in the tables:

| STL | Plate | What changed | Volume, attempt 1 → 2 [parts] |
|---|---|---|---|
| `beam` | 3 | `BEAM_HOOK` w 3.0 → 2.2: each barb now sits 0.3 a side in its 2.8 release slot and catches under the post ledge (v3-A1-01) | 168782.7 → 168690.5 mm³ |
| `jar_adapter` | 0b | the spout key groove runs 1.0 past the valve's key rib (v3-A1-01); a R0.65 dimple in the +X notch wall for the gate's open detent, and the -X (closed) through-notch widened on +Y to y 4.0 (v3-A1-03) | 6849.3 → 6842.0 mm³ |
| `jar_gate` | 0b | a new in-plane open-detent finger under the stop lug: R0.6 bump, 0.5 inner and 1.2 outer relief slots (v3-A1-03) | 7215.9 → 7163.7 mm³ |

The other 22 STLs are unchanged from attempt 1 (DESIGN_LOG "Attempt 2", reprint list; the volumes in
`../renders/attempt-1/cadcheck.json` and `../renders/attempt-2/cadcheck.json` match). If you already printed attempt 1,
reprint only these three.

**Not printed:** `../stl/tools/tilt45_prop.stl`. It is a v2 attempt-7 leftover dated 25 Oct. It propped the pod at tilt 45
for v2's groove-cap screws (v2 step 11a.0). v3 has no groove cap: the splice is made from below with no pose
(`assembly.held_poses` `[]`). The tilt-45 service jobs run with the servo powered (BOM section 5). Review v3-A1-08 says to
delete it.

## Totals

| | Plates | Time (estimate) | Filament (estimate) |
|---|---|---|---|
| H2D queue | 0b, 2, 3, 5 | 15.8 h | 990 g |
| P1S queue | 0a, 1, 4, 6 | 13.7 h | 829 g |
| **All plates** | 8 | **29.5 h of printing**, about 16 h wall clock with both printers running | **1819 g**: colour A 1587 g, colour B 232 g |

Of that, the 26 machine-part prints are 1737 g. The fit coupons, the test hub gear and the two tools are 82 g.

Have about 1.6 kg of colour A on hand (two 1 kg spools) and about 0.25 kg of colour B.

## Colours (the two-colour scheme, `params.COLOUR_B`)

- **A, warm grey:** static structure and drivetrain: base shell and floor, turntable (posts integral), beam (with the
  integral feed floor and spout), crown, covers, nacelle, journal plate, encoder cap, gears, pinions, thrust ring, leaf.
- **B, terracotta:** the candy path and the touch points: jar adapter, valve, gate, feeder disc, launcher body (chute and
  muzzle), hood, flywheel, thumbwheel.
- Coupons: the colour of the part they are cut from. Tools: any colour. They go on plates of whichever colour has room; the
  pocket coupon goes on a B plate because it must print like the B feeder disc.

The beam now carries v2's spout but stays A, as structure (BOM section 3). Every plate is a single colour, so neither printer
swaps filament mid-plate.

## Settings for every plate

- PLA, 0.4 nozzle, 0.20 mm layers, **3 walls**, 5 top and 3 bottom layers, grid or gyroid infill at the per-part value
  below. The infill values are the manifest's (`parts.<PRT>.infill`, BOM section 3).
- **Supports: none, on every part.** Each STL is already in its print orientation. `cad printcheck` confirms this for all 25:
  0 fails, every part fits the P1S. The accepted warns are short ledges under the 3.0 limit (floor latch barbs and
  controller tongue lips, flywheel nut-pocket roofs, body slivers) [parts]. The longest bridge is 18.2 mm, in the
  turntable's tunnel and hub roofs [parts].
- **Use the same filament, profile and settings for the coupons as for the parts.** They are cut from the real parts at
  whole multiples of 0.2 mm from each part's bed. So every snap catch falls on the same layer boundary as on the full part.
- **Elephant-foot compensation on** (about 0.15) for plate 0b. The gate's 0.5 detent slots run through the first layers
  (hotfix review N2).
- **Brim (5 mm) on:**
  - `jar_valve` (63 tall on 373 mm² of bed contact [parts]);
  - `nip_cover` (56 tall on 282 mm²);
  - `tilt_horn_adapter` (15 tall on 77 mm²);
  - the coupons `c1_beam_hook_post` (26 tall on 12 x 6.8) and `c1_beam_hook_beam` (32 tall on 15 x 15).
  - `nip_wheel` (184 mm²) is small; add a brim if your bed is marginal.
- **100 % infill:** flywheel (inertia and pinch-hub strength); nip leaf (a spring, printed flat so it bends in the layer
  plane); thrust ring; jar gate (its two detent fingers are cut through the blade).
- Nothing to drill or tap. No v3 screw threads into PLA: the motor and adapter screws pass clearance holes into the motor
  and the purchased adapter, the stud and pinch bolts run into nuts, and the centre screws into the servo splines (BOM
  section 2).

## Print order

1. **Fit tests first** (plates 0a and 0b, one on each printer, about 1.5 h).
   - Plate 0a: the snap coupons, the test hub gear and the real tilt horn adapter. Plate 0b: the real jar adapter, valve and
     gate, and the pocket coupon.
   - Do `MEASURE_FIRST.md` items 1 to 4 while the printers start on the pod. Every big plate depends on them:
     - the beam and crown (plate 3) on c1 and c3;
     - the turntable (plate 4) on c1 and c2;
     - the floor (plate 6) on c4;
     - the pinions on the horn test;
     - the feeder disc (plate 2) on `POCKET_D`.
2. **Launcher pod** (plates 1 and 2). The pod uses the launch rig's parameters, so you can check it against the rig you
   already printed (below). Plate 2 also carries the feeder disc, so settle `POCKET_D` (item 4) before it starts.
3. **Pan stage and feeder** (plates 3 and 4). Before them: c1 and c3 pass, and the servo body and horn are checked (items 5,
   6).
4. **Base** (plates 5 and 6). Before them, check:
   - the DeWalt adapter holes (base shell, plate 5);
   - the buck flange, the servo controller and the MotorGo (floor, plate 6; c4 passed).

| Step | H2D | P1S |
|---|---|---|
| 1 | Plate 0b, jar group fit test, 1.5 h | Plate 0a, snap coupons, 1.4 h |
| (fit tests, calipering and coupons: `MEASURE_FIRST.md` 1-4) | | |
| 2 | Plate 2, pod and disc terracotta, 2.5 h | Plate 1, pod grey, 3.6 h |
| (validate the pod) | | |
| 3 | Plate 3, beam and crown, 4.0 h | Plate 4, turntable, 5.8 h |
| 4 | Plate 5, base shell, 7.8 h | Plate 6, floor, 3.0 h |

If a change from `MEASURE_FIRST.md` alters a part, rebuild before printing that plate:
`cd ../blender && cad build build_assembly.py && cad check model.blend checks.json`. Then re-copy the changed STLs from `../stl/`
into the plate folder. Re-run `tools/fit_coupons.py` on a fresh copy of the model if the change touched a coupon's parent part.

## Validate the pod against the rig (after plates 1 and 2)

The pod shares the rig's parameters, but it is **not a copy of the rig's parts**. The same:

- the wheel: R35 land between R36 flanges, wheel plane x 21, D-shaft pinch hub, M3 x 20 pinch bolts;
- the motor face and the crush ribs;
- the rear-shaft magnet and the Plink pegs;
- the thumbwheel's Ø17 envelope.

Different from the rig (and from v2), in how it holds together:

- the motor screws clamp the body and the nacelle plate together; there are no nacelle screws;
- the encoder cap snaps in (2 in-plane arms) instead of 2 screws, and its flange seat sets the air gap;
- the hood hangs on printed Ø5 stubs, and the journal plate presses onto 3 crush-rib pegs (no hinge axle, no plate screws);
- the nip cover slides on a 45 deg dovetail with a detent, and the leaf root slides into its T-slot (no screws);
- the thumbwheel's nut slides in through a side slot, and its max-gap spigot is integral (v2's stop sleeve is gone);
- the nip stop pad is part of the body.

What to check on the bench (`ASSEMBLY.md` 6a-6g):

- the wheel slides onto the motor's D-shaft and clamps;
- the motor face screws (M3 pan x 10) sit below the web with daylight to the spinning wheel;
- the encoder cap clicks in and its flange seats flat (the Plink at the rig's air gap);
- the nip cover's detent clicks, and the thumbwheel turns through the finger slot between the two stops;
- a thick candy pushed into the nip by hand lifts the leaf and passes.

If the rig has given you `NIP_SET`, `G_IN`, leaf preload or tape-thickness numbers, put them into `params.py` and rebuild
**before** printing plate 2 (hood, body).

## Plates

### Plate 0a-fit-coupons-grey  (P1S, colour A warm grey)

Estimate: **1.4 h, 67 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `c1_beam_hook_post` | 1 | turntable's right-post top, x 37..52, y 11..26, z 226..253; bed = the z 226 cut (posts print upright, as on the turntable) | 20 % | 3 | 12 x 6.8 x 26 | 5 | 1.9 |
| `c1_beam_hook_beam` | 1 | beam over the right-front hook, same x, y; bed = the beam's top face (as on the beam), hook grows up | 30 % | 3 | 15 x 15 x 32 | 7 | 3.2 |
| `c2_hub_socket` | 1 | turntable centre, x and y within ±30, the whole 10 mm disc; bed = the turntable's own bed face | 20 % | 3 | 60 x 60 x 10 | 16 | 17.3 |
| `c3_crown_hook_crown` | 1 | crown round the rear-left hook, x -46..-26, y -32..-12, z 251..276; bed = the z 276 cut (crown prints top-down), hook grows up | 20 % | 3 | 20 x 20 x 24 | 5 | 2.6 |
| `c3_crown_hook_beam` | 1 | beam round the same hook slot, z 249..264; bed = the beam's top face | 30 % | 3 | 20 x 20 x 11 | 4 | 2.9 |
| `c4_card_guides` | 1 | floor, partition wall and both MotorGo guides, x -77..-1, y -96..-58, z 0..30; bed = the floor's own bed face | 15 % | 3 | 76 x 38 x 30 | 20 | 18.5 |
| `hub_gear` (test copy) | 1 | gear face on the bed, hub tube up (3 snap fingers and 3 dogs grow up; barb catch faces 0.5 ledges) | 40 % | 3 | 57 x 57 x 22.5 | 18 | 17.3 |
| `tilt_horn_adapter` | 1 | key end (-X) on the bed; 45 deg cone to the disc, horn pocket up, the 8 pins grow up from its floor | 60 % | 3 | 26 x 26 x 15 | 4 | 2.9 |

### Plate 0b-fit-jar-terracotta  (H2D, colour B terracotta)

Estimate: **1.5 h, 83 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `jar_gate` **(hotfix)** | 1 | flat, chamfer, tab and stop lug up; the detent finger bends in the layer plane | 100 % | 3 | 61.5 x 56.8 x 8.6 | 9 | 8.9 |
| `jar_adapter` **(hotfix)** | 1 | lid disc (glass side) on the bed, spout up | 40 % | 3 | 69 x 69 x 11.9 | 10 | 8.5 |
| `jar_valve` | 1 | skirt + baffle bottom on the bed; lug undersides 50 deg, snap fingers and pads grow up | 40 % | 3 | 71 x 69.5 x 63.1 | 55 | 56.1 |
| `tools/test_pocket_coupon` | 1 | flat, chamfered pocket rims up (print it like the feeder disc) | 40 % | 3 | 51.1 x 51.1 x 8 | 9 | 9.5 |

### Plate 1-pod-grey  (P1S, colour A warm grey)

Estimate: **3.6 h, 208 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `nacelle` | 1 | front plate on the bed, journal up (duct roof bridges 15 mm) | 25 % | 3 | 95.5 x 80.5 x 99.7 | 130 | 140.9 |
| `launcher_cover` | 1 | inner face on the bed; rebated edge steps in toward the top | 25 % | 3 | 109.9 x 119 x 4 | 23 | 24.8 |
| `journal_plate` | 1 | inner face on the bed; lap step, journal, socket and stop lug grow up | 30 % | 3 | 64.6 x 52.5 x 20.2 | 12 | 9.9 |
| `encoder_cap` | 1 | back face on the bed, spigot and pegs up | 40 % | 3 | 51 x 45.6 x 8.5 | 8 | 7.1 |
| `nip_cover` | 1 | +v end on the bed (v3: no screw block; dovetail tongue, skirt lip and detent arm); shell and end walls grow up as vertical walls; skirt bridges at the top; finger slot 22 x 8.3 in the -v end wall over the thumbwheel rim (v2-A1-02) | 30 % | 3 | 29.1 x 17.6 x 56 | 18 | 9.7 |
| `nip_leaf` | 2 | flat: strip's outer face on the bed, root block and pads up (bending stress in the layer plane) | 100 % | 3 | 21.9 x 42.6 x 7.8 | 4 | 3.5 |
| `tools/encoder_jig` | 1 | as exported: flat face on the bed (magnet glue jig, step 6b) | 20 % | 3 | 44 x 49.1 x 15.2 | 10 | 9.0 |

### Plate 2-pod-feeder-terracotta  (H2D, colour B terracotta)

Estimate: **2.5 h, 149 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `launcher_body` | 1 | left (motor) wall outer face on the bed; profile extruded so every wall is vertical | 25 % | 3 | 128.5 x 122.2 x 29.6 | 71 | 77.2 |
| `flywheel` | 1 | motor-side web face on the bed; rim and hub grow up (top flange has a 45 deg underside) | 100 % | 3 | 72 x 72 x 19.9 | 38 | 41.2 |
| `hood` | 1 | on its side face (profile extruded, all walls vertical; stud pocket has a vertex up) | 40 % | 3 | 75.3 x 58.8 x 25 | 13 | 11.7 |
| `nip_wheel` | 1 | outer face on the bed; integral max-gap spigot up; the tw nut slides in through the radial side slot (0.5 skin over it) | 50 % | 3 | 16.9 x 16.9 x 14.4 | 3 | 1.3 |
| `feeder_disc` | 1 | gear band on the bed, fins up | 40 % | 3 | 69 x 69 x 14 | 17 | 17.6 |

### Plate 3-beam-crown  (H2D, colour A warm grey)

Estimate: **4.0 h, 255 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `beam` **(hotfix)** | 1 | top face (feed floor, z 263) on the bed; spout, tongues and the 4 snap hooks grow up | 30 % | 3 | 216 x 96 x 37.5 | 89 | 98.5 |
| `feeder_crown` | 1 | top plane (z 322: socket rim + closed lobe roof) on the bed; lip, socket cone, leg cones, pocket floors print as floors or 45-50 deg cones; the 3 snap hooks grow up | 20 % | 3 | 151.5 x 96 x 70 | 120 | 132.2 |
| `feeder_pinion` | 1 | gear face on the bed, horn pocket up (the 8 pins grow up from its floor) | 60 % | 3 | 47.8 x 48 x 10.7 | 12 | 12.2 |
| `thrust_ring` | 1 | flat | 100 % | 3 | 88 x 88 x 2 | 11 | 11.9 |

### Plate 4-turntable  (P1S, colour A warm grey)

Estimate: **5.8 h, 376 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `turntable` | 1 | bottom face on the bed, posts upright (tunnel roofs and the hub roof bridge <= 23 mm; servo pocket, idler slot and U-slots open to the top; release-slot roofs bridge 4.2) | 20 % | 3 | 216 x 216 x 160 | 339 | 376.5 |

### Plate 5-base-shell  (H2D, colour A warm grey)

Estimate: **7.8 h, 503 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S no.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `base_shell` | 1 | upside down: deck face on the bed, walls up | 15 % | 3 | 241.2 x 240 x 87 | 398 | 441.1 |
| `pan_servo_mount` | 1 | plate top on the bed, pocket walls up | 30 % | 3 | 84 x 66 x 43.7 | 34 | 30.5 |
| `pan_pinion` | 1 | gear top on the bed, horn pocket up (the 8 pins grow up from its floor) | 40 % | 3 | 56.9 x 56.9 x 10.8 | 14 | 13.8 |
| `hub_gear` | 1 | gear face on the bed, hub tube up (3 snap fingers and 3 dogs grow up; barb catch faces 0.5 ledges) | 40 % | 3 | 57 x 57 x 22.5 | 18 | 17.3 |

### Plate 6-base-floor  (P1S, colour A warm grey)

Estimate: **3.0 h, 178 g** (geometry model, not sliced; includes 6 min plate start). Footprint check (bounding rectangles, 6 mm apart): H2D fits, P1S fits.

| STL | Qty | Orientation (already applied in the STL) | Infill | Walls | Size in print orientation (mm) | min | g |
|---|---|---|---|---|---|---|---|
| `base_floor` | 1 | flat, partition wall and bosses up (the v2 partition printed upright too: rear face was its bed) | 15 % | 3 | 240 x 240 x 85.5 | 172 | 177.9 |

## Plate folders

- `plates/0a-fit-coupons-grey/` holds `hub_gear_test.stl`, a copy of `hub_gear.stl` for the c2 test only. The c2 joint can't
  be released, so the test gear stays in its coupon. The fitted hub gear is on plate 5.
- `plates/1-pod-grey/` has `nip_leaf.stl` and `nip_leaf_spare.stl`, the same part twice: one fitted, one kept unloaded as the
  creep reference.
- Every other part is printed once.
- The coupons are written by `tools/fit_coupons.py` (run from `BUILD/` on a copy of `../blender/model.blend`). The two tools
  are `encoder_jig` (magnet glue jig, step 6b) and `test_pocket_coupon` (sets `POCKET_D`).
