# Review: M&M Launcher Turret v2, attempt 3

Checks re-run: `CADCHECK PASS: 0 fail, 34 warn (0 untriaged, 34 accepted)` on `/tmp/rv3/model.blend` (tools f039205, the designer's pin, 134 s). The warn set is identical to the designer's `renders/attempt-3/cadcheck.json` (set difference empty). Copy: `review/cadcheck.json`.
- Coverage: parts 36; interference/clearance 175 objects in all four collections, 4562 pair-poses, 2.5 deg overtravel; fasteners 103 + 4 nuts at 15 poses / 29 steps; service 8; drop 3; index 6; slide 11; distances 57 rows; stacks 3; flexures 2; stability 1728 poses; cables 14 (14 with a lead length).
- Not checked (quoted): "pilot/clearance hole diameters; wrench access to nuts", "dynamic loads (recoil, pan acceleration), friction/sliding", "cables: bend radius, slack across joints, connector positions", "teardown step count, alignment-jig datums, aesthetics, BOM correctness".
- Review rows: `review/review_rows.json` -> `review/cadcheck_review.json` (`--only drop,slide,distances --overlay-only`): **2 fail** (A2-01, thick candy at full lift). The thick-candy drop and the base-floor slide pass. Probes: `/tmp/rv3probe/lentil_tilt.py` (leaning lentil pairs), `/tmp/rv3probe/gate_move.py` (gate at 0..52.35). Log: `review/notes.md`.

| Metric | Score | Anchor matched | One-line reason |
|---|---|---|---|
| Functionality | 8 | "Works. At most 2 major issues, each with a known fix under 1 hour of CAD and no reprint of a big part" | Every attempt-2 item has a row, and every row passes. One major is left: the min-gap fix was sized for the nominal 7.0 candy. The params declare MM_T up to 7.5, and that candy is rigidly squeezed by 0.39 at full leaf lift over about half the thumbwheel window. The encoder lead also stops 430 mm short of the MotorGo in the BOM. |
| Manufacturability | 8 | 9 not met: "nothing would change the print, the assembly" | 0 fastener fails, all parts fit the P1S, no supports, and all 34 warns are triaged with measured reasons. Three BOM errors would change what you buy or build: the stud is M3 x 20 in the BOM but x 16 in the model, M3 x 9 is not a stock length, and the encoder lead is missing. |
| Aesthetics | 8 | "each failed item costs a point from 10" (2 failed) | One EB/CR set everywhere except the new detent clip. That clip has EB 0.3 on a 2.6-6 mm tab, sharp plate corners 14 mm proud of the valve, and a pan head that stands proud, all visible in `iso.png`. No PCB or motor can shows, and the colours still encode the candy path. |

## Previous issues

| Issue | Status | New number |
|---|---|---|
| A2-01 nip leaf runs out of travel before a candy passes | **PARTIAL** | Nominal candy: the bare gap at full lift is 7.613 / 7.928 / 8.461 at hood +0.327 / 0 / -0.558, against 7.5 (pass). It passes with only 0.12 mm of leaf travel left (1.38 of 1.5 used). Declared max candy (MM_T 7.5, needs 8.0): **7.613 and 7.928 fail**, 8.12 at hood -0.2 passes (review row). NIP_PASS uses MM_T_NOM. |
| A1-03 Ø pocket admits an edge-on pair | **PARTIAL** | The pocket is Ø13.9 (4 ray rows read 13.90). A min 12.5 x 6.3 pair overlaps by **-0.016 mm³** each, which is at the 0.01 mm³ reporting floor of `cad q dist`, so the margin is zero. A nominal 13 x 7 pair overlaps by -6.13 mm³. Leaning pairs fit worse: 10 / 20 / 30 deg give -0.095 / -1.28 / -16.9 mm³. A flat 13.5 x 7.5 candy clears by 0.198. |
| A1-09 gate has no detents | FIXED | The clip bump reads 0.10 seated closed and 0.10 at gate +52 (open notch, moved-gate probe). It rides the blade at -0.43 mm³ at +26 (the designed 0.4 lift). Flexure 16.1 MPa, beam 0.0 deg to the bed. Open stop at +52.35 reads 0.00. |
| A1-08 thin walls / steep overhang | FIXED | launcher_body min wall 1.59 with no thin samples (A2: 1.12). nip_cover overhang is 19.5 mm² (A2: 171). Every remaining thin-wall sample is located and accepted. |
| A2-02 lead lengths and pan slack undeclared | **PARTIAL** | 14/14 routes now carry lead_len, and all are shorter than their leads. The pan U-loops add +51.4 and +59.9 (≥ 45). But CAB_encoder (150) ends at the journal bore, and the ~430 mm onward through the bundle and base lead has no purchased lead in the BOM. CAB_bus_pan has 9.5 mm spare. |
| A2-03 thumbwheel reachable on half its rim | FIXED | Rim crest 24.511. Fingertip-vs-shelf rows 25.578 / 25.032 / 23.634 (≥ 24.9 / 24.4 / 22.7). `r03_nip_thumbwheel_closeup_tilt0.png` shows the rim below the cover edge next to the scallop. |
| A2-04 config gaps | FIXED | `unordered_solids_assumed_present` [], step 10a reads M2 x 8, the leaf `flexures` row passes at 2.2 deg, the nip rays are in the PIV_hood frame, and hood x nip_wheel is min_clearance 0.5. |
| A2-05 drop margin at +46 | FIXED | Flattest slide 33.3 at gap 6.2 / tilt 46 (≥ 28 + 5). With a 7.5 payload: 34.2 (review drop row, 31/31 hit at both stops). |

## Measurements

| Item | Value | Source |
|---|---|---|
| Full check | 0 F / 34 W, all accepted, identical to the designer's | `review/cadcheck.json` |
| Index ±60 | 1 window each ([50,60], [-60,-50]); column 0 windows at jar drift 0/5/10/15 | `checks.index` |
| Nip ray at the stops (static) | 6.202 (+0.327) / 7.007 (-0.558) | `checks.distances` |
| Bare gap at full lift (-1.493), hood +0.327 / 0 / -0.2 / -0.558 | 7.613 / 7.928 / 8.12 / 8.461 (need 8.0 for MM_T max 7.5 + 0.5 tape) | `review/cadcheck_review.json` distances |
| Leaf travel used by a nominal candy at the min stop | 1.38 of 1.5 (0.94 mm gap per mm travel) | derived from the two rows above |
| Thumbwheel to roof along the stud | 6.000 home / 4.495 full lift (leaf solid) | `checks.distances` |
| Drop, 7.0 payload, both stops x tilt -3..46 | 31/31 hit, flattest 33.3 | `checks.drop` |
| Drop, 7.5 payload (review), both stops x tilt -3/0/45/46 | 31/31 hit, flattest 34.2 | `review/cadcheck_review.json` |
| Lentil pair 12.5 x 6.3 upright / lean 10 / 20 / 30 deg | -0.016 / -0.095 / -1.28 / -16.9 mm³ (top z 275.5 < ramp 276.8) | `cad q dist ZMM_a PRT_feeder_disc` on `/tmp/rv3probe/mm_*.blend` |
| Lentil pair 13 x 7 upright / lean 20 / 35 | -6.13 / -19.2 / -69.1 mm³ | same |
| Gate detent vs gate at +0 / +26 / +51 / +52 / +52.35 | 0.10 / -0.43 mm³ / -0.20 mm³ / 0.10 / 0.00 | `cad q dist PRT_gate_detent PRT_jar_gate` on `/tmp/rv3probe/gate_*.blend` |
| FST_detent_0 tip to gate over the travel | ≥ 2.652 | same probe |
| Base floor + electronics slide -Z 40 (BOM service) | not blocked (0.0 is the seat) | review slide row |
| Fasteners: model vs BOM | All match except FST_nip_stud: manifest "M3_cap x 16", BOM "M3 x 20 hex head" | `manifest.json` vs BOM section 2 |
| Cables | encoder 84.1/150 (ends at the journal bore); bundle 265.4/350; base 164.8/250; bus_pan 290.5/300 | `checks.cables` |
| Stability | worst 31.2 deg (1728 poses); cg_grid 29.9 deg at tilt 46 | `checks.stability`, `cg_grid.txt` |
| Flexures | leaf 30.7 MPa at solid, 2.2 deg; detent 16.1 MPa, 0.0 deg | `checks.flexures` |

## Issues (ranked)

**A2-01 (major, functionality): the min-gap stop was sized for the nominal candy, not the declared maximum.**
- `params.py` declares `MM_T = (6.3, 7.5)`, but `NIP_PASS = MM_T_NOM + TAPE_T = 7.5`, and the checks row asserts ≥ 7.5.
- A 7.5 candy on 0.5 tape needs a bare gap of 8.0 at full leaf lift. The review row fails at hood +0.327 (7.613) and at hood 0 (7.928), and passes from about hood -0.07. So every setting from 6.2 to about 6.57 (46 % of the 6.2..7.0 window) ends in a rigid 0.07-0.39 mm squeeze with the leaf solid.
- Even the nominal candy uses 1.38 of the 1.5 mm leaf travel at the min stop, so the leaf cycles to within 0.12 mm of solid (about 29 MPa) on every shot.
- The window is also 0.8 mm wide, against the rig's 5..12 thumbwheel range (brief section 2). BOM section 8 only lists it as "rig feedback to come".
- Fix:
  1. Assert `HOOD_GAP_LIFT >= MM_T[1] + TAPE_T` and adopt the review row (min 8.0 at hood +0.327 / 0 / -0.558, full lift).
  2. Caliper the 20 candies first. If MM_T max ≤ 7.1, the current geometry passes. Otherwise raise the nip cover roof 0.5 along the stud axis, so LEAF_TRAVEL goes 1.5 -> 2.0 (full-lift gap ≈ 8.08 at the min stop).
  3. Relieve the body bay 0.5 where the hood sits at -2.6 deg effective (hood to body is 0.50 at the max setting today).
  4. Re-run the leaf `flexures` row: about 36 MPa at solid. Thin LEAF_T 2.5 -> 2.3 if you want it near 31.

**A2-02 (minor, functionality): the encoder signal has no lead between the journal bore and the MotorGo.**
- `CAB_encoder` (BOM item 15, 150 mm JST extension) is routed 84.1 to the left journal end. The BOM says it "continues in the bundle and the base lead". Those routes are 265.4 + 164.8 mm, and their only purchased item is 16 AWG phase wire in 3 colours (item 13).
- So about 430 mm of 5-conductor encoder lead is in no BOM row. It also shares a sleeve with the three BLDC phase wires, and nothing about noise is stated.
- `CAB_bus_pan` keeps only 9.5 mm spare on a 300 lead.
- Fix:
  - Add a BOM row: 5-wire JST-SH (or the Plink's own) lead of ≥ 550 mm from the Plink to the MotorGo encoder JST, one piece and unspliced across both joints. Model `CAB_encoder` as one route with `lead_len` 550.
  - Prefer a twisted or shielded lead, and route it on the opposite side of the sleeve from the phases.
  - List the next bus-lead length up (Hiwonder 350) for the pan servo.

**A1-03 (minor, functionality): the min-size edge-on pair is blocked by a hair.**
- With Ø13.9, the 12.5 x 6.3 pair overlaps by only 0.016 mm³. That is at the 0.01 mm³ floor of `cad q dist`, so the margin is effectively 0.05 radial (needs R 7.0, pocket R 6.95).
- Nominal pairs are well blocked (-6.13 mm³), and leaning (V) pairs fit worse than upright ones (probe), so the risk is a double feed only when two minimum-size candies meet.
- A flat 13.5 candy has 0.198 radial. Both edges of the window are at the mercy of print shrink and candy spread.
- Fix: caliper 20 candies (MM_D, MM_T min/max). Print a 3-pocket test disc with Ø13.7 / 13.9 / 14.1 and record which one passes the flat max and blocks a min pair. Set POCKET_D from that and keep the 4 ray rows at ±0.1 of it.

**A3-01 (minor, aesthetics + manufacturability): the gate detent clip breaks the form language and uses a non-stock screw.**
- `GATE_DETENT["edge"] = 0.3` is applied to the whole clip, including its 2.6-6 mm tab. The declared EB is 1.0 ± 0.5, and the thin gate blade already uses 0.6.
- The 1.2 plate's square corners stand about 14 mm proud of the R34 valve OD (corner at r 48). It reads as a stray grey plate in `iso.png`, `review/r01_*`, `review/r02_*`, and it is a snag point near the gate tab.
- `FST_detent_0` is a pan head with `head="none"`, so it stands proud, and M3 x 9 is not a stock length (BOM section 8).
- Fix:
  - Bevel the tab at EB 1.0 and the plate at 0.6, and round the plate's free end R3 in plan.
  - Counterbore the head Ø6.5 x 1.0 into the tab (3.2 clamp -> 2.2) and use a stock M3 x 10 pan self-tap. The tip then lands where the x 9 tip is now (2.65 above the blade).
  - Optionally print the clip in colour B so it reads as a gate touch point.

**A3-02 (minor, manufacturability): the BOM fastener table lists the wrong nip stud.**
- BOM section 2 says "M3 x 20 hex head (stud) `FST_nip_stud`". The model and params use STUD_L 16 (manifest "M3_cap x 16"), and the params comment places the tip 2.4 under the cover roof at full lift on the 7.0 setting.
- A x 20 stud puts the tip 4 mm further out at the stud window.
- The model's head is a cap cylinder in a hex pocket, so the head key that stops the stud turning with the thumbwheel is not represented.
- Fix: change the BOM row to "M3 x 16 hex head, ISO 4017" and give `FST_nip_stud` a hex-head spec (AF 5.5 x 2.0), so the pocket fit is measured.

**A3-03 (minor, functionality): the check config misses two rows the BOM relies on.**
- The BOM service "Base floor: 8 screws from below" has a `service` row but no `slide_out` row. The review row (floor + partition + MotorGo + buck + controller, -Z 40) passes.
- The full-lift gap row asserts the nominal 7.5, not the declared max (A2-01).
- The detent's open-notch claim ("clicks into a notch at both ends") has no row, because the gate is not a joint. The review probe shows 0.10 at +52.
- Fix: adopt `review/review_rows.json` as is. Add a prismatic `PIV_gate` (0..52.35) if the tool supports one, then turn the detent check into a `distances` row at both ends.

## Check-config audit
- **allow** (10): agreed.
- **fits** (30): agreed.
  - The A2 dispute is resolved: hood x nip_wheel is now min_clearance 0.5, and base_shell x turntable uses contact_normal [0,0,1].
  - post_R x journal_plate is still a contact fit. The 0.156 audit row at tilt 22.5 stands (deferred, accepted as a tool limit).
- **joint limits**: PIV_nip_lift -1.493 is agreed as the leaf-solid stop (6.000 -> 4.495 = pad + strip 4.5 along the stud). PIV_hood -0.558..+0.327 matches the sleeve and the nip_stop (both 0.000).
- **accepted_warns** (34):
  - Overtravel (16), gear tips (4), bridges (3) and the beam overhang: agreed.
  - Thin walls: agreed, but the PRT_gate_detent 1.2 is the beam by design and its 0.3 edge is A3-01.
  - Tilt-servo slide 0.10: agreed. The M2 tip and the journal plate ride the same body, and the screw length tolerance (±0.29) can at most seat the tips.
- **drop_tests**: agreed. Both hood stops x tilt -3/0/22.5/45/46 are covered. `home_only_ok` for PIV_nip_lift is agreed: a candy drops only with the leaf at rest. Missing: a payload at MM_T max (review row added: passes).
- **index_tests**: agreed. They match the documented 0/+60/0 and 0/-60/0 strokes and the 0/60/0/-60/0 column test at jar drift 0..15.
- **distances**: disputed: "v2-A2-01 bare gap at FULL leaf lift ... min 7.5" should be 8.0 (A2-01).
- **service / slide_out** (A2-F2 audit). Each BOM motion or service claim against its row:
  - leaf, tape/flywheel and encoder at tilt 45: match;
  - tilt servo: no pose, BOM none: match;
  - feeder servo: service + slide: match;
  - refill: jar slide at 30 + gate slide 52 + detent (probe only);
  - battery: slide 1.60;
  - pod lift-out at tilt 20: match;
  - base floor: **slide row missing**, added in review, passes;
  - set the nip gap: distances rays (no line-of-sight row type).
  The gate slide row's `ignore: FST_detent_*` is harmless: the screw tip keeps ≥ 2.652 over the travel.
- **flexures**: agreed. The leaf is 30.7 MPa at 2.2 deg and the detent 16.1 MPa at 0.0 deg, both in the layer plane.
- **assembly_order**: matches the BOM steps 1..14. The floor bench sub-assembly drops in clean (the reversed review slide row).
- **params assert**: `NIP_PASS = MM_T_NOM + TAPE_T` is disputed. It should use `MM_T[1]`.

## What is good
- Every attempt-2 row-level finding is closed with a row, and the designer's numbers re-ran identically, down to the warn set.
- The nip has two real printed stops (0.000 contact at both). The jam lift is bounded by a modelled solid leaf stack (4.495) instead of a guessed angle.
- The feeder meters one window per stroke at every drift. The Ø13.9 pocket robustly blocks nominal pairs, and the leaning-pair probe shows upright is the worst case, so the edge-on study is complete.
- The gate now has a positive open stop and a working detent at both ends, with the beam printed in-plane.
- The drop lands on the descending tape 31/31 at both stops, every tilt and both payload sizes, with ≥ 5 deg margin.
- All 34 warns are triaged with coordinates and measured reasons. The bench floor and the battery come out clean.
- The pan slack is modelled as real U-loops with asserted added length.
