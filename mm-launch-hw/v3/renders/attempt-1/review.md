# Review: M&M Launcher Turret v3 (min-hardware), attempt 1

Checks re-run: `CADCHECK PASS: 0 fail, 61 warn (0 untriaged, 61 accepted), 0 config warns` on `/tmp/v3r1/model.blend` (tools c2c282d, `alex-3d-skills-pin`). The result matches the designer's `renders/attempt-1/cadcheck.json`. Copy: `review/cadcheck.json`.
- Coverage (from the report): 25 printed STLs; 74 objects and 5453 pair-poses over 8 swept joints with 2.5 deg overtravel; 11 screws and 3 nuts at 16 poses; 8 service ops; 27 slide-outs; 24 assembly steps with 0 objects in no step; 50 insertions; 24 flexures; stability over 3456 poses; 15 cable routes.
- Not checked (quoted): "pilot/clearance hole diameters; wrench access to nuts; insertion: paths that are not one straight line, parts of the same step against each other, cables; stability: dynamic loads (recoil, pan acceleration), friction/sliding; cables: bend radius of a lead that is not modelled as a route, slack across joints, connector positions; not geometric: teardown step count, alignment-jig datums, aesthetics, BOM correctness".
- **Also not checked:** overlaps between two printed parts on the same body with no `allow`. Interference only tests pairs across a joint. That is how a 0.485 mm³ valve/adapter clash went unseen (v3-A1-01).
- `unbounded_allows` (5): motor x magnet, stud x tw_nut, flywheel x motor, nip_wheel x stud, nip_wheel x leaf. All are glued, threaded or preloaded pairs carried over from v2. Agreed.
- `cad printcheck stl --manifest`: PASS, 25 parts, 0 fail, 9 warn (`review/printcheck.json`). `cad slice --detect`: Bambu CLI unusable (known segfault), so no slicer run.
- `cad bom`: PASS, 5 rows, 0 disagree.
- Review rows: `review/review_rows.json`, giving `review/cadcheck_review.json` (`--only slide,sightlines --overlay-only`): 3 fail, explained below.
- Notes: `review/notes.md`. Renders: 2 of 12 used. `r01` had the camera on the section plane and was deleted. The other is `review/r02_sec_x42.7_beam_barb_in_release_slot.png`.

| Metric | Score | Anchor matched | One-line reason |
|---|---|---|---|
| Functionality | 8 | "Works. At most 2 major issues, each with a known fix under 1 hour of CAD and no reprint of a big part" | Every v2 functional row re-runs the same: drops 31/31 (flattest 34.5), entry arc 8.098 / 8.222 / 8.415, one candy per index. Two majors: the gate is no longer held open (a v2 regression, v3-A1-03), and lifting the machine by its top hangs it on three stages of cross-layer snaps in series (v3-A1-02). |
| Manufacturability | 8 | "Works. At most 2 major issues ... no reprint of a big part" | 0 fails in cadcheck and printcheck, all 25 parts fit the P1S, and BOM = model. Two snap joints can't seat as modelled (v3-A1-01: beam barb wider than its slot, valve key rib into the adapter). Every Z catch clearance is below one 0.2 layer (v3-A1-02). The fixes are on small parts (beam, adapter, hub gear). |
| Aesthetics | 8 | "Each failed item costs a point"; 9 needs every item true | One form language, and colour B still marks the candy path. Two items fail: the hero turntable's edge break is clamped to 0.39 against the declared 1.0 (outside ±0.5), and 2 adapter screw heads show on the deck top in iso, against the brief's "no visible screw heads" goal. |
| Hardware elegance | 7 | "Works, but ... one major that needs a large part reprinted" (same scale) | Counts are excellent: 14 metal (stretch ≤ 16 met), 4 specs, 25 printed. But 12 of the 24 flexures bend across layers at 73-86 % of the 15 MPa limit, against the brief's "beam lies in the layer plane". Catch clearances are 0.05-0.1 in Z, one hook group doesn't catch at all, and the hub joint can never be released. The proper fix (bayonets) reprints the crown, beam and valve. |

## Previous issues (v2 attempt-7 baseline)

| Issue | Status | New number |
|---|---|---|
| V2 A7-01: step 11a needed the pod at tilt 45 with the tilt servo unpowered | **FIXED** | The groove cap is gone (closed tunnels plus a printed bore roof), and the splice is made from below with no pose. `assembly.held_poses` `[]`. Service row `v3-A1 bus splice` uses no pose. Slide "splice pulls -Z" clears with min 1.0. |
| V2 A7-02: tilt and feeder leads in one tube over the splice; no home for the service length | **PARTIAL** | Fixed: separate routes landing 3.0 apart on the splice top (z 92, 8.0 under the z-100 roof); `cables` shows no `kinks` or `shared_runs`. Still open: BOM item 14 says "trim to route + 70 (later the service loop)" but doesn't say where the loop lies once the splice is pushed up. |
| V2 A6-02: launcher bundle/base hand-over off the pan axis | **PARTIAL** (carried, accepted warn) | v2-A2-02 reads 0.929 / 0.009 / 0.696 at pan -90 / 0 / 90 against max 1.0 (v2 A7: 0.916). That leaves 0.071 of margin, and the row still passes only because the sleeves overlap. |
| V2 A7-03: cap-removal row stopped under the pod; stale `why` text | **FIXED** (moot) | The cap is deleted. The v2-A6-02 `why` strings read z 63 / r 6.5. |

Functional baseline vs v2 A7 (no silent regression):

| Row | v2 A7 | v3 A1 |
|---|---|---|
| Drops | 31/31 at every pose, flattest 34.5 @ tilt 46 | same |
| Swept entry arc (min / home / max stop) | 8.098 / 8.222 / 8.415 | same |
| Index +60 / -60, column at drift 0..15 | 1 / 1 window, never open | same |
| Payload min pair blocked / max flat fits | margin 0.06 / 0.14 | same |
| Stability (worst tip) | 31.2 deg | **29.6 deg** (jar stack +36, `JAR_LIFT`) |
| Gate held closed **and open** | detent clip at both ends | **closed only** (v3-A1-03) |
| Valve-to-adapter, crown-to-beam, beam-to-posts, hub-to-turntable | screws (3 / 4 / 7 / 3) | cross-layer snaps (v3-A1-02) |

## Measurements

| Item | Value | Source |
|---|---|---|
| Metal pieces / specs / printed | 11 screws + 3 nuts = **14**; **4** specs (M3 pan x 10 ×6, M3 cap x 6 ×2, M3 cap x 20 ×2, M3 hex x 16 ×1); **25** PRT | `cad rows manifest.json FST_`; `cad q list PRT_*`; `stl/` = 25 STLs |
| Brief targets | metal ≤ 24 (stretch 16): met, stretch met. Specs ≤ 4: met (stretch 3 not met). Printed ≤ 26: met (stretch 22 not met). | build `FASTENERS` / `PARTS` lines |
| Full check | 0 F / 61 W, 0 untriaged | `review/cadcheck.json` |
| Printcheck | 0 F / 9 W, 25 parts | `review/printcheck.json` |
| Beam x turntable **at rest** | **-0.531 mm³** at (42.9, 19.5, 233.8) and (-90.9, -22.5, 232.1) | `cad q dist PRT_beam PRT_turntable`; `interference.allowed_max` 0.53 under the 8.5 allow |
| Beam barb vs release slot | `inside 42.7,16.55,233.5` and `42.7,19.45,233.5` → [turntable, beam]; `42.7,19.35` → beam only. The barb is 3.0 wide (y 16.5..19.5); the slot is 2.8 (`BEAM_HOOK.slot_hw` 1.4) | `cad q inside`; `r02` |
| Valve x adapter at rest (same body, no allow) | **-0.485 mm³** at (-8.4, 25.6, 335.5) / (-5.4, 26.9, 336.0); `inside -7,26.0,335.7` → [adapter, valve]; at z 335.2 → valve only | `cad q dist`, `cad q inside` |
| Snap holds (review rows) | crown +Z blocked 0.15 by beam; hub gear -Z blocked 0.15 by turntable; valve -Z blocked 0.2 by adapter; **beam +Z not tested** (`overlapping_at_rest`, slides 3 mm) | `review/cadcheck_review.json` |
| Z catch clearances | beam 0.05 (`hook_slot_cuts` zc + 0.05), hub 0.05 (`HUB_FINGER` 98.55/98.5), crown 0.1, valve 0.1. All are under one 0.2 layer | params; review rows above |
| Cross-layer flexures | hub ×3 12.6, beam ×4 9.2 / **12.9** release, crown ×3 10.3 / **12.3** release, valve ×2 11.0 (limit 15) | `flexures` rows |
| Lift by the jar (hand calc) | valve fingers carry about 32 N: per finger 2.7 MPa axial + 9.6 bending from the catch moment ≈ **12.3 MPa static across layers**. Crown hooks: about 11.6 MPa. Hub fingers carry the base, about 17 N | `review/notes.md` |
| Gate from the open stop, -X | **not blocked over 10 mm**, min 0.35 | review row `R1 v3-A1-03` (FAIL) |
| Journal plate on its 3 crush-rib pegs, +X | blocked 0.4 by `PRT_turntable` at tilt 0 and 45 (captive) | review rows `R1 v3-A1-04` (pass) |
| Beam-hook tool lines | from the front / rear opening: reach the barb at tilt 0; the right-front line at tilt 45 hits `PRT_nacelle` at 9.55 | review `sightlines` |
| Crown +X hook tool line (30 deg up from the front) | reaches the hook at tilt 0 and 45 | review `sightlines` |
| Hub stack | gear top z 85, deck underside 86.0 (1.0 float); hub gear x turntable 0.05; the gear rises onto the deck when the turret is lifted | `cad q ray 25,0,85.01 0,0,1`, `cad q dist` |
| Rest gaps that are fine | cover x journal plate 0.2, nip cover x body 0.141, gate x valve 0.1, horn adapter x plate 0.169, pinion x feed floor 0.3 | `cad q dist` |

## Issues (ranked)

**v3-A1-01 (major, manufacturability): two snap joints can't seat as modelled.**
- **Beam hooks.** Each barb is 3.0 wide (`BEAM_HOOK.w`) and catches inside a release slot only 2.8 wide (`slot_hw` 1.4). Each barb corner sits 0.1 inside the post wall: `cad q inside 42.7,19.45,233.5` gives [PRT_turntable, PRT_beam], and the total at rest is -0.531 mm³ (`interference.allowed_max` 0.53, hidden under the 8.5 mm³ "ride" allow). In print, the barb rests on the slot jambs instead of clicking under the ledge, so the hook stays deflected 0.4 (7.4 MPa sustained, across layers). There is no positive catch, and PLA creep makes it worse. The review's captive row can't test it: the beam overlaps the turntable at rest and slides 3 mm free. `r02` shows the barb filling the slot window edge to edge.
- **Valve key rib.** The rib's top 0.5 runs into the jar adapter above the end of the key groove (-0.485 mm³, same body, so no check sees it). The adapter would stop up to 0.5 high. The valve barbs have only 0.1 of Z margin over the spout groove's lower wall, so they would then sit on the spout OD below the groove: no latch, and a sustained 11 MPa across layers.
- Fix (under 1 h; reprint the beam (93.8 g) and the jar adapter (8 g)):
  1. `BEAM_HOOK.w` 3.0 → 2.2, or `slot_hw` 1.4 → 1.8, so there is ≥ 0.3 a side.
  2. Run the adapter's key groove 1.0 past the rib top, or stop the rib 0.6 under the spout shoulder.
  3. Add a `distances` row, min 0.05 at rest, for every snap pair on one body (beam/turntable, valve/adapter, crown/beam, hub gear/turntable, encoder cap/nacelle: 0.18 mm³ at rest now).
  4. Adopt the four "hooks hold" captive rows from `review/review_rows.json`, with the `allow` bounded to 0 at rest.

**v3-A1-02 (major, hardware elegance / functionality): the vertical stack is held by cross-layer snap fingers with sub-layer catches, and nothing shows it survives being lifted by the top.**
- 12 of the 24 flexure rows bend across layers (hub ×3, beam ×4, crown ×3, valve ×2), at 73-86 % of the 15 MPa interlayer limit. The brief's toolbox asks for "the beam lies in the layer plane". The beam (12.9) and crown (12.3) hooks are the ones bent at every tilt or feeder servo swap.
- Every Z catch clearance is below one layer: beam 0.05, hub 0.05, crown 0.1 and valve 0.1. The review rows measure the crown, hub and valve stops at 0.15, 0.15 and 0.2. A one-layer slicer rounding (±0.1 per face) turns that into interference, and a hook that can't drop under its ledge then holds a sustained bending preload, which the brief forbids for PLA.
- Lifting the machine by the jar, its natural handle, puts the whole machine on three cross-layer stages in series: band → adapter → **2 valve fingers** → valve lugs → crown → **3 crown hooks** → beam → beam hooks (not seated, v3-A1-01) → turntable → **3 hub fingers** → base. By hand calculation the valve fingers carry about 32 N, which is about 12.3 MPa across layers. A 1.5 g jolt then reaches about 19 MPa, past the limit.
- v2 had 3 / 4 / 7 / 3 screws at these joints. The BOM gives no handling rule, and there is no `stacks` or `distances` row showing any of these joints carries a load, which the brief asks for ("load paths ... under a 750 g jar still need evidence").
- Evidence: `flexures` rows; params `BEAM_HOOK`, `HUB_FINGER`, `CROWN_HOOK`, `VALVE_SNAP`; review captive rows; hand calculation in `review/notes.md`.
- Fix, in this order:
  1. Take the valve fingers out of the jar load path. Either put the bayonet lugs on the adapter (the band clamps it to the glass), or merge `jar_adapter` into `jar_valve` (the joint is already "permanent"; print lid-down) and solve the gate insertion with a flexing stop lug.
  2. Turn crown-to-beam and hub-to-turntable into 3-lug bayonets (about 20 deg twist, lugs bearing in shear), each locked by one in-plane detent arm in a flat flange. The brief lists exactly these two interfaces under toolbox #2.
  3. Wherever a vertical hook stays, use a catch clearance of ≥ 0.3 (1.5 layers) and a 5-10 deg retaining undercut on the catch face.
  4. Add a `stacks` or `distances` pull-out row per joint at 3 × the hanging weight.
  5. Until then, add "lift by the base only" to the BOM, with two finger recesses in the shell walls.

**v3-A1-03 (major, functionality): the gate is held closed but no longer held open, a regression from v2.**
- In v2 A7 the detent clip "clicks into a notch at both ends, so the gate holds closed and open". In v3, only the closed notch exists. The open position is held by the 52.35 positive stop and friction. The designer's own reasoning: the cheek face spans x -15..15 and the travel is 52.
- Review row `R1 v3-A1-03 gate held open`: from `PIV_gate` 52 the blade slides 10 mm back -X with nothing stopping it (min 0.35). Pan reversals and flywheel vibration can walk the 9 g blade back over the bore edge, where it pinches candies or starves the feed.
- The `allow PRT_jar_gate x PRT_jar_valve` `why` still says "between its closed and open notches".
- Fix (no new part; reprint the gate, 8.9 g, and the adapter, 8 g): put a 0.3 bump on the stop lug's -X face and a matching R0.6 x 0.35 dimple in the spout shoulder at the 52.35 stop. Alternatively, put a second in-plane finger on the blade's -X end acting on the adapter's spout notch. Add the review row to checks.json as a pass, blocked within 1.0.

**v3-A1-04 (minor, hardware elegance): the hub-to-turntable joint can never be released.**
- The 3 hub fingers' barbs sit inside the turntable socket at z 98.5, and `why` says "permanent joint, never released". No tool can reach them.
- Taking off the turntable (341 g, 6.5 h, the posts integral) means breaking the hub gear's fingers. That happens if the thrust ring wears, a tunnel lead has to be re-pulled, or the hub gear's teeth strip. That misses the brief's "release without breaking" aim for the main structural joint.
- Fix: the bayonet in v3-A1-02 fix 2 (twist off from below with the floor off), or 3 release windows Ø4 through the turntable cone over the barbs.

**v3-A1-05 (minor, manufacturability / service): multi-hook releases have no tool rows, and one tool line is blocked at tilt 45.**
- The tilt servo swap releases 4 beam hooks, 2 per post 39 apart, and they must be held released together. The feeder servo swap releases 3 crown hooks from under the beam.
- Review `sightlines`: lines from the front and rear openings reach every barb at tilt 0, and the crown +X hook at tilt 0 and 45. The right-front beam-hook line at tilt 45 hits `PRT_nacelle` at 9.55.
- The BOM gives no pose for the hook release, and no row checks it.
- Fix:
  1. Add the 3 sightline rows from `review/review_rows.json`.
  2. State "tilt 0" in the tilt servo swap.
  3. Add `stl/tools/hook_fork.stl`: a 2-prong flat release fork with prongs 39 apart, 2.4 x 0.8, so both hooks on a post release at once.

**v3-A1-06 (minor, aesthetics): visible screw heads and the hero part's edge break.**
- The 2 `FST_adapter` heads are counterbored flush, but they show as two dots on the deck top in `iso.png`. The brief's v3 aesthetic goal is "no visible screw heads".
- `PRT_turntable`'s edge break is clamped to about 0.39 against the declared EB 1.0, outside ±0.5. `launcher_cover` is at 0.49 (`parts` warns, accepted as cosmetic). The turntable is in every hero view.
- Fix:
  1. Add a 0.6 printed press-in cap per counterbore. That is +2 tiny parts, or 1 if a strip covers both, and the turntable part count is unchanged. Alternatively, move the 2 screws under the battery-side lip.
  2. Bevel the turntable drum before the post and hub cuts, as the V2A6-T2 note in the warn says.

**v3-A1-07 (minor, functionality / cables): the bus service loop still has no stated home (carries V2 A7-02).**
- BOM item 14 trims the tilt and feeder leads to "route + 70 (solder length, later the service loop)", and step 11a pushes the splice up the bore. About 2 x 70 mm of lead then has to fold somewhere between the tunnels and the R14 bore, and the splice is 1.0 from the hub-gear bore.
- Fix: name the place, for example the left-post channel for the feeder lead and the right channel for the tilt lead, and show it in one section at the tunnel mouths.

**v3-A1-08 (minor, check config / housekeeping): stale or missing rows.**
- The `allow PRT_jar_gate x PRT_jar_valve` `why` mentions an open notch that doesn't exist.
- The servo controller's removal ("lifts once its 2 tongues are pressed") has no slide row; the BOM says so itself.
- `stl/tools/tilt45_prop.stl` is a v2 A7 leftover (Oct 25) that v3 no longer uses.
- The feeder pinion has no centre screw: the horn hangs on spline friction and can drop 0.3 onto the feed floor (pinion x beam 0.3). That's acceptable, but the BOM should say so.
- Fix:
  1. Correct the `why`.
  2. Add a controller +Z slide row with the tongues on `flex`.
  3. Delete the prop STL.
  4. Add one BOM line on the pinion.

## Check-config audit
- **allow** (19):
  - **Disputed:** `PRT_beam x PRT_turntable` (max 8.5). Its `why` is "barbs ride the ledges", but at rest it covers a 0.53 mm³ barb/slot clash (v3-A1-01). Bound it to 0 at rest; a `fits` rule or a separate ride row should cover the ride.
  - **Disputed `why`:** `PRT_jar_gate x PRT_jar_valve` (stale open notch).
  - The others are agreed. The crush ribs (servo x crown 9.62, pan mount x shell 1.87, body x plate 0.95) and the ride allows (floor x shell 50.46, crown x beam 10.93 during the slide, 0 at rest) are measured and bounded. Encoder cap x nacelle reads 0.18 mm³ at rest where the `why` says 0: minor.
- **Missing check:** the valve/adapter pair (same body, no allow) overlaps 0.485 mm³ unseen. Add a `distances` row per same-body snap pair (v3-A1-01).
- **fits** (30): agreed.
- **accepted_warns** (59 entries, 61 warns):
  - **Disputed:** the 12 vertical-flexure accepts for the serviced beam and crown hooks, and for the valve fingers in the lift path (v3-A1-02). The 15 MPa limit has no margin for repeated release, and the brief asks for in-plane beams.
  - The rest are agreed: tooth tips, designed springs, dovetail edges, ledges under 3.0, and the four hood "not proven" cells, re-measured with `cad q sweep` ≥ 0.158.
- **drop_tests**: agreed. Both hood stops x tilt -3..46, unchanged from v2.
- **index_tests / service / slide_out vs the BOM:**
  - Every motion claim has a row: index ±60 and the column at drift 0..15; 8 service ops; 27 slides covering refill, leaf, tape, encoder, tilt, feeder and pan servo, floor, splice, MotorGo, buck and battery.
  - **Added and run by the review:**
    - captive "hooks hold" rows: crown, hub and valve pass; the beam fails on overlap-at-rest (v3-A1-01);
    - journal plate captive: pass, 0.4;
    - "gate held open": **fail** (v3-A1-03);
    - 3 tool sightlines: one ray fails at tilt 45 (v3-A1-05).
  - Still without a row: the servo controller removal.
- **assembly_order**: matches BOM steps 1..16 (24 labels). `assembly.unordered_solids_assumed_present` `[]`, `held_poses` `[]`. Step 7's `pose` `PIV_tilt` 20 is held by hand before the servo is in. Agreed.
- **Joint ranges / poses**: the review sightline at tilt -3 is outside the 0..45 range (`poses_past_limits`). That's intended as an overtravel probe, and it passes.

## What is good
- **Hardware cut from 107 to 14 metal pieces, 18 to 4 specs, and 36 to 25 printed parts.** That meets the metal stretch target. Every remaining screw is a motor mount, servo centre screw or flywheel clamp, or is justified in the joint table (the adapter's hanging battery load, and the nip stud's preload and 0.4-turn pitch argument).
- **No functional regression in the measured rows.** Drops, the swept entry arc, index, payload, cables and the magnet stack all re-run identically to v2 A7.
- **v2 A7-01 is fixed by design, not by procedure.** The groove cap and its 6 screws became closed tunnels and a printed bore roof. The splice is made and serviced from below, with no pose.
- **The tilt servo drops in from the top.** That removes the post cover. The journal-plate fork takes the key, and the review confirms the journal plate is captive at 0.4.
- **0 printcheck fails on 25 parts.** The designer fixed real v2 support problems: the jar_valve lugs, the base_shell anchor and the post_R top.
- **Strong evidence discipline.** Every new joint has a flexures, slide or service row, bounded allows, and measured `why`s. The designer flagged the joint-table items that were infeasible (open gate notch, valve bayonet, lobe roof) rather than hiding them.
