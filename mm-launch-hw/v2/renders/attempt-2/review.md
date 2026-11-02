# Review: M&M Launcher Turret v2, attempt 2

Checks re-run: `CADCHECK PASS: 0 fail, 44 warn` on `/tmp/rv2/model.blend` (tools 6b62667, the designer's pin). The warn set is identical to the designer's `renders/attempt-2/cadcheck.json` (set difference empty). Copy: `review/cadcheck.json`.
- Coverage: parts 35; interference/clearance 172 objects in all four collections, 4430 pair-poses, 2.5 deg overtravel; fasteners 102 + 4 nuts at 15 poses / 28 steps; service 8; drop 3; index 6; slide 10; distances 39; stacks 3; stability 1 pose; cables 13.
- Not checked (quoted): pilot/clearance hole diameters and wrench access to nuts; **flexures (none declared)**; dynamic loads; cable bend radius, slack and connectors; teardown count, jig datums, aesthetics, BOM correctness.
- Review rows (`review/checks_review.json`): `review/cadcheck_review.json` (distances, slide, drop, flexures), `review/cadcheck_review_index.json` (index at jar drift 20/25/30), `review/cadcheck_review_lift.json` (nip gap at full leaf lift). They add the fails behind A2-01 and the A1-09 stop evidence. The lentil probe is `review/lentils.py`.

| Metric | Score | Anchor matched | One-line reason |
|---|---|---|---|
| Functionality | 8 | "Works. At most 2 major issues, each with a known fix under 1 hour of CAD and no reprint of a big part" | Every A1 functional major is closed: the stops, the finger slot, the servo swap and the drop at every stop and tilt. Two majors remain. Below a 6.1 setting the leaf runs out of travel before a 7 mm candy passes (0.84 rigid at the min stop). The Ø14.4 pocket still seats an edge-on pair 1.5 % under nominal. |
| Manufacturability | 8 | "Works, at most 2 majors" (9 fails: not every warn is explained) | 0 fastener fails, all parts fit the P1S, and there are no supports. The 104 mm hinge bit is listed in the BOM. The nip_cover 171 mm² steep overhang is unexplained, and there is a new 1.12 wall in the body. Two parts are in no assembly step. |
| Aesthetics | 9 | "9 needs every item true" | One EB/CR set: EB 1.0, 0.6 on thin blades (within ±0.5), CR {6, 30}. No PCB or motor can shows: the +X wall rays read 0.5 x 3, and only CAB_usb is exposed. Countersunk heads sit flush. The colours encode the candy path. The gate tab now looks finished. Parting lines were judged visually only. |

## Previous issues

| Issue | Status | New number |
|---|---|---|
| A1-01 nip has no hard stops | FIXED | Nip ray 5.294 at hood +1.315 (lug on PRT_nip_stop, `cad q dist` 0.000). 7.003 at -0.558 (sleeve). Hood to body 0.541 at +1.315 and +2.315. Hood to wheel 4.094 1 deg past the stop. Drops are 31/31 at both stops for tilt -3/0/22.5/45/46 (review drop row). |
| A1-02 gap set only with the cover off at tilt 45 | FIXED | Rays reproduced: `ray 19.5,-2.33,111.274 0,-0.316,0.949` gives PRT_nip_wheel at 14.4 (tilt 0). The tilt-45 ray also gives 14.4. The rim stands 1.1-1.4 proud of the slot end wall (cover hit 15.5-15.8). There is no cadcheck row (tool limit). Ergonomics are tracked in A2-03. |
| A1-03 pocket admits an edge-on pair | **PARTIAL** | Pocket R7.2 (rays 7.2 x 4), floor z 263.0. With the pair placed symmetric on the floor, 13 x 7 overlaps the disc by 0.607 mm³ each, 12.8 x 6.8 by **0.016 mm³** (it fits) and 12.5 x 6.5 clears by **0.154 mm**. |
| A1-04 feeder servo swap needs a teardown | FIXED | Service: lobe cover, reach 44, straight. Slide: servo +Z 60, not blocked. FST_fhorn_ctr deleted. |
| A1-05 crown wall 0.94 at the pilots | FIXED | feedmount to pinion 3.517 (≥ 2.35). Crown has no wall sample under 1.6. |
| A1-06 pod drop-in pose undocumented | FIXED | Slide "v2-A1-06 step 7 reversed" at tilt 20 passes. The step 7 label says nose-up 20. |
| A1-07 magnet stack 0.40 > 0.30 | FIXED | Worst case 0.30 against 0.30, RSS 0.122. Zero margin, but it passes. |
| A1-08 knife edges / bridge | PARTIAL | valve 0.02 → 1.29, gate 0.77 → 1.31, hood 0.91 → none, journal plate 0.95 → 1.29, 48 mm bridge → gone. **New:** launcher_body 1.12 at (10.4/25.6, -14.3, 175.9). nip_cover has 171 mm² of steep overhang (unexplained). |
| A1-09 gate unfinished / open state unmodelled | PARTIAL | The tab is flush with the valve OD (+0.5) with R6/EB1 corners. The open stop is real: a review slide +X 56 is blocked by PRT_jar_adapter at 52.5. There are still no detents. |
| A1-10 feeder form language | FIXED | `parts/feeder.py` has 6 bevel calls, GATE_EB = EB, blade EB 0.6, crown/cover corners R6. |
| A1-11 PCB exposed through the base notch | FIXED | Rows at y 32/50/68: 0.5/0.5/0.5. Only the switch and terminal windows remain. BUY_jar alpha 0.25. |
| A1-12 colours mean nothing | FIXED | COLOUR_B: terracotta is the candy path and the touch points, grey is the structure. |

## Measurements

| Item | Value | Source |
|---|---|---|
| Full check | 0 F / 44 W, identical to the designer's | `review/cadcheck.json` |
| Index ±60 | 1 window each ([50,60] and [-60,-50]); column 0 windows at jar drift 0/5/10/15 | `checks.index` |
| Index, jar drifted 20/25/30 (review) | 0 windows | `review/cadcheck_review_index.json` |
| Nip ray at the stops | 5.294 (+1.315, squeeze 2.21) / 7.003 (-0.558) | `checks.distances` |
| Bare gap at FULL leaf lift (-1.493), ray at y 34, settings hood +1.315 / 1.0 / 0.75 / 0.5 / 0.25 / 0 / -0.3 / -0.558 | **6.685 / 6.982 / 7.212 / 7.44** / 7.67 / 7.901 / 8.18 / 8.416 (need ≥ 7.5 = 7.0 candy + 0.5 tape) | `review/cadcheck_review_lift.json` |
| Same ray, static, at +1.315 / 0.5 / 0 / -0.558 | 5.284 / 6.052 / 6.518 / 7.043 | same |
| cadcheck grip finding at the min stop + full lift | "0.84 mm rigid squeeze on a 7.0 mm payload" | `review/cadcheck_review.json` |
| What really stops the leaf lift (hood 0) | thumbwheel to nip_cover 0.819 at -1.5, **0.256 at -2.0**, -5.1 mm³ at -2.5; stud to cover 2.363 at -2.0 (not the stop the params comment names); hood to body 0.054 at -2.5 | `cad q sweep PRT_nip_wheel PRT_nip_cover PIV_nip_lift -4 -1 0.5` and the others in `review/notes.md` |
| Jam-lift gap at the max setting | about 8.3 (ray y 34). The checks ray at y 37 reads 14.18 because it slips past the hood lip (artefact) | review distances rows |
| Lentil pairs, edge-on, symmetric about the pocket centre (10.5, 18.187), on the floor at z 263 | 13x7: -0.607 mm³; 12.8x6.8: -0.016 mm³; 12.5x6.5: +0.154 mm | `cad q dist ZMM_* PRT_feeder_disc` on `/tmp/rv2/probe/model_mm.blend` (`review/lentils.py`) |
| Drop at both stops x tilt -3/45/46 (review) | 31/31 hit everywhere. Flattest slide 33.8 at tilt 45 (margin 5.8), 32.8 at tilt 46 (4.8), 62.8 at tilt -3 | review drop row |
| Gate open stop | blocked by PRT_jar_adapter at 52.5 (BOM: 52.35) | review slide "+X 56" |
| Nip leaf vs print orientation | beam 2.2 deg to the bed, no finding | review `flexures` row |
| Finger slot at tilt 0 | rim at 14.4; slot end wall 15.5-15.8; guard (PRT_launcher_body) face 10.0, i.e. 4.4 proud of the rim on the +u side; free gap below the slot 19.0 to FST_gcap_3; -Y approach open | `cad q ray` scan in `review/notes.md` |
| Rotating clearances | motor screws to flywheel 1.6; nacelle screws 1.6; cover 2.0; guard 1.594 | `cad q dist` |
| Flywheel balance | pinch bolts at z 163.5 / 176.5 about the z 170 axis, heads alternate sides | `cad q list FST_fw_*` |
| Encoder gap | magnet to Plink 1.0; stack 0.30/0.30 | `cad q dist`, `checks.stacks` |
| Stability | 33.5 deg (1 pose); designer cg_grid 29.9 deg over 64 poses (accepted) | `checks.stability`, `cg_grid.txt` |
| nip_cover overhang | 171 mm²: 54.5 at (16,-12,128) (slot end) and about 65 at the skirt top z 172 | `/tmp/rv2/probe/ovh.py` |

## Issues (ranked)

**A2-01 (major, functionality): below a 6.1 setting the nip leaf runs out of travel before a 7 mm candy passes.**
- With the leaf fully lifted (PIV_nip_lift -1.493), the bare gap is 6.685 at the min-gap stop, 6.98 at hood +1.0, 7.21 at +0.75 and 7.44 at +0.5. A 7.0 candy on 0.5 tape needs 7.5.
- So every setting from 5.3 to about 6.1 (45 % of the thumbwheel window) ends in a **rigid** squeeze, 0.84 mm at the min stop. cadcheck itself warns: "0.84 mm rigid squeeze, name the part that yields".
- The declared lift limit doesn't match the geometry either. The params comment says the stud bottoms on the cover shell at 1.49 deg, but at -2.0 deg the stud is still 2.363 from the cover. The first real contact is the thumbwheel on the nip cover at about -2.1 deg. Even at that real limit the gap at the min stop is about 7.27, still under 7.5.
- Fix (either one):
  - Raise HOOD_GAP_MIN from 5.3 to 6.2 (PRT_nip_stop lands at about hood +0.40 deg), so NIP_SET becomes 6.2..7.0.
  - Or keep 5.3 and give the leaf 2.8 deg of lift (about 2.8 mm at the stud, jack radius 57.6). This means opening the nip cover 1.0 mm above the thumbwheel and relieving the hood/body bay, which touches at -2.5 deg effective, down to -3.4.
- Either way, set PIV_nip_lift's limit to the real first contact. Then add a `distances` row (a PIV_hood-framed ray) asserting a bare gap ≥ 7.5 at full lift at both hood stops.

**A1-03 (major, functionality): the Ø14.4 pocket still seats an edge-on pair of slightly undersized candies.**
- The fix was tuned to exact nominal with zero margin. A 13 x 7 pair is blocked by only 0.6 mm³ (the rim against the pocket chord). A 12.8 x 6.8 pair fits (0.016 mm³ is within faceting). A 12.5 x 6.5 pair sits with 0.15 clear.
- The brief calls the candy "about 13 x 7". Both edge-on candies pass under the baffle ramp (disc + 5.5), so a pair means a double feed, the v1 failure mode the brief names.
- An edge-on pair fits when R² ≥ (T/2)² + (D/2)².
- Fix:
  - Measure 20 candies and declare MM_D (min/max) and MM_T (min/max) in params.
  - Set POCKET_D 14.4 to 13.9 (R 6.95). This blocks a 12.5 x 6.3 pair (it needs R 7.0) and a 12.6 x 6.6 pair (it needs R 7.11), and still clears a 13.5 flat candy by 0.2 radial.
  - Re-run `review/lentils.py` at the min size (it must overlap) and a flat max-size lentil (it must clear). Re-run `stacks: pocket over outlet`.
  - If the window closes after you measure the candies, lower BAFFLE_RAMP_TOP to disc + 3.5. A lone edge-on candy can tip flat in the pocket under that ramp; a pair cannot. Add an index row for it.

**A1-09 (minor, functionality): the gate has a positive open stop but no detents.**
- The open stop works: a slide past 52 is blocked by the adapter at 52.5.
- Nothing holds the gate at 0 or at 52, so flywheel vibration can walk it partly closed (feed starvation) or partly open while the jar is being carried.
- The open state is still outside the interference sweep (no prismatic joint in the tool).
- Fix: add two 0.4 mm detent bumps on a 1.2 x 8 mm cantilever cut into the blade, engaging dimples at 0 and 52. Declare a `flexures` row for it, and add a `slide_out` row at the open position.

**A1-08 (minor, manufacturability): a new thin wall in the body, and an unexplained steep overhang on the nip cover.**
- launcher_body has a 1.12 wall at (10.4/25.6, -14.3, 175.9), at the widened bay next to the hinge.
- nip_cover has 171 mm² >45 deg with supports=no: 54.5 mm² at the slot end (16,-12,128) and about 65 at the skirt top. BOM section 7 lists it without a reason.
- Fix:
  - Thicken the bay rim to 1.6 by stepping the bay hull 0.5 inboard above z 172.
  - Turn the cover's slot-end underside into a 45 deg chamfer, or state why a 7.7 mm bridge prints clean, and re-run `parts`.

**A2-02 (minor, functionality): the pan-axis slack and lead lengths are still undeclared.**
- Only `CAB_phase_*` has a `lead_len` (80). The bus (254 / 218 / 325), UART (214) and encoder (84) rows have none.
- The hub U-loop is not modelled, although the brief requires slack for ±90 pan.
- Fix:
  - Add `cable_leads` for every purchased lead (Hiwonder bus lead length, JST extension).
  - Model the U-loop in the Ø28 hub bore with ≥ 45 mm slack per cable (π/2 x R 14 x 2 ≈ 44 for ±90).
  - Re-run `cables`.

**A2-03 (minor, functionality): the thumbwheel is reachable only on half its rim.**
- At tilt 0 the rim stands 1.1-1.4 proud of the slot end wall, but the guard land face sits 4.4 mm **proud of the rim** on the other side of the 7.5 slot. The free gap below the slot is 19.0 mm to the groove cap.
- A fingertip sphere (R8) only touches the rim's -u half. It works, but it is fiddly, and no check row covers it.
- Fix: chamfer the guard land edge next to the slot 3 x 45 deg, or raise TW_R 8.5 to 9.5 so the rim stands ≥ 2 proud of both edges. Record the access as a `distances` ray row (it is a fixed origin, which works today).

**A2-04 (minor, manufacturability): the check config has gaps that let BOM claims escape rows.**
- PRT_nip_stop_sleeve and FST_valve_* are in no `assembly_order` step, so they are present from step 1 in access tests.
- Step 10a says "M2 x 4", but the model and the BOM use M2 x 8.
- No `flexures` row is declared for the leaf. The review row passes at 2.2 deg.
- The fixed nip ray (y 37) slips past the hood lip at full lift and reads 14.18.
- Fix: add the sleeve to 6e and FST_valve_* to 12, correct the label, add the leaf `flexures` row, and move the nip rays into the PIV_hood frame.

**A2-05 (minor, functionality): drop margin at the +46 hard stop.**
- At gap 5.3 and tilt 46 the flattest slide is 32.8 against a 28 stall (4.8, under the 5 deg rule).
- At the firmware limit of 45 it is 33.8 (5.8).
- Fix: steepen the chute entry wall by 1 deg, or keep the firmware clamp and note the margin per tilt in the BOM. If A2-01 is fixed by raising the min gap, this goes away (gap 7.0 reads 33.5 at tilt 46).

## Check-config audit
- **allow** (10): agreed. Both the free-state leaf in the thumbwheel and the stud in the thumbwheel nut are physical.
- **fits**:
  - `PRT_hood x PRT_nip_wheel contact` is disputed as unnecessary. They never come within 5.7 over -0.558..1.315 (`cad q sweep`), and a contact fit would hide a future rub. Use min_clearance 0.5.
  - `PRT_base_shell x PRT_turntable contact` still hides the R20/R20.3 journal (deferred by the designer; agreed as a tool limit).
  - The others are agreed. The new `post_R x journal_plate` audit row (0.156 at tilt 22.5) closes the A1 note.
- **joint limits**: `PIV_nip_lift` -1.493 is disputed. The real first contact is the thumbwheel on the cover at about -2.1, and the param comment names the wrong stop (A2-01).
- **drop_tests**:
  - The main row never ran tilt -3 or the hood stops at 45. The review rows pass (31/31).
  - Missing: a drop or grip row at full leaf lift.
- **distances**:
  - Missing a full-lift gap row (A2-01).
  - The fixed y 37 ray misses the hood at full lift.
- **index_tests**: these match the documented 0/+60/0 and 0/-60/0 motion (BOM "How it works"), so they are agreed. The review drift rows at 20/25/30 pass.
- **service / slide_out** (A2-F2 audit). Every BOM service claim has a row, and each row's pose matches the BOM:
  - leaf: tilt 45;
  - tape/flywheel: tilt 45;
  - encoder: tilt 45;
  - tilt servo: no pose;
  - feeder servo: service plus slide;
  - base floor;
  - refill: the gate slide, plus the review stop row (52.5), plus the jar lift;
  - battery.
  The one exception is "Set the nip gap", which rests on `cad q` rays (the tool has no line-of-sight row). The rays were reproduced.
- **flexures**: none declared, although the leaf is a spring (added in review: passes).
- **assembly_order**: matches the BOM steps. The sleeve and the valve screws are unassigned, and the 10a label is stale (A2-04).
- **Overclaims in the BOM**:
  - "A jam lifts the leaf to gap 8.35" is roughly true (about 8.3), but the lift is not the stop the params name.
  - The nip section implies the whole NIP_SET window works; it doesn't below 6.1 (A2-01).

## What is good
- Every A1 major is closed with a row:
  - two real nip stops (contact 0.000 at both);
  - 0.541 hood to body;
  - the finger slot works with the cover on, at tilt 0 and 45;
  - the feeder servo comes out with 2 screws;
  - the crown pilots have 3.5 mm to the pinion.
- Metering is robust. Each stroke opens one window, and the column never opens to the outlet even with the jar fully unlocked (30 deg).
- The drop lands on the descending tape 31/31 at every stop and tilt, including -3 and 46.
- Rotating parts keep ≥ 1.59 mm (motor screws 1.6, which meets the rig's 1.5 rule). The pinch bolts are balanced, and the encoder stack passes at 0.30.
- The feeder and gate now share the form language. The gate tab is flush and has a positive stop. The controller shows only its switch and terminal. The glass jar reads as the hero, and terracotta traces the candy path.
- The BOM is accurate row for row. Every number I re-ran matched, except the two items above.
