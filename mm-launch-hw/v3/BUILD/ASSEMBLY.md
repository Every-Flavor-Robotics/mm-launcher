# M&M launcher v3: assembly

This is the same sequence as BOM section 4 and `checks.json` `assembly_order` (`../BOM_AND_ASSEMBLY.md`), rewritten for the
bench, with the attempt-2 hotfix folded in (BOM "Attempt 2 (hotfix) notes"; `../renders/attempt-2/`). The step labels are
the 24 checks.json labels. cadcheck tested tool access for every screw at the step where it is driven, and a straight
insertion for every part, with only the parts placed so far present (`../blender/cadcheck.json`: 0 fail).

v3 holds the machine together with 11 screws and 3 nuts (manifest `fastener_summary`). Everything else is a snap, a slide,
a press-fit peg or a printed pin. Each of those steps below says what you should feel or hear when it seats (**Seats**) and
how it comes apart for service (**Release**). The stresses quoted are the `flexures` rows; "in plane" means the spring
bends in the layer plane, "across layers" means it doesn't.

> **WARNING: lift and carry the machine by the base only. Never by the jar, the crown or the beam.**
>
> Review v3-A1-02 (`../renders/attempt-1/review.md`). Lift it by the jar and the whole 4075 g machine [stability] hangs on
> three sets of snap fingers in a row, and every one of them bends across layers:
> - band, then adapter, then the **2 valve fingers**: about 32 N, 12.3 MPa by hand calculation; a 1.5 g jolt takes them to
>   about 19 MPa, past the 15 MPa interlayer limit;
> - then the crown, then the **3 crown hooks**, then the beam, then the **4 beam hooks**;
> - then the turntable, then the **3 hub fingers**, then the base.
>
> Every one of those catches has less than one layer (0.05 to 0.1) of Z clearance. This stays true until the bayonet
> redesign planned in `../renders/attempt-2/progress.md`, which isn't started. To move the machine: battery out, then both
> hands flat under the base shell. If it has to go on its side (step 11a, service), take the jar off first.

Directions: **+Y is the front** (muzzle), +X is the right side (battery and servo-controller side), Z is up. "Bench" steps are
sub-assemblies built off the machine and merged later. There are no steps 3, 4 or 5 (the numbering follows the model).

**Renders:**

- New, 960 px, made for this guide in `renders/` (`tools/step_renders_v3.py`, rendered from a copy of the model):
  - `s01a_pan_drive_bench`, `s02b_hub_gear_from_below`, `s06_pod_bench`, `s08_tilt_servo_in_post`;
  - `s11_crown_on_beam`, `s12_floor_bench`, `s14_jar_bench_from_below` (the M&M fill is hidden).
- From the design, 1800 px, in `../renders/attempt-1/`: `exploded`, `iso`, `rear`, `side`, `tilt45`, `jar_unlocked`, and
  the sections `sec_hub_roof_y4.0`, `sec_beam_hook_y18_xR`, `sec_crown_hook_y0_xR`, `sec_gate_finger_z325`. Three STLs
  changed after these were rendered (the beam, jar_adapter and jar_gate, in the hotfix), so the beam-hook and gate sections
  show the attempt-1 shapes.

## Step 0: before you start

- **Prints:** plates 0a to 6 (`PRINT_PLAN.md`), and the two tools: the encoder jig (plate 1) and the pocket coupon (plate 0b).
  You don't need the v2 45 deg prop: no v3 step uses a tilt pose (`assembly.held_poses` `[]`).
- **Measured and fit-tested:** `MEASURE_FIRST.md` is done, including the fit coupons (item 2) and the early jar group (item 3).
  If anything changed, rebuild the model.
- **Servos on the bench, through the controller:**
  - give the pan, tilt and feeder servos different bus IDs (they all ship as ID 1, and after step 11a they share one bus);
  - label each servo with its ID;
  - command each servo to its mid position (500 on Hiwonder's 0..1000 scale) before its horn goes on, and don't turn the
    output by hand after that. Mid is pan 0, tilt 0 and the feeder's park position. Fine trim is done in firmware at step 16.
- **Horns:** there are no horn screws in v3. Each horn presses into a 2.7-deep pocket over 8 printed Ø2.0 pins that go into
  its 8 Ø2.2 holes (BOM item 5). Keep the horns' own screws in the bag.
- **Tape check:** the hockey tape is 1 in wide (it is trimmed to 13.8 at step 6f).

## Base

### 1. Base shell upside down; DeWalt adapter

- **Tools:** a driver to suit your M3 pan heads.
- **Fasteners:** 2 x M3 pan x 10 (`FST_adapter_0/1`).
- **Do:** lay the base shell deck-down. Put the adapter into its 4 deck fences (0.4 clearance). Drive the 2 screws from the
  deck top, through the counterbores at the two diagonal corners, into the adapter's own holes. That gives 8.5 of thread in
  the adapter [fasteners: FST_adapter_0/1].
- **Check:**
  - both heads sit flush in their 2.4 counterbores;
  - the battery slides on and off the rail by hand;
  - the screw tips sit 5.46 above the battery face, so nothing scrapes the pack [distances: FST_adapter_0/1-BUY_battery].

### 1a. Pan drive, bench: horn, pinion, servo, mount

Render: `renders/s01a_pan_drive_bench.png`.

- **Tools:** 2.5 mm hex L-key.
- **Fasteners:** 1 x M3 x 6 socket cap (`FST_pinion_ctr`, the centre screw).
- **Do:**
  - press the horn into the pinion's 2.7 horn pocket, with its 8 holes over the 8 printed pins;
  - put the pan servo into the mount pocket (0.3 clearance);
  - press the pinion and horn onto the spline **with the servo still at mid**;
  - drive the centre screw through the pinion's Ø6.5 hole. Its head bears on the horn disc and the screw gets 6.0 of
    engagement [fasteners: FST_pinion_ctr].
- **Seats:** with all 8 pins lined up, the horn drops the last 2.4 (the pin length) under thumb pressure and stops flat on
  the pocket floor, 0.2 below the mouth. If it rocks, a pin is outside its hole: lift it off and turn it a hole.
- **Release:** take the centre screw out and pull the pinion off the spline. Lever the horn out of its pocket with a thin
  blade; only friction holds it axially.
- **Check:** the servo can't rock in its pocket, and the pinion teeth spin true on the spline.

### 1b. Pan drive onto the deck posts (merge)

- **Do:** stand the shell the right way up on its walls, with the floor off. Press the mount plate up onto the 4 deck posts.
  Each post-end pin (R2.0 x 3.5) goes into a plate hole with 3 crush ribs (`PAN_POST_RIB`, 0.15 interference). Push until
  the plate sits on all 4 post shoulders.
- **Seats:** a firm, even press with no click, ending in a dead stop on the shoulders. The ribs take 1.87 mm³ of crush
  [slide: v3-A1 pan drive off the deck posts -Z]. The pinion is now trapped between the mount plate and the deck.
- **Release (service "pan servo swap"):** with the floor off, pull the pan drive straight down (-Z) off the posts. It clears
  with 0.14 [slide: v3-A1 pan drive off the deck posts -Z]. With the floor in, the floor's servo column backs it, blocked at
  0.5 [slide: v3-A1 pan drive captive].
- **Check:** the pinion is clear of the deck hole edge all the way round.

### 2a. Thrust ring and turntable

- **Do:** lay the thrust ring on the deck round the hole. Set the turntable (posts integral) on the ring, with its hub socket
  over the deck hole.
- **Check:** the turntable sits flat on the ring and turns freely by hand.

### 2b. Hub gear up from below (permanent)

Render: `renders/s02b_hub_gear_from_below.png` (looking up at the deck).

- **Do:**
  - hold the turntable down on the ring and reach under the deck (or tip the shell onto its side, holding the turntable);
  - turn the hub gear so its 3 dogs line up with their pockets in the turntable socket;
  - mesh it with the pan pinion **with the pan servo at mid and the posts square across the base, so the pod will face +Y
    (pan 0)**;
  - push it straight up (+Z) through the deck hole and the ring into the socket.
- **Seats:** 3 clicks, close together, as the finger barbs (0.45) flex through the socket and snap over its ledge (12.6 MPa,
  across layers [flexures: v3-A1 hub snap finger 1..3]). Afterwards the gear hangs from the turntable, its top 1.0 under the
  deck (gear top z 85, deck underside z 86, review "Hub stack").
- **Release: none.** The barbs sit inside the socket where no tool reaches them. checks.json calls this joint permanent
  (v3-A1-04). Taking the turntable off breaks the fingers; the hub gear is a 15.6 g reprint. That is why the c2 coupon
  (`MEASURE_FIRST.md` item 2) comes first.
- **Check:** the turntable turns smoothly to both pan stops with no gear bind, and lifts no more than about 1.0 before the
  gear meets the deck.

## Launcher pod (bench)

Render: `renders/s06_pod_bench.png`. Exploded view: `../renders/attempt-1/exploded.png`.

### 6a. Motor into the nacelle; body on

- **Tools:** a driver for M3 pan heads, side cutters, soldering iron, heat gun.
- **Fasteners:** 4 x M3 pan x 10 (`FST_motor_0..3`, machine screws into the motor face, 4.5 engagement [fasteners]).
- **Do:**
  - push the motor into the nacelle bore (crush ribs; scrape a rib if it's too tight);
  - fit the body onto the nacelle plate (both centre on the motor's front boss);
  - drive the 4 motor screws from inside the guard. They now clamp the body wall and the nacelle plate together; there are no
    other screws in this joint;
  - cut the motor leads to about 55 and solder them to the three 16 AWG extensions, with the joints staggered along the
    journal bore and each under 4.8 mm heat-shrink;
  - thread the leads out through the hollow journal.
- **Check:** the motor-screw heads sit below the wheel's web plane with daylight to the wheel (the brief asks for 1.5 or more
  to anything rotating).

### 6b. Magnet and encoder cap

- **Tools:** encoder jig (printed), superglue.
- **Do:**
  - put the magnet in the jig's pocket and the jig spigot in the motor's Ø8 rear access hole, then glue the magnet to the
    rear shaft end. Wait 10 min;
  - press the Plink onto the encoder cap's pegs (Ø2.4 pegs in its Ø2.5 holes);
  - push the cap +X into the nacelle's rear counterbore (it comes off -X). Its lobe keys it, so it only goes in one way round. Push until both
    arms click.
- **Seats:** 2 clicks. The arms' 0.6 barbs drop into the groove in the counterbore wall (14.6 MPa, in plane [flexures]). The
  flange then sits flat on the counterbore floor, and that sets the air gap (`ENC_GAP` 1.0).
- **Release (service "encoder", in the machine at tilt 45, powered):** squeeze the 2 arms together and pull the cap -X
  [slide: v3-A1 encoder cap pulls off -X, arms 4.25 mm³ on an 8 mm³ allow].
- **Check:**
  - the magnet is centred; the stack's worst case is 0.30 against 0.30 [stacks: magnet centring];
  - the flange is flat all the way round. The model still has 0.18 mm³ of cap/nacelle overlap at rest (hotfix review,
    "Carried"). If a gap shows under the flange, the barb is riding the groove edge: ease the groove's outer edge with a
    knife rather than forcing the cap.
  - Plug in the long JST-SH encoder lead.

### 6c/6d. Hood, nip stud, journal plate

- **Fasteners:** the M3 x 16 hex-head stud (`FST_nip_stud`, captive, never driven).
- **Do:**
  - slide the hood -X onto the body's Ø5 hinge stub, through the open +X side of its bay;
  - pass the stud head-first through the guard slot into the hood's hex pocket, with the flats keyed;
  - press the journal plate -X onto the body's 3 crush-rib pegs (Ø5, 0.1 interference, `JP_PEG`), with its bore over the
    hood's +X stub.
- **Seats:** the pegs take a firm, even press and stop dead on the body face, with no click. The hood swings on its Ø5 stubs
  with 0.15 radial clearance (`PIN_CLR`).
- **Release:** none in the plan. checks.json calls the journal plate "not serviced" (DESIGN_LOG joint table, FST_jp). In the
  machine the right post holds it on (+X blocked at 0.4, review row R1 v3-A1-04). On the bench, pry it off evenly.
- **Check:** the hood swings freely and the stud doesn't spin in its pocket.

### 6e. Thumbwheel, leaf, nip cover

- **Fasteners:** 1 M3 nut (`FST_tw_nut`).
- **Do:**
  - slide the nut into the thumbwheel's radial side slot (it sits under a 0.5 skin). A drop of superglue keeps it there;
  - thread the thumbwheel onto the stud and set the gap;
  - drop the leaf into the nip cover's T-slot, root block between the roof and the land, stud in its fork;
  - slide the nip cover -V along the land's 45 deg dovetail until the detent clicks at the rebate stops.
- **Seats:** one click from the detent arm's 0.45 bump (13.8 MPa, in plane [flexures]). The leaf preload bears on the
  dovetail faces, never on the detent (DESIGN_LOG joint table, FST_nipcover).
- **Release (service "nip leaf", in the machine at tilt 45, powered):** press the detent, slide the cover +V off its
  dovetail, then slide the leaf out of the T-slot [slide: v3-A1 nip cover + leaf slide off the land's dovetail]. While the
  cover is on, the leaf is captive (blocked at 1.0 [slide: v3-A1 nip leaf captive]).
- **Check:** with the cover on, a fingertip rolls the thumbwheel through the 22 x 8.3 slot between its two printed stops,
  gap 6.2..7.0. The spare leaf goes in the bag, unloaded, as the creep reference.

### 6f. Tape and flywheel

- **Tools:** knife, calipers, 2.5 mm L-key.
- **Fasteners:** 2 x M3 x 20 socket cap + 2 M3 nuts (`FST_fw_bolt_0/1`, `FST_fw_nut_0/1`, the pinch bolts).
- **Do:**
  - wrap the 1 in tape once round the land, sticky side down;
  - cut both ends square and **butt-join them, no overlap**;
  - trim both edges with the knife against the flanges to the 13.8 land;
  - slide the wheel onto the D-shaft and tighten the pinch bolts through their nuts with the L-key from +X.
- **Check:** caliper the tape at three places and at the seam: **0.5 or less** (`TAPE_T`). An overlap doubles it and eats the
  0.098 entry-arc margin (8.098 against 8.0 at the min stop [distances]), so re-wrap if needed. The wheel spins with no rub;
  it comes off +X at tilt 45 with 1.59 to spare [slide: flywheel off +X at tilt 45].

### 6g. Wheel-side cover

- **Do:** slide the cover's 2 hook tabs and its latch hook under the journal plate's edge. On the bench at tilt 0 that means
  moving the cover backward and up together (-Y +Z; it comes out along `insert_dirs` (0, 0.71, -0.71)). Keep going until the latch clicks.
- **Seats:** one click from the 0.8 latch hook (13.0 MPa, in plane [flexures]).
- **Release (service "tape / flywheel", tilt 45):** press the latch and slide the cover +Y off its hook tabs [slide: v3-A1
  wheel-side cover slides off +Y]. Then loosen the pinch bolts with the 2.5 L-key (15.5 of reach at tilt 45 [service]).
- **Check:** spin the wheel by hand: silent.

## Pod, tilt and beam

### 7. Pod into the post U-slots (merge)

- **Do:** hold the pod nose-up about 20 deg and lower it straight down until both journals seat in the U-slots, then level
  it. Nothing is back-driven: the tilt servo isn't in yet (step `pose_how`). Route the phase and encoder bundle out of the
  left journal.
- **Check:** both journals sit fully down in their slots. Lifting it out the same way clears with 0.2 [slide: v2-A1-06 step
  7 reversed].

### 8a. Tilt drive, bench

- **Tools:** 2.5 mm hex L-key.
- **Fasteners:** 1 x M3 x 6 socket cap (`FST_tilt_horn_ctr`, the centre screw, through the Ø6.5 key hole).
- **Do:** press the horn into the tilt horn adapter's pocket (8 pins), as at 1a. Fit the adapter to the tilt servo's spline
  **with the servo at mid**, then drive the centre screw.
- **Seats:** as at 1a: the horn drops flat once all 8 pins line up.
- **Check:** the double-D key's flats (12 AF) are square to the servo body, so they stand vertical at tilt 0.

### 8. Tilt servo dropped into the right post (merge)

Render: `renders/s08_tilt_servo_in_post.png`.

- **Do:**
  - hold the pod level by hand (tilt 0);
  - lower the servo, horn and adapter straight down (-Z) into the right post's open-top pocket, with the key going into the
    journal plate's top-open fork (12.3 slot, 0.15 a side);
  - pull the tilt bus lead down the right post channel and through the turntable tunnel to the hub bore. The tunnels are
    closed, so push a stiff wire or nylon line through first and draw the lead after it.
- **Seats:** it slides down freely and stops on the pocket floor, with no click. The beam holds it in at step 9.
- **Release (service "tilt servo swap"):** jar, crown and beam off; the servo, horn and adapter lift out +Z at tilt 0 with
  0.15 to spare [slide: v3-A1 tilt servo + adapter lift +Z]. Undo the centre screw on the bench.
- **Check:** the pod doesn't move unless the servo turns: there is no free play at the key.

### 9. Beam (hotfix reprint)

- **Do:**
  - lower the beam (feed floor and spout integral) onto the posts. Its tongues go into both U-slots and over the servo
    pocket, and its 4 hooks go into the slots in the post tops;
  - push down evenly over both posts until all 4 hooks click;
  - lay the launcher bundle (phases + encoder, in the 6 mm sleeve) down the left post channel and through the tunnel, with
    the pull line.
- **Seats:** 4 clicks, two per post. The barbs flex 0.5 past the post-top ledges (9.2 MPa, across layers [flexures: v3-A1
  beam hook post L/R front/rear]). With the hotfix hooks (2.2 wide, 0.3 clear of the release-slot jambs [distances: A2
  hotfix (v3-A1-01) beam-hook barb]) each barb drops under its ledge. The beam then rests on the post tops (beam to
  turntable 0.0, hotfix review).
- **Release (service "tilt servo swap"; jar and crown off; pod at tilt 0):**
  - each post has a 2.8-wide release slot in its inner face at each hook (2 per post, 39 apart);
  - push each barb outboard 0.7 with a flat screwdriver no wider than 2.5 (12.9 MPa at release), holding both hooks on one
    post released while you lift that end;
  - the beam and feeder lift +Z [slide: v3-A1 beam + feeder lift +Z, flexed 5.84 mm³];
  - do it at tilt 0: from the front and rear openings, a straight line reaches every barb at tilt 0, but at tilt 45 the
    nacelle blocks the right-front one (review v3-A1-05, sightlines).
- **Check:**
  - lift each end of the beam gently: it rises no more than about 0.1 [slide: A2 hotfix (v3-A1-01) beam hooks hold, blocked
    at 0.1];
  - the tilt servo is captive: the beam's tongue stops it at 0.75 [slide: v3-A1 the beam keeps the tilt servo captive].
  - **Don't swing the pod by hand from here on:** that back-drives the tilt servo's gears. The tilt range is checked under
    power at step 16 (printed stops at -3 and +46).

## Feeder

### 10a. Disc

- **Do:** lay the feeder disc on the beam's feed floor, gear band down, in the **park** position: solid disc over the outlet,
  with the pockets at ±60 from it (`FEED_FIRE`).
- **Check:** looking down the outlet at the drop axis (x 21, y 0), you see solid disc, not a pocket.

### 10b. Crown upside down, bench: servo and pinion

- **Do:**
  - turn the crown upside down;
  - push feeder servo #3, horn on, up into the closed lobe pocket from below, past the 4 crush ribs (0.1 interference,
    `CRUSH_RIB`), until its top meets the lobe roof (0.05);
  - press the feeder pinion onto the horn (8 pins), **servo at mid**;
  - lead the feeder bus lead out of the lobe.
- **Seats:** a firm push over the ribs and a dead stop on the roof. The pinion presses on with no click. The pinion has no
  centre screw: spline friction holds it, and if it slips it can only drop 0.3, onto the feed floor (review v3-A1-08).
- **Release:** with the crown off the machine, the servo, horn and pinion come out of the lobe -Z, min 0.35, 9.62 mm³ of rib
  crush [slide: v3-A1 feeder servo + horn + pinion out of the lobe -Z].

### 11. Crown onto the beam (merge)

Render: `renders/s11_crown_on_beam.png`.

- **Do:**
  - lower the crown straight onto the beam: the pinion meshes the disc band (disc at park, servo at mid), the disc land goes
    into the crown lip, and the 3 hooks go through their slots in the beam;
  - push down until all 3 hooks click;
  - feed the feeder bus lead down through the beam, then the left post channel and the tunnel.
- **Seats:** 3 clicks as the 0.55 barbs snap out under the beam's pocket roofs (10.3 MPa, across layers [flexures: v3-A1
  crown hook]). The crown then can't lift: the review's captive row stops it at 0.15.
- **Release (service "feeder servo swap", jar off):** from under the beam (about 10 mm over the pod), press each of the 3
  barbs inward 0.6 with the flat screwdriver (12.3 MPa), and lift the crown group +Z. It clears with 0.14, and the disc stays
  on the feed floor [slide: v3-A1 crown group lifts +Z]. The line to the +X hook reaches at tilt 0 and at tilt 45 (review
  sightlines).
- **Check:** the crown sits flat on the beam all round, and the disc turns with the servo.

## 11a. Bus splice from below

No tilt pose and no cover to remove: the turntable's closed tunnels and printed bore roof replace v2's groove cap (review: V2
A7-01 FIXED).

- **Tools:** side cutters, wire strippers, soldering iron, heat gun, card or foil, pull line.
- **Do:**
  1. Jar not fitted yet, floor off. Lay the shell on its side.
  2. Pull the tilt, feeder and pan leads down out of the hub-gear bore.
  3. Cut the hub-end plug off each lead.
     - **Trim the tilt and feeder leads to route + 70** (BOM item 14). Their routes are 203.7 on the 300 lead and 324.6 on
       the 500 lead [cables].
     - The pan lead uses 290.2 of its 350 (U-loop 277.5 + tail 12.7) [cables.chains: pan bus lead]. Leave it long.
     - Strip the leads and solder like wires 3-to-1: V+ to V+, GND to GND, signal to signal. Shield the PLA with card or foil.
     - Heat-shrink each joint (4.8 mm), then the three together (12.7 mm).
     - **The finished splice must be Ø10 x 20 or smaller** (BOM 14a).
  4. Push the splice up the hub-gear bore to its seat: bottom z 72, top z 92 (`BUS_JCT`). It passes the hub-gear bore with
     1.0 and the bore wall with 6.574 [distances: v2-A5-03].
  5. **Service length:** the model gives no home to the 2 x 70 of trimmed spare (review v3-A1-07, still open). Push the
     tilt lead's spare back up toward the right post channel and the feeder lead's toward the left, so the bore under the
     splice stays clear.
  6. **Bundle hand-over:** where the launcher bundle sleeve meets the base-lead sleeve (az 235, r 4, z 70), overlap the
     sleeves loosely, with no tie. It swings a 5.7 chord over ±90 pan (BOM section 1, accepted warn).
- **Seats:** the splice can't climb more than 8.0, because the printed bore roof at z 100 stops it [slide: v3-A1 the
  turntable's bore roof keeps the splice captive, blocked at 8.1].
- **Release (service "bus splice"):** with the floor off, the splice pulls -Z out of the hub-gear bore with 1.0 to spare
  [slide: v3-A1 bus splice pulls -Z].
- **Check:** turn the turntable slowly to both pan stops and watch from below: nothing pulls tight.

## Base floor

### 12. Floor, bench: MotorGo, buck, controller

Render: `renders/s12_floor_bench.png`.

- **Do:**
  - slide the MotorGo down its 2 card guides (1.77 PCB in a 2.07 slot, `MG_GUIDE`) to the slot-bottom stop. Its components
    face -Y and the USB-C receptacle points up;
  - slide the buck +X under its 2 hook rails (45 deg lips over its two fin-free flange strips) to the end stops;
  - lay the servo controller in its +0.4 fences on its 4 seat bosses, and press it down until both tongues click over its
    short edges. Don't drill the bosses: in v3 the board has no screws (BOM item 6);
  - press the UART lead into the 2 floor clips (`UART_CLIPS`), with a dab of hot glue.
- **Seats:**
  - MotorGo: it slides with light friction and stops on the slot bottom, with no click;
  - buck: it slides freely and stops on the end stops [slide: v3-A1 buck +X, blocked at 0.4];
  - controller: 2 clicks as the 1.0 lips pass the PCB edges (12.8 MPa, in plane [flexures]). It is then held down within
    0.3 [slide: v3-A1 servo controller held down].
- **Release, on the bench:**
  - MotorGo: unplug the USB-C and slide it +Z out of the guides (min 0.15 [slide: v3-A1 MotorGo slides +Z]);
  - buck: slide it -X off its rails [slide: v3-A1 buck slides -X];
  - controller: press both tongues outward (15.4 MPa at release) and lift it. No slide row covers this (BOM section 5).

### 13. Base cables, floor into the shell (merge)

- **Tools:** soldering iron.
- **Do:**
  1. With the floor held under the open shell, connect the base cables:
     - 12 V: adapter to buck, buck to MotorGo, buck to controller;
     - UART, USB-C and the pan bus lead to the controller;
     - the launcher base lead: the three phases soldered to the MotorGo J6/J8 pads (BOM item 13), and the encoder JST.
  2. Check that both U-loops hang free under the hub gear. They are the ±90 pan slack.
  3. Push the floor straight up (+Z) into the shell until all 4 arms click into the wall-foot keepers.
- **Seats:** 4 clicks: the 2 +Y latches (16.1 MPa engage, in plane) and the 2 -Y detents (14.0 MPa, in plane) [flexures].
  When it is home:
  - the deck ribs sit 0.75 over the MotorGo [slide: v3-A1 MotorGo captive];
  - the shell's -X ribs hold the buck at 0.4 [slide: v3-A1 buck captive -X];
  - the floor's column backs the pan servo at 0.5 [slide: v3-A1 pan drive captive].
- **Release (service "base floor"):** press the 2 +Y latches through their finger holes (21.4 MPa at release). The -Y
  detents have 45/45 barbs and pop out on the pull. The floor drops -Z with the electronics, with 1.6 to spare [slide: v3-A1
  base floor + electronics drop -Z]. The phases are soldered, so lower it gently on its leads and unplug the rest as it
  comes down.
- **Check:** the floor sits flush all round. Turn the turntable to both pan stops: nothing pulls tight or rubs the gears.

## Jar, battery, power-up

### 14. Jar, bench (gate and adapter are hotfix reprints)

Render: `renders/s14_jar_bench_from_below.png`. If you did `MEASURE_FIRST.md` item 3, this group is already built; skip to
step 15.

- **Do, in this order** (the gate can't go in once the adapter is on, DESIGN_LOG feeder item):
  1. **Gate:** check its slots first (`MEASURE_FIRST.md` item 3a). Slide it -X into the valve's slot under the cheek pads,
     stop lug up, until its closed finger clicks into the closed notch.
  2. **Jar:** fill it upright, put the printed adapter disc into the band in place of the flat lid, and screw the band on.
  3. **Valve onto the spout:** hold the valve and gate upside down over the upright jar (gate closed). Push them straight
     down onto the adapter spout: the spout-tip notch goes over the gate's stop lug and the valve's key rib goes into the
     spout's key groove. With the gate closed, its open-detent bump sits in the adapter's widened closed notch with 0.35
     clear (BOM hotfix notes). Push until both cheek fingers click into the spout groove and the spout shoulder sits on
     the cheek tops. Then turn the whole group over. (BOM step 14 describes the same joint the other way up, with the jar pushed down
     onto the valve; with the jar already filled, this way round spills nothing.)
- **Seats:**
  - gate: one click at closed (the finger's 0.4 bump, 14.0 MPa, in plane; about 0.7 N to walk out, hotfix review);
  - valve: 2 clicks from the cheek fingers (0.4 deflection, 11.0 MPa, across layers [flexures: v3-A1 valve snap finger
    ±Y]). The adapter stops when its shoulder lands on the cheek tops. The key groove runs 1.0 past the rib, so the rib
    can't hold it up [distances: A2 hotfix (v3-A1-01) valve key rib top].
- **Release:** none in the plan. The gate is captive once the adapter is on, and no service row separates the adapter from
  the valve. For a refill, unscrew the glass from the band: the band, adapter, valve and gate stay together as one group.
- **Check:**
  - **shoulder contact (hotfix review N1):** press the group together and look at the ±Y cheek pads from the side, against a
    light. There must be no daylight between the shoulder and the pad tops, and a 0.1 feeler mustn't go in. The group mustn't
    rock on the valve. The shoulder's underside is a 45 deg chamfer, so the jar's weight bears on a line at the pads' inner
    top edge (r 27.65). If that contact is lost, the weight goes onto the 2 cross-layer valve fingers. Don't run it like
    that: see `MEASURE_FIRST.md` item 3b;
  - **gate open (hotfix, v3-A1-03):** pull the tab +X. About 1 mm before the hard stop you feel a light click, and the gate
    stays open [slide: A2 hotfix (v3-A1-03) gate held open, blocked at 0.2]. It stops hard at 52.35 [slide: v3-A1 gate open
    stop]. The open click is lighter than the closed one: about 0.4-0.5 N to walk out (hotfix review hand calc);
  - **gate closed:** push it -X past the open click until the closed finger clicks into its notch [distances: v3-A1 gate
    detent finger seated, 0.1].

### 15. Jar onto the feeder (merge)

- **Do:** close the gate. Drop the jar group into the crown socket at +30 and twist it to 0 (`PIV_jar` 30).
- **Check:** the jar is locked. Twisting it back to +30 lifts it off [slide: jar group lifts off when unlocked].
- **Release (service "refill"):** close the gate (closed click), twist to +30 and lift. Unscrew the glass from the band,
  refill, screw it back on. Carry the jar group by itself, never the machine by the jar.

### 16. Battery and first power-up (bench, wheel not spinning)

- **Do:** slide the pack onto the adapter rail from +X. It comes off again with no tool, with 1.6 to the floor along the way
  [slide: battery out +X].
- **First power-up:**
  1. Power up with the flywheel motor disabled.
  2. Ping each servo by ID.
  3. Command tilt 0 and check the pod is level. If it isn't, set a tilt offset in firmware rather than moving the horn.
  4. Command pan 0 (pod facing +Y) and the feeder to park (solid disc over the outlet), and trim any offsets.
  5. Clamp firmware tilt to 0..45; the printed stops are at -3 / +46.
  6. Only then spin up the flywheel.
- **Check:**
  - one fire command (disc +60, back to 0) drops exactly one candy, and the next shot uses -60 [index: one window at +60 and
    one at -60];
  - log the leaf preload on day 0 (v2 BOM section 0, "Leaf creep").
