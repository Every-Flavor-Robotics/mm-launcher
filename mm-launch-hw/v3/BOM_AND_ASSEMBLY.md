# M&M Launcher Turret v3 (min-hardware): BOM and Assembly (attempt 1)

v3 is the min-hardware, min-part-count branch of v2 attempt 7 (`DESIGN_BRIEF.md`). The machine works the same way: the
jar, feeder, nip, flywheel, drop path, index and payload rows are v2's, re-run on the v3 model. Only how the parts are
held together has changed. The v2 document (`../v2/BOM_AND_ASSEMBLY.md`, section 0) still describes how the machine works.

All dimensions are in mm. Every number comes from `blender/params.py`, and each subsystem is one module in `blender/parts/`.
The 25 printed parts are in `stl/`, in print orientation. Evidence comes from `blender/cadcheck.json` (tools c2c282d).
Rows added in v3 attempt 1 carry the tag `v3-A1`; older rows keep their v2 tags. Each claim names the row it comes from:
`[slide: ...]`, `[service: ...]`, `[flexures: ...]`, `[distances: ...]`, `[fasteners: FST_x]`, `[cables]`, `[stability]`,
`[parts]`, `[printcheck]` or `[cad q ...]`. `manifest.json` `parts.<name>.bom_item` names the purchased item behind
`FST_nip_stud`, `CAB_encoder`, `CAB_bus_*` and `BUY_bus_junction`. `parts/finish.py` builds those texts from params and the
built paths, so they follow the model.

## Evidence summary

- **Counts** (build output):
  - `FASTENERS 11 screws, 4 distinct spec x length: M3_cap x 20 (2), M3_cap x 6 (2), M3_hex x 16 (1), M3_pan x 10 (6)`
  - `PARTS 25 printed, 14 metal (11 screws, 3 nuts/pins)`
  - v2 attempt 7 had 103 screws, 4 nuts, 18 specs and 36 printed parts. The brief's targets are <= 24 metal pieces, <= 4
    specs and <= 26 printed parts. The plan listed "10 screws + 4 nuts". That is the same 14 pieces with the
    `M3_hex` nip stud counted as a nut/pin. The build counts the stud as a screw.
- **Full `cad check`: PASS, 0 fail, 61 warn, 0 untriaged, 0 config warns.** `stale_accepts` `[]`, `summary.unused_allows`
  `{}`, `poses_past_limits` `[]`, `assembly.held_poses` `[]`, `assembly.unordered_solids_assumed_present` `[]`. Every warn
  is in `accepted_warns` in the `{check, kind, object, why}` form, and none uses the old substring `match` (section 7).
- **`cad printcheck stl --manifest blender/manifest.json`: PASS, 25 parts, 0 fail, 9 warn**, all 9 accepted with a reason
  (section 7). Every part fits the P1S (256 x 256 x 256). The largest are `base_shell` 241.2 x 240 x 87 and
  `turntable` 216 x 216 x 160 [parts].
- **`cad bom BOM_AND_ASSEMBLY.md blender/manifest.json`**: 0 disagree, 0 modelled screws in no row (section 2).
- **Stability**: worst tip angle 29.6 deg over 3456 poses (pan -90, tilt 45, feeder -60), 4075 g [stability].
- **Drop / nip / index / payload (v2 rows, unchanged and passing):**
  - drops: 31/31 rays hit at every pose; flattest slide 34.5 deg at tilt 46 [drop];
  - nip, swept entry arc at full lift: 8.098 / 8.222 / 8.415 >= 8.0 at the min stop, home and max stop [distances];
  - index: one window at +60 and one at -60, column never open at drift 0/5/10/15 [index];
  - payload: the min pair is blocked; the max flat candy fits with a 0.14 margin [payload].

## 1. Purchased parts

| # | Part | Qty | Model object | Mass (g) | v3 mounting (no screws unless named) |
|---|---|---|---|---|---|
| 1 | MotorGo Axis (ESP32-S3 BLDC driver) | 1 | `BUY_motorgo_axis` | 25 | Slides down 2 card guides on the floor's partition wall (1.77 PCB + 0.3) to a slot-bottom stop. A deck rib sits 0.75 over its top edge [slide: v3-A1 MotorGo captive, blocked by `PRT_base_shell` at 0.75]. No M2.5 screws. |
| 2 | XTEAM XTI-3674 1900KV inrunner | 1 | `BUY_motor` | 200 | Nacelle bore (crush ribs). The 4 motor-face screws clamp the launcher body and the nacelle plate together. |
| 3 | Plink MT6701 encoder + JST cable | 1 | `BUY_plink_encoder` | 3 | On the encoder cap pegs. The cap snaps into the nacelle (2 in-plane arms). |
| 4 | Diametric magnet Ø6 x 2.5 | 1 | `BUY_magnet` | 1 | Glued to the rear shaft with the encoder jig (v2 tool print). |
| 5 | Hiwonder bus servo + round horn | 3 | `BUY_servo_pan/tilt/feeder`, `BUY_horn_*` | 66 + 4 each | Pan: the mount is pressed onto 4 deck posts and backed by the floor column. Tilt: drops into the right post's open-top pocket, and the beam tongue closes the pocket. Feeder: goes up into the crown lobe (crush ribs). Each horn sits in a 2.7 pocket with 8 printed Ø2.0 pins, so there are no horn screws. |
| 6 | Hiwonder bus servo controller | 1 | `BUY_servo_controller` | 30 | +0.4 fences plus 2 in-floor snap tongues over its short edges [slide: v3-A1 servo controller held down, blocked at 0.3]. |
| 7 | DeWalt 20V battery adapter | 1 | `BUY_dewalt_adapter` | 90 | 4 deck fences take the shear. **2 x M3 pan x 10** (diagonal corners, counterbored flush) go into the adapter's own holes. |
| 8 | DeWalt 20V battery | 1 | `BUY_battery` | 620 | Slides onto the adapter rail, last; it comes out +X [slide: battery out +X, min 1.6]. |
| 9 | 12 V buck converter, finned 73.8 x 73.8 x 31 | 1 | `BUY_buck_12v` | 180 | Its flange strips slide +X under 2 floor hook rails (45 deg lips) to end stops. 2 shell wall ribs hold the -X end [slide: v3-A1 buck rows, blocked at 0.4 / 0.6 / 0.4]. |
| 10 | USB-C cable, straight plug | 1 | `BUY_usbc_plug`, `CAB_usb` | 10 | Plugs vertically into the MotorGo and leaves through the rear niche. |
| 11 | Ball/Kerr regular-mouth pint jar + its metal band | 1 | `BUY_jar`, `BUY_jar_band` | 350 + 15 | The user's own. The jar stack sits 36 higher than in v2 (`params.JAR_LIFT`, so that the crown prints top-down). About 400 g of M&Ms (`BUY_mm_fill`). |
| 12 | Cloth hockey tape, 1 in (25 mm), trimmed to the 13.8 land | about 0.25 m | `BUY_tape` | 2 | Flywheel land R35..35.5 (`TAPE_T` 0.5). Butt-join the ends, no overlap, and check the wrap is 0.5 or less with calipers (v2-A5-02). |
| 13 | 16 AWG silicone wire, 3 colours, + braided sleeve | 3 x 700 | `CAB_phase_*`, `CAB_launcher_bundle`, `CAB_launcher_base` | - | Motor leads (80, path 62.5) are extended in the journal bore. Each phase is one wire from that splice to the MotorGo pads: 481.1 of 700 [cables.chains: phase conductors (BOM item 13)]. The bundle runs 262.6 of 350 and the base lead 156.1 of 250 [cables]. |
| 14 | 3-pin Hiwonder servo bus leads | 3 | `CAB_bus_pan` + `CAB_bus_pan_tail`, `CAB_bus_tilt`, `CAB_bus_feeder` | - | **Pan 350:** one wire, static U-loop 277.5 + `PIV_pan` tail 12.7 = 290.2 of 350 [cables.chains: pan bus lead]. It is handed over on the pan axis at (0, 0, 63) (`BUS_PAN_AX`). **Tilt 300:** route 203.7. **Feeder 500:** route 324.6 [cables]. Cut the hub-end plug off each lead. Trim tilt and feeder to their route + 70 (solder length, later the service loop). |
| 14a | 3-way bus junction (star splice) | 1 | `BUY_bus_junction` | 8 | 3 x 3-to-1 solder splices under heat shrink, sleeved together, **20 long or less**. Modelled as a Ø10 x 20 envelope on `PIV_pan` in the R14 hub-tube bore at r 7 / az 35, z 72..92. Soldered below the deck at step 11a and pushed up the bore. The turntable's printed bore roof (z 100) stops it rising [slide: v3-A1 the turntable's bore roof keeps the splice captive, blocked by `PRT_turntable` at 8.1]. Splice to bore 6.574 (>= 1.0) [distances: v2-A5-03]. |
| 15 | 5-wire JST-SH encoder lead, >= 550, one piece, twisted | 1 | `CAB_encoder` (+ bundle and base) | - | Plink to MotorGo, unspliced. In the journal bore it runs on the far side of the sleeve from the 3 phases: S -1.6 vs S +0.5, so the two no longer share a tube (v3-A1 finish). Route 504.6 against 545 (lead less the plugs) [cables.chains: encoder signal (BOM item 15)]. `CAB_encoder` route 85.9, budget 126.3 (`parts/finish.py`). |
| 16 | UART lead, 4-wire | 1 | `CAB_uart` | - | Lead 300, routed 213.8 [cables]. |
| 17 | 12 V leads | 3 | `CAB_12v_in/mg/ctrl` | - | Leads 200 / 100 / 250, routed 119.4 / 45.2 / 168.8 [cables]. |

**Bundle hand-over (accepted warn, v2 review A6-02):** the launcher bundle and base lead meet at `BUS_LB_JCT` (az 235, r 4,
z 70), off the pan axis. The end swings a 5.7 chord over ±90 pan. Join the conductors with the sleeve loose over the joint
(no zip tie) so it can flex 6 mm. The pan axis below z 72 already carries the pan-bus tail.

## 2. Fasteners (from `manifest.json`)

All metal is M3, in 4 spec x length combinations. No screw holds two printed parts together. Each one is a motor mount, a
servo centre screw, the purchased adapter, the flywheel clamp or the nip adjuster (brief: "Metal that is allowed").

| Size | Qty | Objects (assembly step) |
|---|---|---|
| M3 x 10 pan | 2 | `FST_adapter_0/1` (1): DeWalt adapter to the deck, diagonal corners, counterbored flush; thread 8.5 in the adapter [fasteners: FST_adapter_0/1]; tips 5.46 above the battery face (>= 3) [distances: FST_adapter_0/1-BUY_battery] |
| M3 x 10 pan | 4 | `FST_motor_*` (6a): from inside the guard into the motor face, clamping body + nacelle; engagement 4.5 [fasteners] |
| M3 x 6 cap | 2 | `FST_pinion_ctr` (1a), `FST_tilt_horn_ctr` (8a): servo centre screws, driven on the bench through the part's Ø6.5 hole; engagement 6.0 in the horn [fasteners] |
| **M3 x 16 hex head, ISO 4017 (AF 5.5 x 2.0)** (stud) | 1 | `FST_nip_stud` (6c/6d): captive head in the hood's hex pocket, never driven (`fasteners.captive`); 2.4 thread in `FST_tw_nut` [fasteners: FST_nip_stud] |
| M3 x 20 cap | 2 | `FST_fw_bolt_0/1` (6f): flywheel pinch bolts through `FST_fw_nut_0/1`; 2.5 L-key at tilt 45 [service: v3-A1 tape / flywheel, L-key 15.5] |
| M3 hex nut | 3 | `FST_fw_nut_0/1` (6f), `FST_tw_nut` (6e, slid into the thumbwheel's side slot); none exposed [fasteners.nuts] |

Every modelled screw passes the head-buried, engagement, bolt-to-nut, purchased-part and access checks at its step [fasteners]
(0 fails, 0 fastener warns).

## 3. Printed parts (25, PLA, no supports)

Colours (`params.COLOUR_B`): **B = terracotta** for the candy path and touch points; **A = warm grey** for structure and
drivetrain. The beam now carries the v2 feeder housing's spout but stays A (structure). Grams and hours are the cadcheck
estimates [parts]. Every part is `supports: no`, backed by `cad printcheck` with 0 fails (the warns are in section 7).

| STL | Colour | Infill % | Print orientation (manifest `orient`) | g | h | v3 change |
|---|---|---|---|---|---|---|
| base_shell | A | 15 | upside down: deck face on the bed, walls up | 355.2 | 6.73 | 8 floor columns gone, keeper pockets, -X buck ribs, deck MotorGo ribs |
| base_floor | A | 15 | flat; partition wall, card guides, hook rails and bosses up | 168.0 | 3.24 | + partition (merged), 2 latches, 2 detents, 2 controller tongues |
| pan_servo_mount | A | 30 | plate top on the bed, pocket walls up | 27.5 | 0.61 | pressed onto 4 deck posts (crush ribs) |
| pan_pinion | A | 40 | gear top on the bed, horn pocket up (8 pins grow up) | 13.4 | 0.35 | horn pocket + 8 pins |
| thrust_ring | A | 100 | flat | 11.9 | 0.32 | - |
| turntable | A | 20 | bottom face on the bed, posts upright (tunnel and hub roofs bridge <= 24.7) | 340.9 | 6.46 | + post_L, post_R (merged), tunnels, bore roof |
| hub_gear | A | 40 | gear face on the bed, R20 hub tube up (3 snap fingers, 3 dogs) | 15.6 | 0.39 | + hub tube, snaps up into the turntable |
| beam | A | 30 | top face (feed floor, z 263) on the bed; spout, tongues and 4 snap hooks up | 93.8 | 1.85 | + feeder housing (merged), 4 hooks |
| tilt_horn_adapter | A | 60 | key end (-X) on the bed; 45 deg cone, horn pocket up (8 pins grow up) | 2.7 | 0.15 | horn pocket + 8 pins, double-D key |
| nacelle | A | 25 | front plate on the bed, journal up (duct roof bridges 15) | 124.3 | 2.42 | encoder counterbore + snap groove |
| launcher_body | B | 25 | left (motor) wall outer face on the bed; every wall vertical | 69.3 | 1.39 | + nip stop (merged), hinge stub, 3 journal-plate pegs, dovetail land |
| journal_plate | A | 30 | inner face on the bed; lap step, journal, fork and stop lug grow up | 9.5 | 0.28 | top-open fork, hinge bore, 3 crush-rib peg holes |
| launcher_cover | A | 25 | inner face on the bed | 25.3 | 0.57 | 2 hook tabs + in-plane latch arm |
| hood | B | 40 | on its side face (profile extruded, all walls vertical) | 10.2 | 0.29 | O5 hinge stubs |
| nip_wheel | B | 50 | outer face on the bed; integral max-gap spigot up; nut slides into the radial side slot | 1.3 | 0.12 | + nip_stop_sleeve (merged as the spigot) |
| nip_leaf | A | 100 | flat: strip's outer face on the bed (bending in the layer plane). Print 2: one fitted, one spare | 3.5 | 0.16 | root block slides into the cover's T-slot |
| nip_cover | A | 30 | +v end on the bed; shell and end walls grow up; finger slot 22 x 8.3 | 8.8 | 0.26 | dovetail tongue + skirt lip + in-plane detent |
| flywheel | B | 100 | motor-side web face on the bed; rim and hub up | 41.2 | 0.87 | - |
| encoder_cap | A | 40 | back face on the bed, spigot and pegs up | 7.1 | 0.23 | 2 in-plane snap arms |
| feeder_crown | A | 20 | top plane (z 322) on the bed; 3 snap hooks grow up | 113.3 | 2.22 | + feeder_cover (merged), one top plane, 3 hooks |
| feeder_pinion | A | 60 | gear face on the bed, horn pocket up (8 pins grow up) | 12.0 | 0.32 | horn pocket + 8 pins |
| feeder_disc | B | 40 | gear band on the bed, fins up | 17.0 | 0.42 | - |
| jar_adapter | B | 40 | lid disc (glass side) on the bed, spout up | 8.0 | 0.25 | key groove + snap groove on the spout |
| jar_valve | B | 40 | skirt + baffle bottom on the bed; lug undersides 50 deg; snap fingers up | 48.3 | 1.00 | 36 taller skirt, 2 cheek snap fingers, key rib |
| jar_gate | B | 100 | flat; the detent finger bends in the layer plane | 8.9 | 0.27 | + in-plane detent finger (replaces gate_detent) |

Gone since v2 (11 parts): base_partition, pan_servo_clamp, groove_cap, post_L, post_R, post_R_cover, feeder_housing,
feeder_cover, nip_stop, nip_stop_sleeve, gate_detent. Each was merged or made unnecessary; DESIGN_LOG "Attempt 1: plan",
joint table.

## 4. Assembly (the same steps, in the same order, as `checks.json` `assembly_order`)

cadcheck tests each screw's tool access at the step where it is driven, with only the parts of earlier steps present. Each
part, and each bench group at its merge, must come out along a straight line past the earlier parts [insertion]. "Bench"
steps are sub-assemblies, merged later. The labels are the checks.json labels; there are no steps 3, 4 or 5.
`assembly.unordered_solids_assumed_present` is `[]`, and no step moves a servo-held joint before power
(`assembly.held_poses` `[]`).

- **1** Base shell upside down. Put the DeWalt adapter into its 4 deck fences. Drive 2 x M3 pan x 10 (diagonal corners,
  counterbored flush) from the deck top into the adapter's own holes.
  - **1a** (bench, pan drive) Press the horn into the pinion's 2.7 horn pocket so the 8 printed pins go into the horn
    holes. Put the servo into the mount pocket (0.3 clearance). Press the pinion + horn onto the spline. Drive the centre
    screw (M3 x 6 cap, 2.5 L-key) through the pinion's Ø6.5 hole.
  - **1b** (merge) Stand the shell on its walls, floor off. Press the pan drive up onto the 4 deck posts (crush ribs). The
    pinion is now trapped between the mount plate and the deck.
- **2a** Thrust ring on the deck. Turntable (posts integral) onto the ring.
- **2b** Push the hub gear (with its R20 hub tube) up from below through the deck hole into the turntable socket. Line up the
  3 dogs; the 3 snap fingers click over the socket ledge (12.6 MPa [flexures: v3-A1 hub snap finger 1..3]; `insert_ok`: the
  barbs flex past).
- **6a** (bench, pod) Motor into the nacelle bore (crush ribs). Body onto the nacelle plate; both centre on the motor's
  front boss. Drive 4 x M3 pan x 10 from inside the guard. Phase leads into the journal bore.
- **6b** (bench, pod) Glue the magnet with the jig. Plink onto the cap pegs. Push the encoder cap -X into the nacelle
  counterbore until its 2 arms click (keyed; 14.6 MPa in the layer plane [flexures]).
- **6c/6d** (bench, pod) Hood onto the body's -X hinge stub. Pass the hex stud (M3 x 16 ISO 4017) head-first through the
  guard slot into the hood's hex pocket (captive). Press the journal plate -X onto the body's 3 crush-rib pegs, with its
  bore over the hood's +X stub.
- **6e** (bench, pod) Slide the nut into the thumbwheel's side slot. Thumbwheel onto the stud; set the gap. Drop the leaf
  into the nip cover's T-slot (root block between the roof and the land, stud in its fork). Slide the nip cover -V along
  the land's 45 deg dovetail until the detent clicks at the rebate stops (13.8 MPa [flexures]).
- **6f** (bench, pod) Flywheel onto the D-shaft. Two M3 x 20 pinch bolts through their nuts (L-key from +X). Wrap the
  tape (item 12).
- **6g** (bench, pod) Wheel-side cover onto the body rim: slide its 2 hook tabs and latch hook under the journal plate's
  edge until the in-plane latch clicks (13.0 MPa [flexures]).
- **7** (merge) Hold the pod nose-up about 20 deg (tilt +20) and drop it into the post U-slots. The step's `pose` is
  `PIV_tilt` 20. It is held by hand, and the tilt servo is not in yet, so nothing is back-driven. This clears the
  journal-plate stop lug past the post lug [insertion: no warn; slide: v2-A1-06 step 7 reversed, min 0.2].
- **8a** (bench, tilt drive) Press the horn into the adapter's horn pocket (8 pins). Adapter + horn onto the servo spline.
  Centre screw (M3 x 6 cap) through the 6.5 key hole.
  - **8** (merge) Hold the pod level by hand. Drop the tilt servo + adapter -Z into the right post's open-top pocket, with
    the key into the journal plate's top-open fork. Pull the tilt bus lead down the right post channel and through the
    turntable tunnel to the hub bore (pull cord).
- **9** Lower the beam (feed floor + spout integral) onto the posts. Its tongues close both U-slots and the servo pocket,
  and the 4 hooks click (9.2 MPa engage, 12.9 at release [flexures: v3-A1 beam hook post L/R front/rear]). Run the launcher
  bundle down the left post channel and through the tunnel.
- **10a** Lay the disc on the beam's feed floor.
  - **10b** (bench, feeder) Crown upside down. Feeder servo + horn up into the closed lobe pocket (crush ribs). Press the
    pinion onto the horn (8 pins). Feeder bus lead out of the lobe.
  - **11** (merge) Lower the crown onto the beam: the pinion meshes the disc band and the disc land enters the crown lip.
    The 3 hooks click through the beam (10.3 MPa [flexures: v3-A1 crown hook]). Feeder bus through the beam and down the
    left post channel + tunnel.
- **11a** Bus splice from below, with no tilt pose. Lay the shell on its side, floor still off. Pull the tilt, feeder and
  pan leads down out of the hub-gear bore. Solder the 3-way splice (item 14a) below the deck and push it up the bore to
  its seat.
- **12** (bench, floor) MotorGo down its 2 card guides to the stop. Slide the buck +X under its 2 hook rails to the end
  stops. Press the servo controller into its fences until the 2 tongues click.
  - **13** (merge) Plug in the base cables. Push the floor straight up (+Z) into the shell until the 2 -Y detents and the 2
    +Y latches click into the wall-foot keepers (latches 16.1 / 21.4 MPa and detents 14.0 MPa, in the layer plane
    [flexures]). The shell's -X ribs now hold the buck, the deck ribs the MotorGo, and the floor column the pan servo.
- **14** (bench, jar) Adapter into the band, band onto the jar. Slide the gate -X into the valve's slot until its finger
  clicks into the closed notch (14.0 MPa in plane). Push the jar group straight down onto the valve (key rib in the key
  groove) until the 2 cheek fingers click into the spout groove (11.0 MPa [flexures: v3-A1 valve snap finger ±Y]).
  - **15** (merge) Jar onto the feeder: drop it in at +30 and twist to 0 (`pose` `PIV_jar` 30).
- **16** Battery onto the adapter rail, +X to -X, last. First power (`powered`).

## 5. Service (each row is a cadcheck `service` or `slide_out` result)

**Tools:** a 2.5 hex L-key (flywheel pinch bolts, servo centre screws on the bench) and a small flat screwdriver (beam and
crown hook releases). Everything else is tool-free.

| Task | How | Tool | Evidence |
|---|---|---|---|
| Refill | Close the gate (finger detent), twist the jar to +30, lift it off | none | [slide: jar group lifts off when unlocked] |
| Set the nip gap | Roll the thumbwheel through the 22 x 8.3 finger slot, cover on | none | [sightlines: v2-A3-A2-03 fingertip line reaches the thumbwheel rim first] 3/3 rays at home, tilt 45 and full lift |
| Nip leaf | Tilt 45 (powered). Press the nip cover detent and slide the cover +V off its dovetail. Slide the leaf out of the T-slot | none | [service: v3-A1 nip leaf swap]; [slide: v3-A1 nip cover + leaf slide off the land's dovetail]; [slide: v3-A1 nip leaf captive, blocked by `PRT_nip_cover` at 1.0] |
| Tape / flywheel | Tilt 45. Press the cover latch and slide the wheel-side cover +Y off its hook tabs. Loosen the 2 pinch bolts. The wheel slides off +X | 2.5 L-key | [service: v3-A1 tape / flywheel] L-key 15.5 at tilt 45; [slide: v3-A1 wheel-side cover slides off +Y]; [slide: flywheel off +X at tilt 45] min 1.59 |
| Encoder | Tilt 45. Squeeze the 2 cap arms and pull the cap -X | none | [service: v3-A1 encoder]; [slide: v3-A1 encoder cap pulls off -X] arms bounded at 4.25 mm³ (allow 8) |
| Tilt servo | Jar off, crown off. Release the 4 beam hooks through the post slots and lift the beam. Servo + horn + adapter lift +Z out at tilt 0. Centre screw on the bench | flat screwdriver; L-key on the bench | [service: v3-A1 tilt servo swap]; [slide: v3-A1 beam + feeder lift +Z] hooks 7.97 mm³ (allow 8.5); [slide: v3-A1 tilt servo + adapter lift +Z] min 0.15; [slide: v3-A1 the beam keeps the tilt servo captive, blocked at 0.75] |
| Feeder servo | Jar off. Release the 3 crown hooks from under the beam and lift the crown group. On the bench, the servo comes out of the lobe -Z | flat screwdriver | [service: v3-A1 feeder servo swap]; [slide: v3-A1 crown group lifts +Z] 10.93 mm³ (allow 12), min 0.14; [slide: v3-A1 feeder servo + horn + pinion out of the lobe -Z] min 0.35 |
| Base floor | Press the 2 floor latches through their finger holes. The floor drops -Z with the MotorGo, buck and controller; unplug the leads as it comes down | none | [service: v3-A1 base floor off]; [slide: v3-A1 base floor + electronics drop -Z] min 1.6 |
| Bus splice | Floor off. The splice pulls -Z out of the hub-gear bore | none | [service: v3-A1 bus splice]; [slide: v3-A1 bus splice pulls -Z out of the hub-gear bore] min 1.0 |
| Pan servo | Floor off. The pan drive pulls -Z off the deck posts. Centre screw on the bench | L-key on the bench | [service: v3-A1 pan servo swap]; [slide: v3-A1 pan drive off the deck posts -Z] min 0.14; [slide: v3-A1 pan drive captive, blocked by `PRT_base_floor` at 0.5] |
| Electronics on the floor | On the bench: the MotorGo slides +Z out of its guides (USB-C unplugged) and the buck slides -X off its rails. The controller lifts once its 2 tongues are pressed (no slide row) | none | [slide: v3-A1 MotorGo slides +Z out of its card guides] min 0.15; [slide: v3-A1 buck slides -X out of its hook rails] |
| Battery | Slides out +X | none | [slide: battery out +X] min 1.6 |

## 6. Renders and sections (`renders/attempt-1/`, `CAD_RENDER_FINAL=1`)

- View set (1800 px): `iso.png`, `iso_front_left.png`, `front.png`, `side.png`, `top.png`, `rear.png`, `exploded.png`, and
  the poses `pan-90_tilt0.png`, `pan+90_tilt45.png`, `tilt45.png`, `jar_unlocked.png`.
- Sections (`cad q section`):
  - `sec_hub_roof_y4.0.png`: through the splice axis (y 4.02). Shows the splice (z 72..92) with its leads in the hub-gear
    tube, and the turntable's 45 deg hub cone up to the flat bore roof at z 100.
  - `sec_beam_hook_y18_xR.png`: through the right post's front beam hook (x 43.7, y 18). Shows the hook hanging from the
    beam into its slot in the post top, the barb under the ledge, and the release slot.
  - `sec_crown_hook_y0_xR.png`: through the +X crown hook (x 37.25, y 0). Shows the hook running down through its beam
    slot to the barb at the beam underside.
  - `sec_gate_finger_z325.png`: horizontal section at the gate finger (z 325.35). The in-plane finger's bump sits in the
    closed notch of the +Y cheek.

## 7. Warns (61, all triaged in `checks.json` `accepted_warns`)

Every entry is in the `{check, kind, object, why}` form, plus `match` to pin a measured number or `"any": true`. The 13 v2
substring entries were converted with `summary.accept_suggestions` (the config warn is gone).

- **parts (29):**
  - gear tooth tips (pan pinion, feeder pinion, disc);
  - designed thin springs: the snap arms and fingers of the encoder cap, hub gear, beam, crown, valve and gate, and the
    crown crush ribs;
  - 45 deg dovetail edges (body, nip cover) and the nip wheel's 0.5 nut-slot skin;
  - ledges under the 3.0 fail limit: floor latch barbs 1.7, controller tongue lips 1.5 / 1.3, flywheel nut-pocket roofs
    2.9, the body's v2 finger-scallop 2.2 and two first-layer slivers;
  - knife edges: the zip-tie anchor 0.94, the turntable cone 0.60, the journal-plate fork 0.22 at the R15 journal top
    (the journal carries the pod on its lower half);
  - bevel clamps on the turntable and launcher_cover (cosmetic).
- **interference (14):**
  - designed hard stops met inside the 2.5 deg overtravel: tilt lugs at +46, gate stops, thumbwheel seat;
  - hood / nip cover / leaf contacts only at poses 2.5 past their limits;
  - 4 "not proven clear" cells for the hood, all past the hood's -0.558 static stop or the leaf-solid limit. `cad q sweep`
    reads >= 0.158 (hood x nip cover), 6.5 (turntable x hood), 7.39 (hood x flywheel) and 7.89 (hood x tape);
  - 2 feeder sampling-limit cells, measured >= 1.94 and 1.60.
- **flexures (12):** vertical hooks and fingers printed across layers, each under 15 MPa interlayer:
  - hub fingers 12.6;
  - beam hooks 9.2 engage / 12.9 release;
  - crown hooks 10.3 / 12.3;
  - valve fingers 11.0.

  The in-plane arms (floor latches 21.4, controller tongues 15.4, the rest 13-14.6) and the nip leaf (35.5 solid) bend in
  the layer plane and pass.
- **clearance (4):** hood / nip leaf / thumbwheel near misses, only at poses 2.5 past their stops.
- **cables (2):**
  - `CAB_bus_pan_tail` has no lead of its own; it is the last 12.7 of the 350 pan lead (cable_chains);
  - the bundle/base hand-over 5.7 chord (section 1).

## 8. Not done / to confirm

- The jar dimensions (`JAR_*`) are nominal; confirm them with calipers. The buck flange hole spacing ±33.4 is an estimate
  (v2).
- The 0.22 knife edges at the top of the journal-plate fork are accepted, not removed. A later attempt can cut the journal
  crescents above the counterbore slot (a pan_stage / launcher geometry change).
- The bundle hand-over stays off the pan axis (v2 review A6-02, deferred again; it needs the hub routes rebuilt).
- Not checked by cadcheck: teardown count, slack across joints, wrench access to nuts, bend radius of unmodelled leads
  (`cadcheck.json` `not_checked`). Snap retention force and long-term creep of the vertical hooks are by hand
  calculation only (stresses above).
- What cadcheck covers (`cadcheck.json` `coverage`, abridged): 25 printed STLs (manifold, bed fit, overhang, walls, layer
  support); 74 objects / 5453 pair-pose interference tests over 8 swept joints with 2.5 deg overtravel; 11 screws + 3
  nuts for head, engagement and access at 16 poses; 8 service ops; 27 slide-outs; 24 assembly steps, 0 objects in no
  step; 50 straight insertions; 24 flexures against print orientation; stability over 3456 poses; 15 cable routes.
- Final `cadcheck.json` is copied to `renders/attempt-1/cadcheck.json`; the STL contact sheet is
  `renders/attempt-1/stl_sheet.png` (`cad sheet stl`).

## Attempt 2 (hotfix) notes

These notes override sections 3-5 where they differ. See DESIGN_LOG "Attempt 2 (hotfix)".

- **Gate holds open and closed again.** Pull the tab +X: about 1 mm before the stop, the stop lug's small finger
  clicks into a dimple in the spout notch, and the gate stays open [slide: A2 hotfix (v3-A1-03) gate held open,
  blocked at 0.2 by PRT_jar_adapter]. It still stops hard at 52.35 [slide: v3-A1 gate open stop, blocked 52.5]. Push
  it back -X past that click to close: the existing cheek finger clicks into the closed notch as before
  [distances: v3-A1 gate detent finger seated]. Open-detent finger 10.2 MPa in the layer plane [flexures: A2 gate
  open-detent finger]. Step 14 is unchanged: the gate goes in -X from the open side, and the bump clears the widened
  closed notch.
- **Beam hooks** are now 2.2 wide and catch under the post ledges [slide: A2 hotfix (v3-A1-01) beam hooks hold,
  blocked at 0.1], 0.3 a side in the release slot [distances: ... beam-hook barb ... release-slot jamb, 0.3]. The
  screwdriver release is the same.
- **Jar adapter** seats fully on the valve. The key groove now runs 1.0 past the key rib [distances: ... valve key rib
  top ... spout key groove, 1.0].
- **Reprint list (from attempt 1):** `stl/beam.stl` (93.8 g), `stl/jar_adapter.stl` (8 g), `stl/jar_gate.stl` (8.9 g).
  The other 22 STLs are geometrically unchanged. No change to fasteners or purchased parts: 25 printed, 14 metal (11 screws, 3 nuts/pins); 4 specs. Full check 0 fail / 69 warn (`renders/attempt-2/cadcheck.json`).
