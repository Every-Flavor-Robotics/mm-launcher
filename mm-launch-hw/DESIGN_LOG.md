# M&M Launcher Turret: Design Log

## Plan revision (attempt 1, before modeling): brief change notices applied

The architecture below (electronics + battery in the base, hopper + feeder on the pan stage, motor/wheel/hood tilting around a drum-shaped feed opening on the tilt axis) is kept. These items replace the matching parts of the original plan:

1. **Encoder on the motor's rear shaft (change notice 1).** The Ø6 x 2.5 diametric magnet is glued to the rear shaft end through the Ø8 end-cap access hole (shaft end 0.5 mm recessed by default, parameter). A printed **motor cradle** (front plate sandwiched between the motor face and the launcher wall by the 4 motor screws, a saddle under the can, and a rear ring that hugs the can) carries a bolt-on **encoder cap** behind the motor. The cap's spigot fits the same Ø36.3 bore as the can, so the Plink is coaxial with the motor body by construction. The PCB sits component-side toward the magnet on four Ø2.3 pegs (the same peg idea as `prior_plinkholder.stl`), with a nominal 1.0 mm air gap; gap is tuned with paper/printed shims under the cap. The rear ring and cap are slotted on top so the phase-lead block and the JST plug both exit upward. The flywheel hub no longer carries anything.
2. **MotorGo USB-C is vertical (change notices 2 and 4).** The board is imported from `reference/mg_axis.stl` and stands vertically on an internal partition near the rear-left of the base, component side facing the partition, so the USB-C plug passes straight through a rounded cutout in that partition (12.5 x 7 overmold + 1 mm all round). Behind the partition is a closed **USB niche** open only to the rear of the base: the plug and its 25 mm straight length sit inside the base footprint, the cable leaves straight out the back (no bend needed), and a zip-tie anchor bar inside the niche takes cable tugs. The board's standoffs are 12.5 mm (they sit on the component side, which must clear the 12.2 mm tallest part); the 7.25 mm header pins point into open interior space.
3. **Servo horns, controller, battery (change notice 3).** One shared **horn adapter** design (Ø26 disc, Ø20.2 x 1.0 horn recess, 8 pilot dimples on the Ø14 bolt circle, 12 AF hex key) is used on all three servos; the driven parts (pan pinion, tilt journal, feeder disc) carry a matching hex socket. All three servos sit in the same **servo pocket + clamp** design (pan uses a wider flange variant). The servo controller (58 x 42) sits on four solid Ø7 bosses with only centre-punch dimples at the guessed 51 x 35 pattern, plus four corner fences 0.4 mm off the PCB edge. The battery envelope is 115 x 76 x 70; it slides out of the right wall of the base onto the DeWalt adapter, which is screwed under the deck.
4. **Tilt structure.** The launcher is a hanging pod: a printed **trunnion tube** runs from the launcher body's left wall over the motor to the left yoke arm (its bore is the cable path across the tilt axis), and the launcher cover carries the right journal with the servo hex socket. A **feeder plate** bridges the yoke caps above the drum and carries the hopper and feeder servo, closing the yoke into a rigid portal frame.

## Architecture (decided before attempt 1 modeling)

World frame: X right, Y forward (muzzle direction at pan 0), Z up, origin on the table under the pan axis. Units mm.

### What lives where

| Stage | Contents |
|---|---|
| **Static base** (tray + deck + rear lid, 236 x 253 mm) | DeWalt adapter + battery (rear-right bay, battery slides out of the right wall), 12 V buck (rear-left chamber with its own chimney: low wall louvres in, lid slots out), MotorGo Axis (left, on standoffs, port slot in the left wall along its whole edge), Hiwonder servo controller (front-left, switch/terminal window in left wall), pan servo (servo #1, offset 54 mm from the pan axis, drives the turntable through a 1:1 printed spur pair) |
| **Pan stage** (turntable, rotates +/-120 deg) | Two yoke arms with split pillow-block caps, tilt servo (servo #2) in a sleeve on the +X arm, feeder base bridging the arm caps, feeder servo (servo #3) hanging under it, rotary pocket disk, hopper, lid |
| **Tilting launcher** (0 to +45 deg) | Launcher body (motor-side wall, wheel guard, chute, funnel drum, muzzle) + bolt-on cover (encoder side), adjustable hood + shim, flywheel, 3674 motor + rear cradle, encoder PCB + clamp, tilt coupler, -X tilt pin |

Why the motor/wheel/hood tilt and the hopper does not: the wheel/hood/muzzle geometry must be fixed relative to each other, but a hopper that tilts 45 deg loses 45 deg of wall steepness. Keeping the hopper on the pan stage keeps its walls at their printed angle (vertical lower barrel, 60 deg flare) at every tilt.

All electronics stay in the base: low centre of gravity, the USB-C port never moves, and the buck/MotorGo get real airflow. The price is that motor phases (extended), the encoder cable and the servo bus must cross the pan axis; only phases and encoder cross the tilt axis.

### Tilt axis placement and the feed path (works 0 to 45 deg)

* The tilt axis T sits directly above the chute, about 70 mm above and 30 mm behind the wheel centre W. The launcher hangs below T like a pendulum (stable, small servo torque).
* The top of the launcher around T is a drum of radius 20 mm centred on the tilt axis. A fan-shaped funnel opening is cut into the drum. Because the drum surface is a cylinder about the tilt axis, it never moves relative to the fixed feeder plate 2 mm above it, whatever the tilt.
* The feeder outlet (Ø16) in the pan-stage feeder base is directly above T. The M&M falls into the drum opening at every tilt: the opening spans -29 to +81 deg about vertical in launcher frame, which covers the outlet column at both 0 and 45 deg.
* Chute walls: rear wall leans 5 deg (85 deg slope in launcher frame), front funnel wall 45 deg. World slopes: rear wall 85 deg at tilt 0 and 40 deg at tilt 45; front funnel wall 45 deg at tilt 0 and 90 deg at tilt 45; chute 85 deg to 40 deg. Every surface the candy touches stays at 40 deg or steeper.
* Nip entry: the chute drops the M&M onto the rear-top of the wheel (about 50 deg behind top dead centre), where the tape surface moves forward-up. The hood's flared lead-in lip starts at 24 deg behind top. The hood is concentric with the wheel from 18 deg back to TDC, then runs straight forward as the muzzle roof. Exit is tangent at TDC, horizontal in launcher frame, so the launch elevation equals the tilt angle.
* The hood is a separate shoe that slides vertically (+/-1.5 mm, 9 to 12 mm gap before tape) in slotted holes through both side walls. A printed shim between the hood and the guard roof sets the maximum gap, so the M&M load presses the hood against a known stop.

### Encoder (no rear shaft)

The flywheel hub carries a Ø10 nose that pokes 0.9 mm through a Ø13 hole in the cover. A Ø6 x 2.5 diametric magnet is glued into a pocket in the nose tip, coaxial with the D-shaft bore. The Plink PCB sits component-side-in on four printed Ø2.3 pegs (its Ø2.5 holes, 16 mm square) on standoff pads on the cover's outer face, so the MT6701 faces the magnet across a 1.0 mm gap. A printed clamp plate presses on the PCB back with two M3 screws, so service means removing two screws. The JST connector points toward the tilt axis, and the cable leaves between the cover and the PCB.

### Cable plan

* **Pan axis:** the turntable bolts to a hollow gear-hub (Ø28 bore) that turns in the deck. Every pan-crossing cable passes down the hub bore and hangs in a U service loop under the hub inside the base. With 1:1 gearing, pan is +/-120 deg (the full 240 deg servo range), and the bundle only twists.
* **Tilt axis:** the phase bundle (motor to MotorGo, extended with 16 AWG and 4 mm bullets) runs in the motor cradle trough under the motor, then up a recessed groove on the body's -X face. It hops into the -X arm's inner groove about 25 mm below T, where a slack pocket absorbs the 0-45 deg swing. The encoder cable does the same on the +X side (rib channel on the cover, then the +X arm groove).
* **Servo bus:** controller, then up the hub to the +X arm groove, the tilt servo, and the feeder servo under the feeder base. A second leg goes to the pan servo inside the base. No servo cable crosses the tilt axis.
* **Power:** adapter wires go through the divider to the buck; buck output goes through the cross-wall opening to MotorGo VIN and the controller screw terminal.
* **USB-C:** MotorGo to the left-wall port slot, out to the laptop. The board mounts 0/180 deg on a symmetric standoff pattern. Its left edge lines up with a full-length wall slot, and its other edges face open interior, so USB-C reaches the outside from any edge.

### Load paths

* Pan: the turntable rides on a raised Ø120-132 bearing ring on the deck (grease, optional lazy-susan). The gear-hub turns in the Ø40.6 deck journal. The gear underside traps the deck, so the turntable cannot lift. The servo only supplies torque through the pinion.
* Tilt: a printed pin (-X) and a Ø36 printed journal boss on the cover (+X) ride in split pillow blocks (arm + cap). The servo drives through a printed hex coupler (24 AF) screwed to its metal horn, which slides axially into the hex socket in the launcher boss, so the spline carries torque only.

## Attempt 1

Built the full assembly in `blender/build_assembly.py` (parametric, ~1700 lines, Manifold-solver booleans), wrote `blender/checks.py`, exported 29 STLs, rendered `renders/attempt-1/`. Checks: all 35 printed objects (29 unique STLs) manifold, all fit the P1S, **zero unintended interferences at 9 poses** (pan -90/0/+90 x tilt 0/22.5/45), static tip angle >= 44 deg at every pose, hopper ~300 M&Ms (60 required).

### Final layout (world X right, Y forward, Z up)
- **Base 240 x 240 x 90** (shell printed upside down + removable floor plate). Rear-right: battery bay, battery slides out of the right wall onto the adapter screwed under the deck. Left: buck converter beside low intake / high exhaust louvres. Rear-left: MotorGo on a partition, USB niche behind it. Front-right: servo controller on drill-to-fit bosses with a switch/terminal notch in the right wall. Front-centre: pan servo in a pocket hung from four deck posts, driving the hub through a 1:1 36T m1.5 gear pair (pan +/-120 deg).
- **Pan stage:** Ø224 turntable on a printed bearing ring, two yoke arms with split pillow caps, a feeder plate bolted across the caps (portal frame), feeder disc, hopper, lid.
- **Launcher (tilts 0-45 deg about T at z = 212):** Ø70 PLA flywheel (14 mm tape land between 1.6 mm flanges) on the 3674 D-shaft (set screw + 5.7 AF nut trap); body + cover enclose the wheel; motor in a lozenge cradle on the left with the encoder cap behind it; trunnion tube from the body to the left arm (its bore carries the cables); right journal + servo hex socket on the cover.

### Changes from the plan, and why
1. **Encoder moved to the rear shaft** (change notice 1). Cradle bore and encoder-cap spigot share the Ø36.3 motor bore, so the Plink is coaxial by construction; four Ø2.3 pegs (idea from `prior_plinkholder.stl`) locate the PCB. Measured from `plink_encoder.stl`: holes Ø2.5 on a 16 mm square, MT6701 top 3.25 above the PCB back, JST is the tallest part (4.6) on one short edge. With the shaft 0.5 mm recessed the magnet face is at x = -76, IC at -77 (1.0 mm gap), and the JST clears the motor's rear face by 1.65 mm. The JST points up, beside the lead block, both into a slot in the ring/cap.
2. **Hood geometry corrected.** My first build used a hood wrapping 62 deg behind TDC; the section showed it sat right in the drop column under T. Reverted to the plan's intent: hood concentric 0-18 deg, flared lip to 26 deg, and the M&M drops past the lip onto the tape ~55-60 deg behind TDC, where a vertical rear wall keeps it on the wheel (rear wall to flange gap < 7 mm so it cannot fall behind). Hood adjusts **vertically** in slots (+/-1.6 mm) with 1.6 mm shims: 3/2/1 shims = 8.9/10.5/12.1 mm gap before tape.
3. **Tilt sweep clearance cut.** The first interference run showed the guard top hitting the feeder plate and hopper from 22.5 deg up (up to 1200 mm3). The guard outline is now the convex hull minus the launcher-frame image of the plate/hopper zone at every 1.5 deg from 0 to 45 deg, so it clears by construction. The feeder plate's front edge is at y = 13 over the launcher. Side effect: a concave notch in the guard top in front of the fan (visible in the side view).
4. **Feed fan** on the drum spans -25 to +65 deg so the whole Ø16 outlet column is inside it at both tilt extremes; the fan's front edge is a radial cut square to the hood bay so no knife-edge slivers remain.
5. **MotorGo** (change notices 2 and 4): imported `mg_axis.stl`; measured PCB top 1.77, tallest part 12.2, pins to -7.25, extra through-hole stubs 1.3-1.6 under USB and power. Board faces the partition on 12.5 mm teardrop standoffs (component side needs 12.2 + clearance; pins point into open space). The plug (modelled as a 12.5 x 7 x 25 overmold) runs straight through the cutout into a 36 x 36 x 30 niche and out of the rear wall. Checks confirm the overmold does not touch the board.
6. **One horn adapter for all three servos** (change notice 3) with a shared servo pocket + clamp (pan uses an 80 x 80 flange variant to reach posts outside the pinion). Pocket has a molded lead channel on its clamp-end wall and a flange notch so servo leads are never loose.
7. **Battery** modelled as 115 x 76 x 70 with a 12 mm rail stem that nests in the adapter (the only whitelisted overlap besides spline-in-horn). The bay's rear-right corner is open so the corner fillet does not pinch the pack.
8. **Cables:** added a lead duct (motor to trunnion window), left bonnet (journal end to turntable groove), right arm cover, a cap notch + plate-underside groove for the feeder bus, and turntable grooves under a spine. Servo bus runs as two leads from the controller (same bus) instead of a daisy chain across the tilt axis.
9. **Wall-thickness probe** in `checks.py` (ray from each triangle centroid) found and I fixed: screw holes within 1 mm of edges (caps, spine, cover screws on the wrap, servo-pocket flange narrower than its Ø28 adapter hole), counterbores breaking into the turntable centre hole and the hopper flare (hopper lugs moved to the rear, screws now come up from under the plate), cavity knife-edges in the launcher body, and a flywheel nut trap 1.4 mm from the bore.

### Known limitations / for the next attempt
- The feed itself (drop onto tape behind the lip, 9-12 mm gap vs a 7 mm M&M as specified) is geometric, not tested.
- Guard top notch from the sweep cut looks unresolved; could be styled as a deliberate chamfer.
- DeWalt adapter is assumed to accept M3 screws in its four corner holes; if not, a printed strap is needed.
- The controller photo shows the 5 bus ports on the 42 mm edges (the brief says long edges); the corner fences leave both pairs of edges free, so either is fine.
- Remaining wall-probe flags are involute tooth tips (m1.5) and one grazing sample on the lead duct's 2.2 mm slanted wall.
- Bridges up to 21 mm (arm covers, horn recess roof) are used instead of supports.

## Attempt 2

Review of attempt 1 scored 5/6/5. Its blockers were the feed and the arm-cap screw under the feeder disc. Its majors were: no real nip, the horn-adapter sequence, no tilt margin, the launcher had to come out for service, magnet centring, and the unfinished pod. I kept the overall architecture (electronics and battery in the base, hopper and feeder on the pan stage, the drop through a drum on the tilt axis) and the parametric script. I rebuilt the launcher geometry and patched everything around it. Results are in `renders/attempt-2/checks.json`.

### 1. Feed and nip (blocker): from an overshot hood to an undershot hinged backplate
The root cause was structural, not a tuning problem. With the hood above the wheel, the only way in is behind the hood, and there the tape runs upward. The drop comes through the tilt axis and leans 45 deg back in the launcher frame at full tilt, so at high tilt the candy always reached the wheel's rising rear.
- I flipped the nip. The wheel (Ø70, R35 land) now sits on top, and a curved backplate wraps under it from 112 deg behind BDC to 3 deg past BDC. The wheel turns **bottom-forward**, so the whole rear half of the tape moves down into the nip. Wherever the candy touches the rear tape, the tape draws it in. The exit is along the floor at BDC, at tilt + 3 deg.
- New wheel position: W = (37, -52) from the tilt axis, with the tilt axis raised to z 222. The chute sits behind the wheel. Its front wall follows the wheel at 1.5 mm from the flange down to a 1.6 mm fin that ends at psi = 100 deg. Its rear wall runs at 81 deg, which is 36 deg in world at tilt 45. It ends in a 1.6 mm tongue that laps 1.1 mm inside the backplate's top end (shingled), so no edge faces the flow. The tongue inset comes from the backplate's swept envelope over its whole hinge range. Without the tongue, the tracer stalled every drop at the joint at 30-45 deg, so this lap is essential.
- Backplate profile: concentric from 0 to 78 deg, then a quadratic funnel opening to 21 mm at 112 deg. It is **hinged at its top end** (M3 axle) and set by **two jack screws** with lock nuts at psi 45, on a 63 mm lever. It is locked by a clamp screw each side through arc slots. Range at BDC: 5.5 to 12.5 mm, at 0.48 mm per turn. The hinge keeps the funnel top fixed, so the shingle holds at every setting, and it moves the bite zone almost as much as BDC (0.85x at 60 deg). A straight slot would distort the gap along the arc.
- **As-modelled gap: 6.5 mm bare**, about 6.0 mm over tape, so about 1 mm of squeeze on a 7 mm flat M&M. I deviated from the brief's "9-12 mm" because the tracer shows 0 of 37 drops grip at 9 mm at any tilt (a 7 mm candy lying on the plate never touches the tape). The 9-12 range is still reachable.
- Fixed exit floor below the plate's lowest setting, so no adjustment slot shows at the muzzle. The muzzle roof and floor have 4 mm 45 deg flares. The fan front edge widens to +75 deg, and the drum rear edge to -27 deg.
- **New drop tracer in `checks.py`.** It casts 37 rays across the Ø16 spout. They fall, slide along walls (stalling below 20 deg), and record the first tape contact. A sliding candy counts as touching the tape when the local gap is 7 mm or less with no wall in between.
  - At the operating setting, all 37 drops at tilt 0, 15, 22.5, 30 and 45 first meet the **descending rear tape at psi 65-85 deg**, with no stalls.
  - At 9 mm, all stall flat on the plate (reported, not hidden).
  - Images: `feed_trace_tilt0_operating.png`, `feed_trace_tilt45_operating.png`.

### 2. Arm-cap screws under the feeder disc (blocker)
All four cap screws are now countersunk M3 x 45, flush with the plate top (90 deg countersinks), so the disc clears them. `checks.py` now tests every fastener and cable against every solid on a different pivot, which is how this was missed before: 0 overlaps at 15 poses. That check also caught the motor screws pointing the wrong way. They now point -X from counterbores inside the guard, M3 x 10.

### 3. Service with the pod in the yoke (major)
- The right journal moved off the cover onto a **journal plate**. The plate closes the drum, chute and hinge side, carries the collar, journal, hex socket and hard-stop lug, and is screwed to the body with 3 screws. It stays in the yoke.
- The **cover** now has no through-features and 4 countersunk screws, all in front of the right arm at tilt 0 and 45. Its rear edge is rebated under a 2 mm lap on the journal plate. The parting line runs as an arc around the journal, leaves it tangentially, and meets the top chamfer at 90 deg. Below the journal it runs down and back at 45 deg, so neither part has a knife edge.
- Sweeps in `checks.py`, all at tilt 45 and all clear:
  - the cover slides 90 mm in its own plane, forward-down;
  - the flywheel comes off 140 mm along +X, past the right arm and the servo housing;
  - the encoder cap comes off 10 mm along -X.
  Gap changes need no disassembly (jack screws).

### 4. Tilt margin and hard stops (major)
- Hard stops: a lug on the journal plate and two lugs on the right arm's inner face, with radial contact faces. The right arm now prints upright, with its bore an open U at the top. Contact is at -3 and +46 deg. Firmware clamps 0..45, and tilt is locked out during a feed (BOM section 0).
- The feeder plate is raised to 30 mm above the axis, with a Ø22 spout down to 23 mm, so the drum-to-spout gap is 3 mm at every tilt.
- The feeder moved back (axis y -45, disc R56, hopper R58, now about 376 candies). Its servo was turned so the clamp ears trail behind.
- The tilt sweep now runs from -5 to 50 deg in 2.5 deg steps, including fasteners and cables. Pod to feeder plate, hopper and feeder servo: **3.0 mm at 0 deg, at least 3.0 mm from 0 to 45, 3.26 mm at 45 deg.** The only closer approaches are designed running fits (journals in bores 0.2, collars 0.2, adapter in the pocket hole) and the stop faces.
- The guard's top is now one straight chamfer face from the drum top to the wheel wrap, across the full pod width. The convex hull leaves out the drum arc between 0 and 71.7 deg, which the tilt-45 drop column needs clear. The sweep-cut V-notch is gone.

### 5. Horn adapters (major)
A Ø6.5 hole runs on-axis through the hex key. The horn is fixed to the adapter on the bench with countersunk M2 from the horn's servo side, the assembly is pressed onto the spline, and the centre screw is driven through the key. BOM steps 5, 20, 21, 22 and the "Horn adapters" section say the same thing. The pocket walls are relieved to 0.8 mm around the turning horn; the sweep had found 0.3 mm.

### 6. Encoder (major)
- New `encoder_jig.stl` (Tools collection, exported). It is a Ø36.1 plug for the nacelle bore with a Ø6.1 x 2.0 pocket that centres the magnet on the shaft end while the glue cures. It is BOM step 13.
- The Plink frame is rotated so its JST points up the lead slot. Air gap is still 1.0 mm, coaxial by construction.

### 7. The pod's look (major) and detailing (minor)
- The motor cradle, lead duct and trunnion became one **nacelle**. It is a capsule (R26.5 round the motor, R17 round the tilt axis) holding the motor, an internal lead duct, the trunnion bore, collar and left journal. No motor can, lead or duct gap shows, and the encoder cap closes its rear.
- The tilt servo sits under a terracotta **housing** that is arm-width and flush with the cap top. It is held by the two longer clamp screws, with an end-wall vent and a lead notch.
- Edge breaks are 1.0 mm on every printed part (0.5-0.8 only on the horn adapter, journal ends and backplate). Corner radii: 6 mm everywhere except the base footprint (16 mm, the one large radius) and the 3 mm cap tops. A 6 mm corner there cut into the screw holes.
- Visible screws are flush or counterbored: feeder plate, cover, journal plate, encoder cap, servo housing, spine, floor, arm feet and bonnet.

### 8. Minor items
- **Baffle:** both ends ramp at 30 deg, so a candy standing on edge is pushed down. Oscillating 0 <-> 60 index documented.
- **Leads:** motor leads are cut to about 55 mm, with staggered heat-shrunk joints inside the straight trunnion bore. The bonnet is 10 mm deep, the journal bore exit has a 4 mm chamfer for the bend, and the journal end is 0.5 mm off the bonnet.
- **UART:** a 230 mm 4-wire lead in two printed floor clips (`CAB_uart`).
- **Battery and adapter:** battery bay 2.0 mm per side with a 1 mm lead-in chamfer. The adapter is through-bolted with M3 x 30 and nuts.
- **Flywheel:** a two-slot clamping hub on 12 mm of shaft, with two point-symmetric M3 pinch bolts (self-balancing). The web is on the cover side with windows lined up for the L-key. The flange lip is 1.6 mm with a 45 deg underside. Tape land is 12.8 mm.
- **Checks:** 15 poses, cross-pivot fastener and cable checks, the tilt sweep with a feeder-stack clearance metric, the drop tracer, service sweeps, and section renders using the Manifold solver (the EXACT solver failed on the flywheel section).
- Wall-probe flags I fixed: cap screw versus corner radius, the cover-R flange corner, foot counterbores, UART clip, encoder-cap countersinks, flywheel lip, backplate around the clamp pilot (now 6 mm thick), the tongue tip (squared), and the drum crescent at the fan's rear edge. Remaining flags are gear-tooth tips (1.54) and a 1.47 bevel corner on the body near the tongue.

### Numbers
Mass is 2.85 kg with a 5Ah pack. Minimum static tip angle is 41.5 deg (pan 90, tilt 46). Printed parts are 1.46 kg and about 30 h. All 29 STLs fit the P1S: 28 parts plus the jig.

### Known limitations / next
- The tracer is a point-particle model. It does not tumble a 13 x 7 lentil. Bite at 6.0 mm over tape and exit-speed consistency need a physical test with the jack screws.
- Reaching the hinge axle's journal-plate end needs the pod out of the yoke. It only matters if the backplate itself must come out, not for re-taping or gap changes.
- The cover's lower-rear corner has no screw. It is held by the lap and the clamp screw.

## Attempt 3

The attempt 2 review scored 6/5/6. It had one blocker: the L-key couldn't reach the flywheel pinch bolts. It had three functional majors: the feeder double-fed, the pinch bolts were too short, and the nip was rigid. It also had minors on the adapter bolts, the jig datum, gap-adjust access, a bare bus cable, exposed jack hardware and form language. I kept the architecture and the parametric script and edited them in place. Results are in `renders/attempt-3/checks.json`: all pass, with 0 unintended interferences at 15 poses, 0 cross-pivot or same-pivot fastener overlaps, L-key access clear at 10 of 10 positions, a 41.3 deg tip angle, about 1.54 kg and 32 h, and 32 STLs, all on the P1S.

### 1. Flywheel pinch-bolt access (blocker) and bolt length (major)
I took the reviewer's first fix.
- **The web moved to the motor side** (x 9 to 14.1, full R36, so it doubles as the -X flange). The cup between hub (R13.5) and rim (R31.5 inner, 3.5 mm rim) now opens toward the cover.
- **The bolt plane moved to x 19.5.** It stays over the shaft, which ends at x 21, and sits 3.9 mm above the web, so the key's short leg clears it.
- **The clamp halves** are now cantilevers off the web (slot x 14.1 to 26).
- **New check (`lkey_access`).** A Ø2.6 L-key with an 18 mm short leg sits 2 mm into each socket, with a 60 mm long leg. At tilt 45 with the cover off, it was swung through -30, -15, 0, +15 and +30 deg about each bolt axis and tested against every solid and fastener: 10 of 10 positions clear. See `flywheel_lkey_access_tilt45.png`. Along the bolt axis there are 19.3 mm of free run from the head to the rim, enough for the standard short leg.
- **Bolts are now M3 x 20.** With the hub at R13.5 the tip passes the nut by 0.54 mm and stays 0.36 mm inside the hub surface. Reported under `flywheel_pinch_bolts`.
- **Wall probe.** It flagged slivers where the counterbores and nut traps left the hub cylinder. Both now open radially as U-channels, and the slivers are gone.
- **Print orientation** is now the motor-side web face on the bed. The +X flange carries the 45 deg underside.

### 2. Feeder index (major)
The pockets are re-phased by 30 deg (`POCKET_PHASE`). **Servo 0 is now park**, with solid disc over the outlet and 7.5 mm from the nearest pocket edge to the outlet edge. Fire is **+30 then back to 0**, and the next shot is **-30 then back to 0**. Exactly one pocket overlaps the outlet at each fire position, and none at park; `checks.py` (`feeder_index`) reports the centre offsets. The agitator dimples moved between the pockets. BOM section 0 and step 27 are rewritten. The renders are `feeder_index_park0.png` and `feeder_index_fire±30.png`.

### 3. Compliant nip (major)
Prior art first. The attempt-2 jack line was already the right place, being nearly tangent to the hinge arc on a 63 mm lever, and the hinge, the bay envelope and the drop tracer were already right. So I kept `JACK_PT`, `JACK_DIR`, the hinge and the bay, and changed only what holds the plate. The jack screws could only stop the plate **opening**. To stop it **closing**, the stop has to pull. That is why the screws were replaced, not re-tuned.
- **Stud:** one M3 x 20 hex-head stud sits head-down in a hex pocket on the backplate's back face and passes out through a slot in the guard. The slot is the swept hull over the full hinge range, and the head can be pushed in from outside.
- **Thumbwheel:** a printed Ø17 thumbwheel with a captive nut runs on the stud and sits on a new flat **land** across the pod's rear underside. It is the minimum-gap stop.
- **Leaf spring:** a PLA leaf inside the new terracotta **nip cover** (21.9 x 2.0 mm, 34 mm cantilever, printed so the leaf is a vertical wall) presses the thumbwheel onto its seat. Rate is 3.9 N/mm, and preload is **9.0 N** from 2.3 mm of pre-deflection. Root stress is 21 MPa at preload and 44 MPa at the over-travel stop, which comes after 2.5 mm more lift when the leaf hits the shell.
- **Behaviour:** the plate is held at the set gap with 9 N and opens for thick candy, which answers the reviewer's 10 to 20 N at the jack point.
- **Adjustment** is 5.5 to 10.0 mm bare at BDC at 0.48 mm per turn. The bay still swings to 12.5 to clear jams by hand.
- **Removed:** the clamp screws, their arc slots in the left wall and cover, the jack bosses and the lock nuts. No wrench and no tilt-dependent access are needed.
- **Modelling note:** the cover is modelled in its free shape, so its two pads overlap the thumbwheel by the 2.3 mm preload. That is the only new interference whitelist entry, and it is labelled in `checks.py`.
- **Stud and the stud-tip window:** `compliant_nip` lists the stud-tip position at each setting. The stud tip shows through a Ø8 window in the cover as a coarse gap indicator.

### 4. Minors
- **DeWalt adapter bolts:** now M3 x 25 countersunk from the deck, with the nut in a Ø6.5 x 5.5 counterbore on the adapter's battery face. The tip ends 2.4 mm above the battery face. Step 2 says to drill the counterbore if the adapter has none. The battery-rail placeholder was narrowed to sit between the corner holes, as the real rail does. **`checks.py` now tests fasteners against purchased parts on the same pivot.** The only whitelisted case is the motor screws threading into the motor. Result: 0 overlaps.
- **Magnet jig datum:** the jig now has a Ø7.8 x 1.0 spigot that enters the motor's Ø8 rear access hole, with the magnet pocket inside it, and the plug is relieved to Ø35.6 so it no longer locates. The encoder-cap spigot is Ø35.8 with three line-to-line crush ribs. Three more crush ribs at the rear of the nacelle bore centre the can. Exception: the spigot ring is 0.85 mm thick, because the magnet sits inside the Ø8 hole, and the wall probe flags it on this one-use tool.
- **Gap adjust access:** solved by section 3 (thumbwheel, no clamp screws, no lock nuts). The tool list now has a standard L-key and pliers, and no wrench.
- **Bare feeder bus:** the left bonnet now runs up flush with the feeder-plate top (z 258) and covers the plate's left edge. The bus goes from inside the bonnet straight into the cap notch and up into the plate groove, so there is no bare length.
- **Jack hardware under the pod:** it is gone. The stud and thumbwheel sit under the nip cover, which is the land's full width, so its +X face continues the body/cover parting plane.
- **Form language:**
  - The grey feeder-servo pocket is now inside a terracotta **feeder shroud**, held like the tilt-servo housing by the two clamp screws through its floor.
  - The shroud's face toward the pod is the pod's swept envelope plus 3 mm (`sweep_env`), a cylinder about the tilt axis. The feeder-stack clearance stays 3.0 mm at 0 deg and 3.26 at 45.
  - The shroud's rear-bottom edge and the tilt-servo housing's front-top edge now carry the **pod's top-chamfer angle** (`pod_chamfer_cut`).
  - The nip cover uses the 6 mm radius on its outer long edges.
  - The ortho renders are re-framed (ortho scale 440, centred at z 152), so the whole machine, hopper lid to base, is in front, side and rear.

### Deferred
- **Arm tops** are not re-styled. The caps sit directly under the feeder plate, so a chamfer there would leave a notch under the plate edge, and a 6 mm corner on the cap cut into the cap screws in attempt 2.
- **Hopper axis over the pan axis** (attempt-2 review suggestion). The outlet must sit over the tilt axis, and the feeder axis is one pocket radius (45 mm) from it. Moving the feeder axis to the side puts the feeder servo directly over the nacelle, where there is only 13 mm under the plate.

### Known limitations / next
- The leaf numbers are beam theory with E = 3.5 GPa. Printed PLA may be 20 to 30% softer, and it creeps at 21 MPa sustained. The cover is cheap to reprint, or a 0.5 mm shim restores the preload.
- The tracer is still a point-particle model. Bite force and exit-speed consistency need a physical test, which the thumbwheel now makes quick.
- The remaining wall-probe flags are the involute gear tips (1.54 mm), a 1.47 mm bevel corner on the body near the tongue (unchanged), and the jig spigot ring.
