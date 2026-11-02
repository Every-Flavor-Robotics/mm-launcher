# Review: M&M Launcher Turret v2, attempt 5

Checks re-run: `CADCHECK PASS: 0 fail, 34 warn (0 untriaged, 34 accepted)` on `/tmp/rv5/model.blend` (tools dea6536 from `alex-3d-skills-pin`, the designer's pin; 165 s). Copy: `review/cadcheck.json`. All 16 check sections match the designer's `renders/attempt-5/cadcheck.json` exactly. Only `runtime_s` differs.
- Coverage: parts 36. Interference/clearance: 176 objects in all four collections, 5122 pair-poses, 8 joints swept (the new prismatic `PIV_gate` is included). Fasteners: 103 screws + 4 nuts at 16 poses / 29 steps. Service 8. Drop 4. Index 6. Slide 13. Payload 4. Sightlines 3. Assembly 29 steps, 0 objects in no step. Stacks 3. Flexures 2. Stability 3456 poses. Cables 14/14 with lead length, plus 2 chains. Distances: 83 rows. `distances` is not listed in `coverage`.
- Not checked (quoted): "fasteners: pilot/clearance hole diameters ...; wrench access to nuts", "stability: dynamic loads (recoil, pan acceleration), friction/sliding", "cables: bend radius, slack across joints, connector positions", "not geometric: teardown step count, alignment-jig datums, aesthetics, BOM correctness".
- Review rows: `review/review_rows.json` -> `review/cadcheck_review.json` (`--only distances,stacks --overlay-only`), with 45 distance row-poses and 1 stack. Result: **2 fail**, both A5-01.
- `cad bom BOM_AND_ASSEMBLY.md manifest.json`: 18 rows, 0 disagree, 0 modelled screws in no row.
- Measurement log: `review/notes.md`. Renders: `review/r01_*`, `review/r02_*` (2 of the 12 allowed).

| Metric | Score | Anchor matched | One-line reason |
|---|---|---|---|
| Functionality | 9 | "Minor polish only ... cadcheck has 0 fails and every warn is explained"; the functionality 9 list: every payload path is drop-tested at both stops, the working condition is reached (`distances`), sweeps are clear | A2-01 is fixed. At full leaf lift the nip passes the declared 7.5 candy on tape over the **whole** entry arc (8.099 minimum over psi 10..102, at all 3 settings), and 31/31 drops land at every stop with the flattest slide at 34.5. What remains: a 0.1 pass margin at the min stop, an unmodelled bus splice, and leaf creep. All three are minors. |
| Manufacturability | 8 | "Works. At most 2 major issues, each with a known fix under 1 hour of CAD and no reprint of a big part" | 0 fastener fails, every screw reachable, no supports, everything fits the P1S, the BOM matches the model. One major (A5-01): the reshaped detent tab sits 0.322 from the steel jar band, but the designer's own band tolerance chain is 1.26 RSS / 1.90 worst case. The fix is a 1.7 g part. |
| Aesthetics | 9 | "9 needs every item true" | A4-01 is closed. The tab now has one planar 45 deg chamfer with EB 1.0, and the pan head sits flush in its counterbore (`review/r02_detent_tab_closeup.png`). There is one EB 1.0 / CR 6 set, colour B traces the candy path, and no PCB, wire or motor can shows in iso or iso_front_left. |

## Previous issues

| Issue | Status | New number |
|---|---|---|
| A2-01: the full leaf lift does not open the entry arc | **FIXED** | Designer rows, psi 50..80 x 3 settings: 8.105..8.884. Review rows, psi 10/20/30/40/85/90/94/98/102 at the min stop with the leaf solid: 8.277 / 8.319 / 8.311 / 8.241 / 8.105 / **8.099** / 8.183 / 8.782 / 9.676. The minimum is at home 8.219 and at the max stop 8.423, both at psi 90. All are at least `NIP_PASS` 8.0 (A4: 7.50 at psi 80). Hood to the modelled tape at psi 80: 7.607 (at least 7.5). `params` asserts `gap_arc` over psi -3..112, and `finish.py` re-asserts it at 3 settings. |
| A4-01: detent tab notch and proud head | FIXED | One 45 deg chamfer across the tab top with EB 1.0. `FST_detent_0` bbox y max 39.9 equals the back face 39.9; stand-off 0, engagement 4.0 (`fasteners`). The close-up reads as deliberate (`review/r02_detent_tab_closeup.png`). The chamfer brought the band clearance down from 0.5 to 0.322: see A5-01. |
| A4-02: BOM and manifest numbers drift | FIXED | `PRT_nip_cover.orient` reads "finger slot 22 x 8.3". `PRT_nip_leaf.operating` and the BOM table come from `gap_arc`: min stop 0.68 / 28.1 MPa nominal and 0.94 / 34.2 MPa thickest, re-derived as 12.5 + 23.0 x lift fraction. |

## Measurements

| Item | Value | Source |
|---|---|---|
| Full check | 0 F / 34 W, 0 untriaged, stale [], identical to the designer's | `review/cadcheck.json` |
| Full-lift entry arc, min stop, psi 10..102 | min **8.099 at psi 90**, 8.105 at psi 85, 8.183 at psi 94, 8.241 at psi 40 | `review/cadcheck_review.json` |
| Full-lift entry arc, home / max stop | min 8.219 / 8.423 (psi 90) | same |
| Rest gap at the min stop, psi 0 / 50 / 70 / 85 / 90 / 94 | 6.197 / 6.225 / 6.674 / 7.130 / 7.288 / 7.479 | same (rest rows) |
| Rest gap at the max stop, same psi | 7.003 / 6.987 / 7.253 / 7.525 / 7.618 / 7.765 | same |
| Hood to `BUY_tape`, psi 80, min stop, leaf solid | 7.607 (at least `MM_T[1]` 7.5) | same |
| Section: 13 x 7.5 lentils at psi 85 / 90, min stop, leaf solid | the lentil clears both the hood and the tape, by about 0.1 in total | `review/r01_nip_x21_minstop_fulllift_lentil13x7.5_psi85_90.png` |
| Drops, 7.0 and 7.5 candies, both stops x tilt -3..46 | 31/31 hit (`PRT_flywheel` or `BUY_tape`), flattest 34.5 at tilt 46 | `checks.drop` |
| BDC at full lift / jam | 8.282 / 8.592 / 8.781 / 9.123; jam 9.124 (8.8..9.3) | `checks.distances` |
| Leaf hard stop / home along the stud | 4.288 / 6.500 | `checks.distances` |
| Hood to body, static max, leaf solid | 0.532 | `checks.distances` |
| Band to detent tab | **0.322** at (10.67, 35.17, 300.5). The tab top is at z 301.5, 1.0 above the band's lower face at z 300.5 | `cad q dist` / `cad q list`, review row (min 0.7) |
| Band-to-tab tolerance chain (glass/band 1.0, disc in band 0.75, spout in valve 0.15) | RSS **1.26**, worst case **1.90**, against 0.455 radial (0.322 normal on the 45 deg face) | review `stacks` row |
| Gate detent | seated 0.10 at gate 0 and at gate 52; lug to adapter 0.000 at 52.35; blade to valve 0.000 at -0.4; screw tip to blade 2.652 / 14.867 | `checks.distances` |
| Flexures | leaf 35.5 MPa at solid, 2.2 deg to the bed; detent 16.1 MPa | `checks.flexures` |
| Stability | worst 31.2 deg (cadcheck); 29.9 deg (cg_grid, 64 poses including tilt 46) | `checks.stability`, `cg_grid.txt` |
| Cables / chains | encoder 514.3 / 545, phases 492.7 / 700, bus_pan 290.5 / 350 | `checks.cables` |
| `BUY_tape` width | x 14.1..27.9 = 13.8, against BOM item 12 "1/2 in" tape = 12.7 | `cad q list BUY_tape` |

## Issues (ranked)

**A5-01 (major, manufacturability): the detent tab sits 0.322 from the steel jar band, inside the band's own tolerance chain.**
- The A4-01 chamfer replaced the R37.25 relief step (0.5). The tab top still rises to z 301.5, 1.0 above the band's lower face (z 300.5). It wraps the band's lower outer corner at 0.322 normal on a 45 deg face, which is 0.455 radial.
- The clip is screwed to the valve, which sits on the adapter spout. So the band-to-tab position carries the same terms as the designer's own band-to-housing stack: glass/band 1.0, adapter disc in the band 0.75, spout in the valve 0.15. That gives RSS 1.26 and worst case 1.90 against 0.455.
- Every other band row in checks.json uses min 2.0 ("glass/band tolerance +/-1: nothing touches the band (brief 1)"). This row uses min 0.3.
- Consequence: an oversize or eccentric band bears on the PLA tab. That preloads the detent screw, and the band edge scrapes the tab when it is screwed on and off at every refill.
- Evidence: `review/cadcheck_review.json`, which has two fails: the distance row (min 0.7) and the stacks row (RSS 1.26 > 0.455). `cad q dist BUY_jar_band PRT_gate_detent` = 0.322.
- Fix (feeder, `GATE_DETENT`):
  - Cap the whole tab top flat at **z 299.5**, 1.0 below the band face, and keep EB 1.0. Then the band's radial tolerance no longer matters.
  - That still leaves 3.3 over the Ø3.4 clearance hole (top 296.2) and 1.7 over the Ø6.6 counterbore (top 297.8). So the screw, the counterbore and the tip position (2.652 above the blade) are unchanged.
  - Change the row to `BUY_jar_band` > `PRT_gate_detent` min 1.0, and adopt the review `stacks` row.

**A5-02 (minor, functionality): the declared-max candy passes the min-stop entry arc by 0.1, and the tape seam is not specified.**
- At the min stop with the leaf solid, the arc minimum is 8.099 (psi 90) against `NIP_PASS` 8.0. The BOM says the same: 6 % of travel, 0.13 at the stud.
- That 0.1 is within FDM tolerance on the hood's inner face (about ±0.15). It is also less than one extra tape layer: an overlapped wrap doubles `TAPE_T` to 1.0 at the seam. BOM item 12 and step 6f don't say how to join the tape.
- So a 7.5 candy at the min stop can reach the solid leaf and be squeezed rigidly by up to about 0.4 at the seam.
- Evidence: `review/cadcheck_review.json` psi 85..94 rows; `review/r01_nip_x21_minstop_fulllift_lentil13x7.5_psi85_90.png`; BOM section 0 / item 12.
- Fix:
  - BOM 6f: butt-join the tape with no overlap, and caliper the tape at 0.5 or less.
  - BOM section 8: if `MM_T` max is over 7.3 after calipering, use home or above, not the min stop.
  - Adopt the review rows for psi 85 / 90 / 94, which hold the actual minimum.
  - Extra leaf travel buys little here. At psi 90 the full lift opens only 0.81 for 2.2 of travel (0.37 per mm), so `LEAF_TRAVEL` 2.4 would add about 0.07. Meanwhile the leaf-solid stress would rise from 35.5 to about 37.6 MPa. The BOM instruction is the better fix.

**A5-03 (minor, functionality / cables): the 3-way bus junction (item 14a) is real hardware that is neither modelled nor sized.**
- The three bus leads end at (0, 0, 76) on the pan axis, in the R14 hub bore, beside the launcher sleeve.
- The junction rule flagged it. It was cleared through `cable_junctions_ok` `CAB_bus_*` with no object, so the bore fill and the splice's position against the pan twist are unchecked. The splice sits at the static/moving transition, where the U-loop takes ±90 deg.
- Evidence: checks.json `cable_junctions_ok`; BOM 14a ("not modelled ... size in the R14 bore ... unchecked").
- Fix: model the splice as `BUY_bus_junction`, a Ø10 x 25 envelope. Put it on the moving side above the U-loop, tied to the hub, and include it in interference and in the cable rows. Or take the BOM's daisy-chain alternative and route `CAB_bus_feeder` to the tilt servo.

**A5-04 (minor, functionality): the PLA leaf runs at 28 MPa per shot at the min stop on a 12.5 MPa static preload.**
- Nominal candy: 28.1 MPa at the min stop and 24.7 at home. Thickest candy: 34.2 MPa. The preload holds 12.5 MPa at all times.
- That is about 50-60 % of printed PLA strength. It creeps under the constant preload, so the squeeze will relax over weeks, and the leaf fatigues at the min stop.
- Evidence: manifest `PRT_nip_leaf.operating`; `flexures` 35.5 MPa at solid.
- Fix: print a spare leaf (1 g) and list it in the BOM, and log the preload in the rig after one week. If the rig shows relaxation, set `LEAF_L` 34 -> 40 if the cover allows. At the same deflection that is x0.72 stress: 20 MPa nominal at the min stop.

**A5-05 (minor, documentation): model, BOM and render drift.**
- `BUY_tape` is 13.8 wide (x 14.1..27.9), but BOM item 12 buys 1/2 in (12.7) tape. Either buy 14 mm or wider tape trimmed to the land, or set the model width to 12.7 and re-run `drop` (8 of 31 rays already land on the bare land).
- `renders/attempt-5/side.png` crops the jar top and the base bottom. Re-frame it like `front.png`.

**A5-06 (minor, check config): `allow PRT_gate_detent x PRT_jar_gate` is an unbounded ignore.**
- Its own reason is that the riding overlap (0.43 mm³) is under `vol_tol` 0.5, so the rule isn't needed. As written, it would hide a deeper detent-to-gate clash in every gate sweep.
- The slide row already bounds the ride with `flex {PRT_gate_detent: 1.0}`. That is the checklist's pattern (V2A3-T6).
- Fix: delete the allow. If the sweep then flags the ride, replace it with a `fits` rule on the pair at a 1.0 mm³ bound, not an ignore.

## Check-config audit
- **allow** (12): 11 agreed. The new `BUY_tape x PRT_flywheel` (tape on the land) is agreed. `PRT_gate_detent x PRT_jar_gate` is **disputed** (A5-06).
- **fits** (32): agreed. The new rules `jar_valve x jar_gate` and `jar_adapter x jar_gate` (min 0.3, a 0.35 slide clearance) are agreed. `post_R x journal_plate` has no `contact_normal`; the 0.156 audit row stands (deferral agreed).
- **distances**:
  - `BUY_jar_band > PRT_gate_detent min 0.3`: **disputed** (A5-01). It should be min 1.0, consistent with the band rows' 2.0 and the band stack.
  - The entry-arc rows cover psi 50..80. The real minimum is at psi 90 (8.099), so adopt the review psi 85 / 90 / 94 rows.
  - Everything else is agreed, including the new gate hard-stop rows (0.000 at -0.4 and at 52.35) and the open-notch seat (0.10).
- **joint limits**: agreed.
  - `PIV_gate` is prismatic, 0..52 (open notch), home 0, with 1.0 overtravel into both printed stops (accepted warns, with measured 0.000 rows).
  - `PIV_nip_lift` -2.190; `PIV_hood` -0.558..+0.327; tilt 0..45 with lugs at +46.
- **accepted_warns** (34): agreed. Each one quotes an in-range measurement. There are no stale accepts.
- **drop_tests**: agreed. The target is now `[PRT_flywheel, BUY_tape]`. This is physically right: a 7.0 candy on the hood meets the tape at a bare gap of 7.5. A1-A4 were 0.5 conservative. Both stops x tilt -3..46 x 7.0 / 7.5 are covered.
- **index_tests**: agreed. They match the BOM's "+60 then 0, -60 then 0" and the column-never-open sequence at drift 0..15.
- **service / slide_out**: every BOM motion or service claim was checked against its row (A2-F2):
  - leaf, tape / flywheel (the slide now carries `BUY_tape`) and encoder at tilt 45: match;
  - tilt servo slide 60: match;
  - feeder servo (service + slide + lobe-cover slide): match;
  - base floor -Z 40: match;
  - refill (jar lift at 30; gate +X 52 with flex; open stop blocked at 52.5 by the adapter): match;
  - battery +X 120: match;
  - pod lift-out at tilt 20: match;
  - set nip gap: sightlines 3/3 x 3 poses: match;
  - jam about 9.0: the 9.124 row matches.
  No entry was missing. The only rows the review added are the entry-arc, rest-gap, band and stack rows above.
- **stacks**: agreed (3). Add the review band-to-tab stack (A5-01).
- **flexures**: agreed. Both are in the layer plane.
- **assembly_order**: matches BOM steps 1..14. `assembly` reports 176 objects placed, 0 in no step.

## What is good
- A2-01, the issue that took three attempts, is closed properly.
  - The designer found that the review's own `PSI_C` 45 fix stalled 14 drop rows, measured why, and shipped a lift-matched profile instead. That profile holds the full-lift gap at 8.1 along the entry arc while keeping the drops at 34.5 deg or more.
  - The assert now samples the whole arc. It is re-asserted at all three settings and written to the manifest.
- Modelling the tape is honest. It removes the 0.5 conservatism from the drops and makes the pass criterion physical (hood to tape 7.607 against a 7.5 candy).
- The gate is now a prismatic joint. Its open state is in every interference sweep, and it has positive stops at both ends with 0.000 rows and seated-detent rows at both notches.
- The designer's numbers re-ran exactly, the BOM fastener table matches the model, and every BOM claim has a row.
