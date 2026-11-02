# M&M launcher v2: assembly

This is the same sequence as BOM section 4 and `checks.json` `assembly_order` (`../BOM_AND_ASSEMBLY.md`), rewritten for the
bench. cadcheck tested tool access for every screw at the step where it is driven, with only the parts placed so far
present. Do the steps in this order; a few screws can only be reached at their own step.

Directions: **+Y is the front** (muzzle), +X is the right side (battery and servo-controller side), Z is up. "Bench" steps are
sub-assemblies built off the machine and merged later. There are no steps 4 and 5 (the numbering follows the model).

**Renders:**

- New, 960 px, made for this guide in `renders/`:
  - `s02_floor_plate_bench`, `s03_base_turntable_done`, `s06_pod_bench`, `s08_pod_in_posts_tilt_servo`, `s11_feeder_on_beam`;
  - `s11a0_pod_on_45_prop` and `s11a0_prop_closeup` (the prop is drawn blue).
- From the design, 1800 px, in `../renders/attempt-7/`: `exploded`, `iso`, `rear`, `side`, `tilt45`, `jar_unlocked`,
  `sec_hub_bore_x5.73_pan-90`.
- From the review: `../renders/attempt-7/review/r02_sec_y4.02_splice_top_under_groove_cap`.

## Step 0: before you start

- **Prints:** all 9 plates (`PRINT_PLAN.md`), and the three tools: encoder jig, pocket coupon, 45 deg prop.
- **Measured:** `MEASURE_FIRST.md` done, and the model rebuilt if anything changed.
- **Pilots:** clean every Ø2.5 pilot with a Ø2.5 drill if your printer prints holes small. A screw that has to be forced
  splits the boss.
- **Servos on the bench, through the controller:**
  - give the pan, tilt and feeder servos different bus IDs (they all ship as ID 1, and after step 11a they share one bus);
  - label each servo with its ID;
  - command each servo to its mid position (500 on Hiwonder's 0..1000 scale) before its horn goes on, and don't turn the
    output by hand after that. Mid is pan 0, tilt 0 and the feeder's park position. Fine trim is done in firmware at step 15.
- **Tape check:** the hockey tape is 1 in wide (it is trimmed to 13.8 at step 6f).

## Base

### 1. Base shell upside down; DeWalt adapter

- **Tools:** 2 mm hex or Phillips to suit the csk heads, straight bit.
- **Fasteners:** 4 x M3 x 20 countersunk ST.
- **Do:** lay the base shell deck-down. Put the adapter into its fence, then drive the 4 screws from the deck top into the
  adapter's corner holes.
- **Check:** the battery slides on and off the rail by hand. The screw tips sit 4.56 above the battery face (row
  FST_adapter-BUY_battery), so nothing scrapes the pack.

### 1a. Pan drive, bench: horn into the pan pinion

- **Tools:** Phillips #0, Ø2 drill.
- **Fasteners:** 4 x M2 x 8 pan.
- **Do:** press the horn disc into the pinion's 1.0 recess. Drill the 4 dimples through using the horn as the template, then
  screw it in. A dab of superglue under the disc is fine.
- **Check:** the horn sits flat and centred; the pinion teeth spin true on the spline.

### 1b. Pan drive, bench: servo into its mount

- **Tools:** 2.5 mm hex.
- **Fasteners:** 2 x M3 x 12 socket cap ST (clamp); 1 x M3 x 6 socket cap (centre screw).
- **Do:**
  - put the pan servo into the mount pocket and fit the clamp;
  - press the pinion onto the spline **with the servo still at mid**;
  - fit the centre screw through the pinion.
- **Check:** the servo can't rock in its pocket (0.3 clearance).

### 1c. Pan drive onto the deck posts

- **Tools:** 2.5 mm hex, straight bit.
- **Fasteners:** 4 x M3 x 12 socket cap ST.
- **Check:** the pinion is clear of the deck hole edge all the way round.

### 2a. Floor plate, bench: partition and MotorGo

Render: `renders/s02_floor_plate_bench.png`.

- **Tools:** 2 mm hex, straight bit.
- **Fasteners:** 2 x M3 x 10 countersunk ST (partition, from below); 4 x **M2.5 x 10** socket cap ST (MotorGo), or M3 x 10 if
  you changed `MG_*`.
- **Do:** screw the partition to the floor from below. Mount the MotorGo on the partition standoffs, components toward the
  partition and the USB-C receptacle toward the rear niche.
- **Check:** the header pins under the board (7.25 long) clear the partition. The USB-C opening lines up with the niche.

### 2b. Floor plate, bench: buck and servo controller

- **Tools:** Phillips or 2 mm hex, Ø2.5 drill.
- **Fasteners:** 2 x M3 x 8 pan ST (buck); 4 x M3 x 8 pan ST (controller, drill to fit).
- **Do:**
  - screw the buck to its bosses, fins free;
  - lay the controller in its +0.4 pocket, slide switch and terminal toward the +X wall;
  - drill Ø2.5 through the board's own holes into the solid bosses (the dimples are only a guess), then screw it down.
- **Check:** the switch and the terminal sit where the shell's two +X windows will be (`CTRL_SW`, `CTRL_TB`).

### 2c. Turntable, bench: posts

- **Tools:** 2 mm hex, straight bit.
- **Fasteners:** 7 x M3 x 16 countersunk ST, up from the turntable's underside.
- **Do:** screw the left and right posts onto the turntable. **Leave the groove cap and its 6 screws in the bag**: the cap goes
  on at 11a, after every bus lead is in the groove.
- **Check:** the posts stand square to the turntable, and the U-slots at their tops line up across.

### 2d. Turntable into the deck; hub gear from below

- **Tools:** 2.5 mm hex.
- **Fasteners:** 3 x M3 x 12 socket cap ST.
- **Do:**
  - slip the thrust ring over the hub and drop the turntable assembly into the deck hole;
  - from under the deck, mesh the hub gear with the pan pinion **with the pan servo at mid and the posts square across the
    base, so the pod will face +Y (pan 0)**, then screw it up into the hub. The floor is still off; the R28.5 gear is wider than the deck hole, so it can only go on from below.
- **Check:** the turntable turns smoothly by hand to both pan stops, with no gear bind.

### 3. Floor into the shell; base cables

Render: `renders/s03_base_turntable_done.png`.

- **Tools:** 2 mm hex, straight bit, soldering iron.
- **Fasteners:** 8 x M3 x 12 countersunk ST, from below.
- **Do, before the floor closes:**
  - run 12 V (adapter to buck, buck to MotorGo, buck to controller), the UART lead and the USB-C;
  - run the **pan bus lead**: from the controller up the riser, with its U-loop hanging under the hub gear, and up the pan
    axis. Leave its plug on, push the plug end up through the hub bore and coil it above the turntable;
  - run the **launcher base lead**: from the MotorGo J6/J8 phase pads and its encoder connector, through its own U-loop under
    the hub gear, up to the hand-over point in the hub bore.
- **Check:**
  - both U-loops hang free; they are the ±90 pan slack;
  - turn the turntable to both pan stops: nothing pulls tight or rubs the gears;
  - then fit the floor.

## Launcher pod (bench)

Render: `renders/s06_pod_bench.png`. Exploded view: `../renders/attempt-7/exploded.png`.

### 6a. Motor into the nacelle; body on

- **Tools:** 2.5 mm hex / Phillips, side cutters, soldering iron, heat gun.
- **Fasteners:** 4 x M3 x 10 pan (machine, into the motor face); 2 x M3 x 12 pan ST (nacelle to body).
- **Do:**
  - push the motor into the nacelle bore (crush ribs; scrape a rib if it's too tight);
  - fit the body onto the nacelle plate and drive the 4 motor screws and 2 nacelle screws from inside the guard;
  - cut the motor leads to about 55 and solder them to the three 16 AWG extensions, joints staggered along the journal bore,
    each under 4.8 mm heat-shrink;
  - thread the leads out through the hollow journal.
- **Check:** the motor-screw heads sit below the wheel's web plane with daylight. This was 0 mm on attempt 3; the brief now
  asks for at least 1.5 to anything rotating.

### 6b. Magnet and encoder

- **Tools:** encoder jig (printed), superglue, 2 mm hex.
- **Fasteners:** 2 x M3 x 12 countersunk ST.
- **Do:**
  - put the magnet in the jig's pocket and the jig spigot in the motor's Ø8 rear access hole, then glue the magnet to the
    rear shaft end. Wait 10 min;
  - press the Plink onto the encoder cap's pegs, then fit the cap into the bore.
- **Check:** the magnet is centred; the stack's worst case is 0.30 against 0.30. The air gap matches what you set on the rig.
  Plug in the long JST-SH encoder lead.

### 6c. Nip stud and nip stop

- **Tools:** 2.5 mm hex.
- **Fasteners:** the M3 x 16 hex-head stud (never driven); 1 x M3 x 6 socket cap ST.
- **Do:**
  - drop the stud head into the hood's hex pocket, flats keyed;
  - press the nip stop pad into its pocket under the muzzle floor, top flush, and retain it with the M3 x 6 up from the skin.
- **Check:** the stud doesn't spin in the pocket.

### 6d. Backplate (hood), journal plate, hinge axle

- **Tools:** 2 mm hex bit with **104 mm of reach** (accepted warn), 2 mm hex, 5.5 mm nut driver.
- **Fasteners:** 3 x M3 x 12 countersunk ST (journal plate); 1 x M3 x 35 countersunk + 1 M3 nut (hinge).
- **Do:** put the hood into its bay and screw on the journal plate. Drive the hinge axle from -X through the wall, the hood
  boss and the plate into its trapped nut. Do it on the bench; there's no room for the bit later.
- **Check:** the hood swings freely on the axle.

### 6e. Gap setting, leaf, nip cover

- **Tools:** 2 mm hex, 2.5 mm hex.
- **Fasteners:** 2 x M3 x 10 countersunk ST (leaf); 2 x M3 x 14 socket cap ST (cover); the thumbwheel's captive M3 nut
  (superglue it into its trap first).
- **Do:**
  - slide the stop sleeve over the stud, then thread the thumbwheel on;
  - screw the leaf under the nip cover from outside;
  - fit the cover onto its land.
- **Check:** with the cover on, a fingertip rolls the thumbwheel through the 22 x 8.3 slot between its two printed stops,
  gap 6.2..7.0. The spare leaf goes in the bag, unloaded, as the creep reference.

### 6f. Tape and flywheel

- **Tools:** knife, calipers, 2.5 mm L-key.
- **Fasteners:** 2 x M3 x 20 socket cap + 2 M3 nuts (pinch bolts).
- **Do:**
  - wrap the 1 in tape once round the land, sticky side down;
  - cut both ends square and **butt-join them, no overlap**;
  - trim both edges with the knife against the flanges to the 13.8 land;
  - slide the wheel onto the D-shaft and tighten the pinch bolts with the L-key from +X.
- **Check:** caliper the tape at three places and at the seam: **0.5 or less** (`TAPE_T`). An overlap doubles it and eats the
  0.098 entry-arc margin, so re-wrap if needed. The wheel spins with no rub; it is 1.594 from the guard.

### 6g. Wheel-side cover

- **Tools:** 2 mm hex.
- **Fasteners:** 4 x M3 x 12 countersunk ST.
- **Check:** spin the wheel by hand: silent.

## Pod, tilt and beam

### 7. Pod into the post U-slots

- **Do:** hold the pod nose-up about 20 deg and lower it straight down until both journals seat in the U-slots, then level it.
  Route the phase and encoder bundle out of the left journal.
- **Check:** both journals sit fully down in their slots. Lifting it out the same way clears with 0.2 [slide_out v2-A1-06].

### 8a, 8b. Tilt drive, bench

- **Tools:** Phillips #0, Ø2 drill, 2.5 mm hex.
- **Fasteners:** 4 x M2 x 8 pan (horn to adapter); 1 x M3 x 6 socket cap (centre screw, through the Ø6.5 key hole).
- **Do:** fix the horn into the tilt horn adapter, drilling the dimples through the horn. Fit the adapter to the tilt servo's
  spline **with the servo at mid**, and fit the centre screw.
- **Check:** the 12 AF hex key on the adapter is square to the servo body.

### 8. Tilt servo into the right post; post cover

Render: `renders/s08_pod_in_posts_tilt_servo.png`.

- **Tools:** 2.5 mm hex, straight bit.
- **Fasteners:** 4 x M3 x 14 socket cap ST (post cover).
- **Do:** with the pod level (tilt 0), slide the servo, horn and adapter in -X through the right post until the hex key enters
  the journal plate's socket. Lead the tilt bus lead down the post channel to the turntable groove, plug on. Fit the post
  cover.
- **Check:** the pod doesn't move unless the servo turns: there is no free play at the key.

### 9. Beam

- **Tools:** 2 mm hex, straight bit.
- **Fasteners:** 7 x M3 x 16 countersunk ST.
- **Do:** close the U-slots with the beam. Lay the launcher bundle (phases + encoder, in the 6 mm sleeve) down the left post
  channel to the turntable groove.
- **Check:** the beam sits flat on both posts and the journals can't lift. **Don't swing the pod by hand from here on:** that
  back-drives the tilt servo's gears. The tilt range is checked under power at step 15 (designed clearances: beam to pod
  4.9 or more, spout to drum 3.0, printed stops at -3 and +46).

## Feeder

### 10a. Feeder drive, bench

- **Tools:** Phillips #0, Ø2 drill.
- **Fasteners:** 4 x M2 x 8 pan.
- **Do:** fix the horn into the feeder pinion's recess, drilling through the horn as the template.

### 10b. Crown upside down: pinion, then servo

- **Do:** put the pinion and horn in from below. Then drop servo #3 into its pocket from the top, spline pressed into the horn,
  **servo at mid**. There is no centre screw: the lobe cover holds the servo down.
- **Check:** the pinion turns with the servo and doesn't fall out.

### 10c. Feeder disc and floor plate

- **Tools:** 2 mm hex.
- **Fasteners:** 2 x M3 x 8 countersunk ST (from below).
- **Do:** fit the disc from below with its gear band meshed on the pinion, in the **park** position: solid over the outlet.
  Then fit the floor plate.
- **Check:** looking up through the outlet you see solid disc, not a pocket.

### 10d. Feeder upright: bus lead and lobe cover

- **Tools:** 2 mm hex.
- **Fasteners:** 2 x M3 x 12 countersunk ST.
- **Do:** lay the feeder bus lead in its channel and fit the lobe cover. Leave the lead's plug end free; it is spliced at 11a.

### 11. Feeder onto the beam

Render: `renders/s11_feeder_on_beam.png`.

- **Tools:** 2 mm hex straight bit **and** a 2 mm L-key; pod at tilt 0.
- **Fasteners:** 4 x M3 x 16 countersunk ST, up through the beam into the crown.
- **Do:**
  - (-36, -21): straight bit, 58 mm reach;
  - (-36, +21): the L-key (the nacelle blocks a straight bit);
  - the (34, ±20) pair: the L-key.
  - Feed the feeder bus lead down the left post channel to the groove.
- **Check:** the spout keeps 3.0 to the pod drum through the full tilt range.

## 11a. Bus splice and groove cap

Every bus lead reaches the turntable groove only after steps 8, 9 and 11, and the groove cap closes that groove and the hub
bore, so the splice and the cap come last. The cap screws can only be reached with the pod at tilt 45.

### 11a.0 Free the pod and set it on the 45 deg prop (new after review 7)

Renders: `renders/s11a0_pod_on_45_prop.png`, `renders/s11a0_prop_closeup.png`.

- **Tools:** 2.5 mm hex, printed `tilt45_prop`.
- **Fasteners:** remove the 4 x M3 x 14 from the post cover.
- **Why:** the tilt servo can't be powered yet: its lead isn't spliced and the battery goes in at step 14. Forcing the pod
  round would back-drive the servo's gears.
- **Do:**
  1. Take the right post cover off (+X).
  2. Slide the tilt servo, horn and adapter out +X about 10 mm. The hex key leaves its socket after 6.5. **Don't turn the
     servo output while it's out.**
  3. The pod swings free; unpowered it falls nose-down to the -3 stop. Lift the nose to the +46 stop and slide the prop in
     on the turntable from the front: the tall pad under the nip cover, the low foot along the turntable to the right post's
     front face.
  4. Let the pod settle onto the pad.
- **Check:**
  - the pod sits steady at 45 with your hands off;
  - the pad bears on the nip cover's flat underside, not on the thumbwheel (8.5 clear), so the gap setting is untouched;
  - the prop is 8.5 from where the cap goes. Measured in a scratch model with the prop added: 6/6 cap screws take a straight
    bit at 14 with it in place.

### 11a.1 to 11a.9 Splice and cap

- **Tools:** side cutters, wire strippers, soldering iron, heat gun, card or foil, cable tie, 2 mm hex straight bit.
- **Fasteners:** 6 x M3 x 10 countersunk ST (groove cap).
- **Do:**
  1. Pod at 45 on the prop.
  2. Lay the tilt and feeder bus leads and the launcher bundle in the turntable groove, down to the hub bore.
  3. Pull the pan lead up the hub bore until about 60 stands above the turntable; the 350 lead has 57.9 spare over its
     route. Bring the tilt and feeder ends to it.
  4. Cut the three plugs off.
     - **Trim the tilt and feeder leads to route + 70:** hold each end at the bore centre at turntable-top level and cut it
       70 beyond that point. That is about 23 off the tilt lead and 110 off the feeder lead.
     - Leave the pan lead long.
     - Strip the leads and solder like wires 3-to-1 (V+ to V+, GND to GND, signal to signal), with card or foil round the bore
       to shield the PLA.
     - Heat-shrink each joint (4.8 mm), then the three together (12.7 mm).
     - **The finished splice must be Ø10 x 20 or smaller.**
  5. Lower the splice into the hub bore on the side away from the launcher bundle (az 35, toward front-right), bottom at the
     seat (z 74). It passes the hub gear with 1.0.
  6. Tie it to the bundle sleeve with a small cable tie so it turns with the turntable.
  7. Push the spare pan lead back down into its U-loop.
  8. **Dress the service loops:**
     - the tilt lead's spare as a flat S-fold in the groove between the hub and the right post (x 10..60; only the tilt lead
       runs there);
     - the feeder lead's spare pushed back up the left-post channel beside the bundle.
  9. **Check the bundle hand-over (A6-02).** Its moving end swings 5.66 side to side over ±90 pan, so leave the sleeve loose
     there (no tie). Turn the turntable slowly to both pan stops and watch through the bore: nothing pulls tight.
  10. Fit the groove cap over the posts (0.2 to the left post going down) and drive its 6 screws with a straight bit.
- **Check:**
  - the cap sits flat with no lead pinched under it. With a 20 splice there is 8 between the splice top and the cap, room for
    the leads to turn down (`../renders/attempt-7/review/r02_sec_y4.02_splice_top_under_groove_cap.png` shows the tight 25
    case);
  - the splice can't climb out of the bore (the cap stops it).

### 11a.10 Back to tilt 0

- **Tools:** 2.5 mm hex.
- **Fasteners:** 4 x M3 x 14 socket cap ST (post cover).
- **Do:**
  1. Lift the pod nose to +46 and take the prop out. Lower the pod to the -3 stop.
  2. Slide the tilt servo back -X until its hex key re-enters the journal-plate socket. Rock the pod a degree to line up the
     flats.
  3. Refit the post cover.
- **Check:** the pod has no free play at the key. Keep the prop: it's also the service fixture for the splice.

## Jar, battery, power-up

### 12. Jar, bench

Render: `../renders/attempt-7/jar_unlocked.png`.

- **Tools:** 2.5 mm hex, Phillips.
- **Fasteners:** 3 x M3 x 10 socket cap ST (valve, radial); 1 x M3 x 10 pan self-tapping (detent clip).
- **Do:**
  - put the printed adapter disc into the band in place of the flat lid;
  - lay the gate on the valve's gate floor, closed, stop lug up at the -X end;
  - fit the valve over the spout with its 3 radial screws. The gate is captive from now on;
  - hold the detent clip's tab on the +Y cheek, gate closed, so the bump drops into the closed notch. Drive the self-tapper
    -Y until its head is flush in the counterbore.
- **Check:** the gate clicks at closed and at open (52); it stops positively at both ends.

### 13. Jar onto the feeder

- **Do:**
  1. Close the gate and fill the jar.
  2. Screw on the adapter and band.
  3. Flip the jar, drop it into the bayonet at +30 and twist to 0.
- **Check:** the jar is locked; twisting it back to +30 lifts it off.

### 14. Battery

- **Do:** slide the pack onto the adapter rail from +X.
- **Check:** it comes off again with no tool (1.6 to the floor along the way).

### 15. First power-up (bench, wheel not spinning)

- **Do:**
  1. Power up with the flywheel motor disabled.
  2. Ping each servo by ID.
  3. Command tilt 0 and check the pod is level. If it isn't, set a tilt offset in firmware rather than moving the horn.
     After 11a.0 the key went back in at the same flat only if the servo wasn't turned.
  4. Command pan 0 (pod facing +Y) and the feeder to park (solid disc over the outlet), and trim any offsets.
  5. Clamp firmware tilt to 0..45; the printed stops are at -3 / +46.
  6. Only then spin up the flywheel.
- **Check:**
  - one fire command (disc +60, back to 0) drops exactly one candy, and the next shot uses -60;
  - log the leaf preload on day 0 (BOM section 0, "Leaf creep").
