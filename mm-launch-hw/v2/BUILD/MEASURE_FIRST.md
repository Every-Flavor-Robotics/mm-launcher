# M&M launcher v2: measure before you print

Several model values are nominal: from the brief, a datasheet PNG, or a photo. Caliper the real part, compare, and change the
named value if it differs by more than the tolerance given. Items are in print order, so each one is due before the plate
that depends on it (`PRINT_PLAN.md`).

**After any change:** `cd ../blender && cad build build_assembly.py && cad check model.blend checks.json`. It must still say 0
fails. Then copy the changed STLs from `../stl/` into the plate folders; the build rewrites every STL, so compare dates.

Most values live in `../blender/params.py`. Two items live in the shared component table
`~/code-stuff/alex-3d-skills-pin/components/components.json`, which `parts/*.py` read through `placeholders.py`. Those are
marked **components.json**. That file belongs to the skills repo and other projects may read it; to change it for this machine
only, add an override in `params.py` and point the part module at it (one line per value).

## 0. Already checked on the launch rig (pod, plates 1 and 2)

The pod shares these with the rig, so whatever you measured there applies:

- `MOTOR_D`, `MOTOR_L` (35.9 x 74);
- `REAR_SHAFT_RECESS` (0.5, range 0..1);
- the rear access hole Ø8 (`JIG_SPIGOT_D` 7.9);
- `MAGNET_D` x `MAGNET_T` (6 x 2.5);
- the Plink peg / hole fit (`PLINK_PEG_D` 2.4, `PLINK_HOLE_D` 2.5).

If the rig gave you nip numbers (`NIP_SET`, `G_IN`, `LEAF_*` preload, `STUD_L`), enter them before plate 2. **`TAPE_T` 0.5:**
caliper the wrapped tape at step 6f; the min-stop margin is only 0.098.

## 1. Jar and band (before plate 3: jar adapter, valve, feeder housing)

`params.py` `JAR_*` block. Never print glass threads; nothing printed touches the glass or the band.

| Measure | Nominal | Param | Why it matters |
|---|---|---|---|
| Band outside diameter | 73.5 | `JAR_BAND_OD` | Band-to-feeder-housing clearance: worst case 2.4 against a 3.0 design gap [stacks: jar band clears the housing]. A band over about 74 eats that gap. |
| Band top-lip opening (the hole in the band) | 58 | `JAR_BAND_LIP_ID` | The adapter spout (`ADAPTER_SPOUT_OD` 55) must pass it with 1.5 a side. If the lip measures under 57, reduce `ADAPTER_SPOUT_OD` to lip - 3. |
| Band height | 13 | `JAR_BAND_H` | Detent tab clearance under the band lip: 1.0 [distances: v2-A5-01]. |
| Flat lid disc diameter (the one the printed disc replaces) | 69 | `ADAPTER_D` (`JAR_LID_D` is documentation only) | The printed disc must drop into the band like the lid did. |
| Flat lid thickness, and whether the band still screws on with a 1.6 mm disc | 0.6 / 1.6 | `ADAPTER_FLANGE_T` (brief: 1.6 or less) | Stack two coins or a 1.6 shim on the glass and screw the band on. It needs at least 1.5 turns of thread. If not, lower `ADAPTER_FLANGE_T` to 1.2. |
| Glass thread OD, mouth ID | 70 / 60 | `JAR_THREAD_OD`, `JAR_MOUTH_ID` | Clearance only (glass to crown 16.6). |
| Jar body OD, height | 77 / 130 | `JAR_D`, `JAR_H` | Feeder cover clearance 7.6 and the tip check (`JAR_MASS_*`). |

## 2. M&Ms and the pocket coupon (before plate 3: feeder disc)

- **Candies:** caliper 20. Measure the diameter across the flat face, and the thickness at the centre. Enter the min and max
  in `MM_D` (now 12.5..13.5) and `MM_T` (now 6.3..7.5).
  - `NIP_PASS`, the full-lift rows and `LIFT_FLOOR` follow `MM_T` max (params asserts it).
  - If `MM_T` max is over 7.3, run the thumbwheel at home or above, not at the min stop (BOM section 8).
- **Pocket coupon** (printed on plate 2, same PLA and slicer profile as the disc). It has four pockets, Ø13.6 / 13.75 / 13.9 /
  14.1; pocket k has k + 1 rim notches. For each pocket:
  - one flat candy of the largest diameter must drop through;
  - two of the thinnest candies, stood on edge side by side, must not both enter.

  Set `POCKET_D` (now 13.75) to the smallest pocket that passes the first test and blocks the second. The 4 `payload_fit` rows
  and the pocket-diameter rows follow it. Move the rows' 13.65..13.85 window with it.

## 3. Servo horn (before plate 4: feeder pinion; plate 5: tilt horn adapter; plate 7: pan pinion)

**components.json `servo_horn_disc`.** The user confirmed a round 8-hole disc.

| Measure | Nominal | Value | Why it matters |
|---|---|---|---|
| Horn disc OD and thickness | Ø20 x 2.5 | `disc.d`, `disc.t` | The printed recess is disc + 0.2, 1.0 deep (`HORN_RECESS`). This is the fit that centres the horn: too tight and it won't seat, too loose and it isn't centred. |
| Bolt circle of the 8 holes, hole Ø | Ø14, Ø2.2 | `holes.bolt_circle_d`, `holes.d` | Printed as pilot dimples only. You drill through using the horn itself as the template, so an error here only moves the dimples. Check before drilling. |
| Hub OD and height under the disc | Ø9 x 1.4 | `hub.d`, `hub.h` | Seats in the centre of the recess. |
| Spline boss Ø on the servo | Ø6 (estimated) | `hiwonder_bus_servo.spline.boss_d` | The centre-screw access hole is Ø6.5. |
| Servo body | 40 x 20.14 x 40, spline 10 off centre | `hiwonder_bus_servo.body`, `spline.offset_from_body_centre` | The servo pockets in `pan_servo_mount` (plate 9), `post_R` (plate 6) and `feeder_crown` (plate 4) are body + `SERVO_POCKET_CLR` 0.3. |

## 4. MotorGo Axis holes (before plate 9: base partition)

- **The STL shows Ø2.5 holes** (`reference/mg_axis.stl`, measured by the launch rig). The brief and components.json say Ø3.4.
  The model uses M2.5: `MG_SCREW` "M2.5_cap", `MG_HOLE_D` 2.7, `MG_PILOT_D` 2.1.
  - If your board's holes are **Ø3.2 or more**, set `MG_SCREW` "M3_cap", `MG_HOLE_D` 3.4, `MG_PILOT_D` 2.5, and use M3 x 10
    cap screws.
- Hole spacing: 58.0 x 49.0 (components.json `motorgo_axis.holes.rect`, from the STEP). Confirm it.
- Phase pad group J6/J8 position, `MG_PHASE_PAD_STEP` (34.0, -51.0) in STEP coordinates: not in any datasheet, taken from
  the STEP. It sets where the base lead ends, 0.722 above the board. If the pads are elsewhere along that edge, update it so
  the lead length stays honest.

## 5. Servo controller (before plate 7: base shell windows; plate 8: floor bosses)

| Measure | Model | Param | Why it matters |
|---|---|---|---|
| Mounting hole positions | 4 holes on 51 x 35, centred, Ø3.2 (from a photo, **unconfirmed**) | components.json `hiwonder_servo_controller.holes` | The floor has solid Ø7 bosses with a centre-punch dimple only. Lay the board in its +0.4 pocket and drill through its real holes (M3 x 8 pan ST). Changing the value only moves the dimples. |
| Slide switch position along the long edge | y 40.6..58.7 in world (`CTRL_SW`) | `CTRL_SW`, `CTRL_WIN_SW` | The base shell's +X wall has a window for the switch lever (42..57) and one for the terminal. A switch 3 mm off misses its window. |
| Screw terminal position | y 59.6..72.5 (`CTRL_TB`) | `CTRL_TB`, `CTRL_WIN_TB` | Same, for the blue 2-pole terminal. |
| PCB outline | 58 x 42 (confirmed) | `CTRL` (pocket) | The +0.4 pocket locates the board. |

## 6. DeWalt adapter (before plate 7: base shell)

| Measure | Model | Param | Why it matters |
|---|---|---|---|
| Corner screw-hole inset from the adapter's edges | 6.0 (**estimated**) | `ADAPTER_HOLE_INSET` | The 4 x M3 x 20 countersunk self-tappers go down from the deck top into these holes. |
| Corner hole diameter and depth | unknown (components.json: "size unknown") | (none) | M3 self-tapping needs a hole of about 2.5..2.8 with 8 or more of depth. If the holes are 3 or bigger, the screws won't bite: use M3 machine screws with nuts inside the adapter if you can reach, or epoxy. Tips must stay 3 or more above the battery face (4.56 now) [distances: FST_adapter-BUY_battery]. |
| Adapter body | 86.6 x 59 x 23.4 | `ADAPTER` | Fence pocket in the deck. |
| Battery rail stem inset | (10.5, 10.0), **estimated** | `BATT_STEM_INSET` | The corner holes must sit outside the rail channel. If they don't, use M3 x 12. |
| Both battery packs fit | 115 x 76 x 70 envelope | `BATT` | The pack slides out +X with 1.6 to the floor. |

## 7. Buck converter (before plate 8: floor)

| Measure | Model | Param | Why it matters |
|---|---|---|---|
| Flange hole spacing, hole Ø | ±33.4 on one axis, Ø3.8 (read off a PNG) | `BUCK_HOLE_Y` | Floor bosses and the 2 x M3 x 8 pan ST. |
| Body | 73.8 x 73.8 x 31 | components.json `buck_12v_finned.body` | Floor pocket, and airflow round the fins. |

## 8. Smaller items

- **USB-C plug overmold:** 12.5 x 7 or smaller, straight (`USB_STEP`, the rear niche).
- **Hockey tape:** 1 in wide. Trimmed to the 13.8 land, 0.5 or less over the land and at the butt joint (`TAPE_T`).
- **M3 hex nuts:** 5.5 AF, 2.4 thick (the traps are 5.7 AF).
- **The 16 AWG phase wire's OD:** the Ø6 bundle (`BUNDLE_R` 3.0) carries three of them plus the encoder lead through the Ø12
  journal bore. Silicone 16 AWG is about 2.6..3.0 OD. If yours is fatter, try the bundle through a Ø12 hole in scrap before
  the pod goes in.
