# Launch test rig

This rig is the attempt-3 launcher pod cut down to what answers the questions CAD can't:

- the nip squeeze on a real M&M,
- hockey-tape grip and exit speed versus rpm,
- the feed drop into the nip,
- bring-up of the XTEAM 3674 with the Plink MT6701 on the rear shaft and a MotorGo Axis in FOC.

It sits flat on a bench at a fixed 20 deg elevation (exit is about 23 deg). There is no pan, tilt, hopper or base.

## Files

| Path | What it is |
|---|---|
| `build.py` | Parametric build. Run `cad build build.py -- --render --estimate`. It imports `../../blender/build_assembly.py` (attempt 3, read-only) for every launcher dimension, so a change there flows into the rig on the next build. It also writes `checks.json`. |
| `stl/*.stl` | The six parts, in print orientation. |
| `launch_rig.blend`, `manifest.json` | The assembly model (joints `PIV_flywheel` and `PIV_hood`) and its parts list. |
| `cadcheck.json`, `cadcheck_summary.txt` | Check results. |
| `print_estimate.json` | The layer-by-layer time estimate (estimate, not sliced). |
| `renders/` | 800 px renders. `iso*.png`, `exploded.png`, `section_nip_wheel_plane.png` (nip, chute, funnel, with M&M markers), `section_nip_gap_5.png` and `section_nip_gap_12.png` (the gap extremes), `section_stud_leaf_plane.png` (thumbwheel, leaf, stop), `section_motor_encoder_axis.png`. |
| `renders/numbers.json` | Derived numbers: gap per turn, stud positions, leaf spring, encoder stack, key rig coordinates. |

## What is the same as attempt 3, and what changed

**Unchanged.** These come from the attempt-3 builders and STLs:

- **Flywheel:** `stl/flywheel.stl` has the same geometry as attempt 3's (same triangle count, volume and bounding box). That covers the D-shaft clamping hub, the M3 x 20 pinch bolts and the 12.8 mm tape land.
- **Thumbwheel:** `nip_wheel.stl` is identical to attempt 3.
- **Backplate:** same nip profile, hinge and stud position. One change: the stud's hex pocket now opens to the plate's +X edge (111 mm³ removed).
- **Guard cavities:** all from attempt 3 and cut from the same faces: wheel cavity, chute with fin and tongue, nip, muzzle, backplate bay, land and seat.
- **Motor mount:** the motor face screws through 8 mm of PLA, as in attempt 3 (nacelle plate 4 + body wall 4, here merged into one wall).
- **Encoder parts:** the crush ribs, the Plink pegs, the JST slot and the magnet position on the rear shaft are all attempt 3's.

**Changed to fit six parts and about 3 h:**

1. **Guard outline.** The attempt-3 body is a convex hull. Here it is shrink-wrapped to the cavities with a 2.6 mm skin and clipped to the attempt-3 profile.
2. **One-piece cover.** A 1.6 mm cover replaces the attempt-3 journal plate and cover. It carries the hinge-axle thread in a 6 mm boss.
3. **Leaf spring built into the guard.** It replaces the attempt-3 nip cover and keeps the same rate (3.9 N/mm), preload (9.0 N) and 2.5 mm over-travel. It is 28 mm wide x 1.84 mm thick (attempt 3: 21.9 x 2.0), so b·t³ is the same. A rigid 4.5 mm stop beam sits where the cover shell's inner face was.
   - It prints with the leaf in the layer plane: root stress is 19 MPa at preload and 40 MPa at the stop, running along the layers. cadcheck's flexure check passes it at 0 deg.
   - The thumbwheel rim is exposed on the +X side and from below, so **the gap is tuned with a fingertip and nothing comes off**.
4. **Gap range 5.0 to 12.0 mm bare at BDC** (attempt 3: 5.5 to 10.0). The bay swings from 4.8 to 12.5. Below 4.8 the bay cut would start eating the 1.6 mm chute tongue.
5. **Rear cup instead of the nacelle.** A 24 mm deep cup grips the rear of the can on the attempt-3 crush ribs.
   - Its shoulder seats on the motor's rear face, so the magnet-to-sensor gap depends on this part alone and no longer on the 74 mm motor length.
   - It carries the attempt-3 encoder-cap pegs and JST slot, the MotorGo standoffs and the rear foot.
   - The motor and Plink are turned 180 deg about the shaft so the leads point down, toward the MotorGo. The 4-fold screw pattern is unchanged.
6. **Encoder gap prints at 1.5 mm** (attempt 3: 1.0). It is a test knob: paper shims under the Plink close it (protocol B2).
7. **Funnel.** A 33 x 18.5 mm funnel sits on the attempt-3 drop column. Its throat is 16 mm wide, 23 mm above the old tilt axis, which is where the attempt-3 spout ended. Below it the drop runs through the attempt-3 fan, chute and tongue unchanged.
8. **Bench feet.** A front foot sits under the muzzle and a rear foot under the cup. Each has two open notches for M4 wood screws, and the flat pads can take G-clamps. The static tip angle is 23 deg.

## Print list

PLA, 0.2 mm layers, 2 walls, 5 top / 3 bottom layers, grid infill, **no supports**. Every part fits the P1S (and the H2D).

The times are **estimate, not sliced**: a layer-by-layer model in `build.py` (`estimate()`) using the published speeds of Bambu's 0.20 mm Standard P1S profile:

- walls 200/300 mm/s, solid infill 250, sparse infill 270, all capped at 21 mm³/s,
- first layer 50/105 mm/s,
- 80 % motion efficiency and 1.5 s per layer change.

cadcheck's flat 12 mm³/s model is shown next to it for comparison. Slice the STLs yourself for the real number.

| # | STL | Orientation (already applied in the STL) | Infill | Print time (estimate) | Filament | cadcheck model |
|---|---|---|---|---|---|---|
| 1 | `rig_guard.stl` | Outer (motor-side) wall face down; every feature is an extrusion straight up | 15 % | 77 min | 82 g | 1.66 h, 84 g |
| 2 | `flywheel.stl` | Motor-side web down (as attempt 3); 45 deg underside on the top flange | **100 %** (attempt 3; keeps the inertia the same) | 40 min | 44 g | 0.92 h, 44 g |
| 3 | `rig_cover.stl` | Inner face down, hinge boss up | 15 % | 21 min | 21 g | 0.50 h, 21 g |
| 4 | `rig_rear_cup.stl` | Encoder end face down; ring, standoffs and foot flange grow up | 15 % | 18 min | 17 g | 0.42 h, 17 g |
| 5 | `backplate.stl` | On its side face (as attempt 3) | 40 % | 12 min | 11 g | 0.30 h, 11 g |
| 6 | `nip_wheel.stl` | Outer face down, nut trap up (as attempt 3) | 50 % | 2 min | 1 g | 0.12 h, 1 g |
| | **Total** | | | **170 min + 2 plate starts = about 3.0 h** | **175 g** | 3.9 h incl. 6 min per part |

**Plates:**
- Plate A: guard + backplate + thumbwheel.
- Plate B: flywheel + cover + rear cup. Set the flywheel to 100 % infill as a per-object setting.

**If your slicer says well over 3 h,** print plate B first. The rear cup and flywheel are all you need for motor bring-up (protocol section B).

**Tool, not counted above:** for gluing the magnet, use the existing attempt-3 jig, `../../stl/encoder_jig.stl`. Its Ø7.8 spigot locates in the motor's Ø8 rear access hole, so it works on a bare motor.

## Fasteners

M3 unless noted. "ST" means self-tapping into a printed Ø2.5 pilot.

| Use | Qty | Size |
|---|---|---|
| Motor face. Heads go in counterbores inside the guard, floor at 4 mm, so they sit 2 mm below the wheel web. | 4 | M3 x 8 socket head (4 mm of thread in the motor, as attempt 3) |
| Cover to guard | 6 | M3 x 12 pan head ST (10 mm engagement) |
| Backplate hinge axle: from the guard's outer face, through the backplate boss, into the cover boss | 1 | M3 x 40 countersunk (7.5 mm of thread in the cover) |
| Nip stud, hex head in the backplate pocket | 1 | M3 x 20 hex head (DIN 933) |
| Thumbwheel captive nut (dab of superglue) | 1 | M3 nut |
| Flywheel pinch bolts and nuts (attempt 3) | 2 + 2 | M3 x 20 socket head + M3 nut |
| MotorGo Axis on the cup standoffs | 4 | **M2.5 x 8 pan ST** into Ø2.1 pilots. The board's holes measure **Ø2.5** in `reference/mg_axis.stl`, not the Ø3.4 the brief says, so an M3 won't pass. If your board really has Ø3.2+ holes, drill the pilots to Ø2.5 and use M3 x 8 ST. |
| Bench | 4 | M4 wood screws through the foot notches, or 2 G-clamps on the pads |

**Also:** superglue (magnet, thumbwheel nut), hot glue (Plink on its pegs, cable strain relief), and 1/2 in hockey tape.

**Tools:** 2.5 mm L-key, Phillips #1, calipers with a depth rod, and paper (about 0.1 mm per sheet) for the encoder shims.

## Assembly

1. **Magnet.**
   - Measure how far the rear shaft end sits below the motor's rear face (nominal 0.5, range 0 to 1).
   - Superglue the Ø6 x 2.5 diametric magnet to the rear shaft end using the attempt-3 `encoder_jig`: magnet in the pocket, spigot in the Ø8 access hole, face on the rear face.
   - Wait 10 min. Then measure how far the magnet face stands proud of the rear face (`m1`, nominal 2.0).
2. **Rear cup on the bench.**
   - Press the Plink onto the 4 pegs, IC toward the motor, JST toward the slot. Don't glue it yet (shims, step B2).
   - Measure the depth from the cup's shoulder face to the top of the MT6701 (`m2`, nominal 3.5).
   - The air gap is `m2 - m1` (nominal 1.5).
   - Screw the MotorGo to the 4 standoffs, component side facing the guard, USB-C toward the +X side.
3. **Cup onto the motor.** Slide the cup over the rear of the can, lead block in the keyway, until the shoulder touches the rear face. The 3 crush ribs grip; scrape them if they're too tight. Plug the Plink JST through the slot.
4. **Motor onto the guard.** Hold the motor face against the guard's outer wall, shaft through the Ø12 hole. From inside the guard (open +X side) drive the 4 M3 x 8 into the counterbores. Stand the assembly on its two feet.
5. **Nip stop.** The leaf is part of the guard, so the order matters.
   - Slide the thumbwheel in from the +X side between the seat and the leaf, lifting the leaf about 2.3 mm with a screwdriver. Centre it over the stud slot.
   - From inside the backplate bay, push the M3 x 20 hex-head stud tip-first out through the slot into the thumbwheel nut. Thread it in by holding the head and turning the wheel, until about 7.6 mm of tip stands above the seat (the operating gap, 6.5 mm bare).
   - Slide the backplate into its bay from +X so the stud head drops into the plate's open-sided hex pocket.
6. **Flywheel.** Wrap one layer of 1/2 in hockey tape on the land, starting and ending on the trailing side. Put the pinch bolts and nuts in loosely, slide the wheel on until the web is 1 mm off the wall, and tighten with the 2.5 mm L-key from the open +X side.
7. **Cover.** Fit the cover with 6 M3 x 12 pan ST. Then drive the M3 x 40 countersunk hinge axle from the guard's outer face, through the backplate boss, into the cover boss.
8. **Leads and bench.** Solder or connect the 3 phase leads (the stock 80 mm reach the pads) and plug the encoder lead into the MotorGo. Hot-glue the leads to the cup leg as strain relief. Screw or clamp both feet to the bench.

**Gap adjust.** Turn the thumbwheel by its knurl from +X or from below; nothing comes off.
- Each turn is 0.47 mm of gap at BDC. Clockwise seen from outside (from the leaf side) opens the gap, as in attempt 3.
- The stud tip in the stop window is a coarse gauge. It stands 6.0 / 7.6 / 9.2 / 11.3 / 13.4 mm above the seat at a bare gap of 5 / 6.5 / 8 / 10 / 12 mm.
- At the 12 mm end the stud tilts 5.2 deg and the wheel rocks on the edge of its seat. Always confirm the gap with a feeler.

## Test protocol

**Safety:**
- Wear safety glasses.
- Shoot into a cardboard box or a hung sheet 2 to 3 m away. In vacuum, a 10 m/s candy at 23 deg would fly about 7 m.
- Never put fingers past the muzzle or funnel while the wheel turns.
- The first spin-ups use a current-limited bench supply.

### A. Before power

- **A1.** Measure 20 plain M&Ms with calipers: thickness (minimum, mean, maximum) and diameter. Every gap below is reported as **squeeze = thickness − (bare gap − 0.5 mm tape)**.
- **A2.** Measure the real BDC gap with drill shanks or a feeler through the muzzle at the thumbwheel's two ends and at home. The model says 5.0 / 6.5 / 12.0. Write down the thumbwheel turns from the closed stop.

### B. Motor and encoder bring-up (flywheel off first, then on)

- **B1. Wiring.**
  - Phases go to the MotorGo motor pads; the Plink goes to an encoder port.
  - 12 V from a bench supply, current limit 1 to 2 A.
  - USB-C to the laptop.
- **B2. Air gap and field.**
  - With the motor unpowered, read the MT6701 angle while turning the shaft by hand. It should rise smoothly 0 to 360 deg per revolution with no jumps or reversals. Also read the field-strength status if your readout gives it.
  - Start at the as-printed gap (`m2 − m1`, about 1.5). Remove the cup, add one paper shim under the Plink, and re-test.
  - Repeat at 1.5 / 1.2 / 1.0 / 0.8 mm. Record raw-angle noise (standard deviation over 1 s at rest) and any field flags.
  - Keep the largest gap with a clean signal plus margin, then hot-glue the Plink.
- **B3. Pole pairs and direction.**
  - Run the pole-pair and sensor-direction check: SimpleFOC `initFOC` at `voltage_sensor_align` 1 to 2 V. 36xx inrunners are usually 2 pole pairs (4-pole), but use the measured value.
  - Check that a positive velocity turns the wheel **clockwise seen from the cover (+X) side**, so the bottom of the wheel moves toward the muzzle. Backwards throws candy up the chute.
- **B4. Open loop.** Bare shaft, voltage limit 2 V, up to about 500 rpm. Listen for rough spots, and check the encoder velocity matches the commanded speed.
- **B5. Closed-loop velocity,** first on the bare shaft, then with the flywheel and cover on.
  - Start with P = 0.1, I = 2, velocity low-pass Tf 0.01 s, a low voltage limit, and a gentle ramp.
  - Step 1000 → 2000 → 3000 → 4000 → 5000 → 6000 rpm.
  - Log the setpoint, measured rpm, its ripple, phase current and supply power. Note the rpm at which the encoder reading becomes noisy or the loop loses lock.
- **B6. Heat.** Run 5 min at 6000 rpm with no load and read the motor-can and MotorGo temperatures.

### C. Gap sweep (the main experiment)

Use the rpm values that ran clean in B5. Settings:
- **Gaps, bare at BDC:** 5.0, 5.5, 6.0, **6.5** (attempt-3 nominal), 7.0, 7.5, 8.0, then 9, 10, 12 to test the prediction that it no longer grips.
- **Speeds:** 2000, 3000, 4000, 5000, 6000 rpm. The tape surface runs at 7.4 / 11.2 / 14.9 / 18.6 / 22.3 m/s.

Run 10 single candies per cell, dropped one at a time into the funnel from about 5 cm above the mouth. Skip any cell with a crack rate above 30 %, and don't go to a higher rpm at that gap.

**Measuring exit speed cheaply:**
- **Slow-motion phone video.** This is the main method.
  - Shoot at 240 fps, camera perpendicular to the flight path and at least 1 m away to limit parallax, with bright light.
  - Tape a metre rule or a grid in the flight plane, 0.2 to 0.6 m in front of the muzzle. The muzzle exit floor is at x 21, y 127, z 62 mm in rig coordinates.
  - Speed is distance over 4 to 8 frames ÷ (frames / 240). At 15 m/s the candy moves 62 mm per frame, so keep at least 300 mm of scale in view.
  - Read the exit angle from the same clip.
- **Range.** Use this only as a repeatability check. Mark the first-bounce points on paper on the floor or on the backstop, and use the spread across the 10 shots.
  - The vacuum formula is R = v·cosθ/g · (v·sinθ + √(v²sin²θ + 2gh)), with θ = 23 deg and h = table height + 0.06 m.
  - Drag on a 1 g, 13 mm candy is about 1 g at 15 m/s, so range under-reads speed badly. Don't convert range to speed.
- **rpm dip.** From the encoder log: the dip per shot and the time to recover.

**Record per shot** (a spreadsheet row):
- date, candy batch and the A1 thickness statistics,
- bare gap (feeler), thumbwheel turns, rpm setpoint and measured,
- rpm dip and recovery ms, peak phase current,
- fed into the nip (y/n), stall point if not (funnel / chute / plate),
- exit speed, exit angle,
- shell cracked / chocolate on the tape, leaf lift (did the stud tip jump in the window?),
- tape wear after each block, and notes.

### D. Feed checks

- At 6.5 mm and a mid rpm, drop 30 candies, each in a different attitude: flat, on edge, tumbling.
- Count clean feeds, bounce-backs out of the funnel, and stalls on the chute rear wall or the tongue.
- Then repeat at the narrowest and widest gaps that gripped in C.
- cadcheck's fall-and-slide trace has every drop meeting the descending rear tape at 80 to 91 deg behind BDC for gaps of 5, 6.5 and 8. At 10 and 12 every drop stalls flat on the plate (no tumbling is modelled). This is what the drop is meant to confirm or refute.

### What each result changes in attempt 3

| Result | Attempt-3 parameter |
|---|---|
| Best squeeze (speed versus crack rate) and the gap range that grips | `HOOD_GAP` (6.5), `NIP_SET`, `HOOD_GAP_MIN/MAX`, the bay and `TONGUE_IN` |
| Candy slips (exit speed ≪ tape speed) or cracks / smears at a gap that should work | Leaf preload `LEAF_PRE` / `LEAF_T`, the tape choice, the tape land width |
| Exit speed versus rpm (slip ratio) | Target wheel speed (brief: 3000–6000), `WHEEL_R`, motor KV, the FOC voltage limit |
| rpm dip and recovery per shot | Flywheel inertia (`FW_RIM_T`, infill) and the minimum fire interval for the feeder index |
| Feed failures and where they stall | `REAR_WALL_ANG`, fin and tongue (`FIN_R*`, `TONGUE_*`, `LIP_PSI`), spout height `CAP_H` |
| Measured exit angle versus 23 deg | `FLOOR_FIX`, `MUZZLE_ROOF`, muzzle flares, the tilt offset in firmware |
| Clean air-gap window and noise at speed | `ENC_GAP`, `PLINK_IC_TOP`, the encoder-cap seat, jig pocket depth, magnet glue method |
| Pole pairs, alignment, loop gains, temperatures | MotorGo firmware defaults, current limits, nacelle vents |
| Whether the thumbwheel tunes easily by hand | The attempt-3 nip-cover access (see finding 3 below) |

## Attempt-3 problems found while building this

1. **Motor screw heads touch the spinning wheel.**
   - The attempt-3 body counterbores end at x 6 for "M3 x 10 socket head" (DIN 912 head = 3.0 mm), but attempt 3 modelled a 2.0 mm head.
   - A real head's top lands at x 9.0, exactly the flywheel web's face, so there is 0 mm clearance. The nacelle screws are the same.
   - The rig uses a counterbore floor at 4 mm with M3 x 8: still 4 mm of thread in the motor, and 2 mm of clearance.
2. **The nip-cover leaf prints standing up.**
   - Its 21 MPa (preload) and 44 MPa (stop) bending stress cross layer bonds. cadcheck's flexure check (finding A3-F2) fails that orientation.
   - The rig prints the leaf in the layer plane.
3. **Changing the attempt-3 gap means taking the nip cover off** (2 screws). The range is 5.5 to 10 mm, not "without disassembly".
4. **The MotorGo holes are Ø2.5 in `reference/mg_axis.stl`**, not Ø3.4, so attempt 3's "M3 x 8 ST through the board" won't go through. Check the real board.
5. **The nip frame (`nip_frame()`) is left-handed (det −1).**
   - Attempt 3's own `xform` flips the faces, but cadlib's `geom.xform` doesn't.
   - Any part rebuilt from attempt-3 nip geometry with cadlib comes out inside out and silently fails its booleans. That happened here first: the leaf hole and the pads went missing.
6. **Smaller items:**
   - Widening the bay below 5.5 mm starts cutting the 1.6 mm chute tongue (tongue clearance is 0.65 mm at 5.0, 0.49 at 4.5).
   - The stud's hex head sits tilted in its pocket, so at about 12 mm its rim stands about 0.3 mm proud of the plate. Attempt 3's R3.6 slot covers it; a narrower slot doesn't.
   - The flywheel's 45 deg top-flange underside is flagged by cadcheck as a 72 mm "ceiling" (it is exactly 45 deg). It is printable, but watch the first one.
   - cadlib's `render.section` (EXACT solver) floods on the guard. `build.py` has a Manifold-solver copy.

## cadcheck

Result: `cadcheck.json` and `cadcheck_summary.txt`. **PASS: 0 fail, 7 warn.**

**Coverage:**
- parts: manifold, bed fit, overhang, wall probe;
- interference and clearance over all four collections, with `PIV_flywheel` and `PIV_hood` swept over 5.0–12.0 mm plus 0.5 deg of overtravel;
- fasteners: engagement, nut pairing, access per assembly step;
- service: re-tape the flywheel, re-seat the MotorGo;
- 2 slide-out checks, the fall-and-slide drop test, the gap distances and the encoder gap;
- 2 tolerance stacks, the leaf flexure, stability, and cables.

**Key numbers:**
- Gap at the backplate's BDC point: 5.02 / 6.49 / 12.06 mm at the closed end / home / open end. Squeeze at home is 1.01 mm with the leaf declared compliant.
- Encoder air gap 1.50 mm. Tip angle 23 deg.
- Flywheel pinch bolts: the L-key swings 100 deg with the cover off. Every screw reaches with a straight driver or the L-key.

**The 7 warns:**
- the flywheel's 45 deg flange (attempt 3);
- cover edges below 1.6 mm (it is a 1.6 mm plate);
- guard wall 1.27–1.31 mm at the attempt-3 tongue tip and at a lip on the fan's front edge;
- stud 0.58 mm to the guard at the 12 mm end;
- the stud tip standing 4.6 mm proud (the gap indicator, by design);
- the two declared tolerance stacks: air gap worst case 0.65 against 0.5 (RSS 0.31), centring worst case 0.40 against 0.3 (RSS 0.20). Both are measured and shimmed in B2.

**Not checked:** hole diameters, wrench access to nuts, dynamic loads, cable bend radius, aesthetics.
