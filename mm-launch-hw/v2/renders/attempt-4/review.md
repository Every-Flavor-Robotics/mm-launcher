# Review: M&M Launcher Turret v2, attempt 4

Checks re-run: `CADCHECK PASS: 0 fail, 43 warn (0 untriaged, 40 accepted)` on `/tmp/rv4/model.blend` (tools a20a4d7, the designer's pin, 150 s). Copy: `review/cadcheck.json`. Every check section matches the designer's `renders/attempt-4/cadcheck.json` exactly; only `runtime_s` differs.
- Coverage: parts 36. Interference/clearance: 175 objects in all four collections, 4727 pair-poses, 7 joints with 2.5 deg overtravel. Fasteners: 103 screws + 4 nuts at 15 poses / 29 steps. Service 8. Drop 4. Index 6. Slide 12. Payload 4. Sightlines 3. Assembly 29 steps with 0 parts in no step. Stacks 3. Flexures 2. Stability 1728 poses. Cables 14/14 with lead length. Distances: 41 rows (62 row-poses), not listed in `coverage`.
- Not checked (quoted): "pilot/clearance hole diameters; wrench access to nuts", "dynamic loads (recoil, pan acceleration), friction/sliding", "cables: bend radius, slack across joints, connector positions", "teardown step count, alignment-jig datums, aesthetics, BOM correctness".
- Review rows: `review/review_rows.json` -> `review/cadcheck_review.json` (`--only distances --overlay-only`): **6 fail** (A2-01, the nip entry arc at full leaf lift).
- Probes, all in `/tmp/rv4probe/`:
  - `gap_profile.py`: radial land-to-hood gap at psi 0..110, at 6 poses.
  - `psi_c.py`: the same profile from params, run through `cad py`, for sizing the fix.
  - `gate_move.py`: the gate moved 0..52.35.
  - `rot_clear.py`: everything within 3 mm of the flywheel.
- Log: `review/notes.md`.

| Metric | Score | Anchor matched | One-line reason |
|---|---|---|---|
| Functionality | 8 | "Works. At most 2 major issues, each with a known fix under 1 hour of CAD and no reprint of a big part" | One major is left (A2-01). The full-lift gap now passes 8.0 at BDC, but the hood pivots near the candy's entry. Along psi 60..85 the gap at full lift is still 7.50..7.95, so the thickest candy is squeezed rigidly at every setting, and a nominal candy drives the leaf solid at the min stop. The fix is one param (the hood is 10 g). Everything else has a passing row. |
| Manufacturability | 9 | "Minor polish only ... cadcheck has 0 fails and every warn is explained" | 0 fastener fails. Every screw is reachable at its step: the 104 mm hinge bit is in the tool list, the worst straight reach is 58. Nut engagement is the full 2.4 nut, and plastic engagement is 4.0 or more. No supports, every part fits the P1S. The BOM fastener counts match the manifest spec by spec, and the BOM steps match `assembly_order`. |
| Aesthetics | 9 | "9 needs every item true" (one minor detail left) | One EB 1.0 / CR 6 set (the 0.6 blade and 0.4 detent plate have a measured reason). Colour B traces the candy path. No PCB, wire or motor can shows in iso or iso_front_left. The detent clip now has a rounded end and a counterbored head. What's left: the clip tab's band-relief step reads as a notch in close-up, and the pan head still stands 1.4 proud (A4-01). |

## Previous issues

| Issue | Status | New number |
|---|---|---|
| A2-01 nip leaf runs out of travel before the thickest candy passes | **PARTIAL** | Fixed at BDC: rays 8.282 / 8.593 / 8.782 / 9.124 at hood +0.327 / 0 / -0.2 / -0.558, all at least 8.0. Not fixed on the entry arc. At full lift the gap is **7.50 at psi 80, 7.72 at psi 70, 7.94 at psi 60** (min stop), 7.67 at psi 80 (hood 0) and 7.95 at psi 80 (max stop). All of these are below 8.0 (`review/cadcheck_review.json`). The cadcheck nearest gap also reads 6.967 against the 8.282 ray. |
| A1-03 pocket admits an edge-on pair | FIXED | Ø13.75 (4 rays read 13.75). `payload_fit`: the MIN pair 12.5 x 6.3 is blocked with margin 0.06 / 0.06, the nominal pair with 0.34, and the flat 13.5 x 7.5 fits with 0.14. A 4-pocket coupon (13.6 / 13.75 / 13.9 / 14.1) is in `stl/tools/` with the calipering procedure in the BOM. |
| A2-02 encoder lead missing, pan bus lead short | FIXED | BOM item 15 is a one-piece twisted 5-wire lead of at least 550. `CAB_encoder` path 84.1 is within its 114.8 budget, written by `finish.py`. `CAB_bus_pan` is 290.5 / 350. |
| A3-01 detent clip form language, non-stock screw | FIXED | Tab EB 1.0, plate EB 0.4 (0.6 would meet in a knife edge on the 1.2 plate; agreed), R3 plan end. Stock M3 x 10 pan self-tap in a Ø6.6 x 1.0 counterbore: engagement 4.0, tip 2.652 from the gate and 1.142 from the spout (`review/r02_gate_detent_closeup.png`). |
| A3-02 BOM lists the wrong stud | FIXED | The BOM, step 6c and the manifest `bom_item` all read M3 x 16 hex ISO 4017 AF 5.5 x 2.0. The hex-head fit is shown by section only (cadlib has no hex spec; tool limit). |
| A3-03 check-config gaps | FIXED | Base-floor `slide_out` row: not blocked. The full-lift rows are at 8.0. The detent open notch still has no row (no prismatic joint type). The re-run probe reads 0.10 at gate +52, 0.00 at the +52.35 stop, and -0.43 mm³ riding the blade at +13..39. |

## Measurements

| Item | Value | Source |
|---|---|---|
| Full check | 0 F / 43 W, 0 untriaged, stale [], identical to the designer's | `review/cadcheck.json` |
| Nip rest gap, x 21, psi 0..80 (the hood is concentric up to PSI_C 78) | 6.17..6.34 at the min stop; 6.48..6.51 at home; 6.80..7.03 at the max stop | `/tmp/rv4probe/gap_profile.py` |
| Nip gap at full lift (-2.19), x 21, psi 0 / 40 / 60 / 70 / 80 / 90 | min stop 8.16 / 8.23 / 7.93 / 7.71 / **7.48** / 8.03; home - / 8.53 / 8.18 / 7.92 / **7.65** / 8.16; max - / 9.05 / 8.61 / 8.29 / **7.94** / 8.37 | same probe, plus review rows (7.94 / 7.72 / 7.50 at the min stop) |
| Gap opened by the full lift at psi 0 / 60 / 80 (min stop) | 1.97 / 1.70 / 1.14 (the hinge sits at PSI_TOP 112) | derived from the two rows above |
| Analytic full-lift minimum (params, `cad py`) vs PSI_C | 78: 7.49 at psi 80; 60: 7.89; 50: 8.06; **45: 8.14 at psi 50** (8.89 at the max stop) | `/tmp/rv4probe/psi_c.py` |
| cadcheck nearest hood-to-wheel gap at full lift | 6.967 / 7.121 / 7.216 / 7.385 (to the R36 flange at x 14.1, psi about 99). The ray-vs-nearest warn does not fire (its threshold is near + 2.09) | `checks.distances` `nearest_mm` |
| Leaf-solid stop / home along the stud | 4.288 / 6.500 | `checks.distances` |
| Hood to body at the static max with the leaf solid | 0.54 | `checks.distances` |
| Drop, 7.0 and 7.5 payloads, both stops x tilt -3..46 | 31/31 hit, flattest 33.3 (7.0) / 34.2 (7.5) | `checks.drop` |
| Index ±60 | 1 window each ([50,60], [-60,-50]); column windows 0 at jar drift 0/5/10/15 | `checks.index` |
| Gate detent vs gate at 0 / 13..39 / 51 / 52 / 52.35 | 0.10 / -0.43 mm³ / -0.20 mm³ / 0.10 / 0.00 (adapter stop) | `/tmp/rv4probe/gate_move.py` |
| Stationary parts nearest the flywheel | `FST_motor_*` and `FST_nacelle_*` 1.6, body 1.594, cover 2.0 (brief: at least 1.5) | `/tmp/rv4probe/rot_clear.py` |
| Flexures | leaf 35.5 MPa at solid, 2.2 deg; detent 16.1 MPa, 0.0 deg | `checks.flexures` |
| Cables | encoder 84.1 / 114.8, bundle 265.4 / 350, base 164.8 / 250, bus_pan 290.5 / 350 | `checks.cables` |
| Stability | worst 31.2 deg (1728 poses); cg_grid 29.9 at tilt 46 | `checks.stability` |
| Fastener reach | worst straight 58 (`FST_feedmount_0`), hinge 94 (bench, 104 bit listed); detent 16 | `checks.fasteners` |

## Issues (ranked)

**A2-01 (major, functionality): the full leaf lift opens the nip at BDC but not on the entry arc, where the candy is squeezed first.**
- The hood is concentric with the wheel from BDC to `PSI_C` 78 deg. It pivots about `HINGE`, which is at `PSI_TOP` 112, near the entry. So the 2.19 deg leaf lift opens BDC by 1.97 but psi 80 by only 1.14.
- A candy descending on the rear tape is gripped from about psi 85 down. At full lift the entry-arc gap is **7.50 / 7.72 / 7.94** at psi 80 / 70 / 60 at the min stop, 7.67 at psi 80 at home, and 7.95 at psi 80 at the max stop.
- A declared-max 7.5 candy on 0.5 tape (8.0) is therefore squeezed rigidly, by 0.05-0.50 with the leaf solid, at every thumbwheel setting.
- A nominal 7.0 candy (7.5) needs the leaf's entire travel at psi 80 at the min stop, and 87 % of it at home. So most shots cycle the leaf at about 32-35.5 MPa, not the 26.9 MPa the BOM quotes. That is a fatigue risk for a PLA spring.
- Two things hid it:
  - `params.gap_bdc()` samples only psi -2..+2, and the `NIP_PASS` assert and the four full-lift rows sit at BDC (ray y 34).
  - The cadcheck nearest gap (6.967 against the 8.282 ray) is to the flange, below the warn threshold.
- Evidence: `review/cadcheck_review.json` (6 fails); `/tmp/rv4probe/gap_profile.py`; `review/r01_nip_x21_minstop_fulllift_psi80_lentil.png` (the psi 80 candy pinched near the hinge).
- Fix:
  1. Start the hood's entry taper at the jack line: `PSI_C` 78 -> 45. Analytically the full-lift minimum at the min stop rises from 7.49 to **8.14** (at psi 50), and to 8.89 at the max stop. The rest gap over psi 0..45 stays 6.2..7.0, so the grip arc is about 27 mm at R35.
  2. Make the assert sample psi 0..PSI_TOP, not just BDC: `min(gap at full lift over psi) >= NIP_PASS + 0.1`.
  3. Adopt `review/review_rows.json` (psi 60 / 70 / 80 rays at all three hood settings, min 8.0). Add a psi 50 row.
  4. Rebuild, then re-run the drop rows. The G_IN funnel now starts at psi 45, so the flattest slide must stay at least 33.
  5. Re-run the leaf `flexures` row, and quote the stress at the lift a nominal candy actually needs (about 0.66 of travel at the min stop, about 27 MPa).

**A4-01 (minor, aesthetics): the detent clip tab still reads unfinished in close-up.**
- The band relief (R37.25 above z 300) leaves a square step in the tab's top corner.
- The pan head stands 1.4 proud of the tab back face: the `FST_detent_0` bbox reaches y 39.9 against the 38.5 face, with only 1.0 of the head sunk.
- Neither shows at hero scale, but both show in `review/r02_gate_detent_closeup.png`.
- Fix:
  - Run the relief as a full-width 45 deg x 1.5 chamfer across the tab top, so it reads as a deliberate shape instead of a notch.
  - Optionally use an M3 x 10 wafer-head (ISO 7380-style, about 1.65 head) self-tap in the same Ø6.6 x 1.0 counterbore. It stands about 0.65 proud with the same tip position.

**A4-02 (minor, documentation): BOM and manifest numbers that will drift.**
- The BOM's leaf numbers ("thickest candy at the min stop 30.4 MPa, nominal 26.9") and "NIP_PASS ... asserted" rest on the BDC-only helper (A2-01).
- `PRT_nip_cover`'s manifest orient string still says "finger slot 22 x 7.5". The BOM section 8 admits this.
- Fix: after the A2-01 change, regenerate the leaf numbers from the entry-arc minimum, and take the slot text from `FINGER_SLOT` in `launcher.py`.

## Check-config audit
- **allow** (10) and **fits** (30): agreed. `post_R x journal_plate` is still a contact fit, and the 0.156 journal audit row stands (tool limit, unchanged).
- **joint limits**:
  - PIV_nip_lift -2.190: agreed. The leaf goes solid at 4.288 along the stud, and the home reading is 6.500.
  - PIV_hood -0.558..+0.327: agreed. The nip stop and the sleeve both read 0.000.
  - Tilt 0..45 with lugs at +46: agreed.
- **accepted_warns** (40 keys / 43 warns): agreed.
  - The 9 ray-vs-nearest accepts are correct for the rays they name.
  - Note: the same rule is silent on the four full-lift nip rows (8.28 vs 6.97 nearest), which is how A2-01's entry arc stayed hidden.
- **distances**: **disputed (incomplete)**. The full-lift rows ("v2-A3-A2-01 bare gap at FULL leaf lift ... min 8.0") measure only at BDC. Add the review psi 60 / 70 / 80 rows.
- **params assert**: **disputed**. `HOOD_GAP_LIFT = gap_bdc(...)` samples psi -2..+2. The pass rule must take the minimum over the gripped arc.
- **drop_tests**: agreed. Both stops x tilt -3..46 and both payload sizes are covered. `home_only_ok` for nip_lift is agreed.
- **index_tests**: agreed. They match the BOM's "+60 then 0, -60 then 0" and the 0 / 60 / 0 / -60 / 0 column sequence at drift 0..15.
- **service / slide_out**: every BOM motion or service claim against its row (A2-F2):
  - leaf, tape/flywheel and encoder at tilt 45: match;
  - tilt servo, no pose, slide 60: match;
  - feeder servo, service + slide 60 + lobe-cover slide: match;
  - base floor, service + slide -Z 40: match (new);
  - refill: jar at 30 lifts +Z 60 and the gate slides +X 52, both match. The detent open notch has no row (tool limit; probe 0.10 at +52);
  - battery: slide +X 120, min 1.60: match;
  - pod lift-out at tilt 20, +Z 150, min 0.2: match;
  - set the nip gap: sightlines 3/3 x 3 poses plus distances: match.
  No missing entry needed adding. The one motion claim that fails is the jam/pass claim (A2-01), which is a `distances` row.
- **flexures**: agreed (in plane). The leaf's quoted operating stress is disputed (A2-01).
- **stacks**: agreed. The magnet centring reaches its 0.30 limit exactly (accepted in A2 and A3).
- **assembly_order**: matches BOM steps 1..14, and `step_of` places all 175 objects.

## What is good
- The designer's numbers re-ran exactly, down to the warn set. All 40 accepts carry measured reasons, and there are no stale accepts.
- The BDC side of A2-01 is done properly:
  - the leaf travel is 2.2, bounded by a modelled solid stack (4.288);
  - the hood keeps 0.54 to the body with the leaf solid;
  - the thumbwheel stays reachable through the slot at full lift (sightlines 3/3);
  - the fork-to-nut clash was found and fixed (1.289).
- The pocket is balanced between blocking a pair and passing a flat candy, with real `payload_fit` margins. The printable coupon plus caliper procedure turns the last uncertainty into a 30-minute bench test.
- The gate detent works at both ends (0.10 / 0.10), has a positive open stop, and uses a stock counterbored screw that keeps 2.65 to the blade over the whole travel.
- The encoder lead now has an honest length budget written by the build, so it can't drift from the routes.
- Every BOM service and motion claim has a matching row at the stated pose, and every slide is unblocked.
