# M&M Launcher Turret v3 (min-hardware): Design Log

v3 is the minimal-hardware, minimal-part-count branch of v2 attempt 7 (scores 9/8/9). History, every v2 decision and the
v2 rows' origins: [../v2/DESIGN_LOG.md](../v2/DESIGN_LOG.md). Brief: [DESIGN_BRIEF.md](DESIGN_BRIEF.md) over
`../v2/DESIGN_BRIEF.md` and `../DESIGN_BRIEF.md`. Tools: alex-3d-skills `next` at c2c282d (pinned worktree).

## Attempt 1: plan (planner, written before modelling)

### Baseline and targets

| Metric | v2 A7 (`cad build`) | v3 target | v3 A1 plan |
|---|---|---|---|
| Metal screws + nuts + pins | 107 (103 screws, 4 nuts) | <= 24 (stretch 16) | **14** (10 screws, 4 nuts) |
| Distinct screw spec x length | 18 | <= 4 (stretch 3) | **4**: M3 pan x 10, M3 cap x 20, M3 hex x 16, M3 cap x 6 |
| Printed parts | 36 | <= 26 (stretch 22) | **25** |
| Review F / M / A | 9 / 8 / 9 | >= 9 / 9 / 9 | A7-01 (the one major) disappears with the groove cap |

The build now prints `PARTS <n> printed, <n> metal (<n> screws, <n> nuts/pins)` after `FASTENERS` (build_assembly.py).

### Joining toolbox used (types named in the joint table)

- **MERGE**: two parts become one print (same print orientation, no supports, bed fit).
- **CAPT**: captive geometry, held by the next part in the assembly order (no flexure, no screw).
- **SNAP-IP**: in-plane cantilever arm cut through a flat-printed plate; beam and bending in the layer plane. Release by
  fingertip or a flat screwdriver at a pry notch.
- **SNAP-V**: vertical hook or finger (beam across layers). Allowed only with bending stress <= 13 MPa (interlayer limit
  15, `flexures` row with `stress_mpa`), used where the load is a lift or handling load, never a preload.
- **DOVE**: 45 deg dovetail slide (prints without support) + an in-plane detent at the end of travel. Preload bears on the
  dovetail faces, never on the detent (brief: no preloaded spring on a snap).
- **PIN**: printed stub axle or press peg, integral to one part (pin axis along print Z, shear across layers checked by hand
  below 3 MPa).
- **HORN**: servo horn in a 2.7-deep horn pocket with 8 printed O2.0 pins in its 8 O2.2 holes; the servo centre screw clamps the
  part onto the horn (brief "Metal that is allowed"). Torque capacity: 8 pins x 3.14 mm2 x 15 MPa x R7 = 2.6 N m plus clamp
  friction about 2 N m, against a 3.4 N m stall.
- **BAY**: bayonet / quarter turn. Only the v2 jar socket keeps one (it is a joint, `PIV_jar`); new round interfaces use
  straight push-in snaps instead so every removal is a straight `slide_out` row (a twist would need its own joint).

### Joint table (every v2 fastener group, then every printed part)

| v2 group | n | v2 joint | v3 | Type, dims, flexure carrier | Service (v3) | Evidence row (checks.json) |
|---|---|---|---|---|---|---|
| FST_adapter | 4 | DeWalt adapter to deck, M3 csk x 20 self-tap | **keep 2** (diagonal), M3 pan x 10 counterbored flush | Purchased-part interface. Printed alternative tried on paper: the battery top sits directly under the adapter ledge (z 74.6, `BATT`/`ADAPTER`), so no printed lip fits under it; propping the battery on a floor rail would hang the 620 g pack on crush ribs whenever the rail is 0.3 low. 4 deck fences take shear; 2 screws take the hanging load. | none | distances FST_adapter_0/1 to battery >= 3.0 |
| FST_floor | 8 | floor to shell, csk x 12 | **SNAP-IP** | 2 hook tabs on the -Y edge + 2 in-plane latch arms on the +Y edge of PRT_base_floor (L 35, w 2.5, 3 thick; 16.1 MPa engage 1.5, 21.4 at release 2.0) into pockets in the shell's +Y wall | fingertip, through 2 finger holes in the floor | flexures x2; slide floor -Z; allow floor x shell 2.0 |
| FST_partition | 2 | partition to floor | **MERGE** partition into PRT_base_floor (wall grows up from the floor, same as v2's partition print) | - | - | parts, printcheck |
| FST_mg | 4 | MotorGo M2.5 x 10 | **CAPT** card guides (2 vertical slotted rails, 1.77 PCB + 0.3) on the floor's partition wall; board slides down; a rib from the deck underside sits 0.5 over its top edge | floor off, board slides up out of the guides | slide "MotorGo captive" (blocked by base_shell <= 1.5) |
| FST_buck | 2 | buck flange M3 pan x 8 | **CAPT** or SNAP-IP: flanges slide under 2 printed hook rails on the floor bosses, stopped by an in-floor tongue (SNAP-IP, beam in the floor plane); or a deck rib 0.5 over its top (agent picks, adds the flexures row if a tongue) | floor off | slide (base item adds) |
| (ctrl) | 0 | controller on drill-to-fit bosses | **CAPT**: +0.4 fences + deck rib or 2 floor tongues over the PCB edge | floor off | slide (base item adds) |
| FST_panservo | 4 | pan mount to deck posts, cap x 12 | **CAPT**: mount pressed up onto the 4 deck posts (crush ribs); the floor's servo column (top 0.3 under the servo, z 27.8) backs the whole pan drive | floor off, drive pulls -Z | slides "pan drive captive" (blocked by floor <= 1.0), "pan drive off the deck posts" |
| FST_panclamp | 2 | servo clamp | **eliminated** with PRT_pan_servo_clamp: the floor column replaces the clamp; the pinion (R27) is also trapped between the mount plate and the deck, so the servo cannot fall even with the floor off | as above | as above |
| FST_pinion | 4 | horn to pan pinion, M2 x 8 | **HORN** pocket + 8 pins in PRT_pan_pinion (pins grow up: pinion prints recess up) | - | - |
| FST_pinion_ctr | 1 | pan centre screw M3 cap x 6 | **keep** (allowed: servo centre screw) | bench | - |
| FST_gcap | 6 | groove cap to turntable | **eliminated** with PRT_groove_cap: the groove becomes closed tunnels printed in the turntable (roof = 10 mm bridge in the bottom-down print), the hub bore gets a printed roof (bridge <= 24); the splice is made and serviced from below with the floor off | floor off, splice -Z out of the hub-gear bore | slides "splice pulls -Z", "bore roof keeps the splice captive" |
| FST_post | 7 | posts to turntable | **MERGE** post_L + post_R into PRT_turntable, printed bottom-down (posts upright, exactly as v2 printed them; 216 x 216 x 170, about 350 g) | - | parts, printcheck |
| FST_hub | 3 | hub gear up into the hub | **SNAP-V** + dogs: the R20 hub tube moves from the turntable to PRT_hub_gear (it cannot print below a bottom-down turntable); 3 dogs carry pan torque, 3 fingers (L 15, t 1.2, d 0.45, 12.6 MPa) click over a ledge in the turntable socket | permanent | flexures x3; fits hub_gear x turntable |
| FST_beam | 7 | beam to posts | **SNAP-V**: 4 hooks on PRT_beam (2 per post, L 20, t 1.4; 9.2 MPa engage, 12.9 MPa at the 0.7 release) into ledges in the post tops | flat screwdriver through a slot on the posts' inner faces (hidden behind the pod) | flexures x4; slide "beam + feeder lift +Z"; allow beam x turntable 2.0 |
| FST_postcover | 4 | right post cover | **eliminated** with PRT_post_R_cover: the right post pocket and the journal plate socket open to the top; the tilt servo drops in -Z at tilt 0 and the beam tongue closes the pocket (CAPT) | beam off, servo lifts +Z | slides "tilt servo lifts +Z", "beam keeps the tilt servo captive" |
| FST_tilt_horn | 4 | horn to tilt adapter, M2 x 8 | **HORN** pocket + 8 pins in PRT_tilt_horn_adapter; the adapter prints key-down with a 45 deg cone so the pins grow up | - | - |
| FST_tilt_horn_ctr | 1 | tilt centre screw | **keep** (allowed) | bench | service "tilt servo swap" |
| FST_motor | 4 | motor face screws M3 pan x 10 | **keep** (allowed). They now also clamp the launcher body wall to the nacelle plate | - | fasteners |
| FST_nacelle | 2 | body to nacelle | **eliminated**: the 4 motor screws clamp body + nacelle plate to the motor face; both bores centre on the motor's front boss | - | fasteners FST_motor engagement |
| FST_enc | 2 | encoder cap | **SNAP-IP**: 2 in-plane arms in the cap flange (L 18, w 1.5, 14.6 MPa at release 0.6) click into a groove in the nacelle's rear counterbore; keyed for the Plink orientation; air gap set by the flange seat | tool-free, tilt 45, squeeze and pull -X | flexures x2; slide "encoder cap pulls off -X"; allow cap x nacelle 1.0 |
| FST_jp | 3 | journal plate to body | **PIN + CAPT**: 3 O5 x 4 crush-rib pegs grow +X from the body's top (print) face into blind holes in the journal plate; axially captive between the body and the right post (gap <= 1.4 < peg 4). Tilt torque on 3 pegs at R18: 3.4 N m stall -> 63 N per peg, 3.2 MPa | not serviced | fits turntable x journal plate (stops) |
| FST_cover | 4 | wheel-side cover | **DOVE-lite**: 2 hook tabs on the cover's -Y edge under body-rim lips + 1 in-plane latch arm (L 22, w 1.5, 13.0 MPa at release 0.8); removal = the v2 path, slide +Y at tilt 45 | tool-free, tilt 45 | flexures; slide "wheel-side cover slides off +Y"; allow cover x body 1.0 |
| FST_hinge + nut | 2 | hood hinge axle M3 x 35 + nut | **PIN**: O5 stub grows +X from the body's left wall into the hood's -X bore; O5 stub grows +X from the hood into the journal plate bore; the journal plate captures the hood axially. Nip load about 20-30 N on O5 stubs: 1.5 MPa | not serviced | fits hood x body, hood x journal plate (0.1) |
| FST_nip_stud | 1 | captive hex stud | **keep**. Printed coarse thread rejected: the stud carries the leaf preload (creep), the 6.2..7.0 setting is 1.6 turns at M3 but 0.4 turn at pitch 2, and an OD 12 thread does not fit the R8.5 thumbwheel or the R4.4 guard slot | - | fasteners.captive |
| FST_tw_nut | 1 | thumbwheel captive nut | **keep** (with the stud) | - | - |
| FST_nipstop | 1 | nip stop pad screw | **MERGE** PRT_nip_stop into PRT_launcher_body (its contact face is a vertical wall in the body's print, as it was in the pad's) | - | distances hood x body max 0.05 at the stop |
| FST_nipcover | 2 | nip cover to land | **DOVE**: cover slides along the land on 45 deg dovetails; one detent arm along x (13.8 MPa). The leaf preload (7-20 N) bears on the dovetail faces | tool-free, tilt 45 | flexures; slide "nip cover + leaf slide off"; allow nip cover x body 1.0 |
| FST_leaf | 2 | leaf to cover | **CAPT**: leaf root block slides along x into a T-slot in the cover; captive while the cover is on | cover off, leaf slides out | slide "nip leaf captive" |
| FST_fw_bolt + nut | 2 + 2 | flywheel D-shaft clamp | **keep** (allowed) | L-key at tilt 45 | service "tape / flywheel" |
| FST_feedmount | 4 | feeder to beam | **SNAP-V**: 3 hooks on the crown skirt (L 16, t 1.0, 10.3 MPa) through slots in the beam, barbs on the beam underside | flat screwdriver from under the beam (10 mm over the pod) | flexures x3; slide "crown group lifts +Z"; allow crown x beam 2.0 |
| FST_fplate | 2 | feeder floor plate to crown | **MERGE** PRT_feeder_housing (floor + spout) into PRT_beam: both printed top-face-down; the beam top rises to z 263 so the whole top is one bed face | - | parts; fits beam x disc / pinion |
| FST_fcover | 2 | lobe cover to crown | **MERGE** PRT_feeder_cover into PRT_feeder_crown (closed lobe roof, crown already prints top-down); the servo goes in from below | crown off, servo out -Z | slide "feeder servo + horn + pinion out of the lobe -Z" |
| FST_fhorn | 4 | horn to feeder pinion | **HORN** pocket + 8 pins; no centre screw (as v2) | - | - |
| FST_valve | 3 | valve to adapter spout, radial | **printed joint, feeder item decides** among: (a) bayonet on the spout OD in L-slots cut in the 11.6-thick cheeks, rotation keyed by the gate's stop lug in the spout notch (gate inserted after the twist); (b) push fit with a key rib + SNAP-V detent fingers cut in the cheeks (<= 12 MPa). Constraint: the refill twist (jar +30) and relock must not turn the valve on the spout | refill unchanged | slide "jar group lifts off"; feeder item adds flexures rows |
| FST_detent | 1 | gate detent clip | **eliminated** with PRT_gate_detent: an in-plane finger cut in the flat-printed gate blade (L 15, w 1.5, d 0.4, 14.0 MPa) clicks into closed / open notches in the +Y cheek | - | flexures; distances gate x valve <= 0.15 (closed, open); allow gate x valve 1.0 |

| Printed part (v2) | v3 |
|---|---|
| base_shell, base_floor, pan_servo_mount, pan_pinion | kept (floor absorbs the partition) |
| base_partition | merged into base_floor |
| pan_servo_clamp | eliminated (floor column) |
| thrust_ring | kept (merging it needs the turntable printed top-down, which the integral posts forbid) |
| turntable, post_L, post_R | one part, PRT_turntable |
| groove_cap | eliminated (tunnels + bore roof) |
| hub_gear | kept, gains the R20 hub tube |
| post_R_cover | eliminated (top-loaded tilt servo) |
| beam, feeder_housing | one part, PRT_beam |
| tilt_horn_adapter | kept (pins) |
| nacelle, launcher_body, journal_plate, launcher_cover, hood, nip_wheel, nip_leaf, nip_cover, flywheel, encoder_cap | kept |
| nip_stop | merged into launcher_body |
| nip_stop_sleeve | merged into nip_wheel as a spigot (or the hood, launcher item's choice; the fit pair is hood x nip_wheel either way) |
| feeder_crown, feeder_cover | one part, PRT_feeder_crown |
| feeder_pinion, feeder_disc, jar_adapter, jar_valve, jar_gate | kept |
| gate_detent | eliminated (finger in the gate) |

Count: base 4 + pan stage 5 + launcher 10 + feeder 6 = **25 printed**. Metal: 4 motor + 2 + 2 flywheel + 1 + 1 nip + 2
centre + 2 adapter = **14**.

### v3 architecture

**Stack and who locks whom.**
1. Shell (on its wall edges, floor off) <- adapter (2 screws) <- pan drive pressed on the deck posts.
2. Thrust ring <- turntable (posts integral) <- hub gear snapped up from below (the hub gear's top bears under the deck, so
   the turntable cannot lift off the base).
3. Pod (bench: nacelle + body clamped by the motor screws; hood on the body stub; journal plate on 3 pegs captures the hood;
   nip cover on its dovetail; wheel-side cover on its latch; encoder cap snapped) drops into the U-slots.
4. Tilt servo + adapter drop into the open-top right post pocket; the key enters the journal plate's top-open fork.
5. **Beam locks** the journals, the tilt servo and (by its weight path) the posts' tops: 4 hooks.
6. Disc on the beam's feed floor; **crown** (servo, horn, pinion inside) lowered over it: 3 hooks.
7. Splice from below; **floor locks** the pan drive and every board (deck ribs, card guides): 2 latches.
8. Jar (bayonet, unchanged) and battery (rail, unchanged) last.

**Load paths that changed.** Pan torque: pinion pins -> hub gear dogs -> turntable. Tilt torque: adapter pins -> fork flats
-> journal plate pegs -> body. Lift-by-the-jar (about 25 N, design 100 N): jar bayonet -> crown hooks (3 x about 150 N at
15 MPa across layers) -> beam hooks (4) -> turntable -> hub gear fingers -> deck underside. Nip preload: leaf -> cover
dovetail faces -> body (no snap carries it).

**Print orientations (all unchanged except):** turntable bottom-down (was top-down; posts were already upright); beam top-down
with the top at z 263 everywhere (was 260 + a separate floor plate); crown top-down with the closed lobe roof on the bed
(the lobe cover printed that way already); tilt adapter key-down with a 45 deg cone (was recess-down); gate flat (finger in
plane); floor flat with the partition wall and card guides up.

**Form language.** No visible screw head is left on the machine: the 2 adapter screws sit counterbored in the deck outside the
turntable, the motor screws inside the guard. The post cover seam and the groove cap strip disappear from the iso views. The
beam's 3 mm thicker top continues the crown's base line (DP3). Colour: the beam now carries the spout (candy path, B) but is
structure (A); keep A and note the trade-off (an H2D two-colour print can restore B on the spout).

### Assembly order (checks.json `assembly_order`, 25 steps)

1 shell + adapter; 1a/1b pan drive (bench, merge); 2a ring + turntable; 2b hub gear; 6a-6g pod (bench); 7 pod in;
8a/8 tilt drive (bench, merge, dropped -Z); 9 beam; 10a disc; 10b/11 crown (bench, merge); 11a splice from below;
12/13 floor (bench, merge) + base cables; 14/15 jar (bench, merge at +30); 16 battery (`powered`). No step needs a held
pose: A7-01 cannot recur (the only servo-held joint, tilt, is never posed before power).

### Service (checks.json `service`, all tool-free except two)

| Op | v3 method | Tool |
|---|---|---|
| Refill | unchanged (jar +30, lift; gate finger detent) | none |
| Nip gap | unchanged (thumbwheel through the finger slot) | none |
| Nip leaf | tilt 45, nip cover off its dovetail, leaf out of the T-slot | none |
| Tape / flywheel | tilt 45, wheel-side cover off +Y, pinch bolts | 2.5 L-key |
| Encoder | tilt 45, cap pulled -X | none |
| Tilt servo | jar off, beam + feeder off, servo +Z | flat screwdriver (beam hooks) |
| Feeder servo | jar off, crown off, servo -Z out of the lobe | flat screwdriver (crown hooks) |
| Base floor | 2 latches, floor -Z | none |
| Bus splice | floor off, splice -Z out of the hub-gear bore | none |
| Pan servo | floor off, drive -Z off the posts; centre screw on the bench | hex key (bench) |

### Work items (attempt 1, one build agent each, in order)

1. base, 2. pan_stage, 3. launcher, 4. feeder, 5. finish (BOM, warn triage, full check, printcheck, renders).
Each owns its rows in checks.json (rows tagged `v3-A1`, `_todo` notes say what to make exact).

### Deferred (with reason)

- v2 review A6-02 (minor, cables): bundle hand-over at r 4 off the pan axis; untouched by the hardware goal; the row
  v2-A2-02 stays (0.916 / 1.0). Revisit when the tunnel routes are rebuilt if the pan_stage item has time.
- Stretch targets (16 metal is met; 3 specs and 22 parts are not): 3 specs would need the stud and the pinch bolts on one
  spec; 22 parts would need nacelle + body and thrust ring merges that do not print without supports.
- Valve-to-adapter joint geometry: decided by the feeder item between the two options above.

## Attempt 1

(Subsystem work items append their results here: rows -> values, deltas from the plan, tool issues.)

### pan_stage (work item 2)

Rows -> values (cadcheck subset run on the built model; full run in `blender/cadcheck.json`):
- MERGE posts -> PRT_turntable, printed R_ID (bottom-down, 216 x 216 x 160). printcheck 0 fails; 2 warns are the 1.9 mm flat
  roofs of the front beam-hook release slots (the barb ledge; accepted_warns).
- Hub: the turntable's hub cavity is a 45 deg cone (R20.3 at the bed to R12.3 at z 100) with a flat roof (24.6 bridge). A flat
  socket ceiling over the R14 bore printed as a 6.5 mm cantilever ring (printcheck fail, first build), so the hub tube on
  PRT_hub_gear ends in a matching 45 deg chamfer (0.3 under the cone) and the dogs / fingers rise into pockets in the cone wall.
  Fingers: flexures rows 12.6 MPa (L 15, t 1.2, 0.45); insertion step 2b `insert_ok` (barbs flex); fits base_shell x hub_gear
  0.259 (min 0.1), hub_gear x pan_pinion 0.144.
- Tunnels: floor 93.6, roof 100.3 (bridge 10), R15 centreline bends from the post channels; in |x| < 13 the tunnel / hub pocket
  ceiling (100.3) sits 0.3 over the bore roof (100.0) so the two bridges print on different layers (one 34 mm bridge otherwise).
- Splice: BUS_JCT l 20, z 72..92. Slides: "bore roof keeps the splice captive" blocked by PRT_turntable at 8.1 (at_mm 7.9..8.2);
  "splice pulls -Z" clear over 90, min 1.0 (PRT_hub_gear). No kinks or shared runs at the splice; the two bus leads land on the
  splice top 3.0 apart (params hub_bus) after 2.9 straight + R2.5; the pan tail ends on the bottom face (5 straight).
- Tilt servo top-loaded: slide "tilt servo + adapter lift +Z" clear (min 0.15 = the fork's side gap, row min 0.1); "beam keeps
  the tilt servo captive" blocked by PRT_beam at 0.75 (tongue 0.43 over the servo top, step 0.25). The journal plate fork
  (IF_TILT_FORK_W 12.3, IF_TILT_FORK_R 6.8, counterbore opened 2 x 13.3) is cut in launcher.py build_journal_plate.
- Beam: feed floor merged (feeder.housing_geom, owned by the feeder item), top z 263, 4 hooks (9.2 / 12.9 MPa), slide "beam +
  feeder lift +Z" clear with the four barbs riding 7.97 mm3 (allow beam x turntable max 8.5). 3 crown-hook slots at
  IF_CROWN_HOOKS with 2 mm barb pockets in the underside (nothing proud of z 252).
- Final full check: 28 F / 80 W, none on a pan_stage row (FST_jp_0..2 belong to the launcher item); stability 31.1 deg; printcheck
  turntable, hub_gear, beam, tilt_horn_adapter 0 F / 0 W.
- Deltas from the plan: hook positions moved to the posts' inner faces (x -91 / 43) so the release slots are 3 mm long; crown
  hook slot +X moved from x 44 (on the right post's U-slot tongue) to x 36.5; FST_feedmount x4 and FST_fplate x2 deleted here with
  the housing (the feeder item adds the crown hooks).

### feeder (work item 4)
- **Feed floor + spout**: stays in `feeder.housing_geom`, unioned into PRT_beam by `pan_stage.build_beam` (one function, owned
  here). Disc running face = beam top z 263. PRT_feeder_housing, FST_fplate x2 gone.
- **Jar stack raised 36 mm (`params.JAR_LIFT`) — deviation from the plan.** The plan said "close the lobe roof into the
  crown, the crown already prints top-down". It can't as planned: the v2 lobe cover rose from the crown top (z 286) to
  322.3. A one-piece crown with its roof on the bed would leave the R44.5 socket rim hanging 36 mm over the bed. Printed
  bottom-down instead, the hooks would sit under the bed. So the socket rim and the lobe roof now share one top plane at
  z 322, and everything above the socket floor moves up 36 mm: socket, lugs, gate, valve top, adapter, band, glass. The
  valve skirt gets 36 mm longer inside the R31.35 chamber bore. Nothing under it moves: beam, disc, pinion, servo,
  baffle, drop, index and payload rows.
- **Crown** (PRT_feeder_cover, FST_fcover x2, FST_feedmount x4 deleted): one convex lobe hull (lobe + bus tab) with a CH
  45 deg top chamfer, at full height. Servo pocket open down to the beam face. Roof underside 0.05 over the servo top
  (`LOBE_ROOF_Z` 316.25), with a blind idler-boss recess. 4 crush ribs (1.0 wide, 0.1 interference, 45 deg lead-in),
  allow servo x crown 12 mm3 (9.6 measured). 3 SNAP-V hooks (`CROWN_HOOK`: L 16 root z 268 -> tip 252, t 1.0, w 5, barb
  0.55 outward, catch 0.1 under the 254 pocket roof): 10.3 MPa engage, 12.3 MPa at the 0.6 release. Flexures rows exact.
  Allow crown x beam raised 2.0 -> 12 mm3 (slide measures about 11).
- **Pinion HORN** (FST_fhorn x4 deleted): 2.7 pocket in an R12 hub + 8 O2.0 x 2.4 pins. No centre screw. The pinion sits
  0.3 over the feed floor, so it can't drop off the pins. Hub cavity in the crown R12.45 (fits 0.3 with facet sag).
- **Gate detent** (PRT_gate_detent, FST_detent deleted): SNAP-IP finger along the blade's +Y edge (`GATE_FINGER`: root
  x -3, bump x 12, L 15, w 1.5, R1 bump 0.4 into the +Y cheek face): 14.0 MPa in the layer plane. It clicks into a R1.1
  notch at x 12; distances row = ray from the 0.1 gap along the bump centre line. **Closed notch only — deviation.** The
  +Y cheek face spans x -15..15 (R34 body) and the travel is 52 mm, so no point of the blade meets that face at both ends
  of the travel. In the open state the blade only touches the valve at x 25..34 (inside the cheeks' outline), so no
  in-plane open notch exists. Open is held by the positive stop (lug on the spout shoulder at 52.35, distances +
  slide_out blocked rows) and friction. The v3-A1 "bump seated in the open notch" distances row is removed.
- **Valve to adapter spout: option (b), push fit** (FST_valve x3 deleted). Option (a) was rejected: a bayonet twist
  sweeps the spout tip over the gate's stop lug (0.35 under the spout bottom), and the gate can't go in after the twist
  because the lug can't pass the +X open-stop shoulder. Joint parts:
  - The spout goes straight down into the cheeks, its tip notch over the stop lug.
  - A 3 x 0.75 key rib on the +Y cheek pad runs in a spout key groove, so the refill twist (+30) and the relock turn the
    jar group as one.
  - The spout shoulder R28.3 bears on the cheek tops and pads (jar weight; band lip ID R29 stays 0.7 clear).
  - Centring pads on the +/-Y cheeks sit above the blade with 50 deg undersides.
  - 2 SNAP-V fingers in the +/-Y cheeks take the lift (`VALVE_SNAP`: x 2..8, t 1.0, root z 321, barb R27.1 into a R27.0
    groove round the spout): 11.0 MPa <= 12. Flexures rows added.
  - Bench order: gate slid -X into the slot under the pads (clicks closed), then the jar group pushed down onto the valve.
- **Valve lugs**: 50 deg undersides from the body (z 311) to the R37 tip; the crown's L-slot leg floors are the matching
  cone. This clears the baseline 5.5 mm cantilevers at z 274.9.
- Counts: FASTENERS 11 screws, 4 distinct; PARTS 25 printed, 14 metal (11 screws, 3 nuts/pins). The plan's "10 screws +
  4 nuts" is the same 14 items: the M3_hex nip stud is counted by the build as a screw.
- Evidence: full `cad check` 0 F / 63 W (13 untriaged; the 2 feeder "not proven clear" sampling warns, measured >= 1.94 /
  1.60 mm with cad q, were accepted after the run: `--only interference` 0 F, 4 untriaged, none feeder). Index +60/-60 one
  window each ([50,60] / [-60,-50]); column never open at drift 0/5/10/15. Slide rows:
  - jar lifts at PIV_jar 30: clear;
  - gate opens +X 52: min 0.35, the finger bounded by allow gate x valve 1.0;
  - open stop: blocked at 52.5 by PRT_jar_adapter;
  - crown group +Z: clear, 10.93 mm3 on the beam allow;
  - servo out of the lobe -Z: clear, 9.62 mm3 crush ribs.
  Flexures: 3 hooks 10.3, gate finger 14.0 (in plane), valve fingers 11.0. Jar band stack: worst case 2.4 / RSS 1.31 vs 3.0,
  unchanged. Printcheck on the 7 feeder/jar parts: 0 F. Stability: 29.6 deg (31.1 before the 36 mm jar lift).

### Attempt 1 results (finish, work item 5)

**Counts (build output, `CAD_RENDER_FINAL=1 cad build ... --render`):**

    FASTENERS 11 screws, 4 distinct spec x length: M3_cap x 20 (2), M3_cap x 6 (2), M3_hex x 16 (1), M3_pan x 10 (6)
    PARTS 25 printed, 14 metal (11 screws, 3 nuts/pins)

| Metric | v2 A7 | v3 target | v3 A1 plan | v3 A1 built |
|---|---|---|---|---|
| Metal pieces | 107 | <= 24 (stretch 16) | 14 | **14** (11 screws + 3 nuts) |
| Distinct specs | 18 | <= 4 (stretch 3) | 4 | **4** |
| Printed parts | 36 | <= 26 (stretch 22) | 25 | **25** |

**Evidence (final runs):**
- `cad check model.blend checks.json`: PASS, 0 fail, 61 warn, 0 untriaged, 0 config warns. The other summary fields:
  - `stale_accepts` `[]`, `summary.unused_allows` `{}`, `poses_past_limits` `[]`;
  - `assembly.held_poses` `[]`, `assembly.unordered_solids_assumed_present` `[]`;
  - stability 29.6 deg.
- `cad printcheck stl --manifest blender/manifest.json`: PASS, 25 parts, 0 fail, 9 warn (all accepted ledges / slivers).
  Every part fits the P1S.
- `cad bom BOM_AND_ASSEMBLY.md blender/manifest.json`: PASS, 5 rows, 0 disagree, 0 modelled screws in no row.

**Joint table, measured (plan row -> the row that proves it, value):**

| v2 group | v3 joint | Evidence row | Measured |
|---|---|---|---|
| FST_adapter x4 | keep 2, M3 pan x 10 | fasteners FST_adapter_0/1; distances FST_adapter_0/1 to battery | engagement 8.5; tip 5.46 >= 3 |
| FST_floor x8 | 2 SNAP-IP latches + 2 detents | flexures floor latches / detents; slide base floor drops -Z | 16.1 / 21.4 MPa, 14.0 MPa (in plane); 50.46 mm³ on the floor x shell allow, min 1.6 |
| FST_partition x2 | MERGE into base_floor | parts / printcheck base_floor | 0 fail; 1.7 latch-barb ledges accepted |
| FST_mg x4 | CAPT card guides + deck rib | slide MotorGo captive / slides out | blocked by base_shell at 0.75; out +Z min 0.15 |
| FST_buck x2 | CAPT hook rails + shell ribs | slide buck -X / +Z / +X / out | blocked at 0.4 / 0.6 / 0.4; out -X clear |
| (ctrl) | fences + 2 SNAP-IP tongues | slide controller held down; flexures | blocked at 0.3; 12.8 / 15.4 MPa |
| FST_panservo x4 + clamp x2 | CAPT deck posts + floor column | slide pan drive captive / off the posts | blocked by base_floor at 0.5; off -Z min 0.14, 1.87 mm³ crush ribs |
| FST_pinion x4 | HORN pocket + 8 pins | parts pan_pinion; fasteners FST_pinion_ctr | 0 fail; centre screw 6.0 engagement |
| FST_gcap x6 | eliminated: tunnels + bore roof | slide bore roof keeps the splice captive / splice pulls -Z | blocked by PRT_turntable at 8.1; out -Z min 1.0 |
| FST_post x7 | MERGE posts into turntable | printcheck turntable | 0 warn, max bridge 24.7 |
| FST_hub x3 | SNAP-V fingers + dogs | flexures hub snap finger 1..3; insertion 2b insert_ok | 12.6 MPa (accepted vertical) |
| FST_beam x7 | SNAP-V 4 hooks | flexures beam hook x4; slide beam + feeder lift +Z | 9.2 / 12.9 MPa; 7.97 mm³ on the 8.5 allow, min 0.2 |
| FST_postcover x4 | eliminated: top-loaded tilt servo | slide tilt servo lifts +Z; beam keeps it captive | min 0.15; blocked by PRT_beam at 0.75 |
| FST_tilt_horn x4 | HORN pocket + 8 pins | fasteners FST_tilt_horn_ctr | engagement 6.0 |
| FST_nacelle x2 | eliminated: motor screws clamp both | fasteners FST_motor_0..3 | engagement 4.5 each |
| FST_enc x2 | SNAP-IP 2 arms | flexures; slide encoder cap pulls off -X | 14.6 MPa; 4.25 mm³ on the 8 allow, min 1.0 |
| FST_jp x3 | PIN 3 crush-rib pegs + CAPT | fits / interference journal plate (0 fail) | stop lugs at +46 (accepted collide-only) |
| FST_cover x4 | hook tabs + SNAP-IP latch | flexures; slide wheel-side cover off +Y | 13.0 MPa; clear (0.00 = the seat) |
| FST_hinge + nut | PIN O5 stubs | distances hood bay gaps | 0.55 side, 2.445..4.089 back |
| FST_nip_stud + FST_tw_nut | keep | fasteners FST_nip_stud | captive; nut 2.4 engaged |
| FST_nipstop | MERGE into launcher_body | distances hood x body at hood 0.327 | 0.0 (max 0.05) |
| FST_nipcover x2 | DOVE + SNAP-IP detent | flexures; slide nip cover + leaf off +V | 13.8 MPa; clear |
| FST_leaf x2 | CAPT T-slot | slide nip leaf captive | blocked by PRT_nip_cover at 1.0 |
| FST_fw_bolt + nut x2 | keep | service tape / flywheel | L-key 15.5 at tilt 45 |
| FST_feedmount x4 | SNAP-V 3 crown hooks | flexures crown hook x3; slide crown group +Z | 10.3 / 12.3 MPa; 10.93 mm³ on the 12 allow, min 0.14 |
| FST_fplate x2 | MERGE housing into beam | printcheck beam | 0 warn |
| FST_fcover x2 | MERGE cover into crown | slide feeder servo out of the lobe -Z | min 0.35, crush ribs 9.62 mm³ |
| FST_fhorn x4 | HORN pocket + 8 pins | parts feeder_pinion | 0 fail |
| FST_valve x3 | push fit, key rib + 2 SNAP-V fingers | flexures valve snap finger ±Y; slide jar group lifts off | 11.0 MPa; clear at jar 30 |
| FST_detent + gate_detent | SNAP-IP finger in the gate | flexures gate finger; slide gate opens / open stop | 14.0 MPa; min 0.35; blocked by PRT_jar_adapter at 52.5 |

**Finish item changes:**
- `accepted_warns`:
  - the 13 remaining substring entries were rewritten as `{check, kind, object, why}` (the planner listed 22; the work
    items had already converted 9);
  - 8 new triaged entries:
    - flywheel nut-pocket roofs 2.9;
    - journal-plate fork knife edges 0.22;
    - launcher_cover bevel clamp;
    - 4 hood overtravel "not proven" cells, measured with `cad q sweep`: >= 0.158 / 6.5 / 7.39 / 7.89;
    - the bundle/base 5.7 chord (v2 A6-02).
  - The 12 vertical-hook flexure warns carry their stresses.
  - The stale allow `BUY_horn_* x PRT_*horn_adapter` (0 mm³, `summary.unused_allows`) was removed.
- Step 7 gets `pose` `PIV_tilt` 20 with a `pose_how`. The pod's insertion warn (blocked by the stop lugs at 3.12) is gone;
  no held pose, because the tilt servo comes in at step 8.
- `CAB_encoder` now runs at S -1.6 in the journal bore, on the far side from the phases. The "one tube" warn with
  CAB_phase_2 (22 mm) is gone; route 85.9 against the budget 126.3.
- `finish.bom_items` rewritten for v3:
  - `FST_detent_0` and the groove-cap / tilt-45 splice text are gone;
  - the splice text is built from `BUS_JCT` (Ø10 x 20, z 72..92), `IF_HUB_BORE_R` and `HUB_ROOF_Z`;
  - the bus lead texts take the splice top (z 92) from params;
  - the encoder text quotes the built budget.
- Stale strings fixed:
  - the v2-A5-03 splice row (x 25 -> x 20);
  - the pan-tail accept (14.6 -> 12.7, route 292.1 -> 290.2);
  - the nip-stop row (now integral on the body);
  - the orientation texts of nip_wheel and nip_cover;
  - `COLOUR_B` lost `PRT_feeder_housing`.
- V2R7 A7-03 (z 64 -> 63, r 6 -> 6.5 in the v2-A6-02 rows): already correct in the carried rows (`BUS_PAN_AX` z 63,
  `LB_LEG_R` r 6.5); `grep "z 64"` on checks.json and parts/*.py finds nothing.

**Deltas from the plan:**
- "10 screws + 4 nuts" in the plan is an arithmetic slip. Its own list is motor 4 + adapter 2 + fw bolt 2 + stud 1 +
  centre 2 = 11 screws, and 2 fw nuts + 1 tw nut = 3 nuts. The 14-piece total and the 4 specs are as planned.
- 24 assembly steps, not the 25 in the plan's heading. The labels and order match the plan's list.
- The journal-plate fork leaves 0.22 knife edges where the R13.3 counterbore slot exits the R15 journal. They are
  accepted, not cut.
- The jar stack is 36 higher (feeder item), and the gate has a closed notch only (feeder item). See those sections.

**Renders** (`renders/attempt-1/`, 1800 px):
- view set: iso, iso_front_left, front, side, top, rear, exploded, plus 4 poses;
- sections: `sec_hub_roof_y4.0.png`, `sec_beam_hook_y18_xR.png`, `sec_crown_hook_y0_xR.png`,
  `sec_gate_finger_z325.png`.
- STL contact sheet in print orientation: `stl_sheet.png` (`cad sheet stl`); final `cadcheck.json` copied to
  `renders/attempt-1/cadcheck.json`.

**What the check covers and does not (quoted from `cadcheck.json`):**
- coverage: "parts: 25 printed objects (25 unique STLs): manifold, bed fit ['P1S', 'H2D'], overhang, wall probe, bed
  contact; layer support check"; "interference/clearance: 74 objects ..., 5453 pair-pose tests, joints swept [8 PIV_*]
  with 2.5 deg overtravel"; "fasteners: 11 screws, 3 nuts; ... access ... at 16 poses, parts present per assembly_order
  (24 steps)"; "service: 8 ops"; "slide: 27 slide-out sweeps"; "assembly: 24 steps, 74 objects placed, 0 in no step";
  "insertion: 50 parts and merged groups"; "flexures: 24 declared springs or snap arms against print orientation";
  "stability: CG and tip angle over 3456 poses"; "cables: 15 routes, 15 with path length, 3 chains".
- not_checked: "fasteners: pilot/clearance hole diameters ...; wrench access to nuts"; "insertion: paths that are not
  one straight line, parts of the same step against each other, cables"; "stability: dynamic loads (recoil, pan
  acceleration), friction/sliding"; "cables: bend radius of a lead that is not modelled as a route, slack across
  joints, connector positions"; "not geometric: teardown step count, alignment-jig datums, aesthetics, BOM correctness".
- Snap release forces, crush-rib fits and hook creep are calculated (flexures stress_mpa), not measured on a print.
