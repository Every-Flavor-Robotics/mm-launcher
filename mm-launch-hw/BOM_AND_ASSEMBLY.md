# M&M Launcher Turret: BOM and Assembly (attempt 3)

All dimensions in mm. Source of truth: `blender/build_assembly.py` (parameters at the top). Printed parts are in `stl/` in print orientation (32 STLs: 31 parts plus the magnet jig). Automated checks: `renders/attempt-3/checks.json`. Results:

- all printed parts are manifold and fit the P1S;
- zero unintended interference at 15 poses (pan -90/0/+90 x tilt -3/0/22.5/45/46);
- zero fastener or cable overlaps across pivots, and zero fastener overlaps with purchased parts on the same pivot (this catches the adapter bolts against the battery);
- a 2.5 mm L-key reaches both flywheel pinch bolts at tilt 45 with the cover off, long leg swung -30 to +30 deg (10 of 10 positions clear);
- at least 3.0 mm from the tilting pod to the feeder plate, hopper and feeder-servo shroud from 0 to 45 deg;
- every traced drop reaches the descending rear of the tape at every tilt from 0 to 45 deg.

## 0. How it works (read this first)

- **Undershot flywheel.** The Ø70 PLA wheel sits on top, and a curved **backplate** (the brief's "hood") wraps under it. The wheel spins with its **bottom moving forward**, so the rear of the tape moves **down** into the nip. Candy drops through the tilt axis, down a chute behind the wheel, and meets the rear of the tape (ψ 66-85 deg behind bottom dead centre at every tilt). The tape drags it into the converging gap and launches it along the floor through the muzzle. Launch elevation = tilt + about 3 deg.
- **Motor direction:** set the MotorGo so that, viewed from the cover (+X) side, the wheel turns **clockwise** (bottom forward). Running it backwards throws candy back up the chute.
- **Compliant nip (new).** The backplate is hinged at its top end and is **not locked**. A hex-head stud sits head-down in a pocket on its back face and comes out through the rear underside of the guard. A knurled **thumbwheel** with a captive nut runs on the stud and rests on a flat seat on the guard. The thumbwheel is a **minimum-gap stop**: the plate can't close past it. A PLA **leaf spring** inside the terracotta **nip cover** presses the thumbwheel onto its seat with about **9 N**. The plate is held at the set gap with that preload, and a thick candy can push it **open** by lifting the thumbwheel against the leaf (3.9 N/mm at the stud). After 2.5 mm the leaf bottoms on the cover shell, which is the over-travel stop.
  - Adjustment range: **5.5 to 10.0 mm bare at BDC**, 0.48 mm of gap per turn of the thumbwheel. **Clockwise opens, counter-clockwise closes** (viewed from outside).
  - Operating setting: **6.5 mm bare = about 6.0 mm over 0.5 mm hockey tape**, about 1 mm squeeze on a 7 mm M&M, now sprung rather than rigid.
  - The bay still lets the plate swing to 12.5 mm, so a jammed candy can be cleared by hand.
  - At 9 mm and wider, a flat M&M never touches the tape (checks: 0 of 37 drops grip at 9 mm). Use those settings only for testing.
- **Tilt:** printed hard stops at -3 and +46 deg (lug on the journal plate against two stops on the right arm). **Clamp the firmware to 0..45 deg**, and **do not move tilt while a feed is in progress**: the drum passes 3 mm under the outlet spout.
- **Feeder index (corrected).** There are 6 pockets at 60 deg. **Park = servo position 0**: here the disc is **solid** over the outlet, because the pockets straddle it at ±30 deg, 7.5 mm clear. **To fire, move to +30 deg** (the pocket that was filling at 60 deg moves over the outlet and drops), **then return to 0**. Next shot: **-30 deg, then 0**. Alternate sides. Exactly one pocket crosses the outlet per fire command; see `feeder_index_park0.png` and `feeder_index_fire+30.png`. Both ends of the knock-off baffle are ramped 30 deg, so a candy standing on edge is pushed down, not sheared.

## 1. Purchased parts

| # | Part | Qty | Where | Notes |
|---|---|---|---|---|
| 1 | MotorGo Axis (ESP32-S3 BLDC driver) | 1 | Base, rear-left, vertical on the partition | Component side faces the partition. The USB-C plug passes straight through into the rear niche. |
| 2 | XTEAM XTI-3674 1900KV inrunner | 1 | Launcher nacelle | Lead block turned to point at the tilt axis. Three crush ribs at the rear of the bore centre the can. |
| 3 | Plink MT6701 encoder + JST 5-pin cable | 1 | Encoder cap at the rear of the nacelle | 1.0 mm air gap to the magnet. JST points up the lead slot. |
| 4 | Diametric magnet Ø6 x 2.5 | 1 | Glued to the motor's rear shaft end | Centred with `encoder_jig`, which locates on the motor's Ø8 rear access hole. |
| 5 | Hiwonder HTS-35H class bus servo + round 8-hole horn | 3 | Pan (base), tilt (right arm, under the housing), feeder (under the feeder plate, inside the shroud) | |
| 6 | Hiwonder bus servo controller (58 x 42) | 1 | Base, front-right | Switch, buttons and screw terminal face the right-wall notch. |
| 7 | DeWalt 20V battery adapter | 1 | Under the deck, rear-right bay | Through-bolted. Its corner holes get a Ø6.5 x 5.5 counterbore on the battery side for the nuts (see step 2). |
| 8 | DeWalt 20V battery (2Ah or 5Ah) | 1 | Rear-right bay, slides out of the right wall | 2.0 mm clearance each side, 1 mm lead-in chamfer. |
| 9 | 12 V buck converter, finned 73.8 x 73.8 x 31 | 1 | Base, left, fins up beside the louvres | |
| 10 | USB-C cable (straight plug) | 1 | MotorGo to laptop | Zip-tied to the niche anchor bar. |
| 11 | Hockey tape, 12-12.7 mm (1/2") wide | about 0.25 m | Flywheel land (12.8 mm between the flanges) | One layer, butt-joined on the trailing side. |
| 12 | 16 AWG silicone wire, red/black/yellow | 3 x 450 mm | Phase extensions | Solder (or use 4 mm bullets) to the motor leads cut to about 55 mm. The joints sit inside the straight trunnion bore. |
| 13 | Heat-shrink 6 mm | 3 x 25 mm | Over the phase joints | Stagger the joints 10 mm apart. |
| 14 | 3-pin servo bus leads | 3 | Controller to each servo | |
| 15 | 5-pin JST encoder extension | about 500 mm | Plink to MotorGo | |
| 16 | 4-wire UART lead (TX, RX, GND, plus a spare) | about 230 mm | MotorGo UART header to the servo controller UART | Pressed into the two floor clips with a dab of hot glue. |
| 17 | Rubber bumper feet Ø12 (optional) | 4 | Floor recesses | Or a hot-glue dot each. |
| 18 | Lazy-susan / 608 bearing | 0 | not used | The printed bearing ring is enough. Grease it lightly. |

## 2. Fasteners

All M3 unless noted. "ST" = self-tapping into a Ø2.5 printed pilot. Clearance holes are Ø3.4. Counterbores are Ø6.5 x 3.2, countersinks 90 deg x Ø6.8. All screws on visible faces sit flush (countersunk) or in counterbores.

| Use | Qty | Size |
|---|---|---|
| Motor face: heads in counterbores inside the guard, through the body wall and nacelle plate into the motor | 4 | M3 x 10 socket head (4 mm thread in the motor) |
| Nacelle to body (from inside the guard, under the wheel) | 2 | M3 x 12 socket head ST |
| Journal plate to body | 3 | M3 x 12 countersunk ST |
| Cover to body (all in front of the right arm at tilt 0 and 45) | 4 | M3 x 12 countersunk ST |
| Backplate hinge axle (from the left wall, through the backplate boss, threads 2.5 mm into the journal plate; it carries no axial load) | 1 | M3 x 30 countersunk |
| **Nip stud** (head-down in the hex pocket on the backplate's back face) | 1 | **M3 x 20 hex head (DIN 933)** |
| **Nip thumbwheel nut** (captive in the thumbwheel) | 1 | M3 nut |
| **Nip cover to the guard land** | 2 | **M3 x 16 socket head ST** |
| Encoder cap to nacelle | 2 | M3 x 12 countersunk ST |
| **Flywheel pinch bolts + nuts** (two-slot clamping hub, point-symmetric; tip 0.5 mm past the nut, 0.4 mm inside the hub) | 2 + 2 | **M3 x 20 socket head** + M3 nut |
| Feeder plate and arm caps into the arms (countersunk flush: the feeder disc runs over the right pair) | 4 | M3 x 45 countersunk |
| Arm feet to turntable (counterbored) | 8 | M3 x 10 socket head ST |
| Turntable to pan hub | 3 | M3 x 10 ST |
| Spine to turntable | 4 | M3 x 10 countersunk ST |
| Left bonnet to arm / right arm cover to arm | 4 / 2 | M3 x 10 / M3 x 12 ST |
| Tilt and feeder servo pocket flanges (into arm and cap; into the 6 mm plate) | 4 + 4 | M3 x 10 ST (feeder: 10 max so the tip stays inside the plate) |
| Tilt servo clamp, through the servo housing end wall | 2 | M3 x 16 countersunk ST |
| **Feeder servo clamp, through the feeder shroud floor** | 2 | **M3 x 16 countersunk ST** |
| Pan servo clamp | 2 | M3 x 10 ST |
| Pan servo pocket to deck posts | 4 | M3 x 14 ST |
| Hopper lugs (from under the plate, countersunk) | 3 | M3 x 12 countersunk ST |
| Floor plate to shell | 6 | M3 x 12 countersunk ST |
| **DeWalt adapter:** countersunk from the deck top, nuts in counterbores on the adapter's battery face. The tip ends 2.4 mm above the battery face. | 4 + 4 | **M3 x 25 countersunk** + M3 nut |
| Buck ears / MotorGo standoffs / servo controller (drill-to-fit) | 2 / 4 / 4 | M3 x 8 ST |
| Horn to adapter (from the horn's servo side, countersunk into the horn) | 4 per horn | M2 x 6 countersunk self-tapping |

Removed since attempt 2: the backplate clamp screws, the jack screws and their lock nuts.

**Tools:** 2.5 mm hex L-key (standard, 18 mm short leg), 2 mm hex key, Phillips #1, small pliers (to hold the adapter nuts), and a DeWalt drill. Drill bits: Ø1.6, Ø2.0, Ø3.2 and Ø6.5, plus a countersink bit. Also a soldering iron, superglue and hot glue. No wrench is needed.

## 3. Printed parts and print settings

PLA, 0.2 mm layers, 3 perimeters unless noted. **No part needs support material.** These spans print as bridges:

- bonnet channel roof (21 mm);
- horn-adapter recess roof (20 mm);
- nacelle duct roof (15 mm);
- turntable groove floors (14 mm);
- nip-cover skirt (24 mm);
- the base-shell niche.

Colours: warm grey = structure, terracotta = the launcher pod, its covers and accents. Filament and time are volume-based estimates from `checks.py`.

| STL | Qty | Print bbox | Orientation | Supports | Infill | g | h |
|---|---|---|---|---|---|---|---|
| `arm_cap_l.stl` | 1 | 30 x 48 x 14 | lying on its side face | no | 30% | 9 | 0.3 |
| `arm_cap_r.stl` | 1 | 30 x 48 x 14 | lying on its side face | no | 30% | 9 | 0.3 |
| `arm_cover_l.stl` (bonnet) | 1 | 156 x 41 x 12 | flange (arm side) down, channel open to the bed | no | 20% | 22 | 0.5 |
| `arm_cover_r.stl` | 1 | 72 x 41 x 8 | flange (arm side) down, channel open to the bed | no | 20% | 9 | 0.3 |
| `base_floor.stl` | 1 | 240 x 240 x 11 | flat, bosses up | no | 15% | 137 | 2.7 |
| `base_shell.stl` | 1 | 240 x 240 x 87 | upside down: deck face on the bed, walls up | no | 15% | 387 | 7.3 |
| `encoder_cap.stl` | 1 | 56 x 53 x 8 | back face on the bed, spigot (3 crush ribs) and pegs up | no | 40% | 9 | 0.3 |
| `encoder_jig.stl` (tool) | 1 | 44 x 49 x 11 | flange on the bed, plug and Ø7.8 spigot up | no | 40% | 9 | 0.3 |
| `feeder_disc.stl` | 1 | 112 x 112 x 14 | upside down: top face on the bed, drive boss up | no | 30% | 42 | 0.9 |
| `feeder_plate.stl` | 1 | 193 x 139 x 13 | upside down: top face on the bed, spout and groove up | no | 25% | 67 | 1.4 |
| `feeder_shroud.stl` **(new)** | 1 | 46 x 54 x 71 | rear face on the bed: walls, floor and both chamfer faces vertical or ≤ 45 deg | no | 20% | 25 | 0.6 |
| `flywheel.stl` | 1 | 72 x 72 x 20 | **motor-side web face on the bed**; rim and hub grow up (top flange has a 45 deg underside) | no | **100%** | 44 | 0.9 |
| `hood.stl` (backplate) | 1 | 76 x 66 x 22 | on its side (profile extruded); stud pocket has a vertex up | no | 40% | 11 | 0.3 |
| `hopper.stl` | 1 | 147 x 147 x 43 | upside down: top rim down | no | 15% | 52 | 1.1 |
| `hopper_lid.stl` | 1 | 149 x 162 x 6 | upside down | no | 15% | 45 | 0.9 |
| `horn_adapter.stl` | 3 | 26 x 26 x 12 | recess down, hex key up | no | 40% | 2 | 0.1 |
| `journal_plate.stl` | 1 | 70 x 62 x 22 | inner face down; lap step, collar, journal, stop lug up | no | 30% | 14 | 0.3 |
| `launcher_body.stl` | 1 | 129 x 130 x 28 | left wall outer face down; all walls vertical | no | 25% | 72 | 1.4 |
| `launcher_cover.stl` | 1 | 110 x 123 x 4 | inner face down | no | 25% | 26 | 0.6 |
| `nacelle.stl` | 1 | 96 x 80 x 106 | front plate down, journal up | no | 25% | 121 | 2.4 |
| `nip_cover.stl` **(new)** | 1 | 28 x 14 x 58 | screw-block end down; leaf, end walls and shell are vertical walls; skirt bridges at the top | no | 30% | 11 | 0.3 |
| `nip_wheel.stl` **(new)** | 1 | 17 x 17 x 5 | outer face down, nut trap up | no | 50% | 1 | 0.1 |
| `pan_hub.stl` | 1 | 57 x 57 x 14 | gear face down | no | 40% | 13 | 0.3 |
| `pan_pinion.stl` | 1 | 57 x 57 x 8 | flat | no | 40% | 12 | 0.3 |
| `servo_clamp.stl` | 3 | 45 x 39 x 4 | flat | no | 30% | 4 | 0.2 |
| `servo_pocket.stl` | 2 | 64 x 36 x 48 | mount face down | no | 30% | 21 | 0.5 |
| `servo_pocket_pan.stl` | 1 | 80 x 80 x 48 | mount face down | no | 30% | 36 | 0.8 |
| `tilt_servo_cover.stl` | 1 | 76 x 45 x 54 | end wall down, open side up (front-top chamfer is vertical in print) | no | 20% | 33 | 0.7 |
| `turntable.stl` | 1 | 224 x 224 x 12 | upside down: top face down, ring up | no | 15% | 151 | 2.9 |
| `turntable_spine.stl` | 1 | 114 x 32 x 4 | flat | no | 30% | 11 | 0.3 |
| `yoke_arm_l.stl` | 1 | 120 x 64 x 28 | lying on its outer face | no | 30% | 50 | 1.0 |
| `yoke_arm_r.stl` | 1 | 33 x 68 x 120 | **upright**, foot down (U bore open at the top; stop lugs on the inner face) | no | 30% | 49 | 1.0 |

Totals with quantities: about **1.54 kg** PLA and **32 h**. Every part fits the P1S (256^3).

Notes per part:
- `flywheel`: print at 100% infill (it's a 6,000 rpm rotor).
  - The web is now on the motor side, so the cup between hub and rim opens toward the cover. That is how the L-key reaches the pinch bolts.
  - The counterbores and nut traps open radially as U-channels, so there are no knife edges.
  - After printing, spin it on the motor at 2,000 rpm before taping. If it buzzes, sand the heavy side of the rim.
- `nip_cover`: print it in its free shape. The two pads on the leaf stand 2.3 mm proud of the thumbwheel face, which is the ~9 N preload once the cover is screwed down. PLA creeps. If the plate starts to chatter after months of use, reprint the cover (11 g) or glue a 0.5 mm shim on each pad.
- `nip_wheel`: press an M3 nut into the trap from the top while it is on the bed, and add a dab of superglue.
- `feeder_shroud`: the face toward the pod is the pod's swept envelope plus 3 mm, a cylinder about the tilt axis, so it is open toward the pod by design.
- `encoder_jig`: the Ø7.8 spigot ring is 0.85 mm thick (2 perimeters) around the Ø6.1 magnet pocket. That is inherent: the magnet sits inside the Ø8 access hole. It is a tool, used once.
- `nacelle`: the front plate is the bed face. The duct roof inside bridges 15 mm, so print it slowly.
- `journal_plate`: the 2 mm lap on its edge overlaps the cover's rebated edge, holding the cover's rear in without screws.
- `yoke_arm_r`: print it upright. The hard-stop lugs on its inner face have radial contact faces and a drafted outer arc.
- `hood` (backplate): print it on its side so the curved surface is all perimeters (smooth for the candy).

## 4. Assembly (one person)

### Base
1. Press 4 rubber feet (or hot-glue dots) into the floor recesses.
2. **DeWalt adapter.**
   - Check the four corner holes on the adapter's battery-side face. Each needs a counterbore Ø6.5 and 5.5 deep for the nut. If there isn't one, drill it with the Ø6.5 bit (3 mm of wall remains to the edge). Drill the holes through to Ø3.2 if they are smaller.
   - Turn the shell upside down and set the adapter into its fence under the deck, wire end toward the bay end wall.
   - Drop a nut into each counterbore, holding it with pliers. Drive 4 countersunk M3 x 25 down from the deck top into the nuts. The screw tips end 2.4 mm short of the battery face.
   - Thread the adapter wires through the slot in the bay end wall.
3. **MotorGo.** Fit it to the four standoffs on the partition, component side toward the partition, so the USB-C receptacle lines up with the rounded cutout. Fix it with 4 M3 x 8.
4. **USB-C.** Plug the cable through the niche from outside, straight into the receptacle (25 mm straight run), and zip-tie it to the anchor bar.
5. **Pan servo.**
   - Prepare the horn adapter on the bench (see "Horn adapters" below).
   - Press the horn and adapter onto the pan servo spline, and drive the horn's centre screw through the Ø6.5 hole in the hex key.
   - Slide the servo into the pan pocket and close the clamp (2 x M3 x 10).
   - Set the 36T pinion on the hex key.
6. **Pan hub.** Drop the hub gear up through the deck hole from below and check that it turns freely. Centre the servo (hub at 0 deg), then screw the pan pocket to the 4 deck posts so the pinion meshes.
7. **Floor plate.**
   - Screw on the buck converter (2 screws, wire bundle toward the centre).
   - Lay the servo controller in its 4 corner fences and mark the real hole positions through the board onto the dimpled bosses.
   - Drill Ø2.5 x 5 deep and fix the board with 4 M3 x 8.
8. **Wiring in the base.**
   - Adapter to buck input. Buck output to MotorGo VIN and to the controller screw terminal.
   - Controller bus port to the pan servo.
   - **UART:** a 4-wire lead from the MotorGo UART pins to the controller UART header, pressed into the two floor clips with a dab of hot glue.
   - Under the hub bore, leave a U-shaped service loop about 120 mm long in the launcher bundle (3 phase extensions, the encoder lead and 2 bus leads).
   - Plug the encoder JST and the phases in at the MotorGo.
9. **Close the base:** floor plate onto the shell with 6 countersunk M3 x 12.

### Pan stage
10. Feed the launcher bundle up through the hub bore. Set the turntable on the deck (bearing ring down, lightly greased) and screw it to the hub top (3 x M3 x 10).
11. Lay the bundle into the turntable grooves: phases, encoder and feeder bus to the left (-X), tilt bus to the right (+X). Screw on the spine (4 countersunk M3 x 10).
12. Screw the left and right yoke arms to the turntable (8 x M3 x 10 into the counterbored feet).

### Launcher pod (on the bench)
13. **Magnet.**
    - Push the motor into the nacelle bore from the rear, lead block first, sliding it along the slot toward the tilt-axis end. The three crush ribs at the rear of the bore should grip the can firmly; if they are too tight, scrape them with a knife. Stop when the motor face sits on the front plate.
    - Put a drop of superglue on the rear shaft end.
    - Drop the magnet into the `encoder_jig` pocket and wipe the pocket with a trace of oil so the glue doesn't stick to the jig.
    - Push the jig in until its **Ø7.8 spigot enters the motor's Ø8 rear access hole** and its face stops on the motor's rear face. The spigot, not the plug, centres the magnet on the shaft and bearing. The plug is relieved 0.35 mm all round.
    - Leave it 10 minutes, then pull the jig straight out. If the spigot bottoms before the face touches (shaft end flush), file the spigot down to 0.5 mm.
14. **Phase leads.**
    - Cut the motor's three leads to about 55 mm.
    - Solder the 450 mm extensions on, staggered 10 mm apart, and heat-shrink each joint.
    - Feed the extended leads up the nacelle's internal duct into the trunnion bore, and fish them out of the journal end with a hook. The three joints end up inside the straight bore (x -60 to -90), not at the bend.
15. **Plink.**
    - Press the PCB onto the 4 pegs of the encoder cap, components toward the motor and the JST toward the slot. Put a dab of hot glue on each peg tip.
    - Plug in the encoder cable and feed it up the slot and duct beside the phases.
    - Press the cap in (its spigot has 3 crush ribs) and screw it on with 2 countersunk M3 x 12.
    - Air gap: 1.0 mm nominal. If the shaft sits deeper than nominal, add a paper shim under the cap flange.
16. Hold the nacelle front plate against the body's left wall. Working from inside the guard, drive the 4 motor screws (M3 x 10) and the 2 nacelle screws (M3 x 12) into the counterbores.
17. **Backplate and nip stop.**
    - Set the hood (backplate) into its bay with its hinge boss over the hinge hole.
    - Screw the journal plate onto the body (3 countersunk M3 x 12).
    - Drive the hinge axle (countersunk M3 x 30) from the left wall's outside, through the backplate boss, into the journal plate.
    - From outside, push the **M3 x 20 hex-head stud** head-first through the Ø7.2 slot in the guard's rear underside. Turn it until the hex head drops into the hex pocket on the backplate's back.
    - Run the **thumbwheel** (nut side toward the guard) onto the stud until it touches the flat seat.
18. **Flywheel.**
    - Wrap one layer of 1/2" hockey tape on the 12.8 mm land, starting and finishing on the trailing side.
    - Put the two pinch bolts (M3 x 20) and nuts loosely in the hub.
    - Slide the wheel onto the D-shaft until the web is 1 mm off the wall.
    - Tighten both bolts with a standard 2.5 mm L-key. The short leg goes in along the bolt axis from the open (+X) side of the cup and the long leg points out toward you; there is room to swing it ±30 deg (`flywheel_lkey_access_tilt45.png`).
19. **Set the gap and fit the covers.**
    - Hold a 6.0 mm drill shank as a feeler between the tape and the backplate at the bottom, through the muzzle.
    - Turn the thumbwheel (clockwise opens, counter-clockwise closes) while pressing the stud tip in, until the shank just drags with the thumbwheel seated. That is about 6.5 mm bare, the operating gap.
    - Fit the **nip cover** over the thumbwheel (2 x M3 x 16 into the land). Its leaf now presses the thumbwheel onto the seat.
    - Fit the cover: slide its rebated rear edge under the journal-plate lap, then drive the 4 countersunk M3 x 12.

### Yoke and feeder
20. Prepare the tilt servo horn adapter on the bench. Lower the pod into the yoke: the nacelle journal into the left arm, the journal-plate journal into the right arm. Fit both arm caps.
21. **Tilt servo.**
    - Press the horn and adapter onto the spline and drive the centre screw through the key hole.
    - Slide the adapter's hex key into the journal-plate socket.
    - Screw the pocket flange to the right arm and cap (4 x M3 x 10).
    - Close the clamp, then fit the terracotta **servo housing** over it with 2 countersunk M3 x 16 through its end wall and the clamp.
    - The lead leaves through the notch in the housing's bottom into the right arm cover.
22. **Feeder servo.**
    - Prepare its horn adapter on the bench, press it onto the spline, and drive the centre screw through the key hole.
    - Fit the servo into its pocket and set the clamp under it.
    - Put the terracotta **feeder shroud** under the clamp and drive the 2 countersunk M3 x 16 through the shroud floor and the clamp into the pocket bosses.
    - Screw the pocket flange under the feeder plate (4 x M3 x 10). The shroud's open rim sits 0.3 mm under the plate. The servo body trails behind the feeder axis.
23. Lay the feeder bus lead in the plate's underside groove (hot-glue dots), from the left cap notch to the feeder pocket's flange notch.
24. Put the feeder plate on the two caps and drive the 4 countersunk M3 x 45 through the plate and caps into the arms. The heads sit flush, so the feeder disc runs clear over the right pair.
25. Fit the left bonnet over the journal end using 4 x M3 x 10. The bonnet now runs up flush with the feeder-plate top and covers the plate's left edge, so the feeder bus goes from the bonnet straight into the cap notch with no bare length. Fit the right arm cover using 2 x M3 x 12.
26. Drop the feeder disc onto the plate so its hex socket engages the adapter key, with the servo at 0 (solid disc over the outlet). Fit the hopper (3 countersunk M3 x 12 from under the plate) and the lid.
27. **Firmware.**
    - Tilt clamped to 0..45 deg, and no tilt moves during a feed.
    - Feeder: park 0, fire +30 → 0, next shot -30 → 0, alternating (section 0).
    - Flywheel turns bottom-forward.

### Horn adapters (all three servos, on the bench)
- Seat the horn in the adapter's 1.0 mm recess (it self-centres).
- Using the horn as a template, drill 4 of the 8 pilot dimples through with a Ø1.6 bit.
- Countersink the 4 horn holes on the horn's servo side, then drive 4 countersunk M2 x 6 from the horn side into the adapter. Add superglue on the interface. The heads sit flush, under the horn, against the servo.
- Press the assembly onto the spline, then drive the horn's centre screw through the Ø6.5 hole in the hex key.

## 5. Service (pod stays in the yoke)

- **Change the nip gap** (any tilt; easiest at tilt 0, from behind):
  1. Remove the 2 nip-cover screws (2.5 mm key) and lift the cover off.
  2. Turn the thumbwheel by hand: clockwise opens, counter-clockwise closes, 0.48 mm per turn. Press the stud tip in to reseat the wheel.
  3. Refit the cover. No wrench or lock nut is involved, and nothing is clamped.
- **Re-tape or re-tighten the flywheel:**
  1. Tilt to 45 deg.
  2. Remove the 4 cover screws, slide the cover forward-down out from under the journal-plate lap, then lift it off.
  3. Loosen the 2 pinch bolts with the L-key from the open side of the cup.
  4. Pull the wheel straight off along +X. At 45 deg it clears the right arm and the servo housing (checked over 140 mm of travel).
  - The backplate stays in place on its hinge axle and stud.
- **Encoder:** tilt to 45 deg so the encoder cap is fully in front of the left arm. Remove 2 screws and pull the cap and Plink straight back (checked clear over 10 mm).
- **Motor:** remove the flywheel, then the 6 screws from inside the guard. Lift the pod out of the yoke (caps off) to slide the motor out of the nacelle rear.
- **Temperature:** on the first runs, measure the motor can after 2 minutes at full speed. If it is over 50 C, open the three diamond vents under the nacelle with a Ø6 drill along their length, or add a second row.

## 6. Cable plan summary
- **Motor phases and encoder:**
  - Motor lead block, then the nacelle's internal duct. The joints are staggered inside the straight trunnion bore.
  - Out of the chamfered journal end (on-axis, twist only, across the tilt axis).
  - The left bonnet (10 mm deep), the turntable groove under the arm foot and spine, and the hub bore. The U service loop below the hub handles +/-120 deg pan.
  - Then to the MotorGo.
- **Servo bus:** two leads from the controller go up the hub bore.
  - One goes right: groove, right arm cover, the notch under the tilt servo housing, then the pocket channel.
  - One goes left: groove, up inside the bonnet (which now reaches the feeder plate), the cap notch, the plate underside groove, the feeder pocket's flange notch, and into the shroud. No bus cable is exposed.
  - The pan servo lead stays in the base.
- **UART:** MotorGo UART pins, two floor clips, then the servo controller UART header (about 230 mm).
- **Power:** adapter, then the buck (inside the base), then MotorGo VIN and the controller terminal.
- **USB-C:** MotorGo, straight through the partition, the niche, and out of the rear, zip-tied to the anchor bar.
