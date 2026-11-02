# M&M launcher v3: measure and fit-test before you print

Several model values are nominal: from the brief, a datasheet PNG, or a photo. Caliper the real part, compare, and change the
named value if it differs by more than the tolerance given. v3 adds a second kind of check. Most joints are now printed
snaps and slides, and their fits depend on your printer as much as on the model. So the first two plates (0a, 0b) are fit
tests, and the big plates wait for them. Items are in print order, so each one is due before the plate that depends on it
(`PRINT_PLAN.md`).

**After any change:** `cd ../blender && cad build build_assembly.py && cad check model.blend checks.json`. It must still say 0
fails. Then:

- copy the changed STLs from `../stl/` into the plate folders (the build rewrites every STL, so compare dates);
- re-run `cad py tools/fit_coupons.py <copy of model.blend>` from `BUILD/` if the beam, turntable, crown or floor changed;
- re-run `cad py tools/print_estimate.py` from `../blender/`.

Most values live in `../blender/params.py`. A few live in the shared component table
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
caliper the wrapped tape at step 6f; the min-stop margin is only 0.098 (8.098 against 8.0 [distances]).

## 1. Jar and band (before plate 0b: jar adapter and valve)

`params.py` `JAR_*` block. Never print glass threads; nothing printed touches the glass or the band. v3 raises the whole jar
stack 36 mm (`JAR_LIFT`), but the jar interfaces are v2's.

| Measure | Nominal | Param | Why it matters |
|---|---|---|---|
| Band outside diameter | 73.5 | `JAR_BAND_OD` | Band-to-feed-floor clearance: worst case 2.4 against a 3.0 design gap [stacks: jar band clears the feed floor]. A band over about 74 eats that gap. |
| Band top-lip opening (the hole in the band) | 58 | `JAR_BAND_LIP_ID` | The adapter spout (`ADAPTER_SPOUT_OD` 55) passes it with 1.5 a side. The spout shoulder (`SPOUT_SHOULDER_R` 28.3, Ø56.6) passes it with 0.7 a side. If the lip measures under 57.6, the shoulder gets tight in the lip: reduce `SPOUT_SHOULDER_R`. |
| Flat lid disc diameter (the one the printed disc replaces) | 69 | `ADAPTER_D` (`JAR_LID_D` is documentation only) | The printed disc must drop into the band like the lid did. |
| Flat lid thickness, and whether the band still screws on with a 1.6 mm disc | 0.6 / 1.6 | `ADAPTER_FLANGE_T` (brief: 1.6 or less) | Stack two coins or a 1.6 shim on the glass and screw the band on. It needs at least 1.5 turns of thread. If not, lower `ADAPTER_FLANGE_T` to 1.2. |
| Glass thread OD, mouth ID | 70 / 60 | `JAR_THREAD_OD`, `JAR_MOUTH_ID` | Clearance only: glass to crown 16.6 [distances: BUY_jar>PRT_feeder_crown]. |
| Jar body OD, height | 77 / 130 | `JAR_D`, `JAR_H` | Band to crown 14.5 [distances], and the tip check: worst 29.6 deg [stability]. |

## 2. Snap and slide fits: plate 0a (before plates 3, 4, 5, 6)

The joints most likely to fail are the vertical snaps whose catches have less than one layer of Z clearance: beam 0.05, hub
0.05, crown 0.1, valve 0.1 (review v3-A1-02). Slicer rounding of ±0.1 per face turns that into either interference (the hook
won't drop under its ledge and stays bent) or slack. Test them on your printer before you commit the turntable (6.5 h) and
the beam.

The coupons are crops of the real parts. `tools/fit_coupons.py` intersects each part with a box and exports it with the
part's own print rotation, so the snap prints on the same layers as on the full part. Print plate 0a in the same grey PLA,
with the same profile and settings, as the parts (`PRINT_PLAN.md`).

| Coupon | What to do | Pass | If it fails |
|---|---|---|---|
| `c1_beam_hook_post` + `c1_beam_hook_beam` (right post, front hook, `BEAM_HOOK` pos (43, 18), hotfix 2.2 barb) | Push the beam crop straight down onto the post crop, hook into the post-top slot. | One click. Then it lifts no more than about 0.1 (model: blocked at 0.1 [slide: A2 hotfix (v3-A1-01) beam hooks hold]). A flat blade, 2.5 wide or less, through the 2.8 release slot in the post's inner face pushes the barb out, and it lifts off. | Won't go fully down or click: the barb is riding the ledge. Slack after the click: the catch is too loose. In either case don't print plates 3 and 4. Take the measured gap to the planner (`BEAM_HOOK`; the review asks for 0.3 catch clearance and a 5-10 deg undercut). |
| `c2_hub_socket` + `hub_gear_test` | Push the test hub gear up into the socket (the coupon is the turntable's own 10 mm disc), dogs into their pockets. | 3 clicks (barbs 0.45). Then it can't be pulled out; the review's captive row stops it at 0.15. | This joint can't be released, so on the real machine a bad fit means a broken hub gear (step 2b). Take it to the planner (`HUB_FINGER` catch_z / ledge_z). The test gear stays in the coupon; cut it out or throw both away. |
| `c3_crown_hook_crown` + `c3_crown_hook_beam` (rear-left hook, `IF_CROWN_HOOKS` (-36, -22)) | Push the crown crop straight down through the beam-crop slot. | One click (barb 0.55 under the 254 pocket roof). It holds against a pull, and a blade from under the beam presses the barb in and it lifts off. | As c1 (`CROWN_HOOK`, `IF_CROWN_HOOK_SLOT`). |
| `c4_card_guides` + the real MotorGo | Slide the board down both guides to the slot-bottom stop. The coupon is the bottom 30 mm of the floor's partition and guides. Its slot mouths have no 1 mm lead-in, because the crop cuts below the full guide's top. | Slides by hand with light friction (1.77 PCB in a 2.07 slot, `MG_GUIDE`) and doesn't rattle. Nothing on the board touches a guide. | Tight: check the PCB thickness and width (item 6), then change `MG_GUIDE` clearance. Parts hit a guide: change `MG_GUIDE` engagement. |
| `tilt_horn_adapter` (the real part) + one of your horns | Press the horn into the adapter's pocket. | All 8 pins go into the 8 horn holes, and the disc drops flat onto the pocket floor, 0.2 below the mouth. | The bolt circle or hole size differs from the model (item 4). Fix `servo_horn_disc` before plates 3 and 5, which carry the feeder and pan pinions with the same pocket. |

## 3. Jar group: plate 0b (before plates 2 and 3)

Plate 0b is the real jar adapter, valve and gate, plus the pocket coupon. They print early because two hotfix-review items can
only be checked on printed parts. If they pass, build step 14 now with the empty jar (`ASSEMBLY.md` step 14) and keep the group.

### 3a. Gate finger slots (hotfix review N2)

The gate has two in-plane detent fingers: the closed one along its +Y edge (`GATE_FINGER`, 0.5 relief slots) and the
hotfix open one under the stop lug (`GATE_OPEN_DETENT`, a 0.5 inner slot and a 1.2 outer slot). The 0.5 slots are about 1.2
line widths at 0.4 mm. First-layer squish can bridge them and lock a finger. Some of the slot length sits inside the
candy column when the gate is closed, where shell chips can lodge.

**Why the gate itself is the coupon:** the review suggests `blender/tools/pocket_coupon.py`, but that script only cuts the
four feeder-pocket bores (Ø13.6 to 14.1). It has no slot to test. The gate is the smallest faithful test: 8.9 g, about 9 min
by the estimate, and it goes on the front of plate 0b.

Check, before the gate goes into the valve:

- hold it up to a light. Every slot must show daylight along its whole length, including where it opens at the blade's -X
  edge (hotfix review: the root is solid at x -10.8, the slot open at x -11.3);
- a 0.3 feeler must pass through the open finger's inner slot (the finger needs 0.3 of its 0.5) and through the closed
  finger's 0.5 slot;
- flex each finger sideways with a fingernail. The open finger must move at least 0.3 (`bump_d`), the closed one at least 0.4,
  and each must spring straight back;
- look at the R0.6 bump on the open finger. It needs 0.3 of engagement, and the review expects it to print rounded, giving
  0.15-0.2. A flat-topped or missing bump means the open click will be weak or absent (check it at step 14).

If a slot is bridged:

- clear it with a 0.3 feeler or a razor saw, from the -X edge inward;
- or reprint the gate with elephant-foot compensation on (about 0.15) and no ironing;
- if it still fuses, ask for the review's model fix: inner slot 0.5 → 0.8 (`GATE_OPEN_DETENT` slot_in), which has room
  toward y 0.7. The closed finger's 0.5 slots (`GATE_FINGER` slot) are just as unproven.

### 3b. Shoulder contact (hotfix review N1)

The jar's weight is meant to bear on the spout shoulder (R28.3) where it sits on the valve cheek tops. The shoulder's
underside is a 45 deg chamfer, so it bears only on a **line** at the ±Y pads' inner top edge (r 27.65). The hotfix's key-groove
notch (3.4 x 1.0) cuts 28 % of the +Y pad's line. A 0.1-0.2 print error on the pad face or the chamfer can lose the
contact. The adapter's weight then hangs on the 2 valve fingers, which bend across layers (11.0 MPa [flexures]).

After the valve clicks onto the spout (step 14, part 3):

- push the group together, then look along the ±Y pads against a light: no daylight;
- a 0.1 feeler must not enter between the shoulder and either pad top;
- the group mustn't rock or click further when you press the jar toward the valve.

If either pad shows a gap:

- don't fill or mount the jar. The joint has no service row, so this group is now scrap;
- ask for the review's fix before reprinting the adapter (8 g): a 0.5 flat on the shoulder underside over r 27.65..28.3 at
  the pads, or end the chamfer at r 27.65.

### 3c. Gate detents and key rib, on the assembled group

- **Closed:** one firm click (about 0.7 N to walk out).
- **Open:** about 1 mm before the hard stop at 52.35, a lighter click (about 0.4-0.5 N, hotfix review), and the gate stays
  open when you shake the group. No click means the bump printed too round (3a).
- **Key rib:** the key groove runs 1.0 past the rib (z 337 against the cheek top at 336 [distances: A2 hotfix (v3-A1-01)
  valve key rib top]), so the rib must not hold the adapter up. If the shoulder doesn't seat (3b), check the rib end first.

## 4. M&Ms and the pocket coupon (before plate 2: feeder disc)

- **Candies:** caliper 20. Measure the diameter across the flat face, and the thickness at the centre. Enter the min and max
  in `MM_D` (now 12.5..13.5) and `MM_T` (now 6.3..7.5).
  - `NIP_PASS`, the full-lift rows and `LIFT_FLOOR` follow `MM_T` max (params asserts it).
  - If `MM_T` max is over 7.3, run the thumbwheel at home or above, not at the min stop (v2 BOM section 8).
- **Pocket coupon** (`tools/test_pocket_coupon`, plate 0b, the same terracotta PLA and profile as the disc). It has four
  pockets, Ø13.6 / 13.75 / 13.9 / 14.1; pocket k has k + 1 rim notches. For each pocket:
  - one flat candy of the largest diameter must drop through;
  - two of the thinnest candies, stood on edge side by side, must not both enter.

  Set `POCKET_D` (now 13.75) to the smallest pocket that passes the first test and blocks the second. The `payload_fit` rows
  and the pocket stack row follow it [stacks: pocket over outlet at fire, worst 0.67 against 1.125].

## 5. Servo horn (before plate 0a: tilt horn adapter; plate 3: feeder pinion; plate 5: pan pinion)

**components.json `servo_horn_disc`.** The user confirmed a round 8-hole disc. **This now matters more than in v2.** v2 only
printed pilot dimples and you drilled through the horn. v3 prints 8 Ø2.0 pins (`PAN_HORN_PIN` R1.0 x 2.4) that must go into
the horn's 8 holes, so the bolt circle and hole size set the fit directly. The plate 0a `tilt_horn_adapter` is the test.

| Measure | Nominal | Value | Why it matters |
|---|---|---|---|
| Horn disc OD and thickness | Ø20 x 2.5 | `disc.d`, `disc.t` | The pocket is disc + 0.2 wide and 2.7 deep (`PAN_HORN_POCKET`). This fit centres the horn. |
| Bolt circle of the 8 holes, hole Ø | Ø14, Ø2.2 | `holes.bolt_circle_d`, `holes.d` | The Ø2.0 pins have 0.1 radial clearance in Ø2.2 holes. A bolt circle off by more than about 0.2 stops the horn seating. |
| Hub OD and height under the disc | Ø9 x 1.4 | `hub.d`, `hub.h` | Seats in the centre of the pocket. |
| Spline boss Ø on the servo | Ø6 (estimated) | `hiwonder_bus_servo.spline.boss_d` | The centre-screw access hole is Ø6.5. |

## 6. Servo body (before plate 3: crown; plate 4: turntable; plate 5: pan servo mount)

**components.json `hiwonder_bus_servo`**: body 40 x 20.14 x 40, spline 10 off centre, spline and idler boss 3.9 proud.

- **Height (spline face to the far face):** the feeder servo seats against the crown's lobe roof with 0.05 to spare
  (`LOBE_ROOF_Z`). A taller servo pushes the pinion down: it has 0.3 to the feed floor (review v3-A1-08).
- **Height over the tilt pocket:** the beam tongue sits 0.43 over the tilt servo's top (`TILT_TONGUE_Z0`) and keeps it captive
  at 0.75 [slide].
- **Width and depth:** the pockets are body + `SERVO_POCKET_CLR` 0.3. The crown lobe adds 4 crush ribs at 0.1 interference
  (`CRUSH_RIB`), so a servo 0.2 over 20.14 wide will be very tight in the crown.

## 7. MotorGo Axis (before plate 0a: c4; plate 6: floor)

No screws in v3: the board slides into 2 card guides on the floor's partition wall (`MG_GUIDE`), and a deck rib keeps it
down. Its holes no longer matter.

- **PCB thickness**, 1.77 (`MG_PCB_T`): the slot is 1.77 + 0.3.
- **PCB width along the 65 edge** (components.json `motorgo_axis.envelope`): the guides grip both 57 mm side edges.
- **Clear edge strips:** the guide covers 2.0 of the header face and only 0.5 of the component face (`MG_GUIDE`; the model's
  parts sit 0.7 / 1.2 from the edges). Check nothing on your board is closer than 0.5 to either side edge on the component
  face.
- **USB-C receptacle position** (`USB_STEP` (57.6, -14.0)): the plug must line up with the rear niche. Use a straight
  12.5 x 7 plug or smaller.
- **Phase pad group J6/J8** (`MG_PHASE_PAD_STEP` (34.0, -51.0), from the STEP): it sets where the base lead ends. If the pads
  are elsewhere, update it so the lead length stays honest.

## 8. Servo controller (before plate 5: base shell windows; plate 6: floor)

| Measure | Model | Param | Why it matters |
|---|---|---|---|
| PCB outline and thickness | 58 x 42 (confirmed) x 1.6 | `CTRL`, components.json `hiwonder_servo_controller.pcb` | The +0.4 fences locate it. The 2 floor tongues catch the top face with a 1.0 lip and hold it within 0.3 [slide: v3-A1 servo controller held down]. A thicker board won't click. |
| Strips along the two short (42) edges | free of parts over y 20..24 and 74..78 | `CTRL_TONGUE_Y`, `CTRL_TONGUE_WD` | The tongue lips sit on them. A part there stops the tongue. |
| Slide switch position along the long edge | y 40.6..58.7 in world (`CTRL_SW`) | `CTRL_SW`, `CTRL_WIN_SW` | The base shell's +X wall has a window for the switch lever (42..57) and one for the terminal. A switch 3 mm off misses its window. |
| Screw terminal position | y 59.6..72.5 (`CTRL_TB`) | `CTRL_TB`, `CTRL_WIN_TB` | Same, for the blue 2-pole terminal. |

The board sits on 4 Ø7 bosses. Don't drill them: the manifest still lists them as `drill_to_fit_boss`, but v3 mounts the
board with no screws (BOM item 6).

## 9. DeWalt adapter (before plate 5: base shell)

| Measure | Model | Param | Why it matters |
|---|---|---|---|
| Corner screw-hole inset from the adapter's edges | 6.0 (**estimated**) | `ADAPTER_HOLE_INSET` | 2 x M3 pan x 10 go down through counterbores at two diagonal corners (`ADAPTER_SCREWS` (0, 3)) into these holes. |
| Corner hole diameter and depth | unknown (components.json: "size unknown") | (none) | The model gives 8.5 of thread [fasteners: FST_adapter_0/1]. M3 needs a hole of about 2.5..2.8 to self-tap. If the holes are 3 or bigger, use M3 machine screws with nuts inside the adapter if you can reach, or epoxy. The tips must stay 3 or more above the battery face (5.46 now [distances: FST_adapter_0/1-BUY_battery]). These 2 screws carry the 620 g pack's hanging load (DESIGN_LOG joint table). |
| Adapter body | 86.6 x 59 x 23.4 | `ADAPTER` | The 4 deck fences (0.4 clearance) take the shear. |
| Battery rail stem inset | (10.5, 10.0), **estimated** | `BATT_STEM_INSET` | The corner holes must sit outside the rail channel. |
| Both battery packs fit | 115 x 76 x 70 envelope | `BATT` | The pack slides out +X with 1.6 to the floor [slide: battery out +X]. |

## 10. Buck converter (before plate 6: floor; plate 5: shell -X ribs)

No screws in v3: its flange strips slide +X under 2 hook rails on the floor (`BUCK_RAIL`), and 2 shell ribs hold the -X end.

| Measure | Model | Param | Why it matters |
|---|---|---|---|
| Body | 73.8 x 73.8 x 31 | components.json `buck_12v_finned.body` | The rails sit 0.3 outside its two edges; the end stops and shell ribs hold it at 0.4 [slide: v3-A1 buck rows]. |
| Flange thickness | 3.0 | `BUCK_FLANGE_T` | The lips sit 0.2 over the flange. A thicker flange won't slide in; a thinner one rattles (held down at 0.6 [slide: v3-A1 buck held down]). |
| Fin-free strip along each rail edge | 3.4 or more | `BUCK_RAIL` lip overlap | The lips cover 3.4 of the flange. Fins inside that strip stop the slide. |

## 11. Smaller items

- **USB-C plug overmold:** 12.5 x 7 or smaller, straight (`USB_STEP`, the rear niche).
- **Hockey tape:** 1 in wide. Trimmed to the 13.8 land, 0.5 or less over the land and at the butt joint (`TAPE_T`).
- **M3 hex nuts:** 5.5 AF, 2.4 thick. One must slide into the thumbwheel's side slot under its 0.5 skin; the other two sit in
  the flywheel's pinch-bolt pockets.
- **The 16 AWG phase wire's OD:** the Ø6 bundle (`BUNDLE_R` 3.0) carries three of them plus the encoder lead through the Ø12
  journal bore. Silicone 16 AWG is about 2.6..3.0 OD. If yours is fatter, try the bundle through a Ø12 hole in scrap before
  the pod goes in.
- **Bus splice:** practise one 3-to-1 joint on offcuts. The finished splice must be Ø10 x 20 or smaller (BOM 14a). It has
  1.0 to the hub-gear bore [distances: v2-A5-03].
