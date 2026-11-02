# Review: M&M Launcher Turret v2, attempt 6

Checks re-run: `CADCHECK PASS: 0 fail, 35 warn (0 untriaged, 35 accepted)` on `/tmp/rv6/model.blend` (tools 36189b8 from `alex-3d-skills-pin`, the designer's pin; 166.8 s). Copy: `review/cadcheck.json`. All 16 check sections match the designer's `renders/attempt-6/cadcheck.json` exactly. Only `runtime_s` differs.
- Coverage: parts 36. Interference/clearance: 177 objects in all four collections, 5126 pair-poses, 8 joints swept with 2.5 deg overtravel. Fasteners: 103 screws + 4 nuts at 16 poses / 29 steps. Service 8 ops / 26 accesses. Drop 4. Index 6. Slide 13. Payload 4. Sightlines 3. Assembly 29 steps, 177 placed, 0 in no step. Stacks 4. Flexures 2. Stability 3456 poses. Cables 14/14 with lead length, plus 2 chains. `distances` (83 row-poses) is not listed in `coverage`.
- Not checked (quoted): "fasteners: pilot/clearance hole diameters ...; wrench access to nuts", "stability: dynamic loads (recoil, pan acceleration), friction/sliding", "cables: bend radius, slack across joints, connector positions (review by section render)", "not geometric: teardown step count, alignment-jig datums (declare stacks), aesthetics, BOM correctness".
- Review rows: `review/review_rows.json` -> `review/cadcheck_review.json` (`--only slide,service --overlay-only`), with 3 slide rows and 1 service op. Result: **1 fail** (A6-01).
- `cad bom BOM_AND_ASSEMBLY.md manifest.json`: 18 rows, 0 disagree, 0 modelled screws in no row.
- Measurement log: `review/notes.md`. Renders: `review/r01_detent_tab_flat_top_closeup.png`, `review/r02_sec_x5.73_hub_bore_junction_closed.png` (2 of the 12 allowed).

| Metric | Score | Anchor matched | One-line reason |
|---|---|---|---|
| Functionality | 9 | "Minor polish only ... cadcheck has 0 fails and every warn is explained"; the functionality 9 list is met: every payload path is drop-tested at both stops, the working condition is reached (`distances`), sweeps are clear, cables have length and slack | 31/31 drops at every stop, flattest 34.5. The full-lift entry arc is swept psi 0..104 at 3 settings (min 8.099). The splice is modelled and clear (>= 1.0 to every bore). What remains is minor: the 0.099 min-stop margin, now covered by the BOM rule, and the pan lead's last stretch to the off-axis splice. |
| Manufacturability | 8 | "Works. At most 2 major issues, each with a known fix under 1 hour of CAD and no reprint of a big part" | 0 fastener fails, every screw reachable, no supports, everything fits the P1S, the BOM matches the model. A5-01 is fixed. One new major (A6-01): BOM step 10d asks you to splice and seat the bus junction in a hub bore that is closed at that step, by the groove cap (2c) above and the base floor (3) below. The fix is BOM text plus one row. |
| Aesthetics | 9 | "9 needs every item true" | The flat-topped detent tab with EB 1.0 and a flush head reads as deliberate (`review/r01_*`). There is one EB 1.0 / CR 6 set, colour B traces the candy path, no PCB, wire or motor can shows in iso or iso_front_left, and `side.png` now frames the jar top and the base bottom. |

## Previous issues

| Issue | Status | New number |
|---|---|---|
| A5-01: detent tab 0.322 from the jar band | **FIXED** | `distances` band to detent **1.000** (min 1.0; `cad q dist` 1.0 at (4.8, 36.44, 300.5)). The tab top is at z 299.5 (`cad q list` hi z 299.5). Stack `v2-A5-01`: worst case 0.8, RSS 0.418, against 1.0. The tab sits wholly under the band's flat lower face, so the band's radial terms no longer apply (agreed). Head flush: stand-off 0, engagement 4.0. Screw tip to gate 2.652 / 14.867. |
| A5-02: 0.099 entry-arc margin at the min stop; tape seam not specified | FIXED | The margin is unchanged: swept rows read 8.099 @ psi 90 / 8.211 @ 92 / 8.397 @ 92, hood to tape 7.599 / 7.711 / 7.897, rest 6.176 / 6.493 / 6.987. The fix the review asked for is in place: step 6f butt-joins the tape and calipers it at 0.5 or less; section 8 says to run at home or above when the calipered `MM_T` max is over 7.3; the five point rows became swept rows over psi 0..104. |
| A5-03: bus junction not modelled | FIXED (new access issue A6-01) | `BUY_bus_junction` is Ø10 x 25 on `PIV_pan` at (5.73, 4.02), z 74..99, 8 g, step 10d. To the turntable 1.945, to the hub gear 1.000, to the bundle 2.846, to the base lead 3.548 / 5.130 / 4.206 at pan -90 / 0 / 90 (swept min 3.536). 0 junction warns. |
| A5-04: PLA leaf creep | FIXED (as asked) | The BOM lists 2 leaves (one spare), a day-0 / 1-week preload log with pass/fail thresholds (6.4 N, 0.12 set), and the `LEAF_L` 34 -> 40 trigger. The 40 leaf is not modelled, as the review allowed. |
| A5-05: tape width and side.png framing | FIXED | Item 12 is 1 in tape trimmed to the 13.8 land (`BUY_tape` x 14.1..27.9). `side.png` shows z 0..432.6 in a 467.2 window, with the jar top and the base bottom in frame. |
| A5-06: unbounded `allow` detent x gate | FIXED | The allow is deleted. A `fits` rule with `contact_normal` [0,0,1] and `min_clearance` 0.05 replaces it: interference min 0.10 at gate 39. Gate slide min 0.08 with `flexed` {}. One accepted overtravel touch at gate -1, past the -0.4 stop. |

## Measurements

| Item | Value | Source |
|---|---|---|
| Full check | 0 F / 35 W, 0 untriaged, stale [], identical to the designer's | `review/cadcheck.json` |
| Full-lift entry arc (swept psi 0..104), min / home / max stop | **8.099 @ 90** / 8.211 @ 92 / 8.397 @ 92 (min `NIP_PASS` 8.0) | `distances` v2-A5-02 |
| Hood to `BUY_tape`, full lift | 7.599 / 7.711 / 7.897 (min 7.5) | `distances` v2-A5-02 |
| Rest gap profile | 6.176 @ 18 / 6.493 @ 0 / 6.987 @ 50 (min 6.1) | `distances` v2-A5-02 |
| Psi 0 station at home and at the max stop | `missed_deg [0]`. BDC is covered by the v2-A3-A2-01 rows at 8.592 / 9.123 | `cad rows ... v2-A5` |
| Drops, 7.0 and 7.5 candies, both stops x tilt -3..46 | 31/31 hit everywhere, flattest 34.5 at tilt 46 | `checks.drop` |
| Index | +60: 1 window 50..60; -60: 1 window -60..-50; column never open at jar drift 0/5/10/15 | `checks.index` |
| Pocket | min pair blocked by 0.06, nominal pair by 0.34, flat max fits by 0.14 | `checks.payload` |
| Band to detent tab | **1.000**; stack worst case 0.8 / RSS 0.418 against 1.0 | `distances`, `stacks` v2-A5-01 |
| Junction to bores / bundle / base lead | 1.945 / 1.000 / 2.846 / min 3.536 over the pan sweep | `distances` v2-A5-03, `interference.min_clearance` |
| Hub bore closure at step 10d | ray +Z from the splice top (5.73, 4.02, 99.5) hits `PRT_groove_cap` at 2.5; ray -Z from its bottom hits `PRT_base_floor` at 70.5 | `cad q ray` |
| Junction out +Z, everything assembled | **blocked at 4 mm by `PRT_groove_cap`** | review slide row (FAIL) |
| Groove cap off at tilt 45 | 6 x `FST_gcap_*` straight 14; the cap lifts +Z 40 with 0.2 to `PRT_post_L` | review service + slide rows |
| Junction out -Z with the floor group off | not blocked, min 1.0 (hub gear) | review slide row |
| Static `CAB_bus_pan` end to the moving splice | 1.2 at pan -25..+42.5, 2.72 / 3.95-4.38 at pan -70 / ±90 (the splice's bottom centre moves 9.9 on its r 7 chord) | `cad q sweep CAB_bus_pan BUY_bus_junction PIV_pan` |
| Assembly steps | junction 10d, groove cap 2c, floor 2a (into the shell at 3), `CAB_bus_pan` 3 | `assembly.step_of` |
| Flexures | leaf 35.5 MPa, 2.2 deg; detent 16.1 MPa, 0.0 deg (both in the layer plane) | `checks.flexures` |
| Stability | worst 31.2 deg (cadcheck); 29.9 deg (cg_grid, tilt 46) | `checks.stability`, `cg_grid.txt` |
| Cables / chains | bus 287.7/350, 206.5/300, 319.6/500; encoder chain 511.8/545; phases 490.2/700 | `checks.cables` |

## Issues (ranked)

**A6-01 (major, manufacturability): BOM step 10d splices and seats the bus junction inside a hub bore that is closed at that step.**
- Item 14a and step 10d say the junction "sits in the hub bore at r 7 ... z 74..99, the tilt and feeder leads entering from above, the pan lead from below". By step 10d the bore is closed at both ends:
  - above, by `PRT_groove_cap` (step 2c). A ray up from the splice top hits it 2.5 mm away at z 102;
  - below, by the base floor (step 3). A ray down from the splice bottom reaches `PRT_base_floor` 70.5 below.
- The review slide row shows `BUY_bus_junction` +Z blocked by `PRT_groove_cap` at 4 mm. So the splice cannot be put into its modelled place, or made there, in the order the BOM gives. The step also doesn't say where the soldering is done, or how the three leads get to it.
- There is an access route, and it is measured:
  - at tilt 45 the 6 `FST_gcap_*` take a straight bit (reach 14), and the groove cap lifts +Z 40 with 0.2 to `post_L`;
  - with the floor group off, the junction drops -Z 70 unblocked (min 1.0).
  - The lead spares (pan 62.3, tilt 93.5, feeder 180.4) are enough to pull all three ends above the turntable for soldering.
- Retention: the splice is held only by a tie to the bundle sleeve, 1.0 from the R13 hub-gear bore.
- Evidence: `review/cadcheck_review.json` FAIL "R6 A6-01 bus junction placed/removed from above"; `cad q ray` lines in `review/notes.md`; `review/r02_sec_x5.73_hub_bore_junction_closed.png`; `assembly.step_of` (junction 10d, groove cap 2c, floor 3).
- Fix (BOM + checks, no reprint):
  1. Rewrite step 10d:
     - tilt to 45 and remove the groove cap (6 x M3 x 10 csk, straight bit);
     - pull the pan lead up through the bore (62 spare) and the tilt / feeder leads down to it;
     - solder and heat-shrink above the turntable;
     - lower the Ø10 x 25 splice into the bore at az 35, so its bottom is at z 74;
     - tie it to the bundle sleeve, push the spare pan lead back into its U-loop, and refit the cap.
  2. Add to checks.json the adopted review rows (groove cap service at tilt 45 and slide +Z 40), plus a slide row that moves the splice -Z 25 into its seat with the cap removed (`ignore` the cap).
  3. Optional: a 2 mm cable-tie slot in the hub-gear bore wall at az 35, so the splice can't drop past z 74 onto the U-loops.

**A6-02 (minor, functionality / cables): the static pan lead ends 1.2 under an off-axis splice that orbits 9.9 mm over ±90 pan.**
- A5's junction sat on the pan axis. At r 7 (az 35), the splice's bottom face centre moves on a 7 mm radius. At pan ±90 it is 9.9 from the static riser end (`cad q sweep`: 1.2 at -25..+42.5, then 2.72 at -70 and 3.95-4.38 at ±90).
- So the last stretch of `CAB_bus_pan` both swings sideways and twists under the hub gear. The U-loop (+61.1) has the length, but this extra lateral swing is not in any row. "Slack across joints" is in `not_checked`.
- The base lead's meeting point (r 4, z 70) does the same. Its `distances` row passes only because the two Ø6 sleeves overlap (0.133 / 0.002 / 0.097).
- Evidence: `review/notes.md` sweep line; `cad q list CAB_bus_pan` (top z 72.8, static).
- Fix, either of:
  - Run the pan lead's last 20 mm on `PIV_pan`: split `CAB_bus_pan` at z 70 into a static loop and a moving tail ending on the splice bottom. Then add a `distances` row (max 1.0) between the loop end and the tail start at pan -90 / 0 / 90.
  - Or move `BUS_JCT` r 7 -> 0 with the bundle at r 7. The bundle is also on `PIV_pan`, and the base meeting point then needs the same tail treatment.

**A6-03 (minor, check config): the swept full-lift rows miss the psi 0 station at home and at the max stop.**
- Both rows report `missed_deg [0]`, so their minima come from psi 2..104. BDC is covered by the separate v2-A3-A2-01 rows (8.592 / 9.123), so no evidence is missing. Still, a swept row that silently drops its first station would hide a real miss elsewhere.
- Evidence: `cad rows review/cadcheck.json v2-A5` ("profile=0:-", `missed_deg=[0]`).
- Fix: start the sweeps at psi 1 (or move the ray origin 0.5 radially inward), so the station lands on the hood face. Then confirm all 53 stations hit at all 3 settings.

## Check-config audit
- **allow** (11): agreed. The A5 detent x gate allow is gone.
- **fits** (33): agreed. The new `PRT_gate_detent x PRT_jar_gate` rule (contact on Z faces only, `contact_normal` [0,0,1], `min_clearance` 0.05) is the right bound. `post_R x journal_plate` still has no `contact_normal`; the 0.156 audit row stands (tool limit, deferral agreed).
- **distances**:
  - band to detent min 1.0 is agreed.
  - The v2-A5-03 junction rows are agreed for clearance. They do not cover how the splice gets into the bore (A6-01) or the static-to-moving lead end (A6-02).
  - The swept entry-arc, tape and rest rows are agreed (A6-03 for the psi 0 station).
  - The `past_limit_ok` flags on the 7 hard-stop rows are agreed: each row measures a printed stop on purpose.
- **stacks**: `v2-A5-01` (vertical, 4 terms, worst case 0.8 against 1.0) is agreed. The tab lies under the band's flat lower face, so the radial chain from review 5 no longer applies.
- **joint limits**: agreed and unchanged.
- **accepted_warns** (35): agreed. The re-triaged `PRT_gate_detent: 64 wall samples` accept quotes the plate and the counterbore rim rays, which matches `r01`. The new gate -1 touch is past the -0.4 stop.
- **drop_tests**: agreed (both stops x tilt -3..46, 7.0 and 7.5 candies).
- **index_tests / service / slide_out vs the BOM (A2-F2):**
  - Every BOM motion or service claim has a matching row: index +60 / -60 one window each and the column never open at drift 0..15; leaf, pod cover, pinch bolts and encoder at tilt 45; tilt servo +X 60; feeder servo and lobe cover +Z; base floor -Z 40; refill (jar +Z at 30, gate +X 52 on flex, open stop blocked at 52.5, hard-stop rows 0.000); battery +X 120; pod lift-out at tilt 20; thumbwheel sightlines 3/3 x 3 poses; jam 9.124.
  - The one new claim is that the junction is placed in the bore at step 10d. It had no row. I added it (`review/review_rows.json`), and it fails (A6-01).
- **assembly_order**: matches BOM steps 1..14. `assembly.step_of` places all 177 objects, `BUY_bus_junction` in 10d. The order is right, but step 10d needs the groove cap off, and nothing in the config records that (A6-01).

## What is good
- A5-01 is closed properly. The tab is now a 6-chord prism with a real EB 1.0. The designer found that A5's n=768 cylinder cut had clamped every tab edge break to about 0.1, and fixed the cause. The vertical stack replaces the radial chain with the right terms.
- The entry arc is now one swept row per setting. It reproduces the review's psi 90 minimum exactly and quotes the whole profile.
- The splice is modelled with real numbers. The designer measured that the first base-lead placement overlapped the swept splice (-5.09 mm³ at pan -90) and moved it, rather than accepting a warn.
- The designer's numbers re-ran exactly, `cad bom` is clean, and every BOM claim but the new splice placement has a row.
