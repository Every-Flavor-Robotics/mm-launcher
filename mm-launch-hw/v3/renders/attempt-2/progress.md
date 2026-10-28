tools: 64c5947
planner baseline | no model change; A1 model.blend re-checked under tools 64c5947 (/tmp/v3p2/baseline.json) | cadcheck 0F/36W (--only insertion,assembly,flexures,interference; 11 untriaged: 10 new same-step insertion warns + nip clearance; 5 accepted_warns now match nothing: the 3 hood and the disc x valve 'not proven' cells are proven by the new turning test) | 11 screws, 25 parts

## Plan
Principle for A2: **rigid lugs or hooks carry every load; in-plane detents only stop the twist or slide.** No SNAP-V finger stays in any load path. A1 had 12 of these. Joints that carry the lift-by-jar chain (jar -> valve -> crown -> beam -> turntable -> base) become bayonets or slide-locks. Each gets a `calcs` row at 3x the hanging weight, limits from mat() and z_eff() with declared walls/infill. Per-snap strain goes against mat('PLA','snap_strain'). Note E is 2200 in cadmat, not the 3500 used in A1's params.
Targets: metal 14 -> 14 or fewer (adapter screw heads hidden; drop to 1 screw if the +X lip works), specs 4, printed 25 -> 24 (thrust ring merged into the turntable).
Items, in order (one build agent each):
1 base: hide the FST_adapter heads under the R108 turntable footprint (corners r <= 104.9), +X lip if needed; controller +Z slide row with tongues on flex; step 12/13 insertion config; delete stl/tools/tilt45_prop.stl.
2 pan_stage hub: J-bayonet between hub gear and turntable (3 lugs, 20 deg, seat 1.5, float 2.0), which removes the 3 SNAP-V fingers and 3 dogs; thrust ring merged into the turntable; drum edge break >= 0.5; home for the bus service loop plus a section.
3 pan_stage beam: slide-lock (drop at x+4, slide -X 4, 4 rigid T-hooks under bridged post ledges, 1 SNAP-IP finger detent), which removes the 4 SNAP-V hooks; fallback is 2 in-plane post-top latches with calcs.
4 feeder crown: 3-lug bayonet into the beam (20 deg, lock sense = jar unlock sense, 45 deg bearing faces, 1 SNAP-IP detent), which removes the 3 SNAP-V crown hooks.
5 jar group: inner bayonet from adapter to valve (2 spout lugs R28.8 into cheek L-grooves, 12 deg, 1 SNAP-IP arc detent for torque only), which removes the 2 SNAP-V cheek fingers and the key-rib clash; gate open detent (stop lug on an in-plane blade finger, bump into a dimple in the +X notch wall); split step 14.
6 finish: checks.json housekeeping, new-tool insertion warns (encoder cap, nip cover, wheel cover, M&M fill poured), stale accepts, same-body distances rows, review rows, BOM/DESIGN_LOG joint table, renders, full check.
Detail: the work[] items in the planner's StructuredOutput (copied to DESIGN_LOG by item 6).

## Tool issues
- (planner) none blocking. The insertion check now tests parts within one step: A1's step 14 (jar + band + adapter + fill + valve + gate in one step) and steps 6b/6e/6g/12/13 warn under 64c5947 with no geometry change.

## Attempt 2 (hotfix: v3-A1-01 + v3-A1-03 only; the bayonet plan above is not started)
- 04:58 build 1: BEAM_HOOK w 3.0 -> 2.2; spout key groove to cheek top + 1.0 (VALVE_KEY_GROOVE_OVER); gate open detent (GATE_OPEN_DETENT: SNAP-IP finger under the stop lug's +Y 1.5, R0.6 bump 0.3 into the +X notch wall, R0.65 dimple slotted 52..52.35; closed through-notch widened to y 4.0). `cad q dist`: beam x turntable 0.0 (A1 -0.531), valve x adapter 0.028 (A1 -0.485); `cad q sweep` gate x adapter 49..53: ride max 0.084 mm3 at 51.25, 0.05 at 52 / 52.25, stop 52.35.
- 04:59 checks.json: allow beam x turntable max 8.5 -> 0 (lift ride moved to that slide's flex); new allow gate x adapter 0.02; flex adapter 0.5 on the two gate-opening rows; review rows 'gate held open' and 'beam hooks hold'; 2 same-body distances rays; flexures row 'A2 gate open-detent finger' 10.2 MPa; 2 accepted flex warns. `--only slide,distances,flexures`: 0 F / 14 W, 0 untriaged. Held open blocked at 0.2 by PRT_jar_adapter; hooks hold blocked at 0.1; open stop blocked 52.5; barb ray 0.3; key rib ray 1.0.
- 05:01 build 2: the post-top hook slot width decoupled from the hook width (BEAM_HOOK post_slot_w 3.0, the A1 value), so the turntable doesn't change. STL geometry diff vs A1: beam, jar_adapter and jar_gate only. Full check started.
- 05:04 the full check found 2 new untriaged warns, both triaged: step 9 beam `insert_ok` (snap; seen now that the allow is 0) and the gate wall-sample accept, 8 -> 18 samples (min 1.49). `--only parts,insertion`: 0 F, 10 untriaged (baseline).
- 05:07 final full check: **0 fail / 69 warn (58 accepted, 11 untriaged = the planner-baseline set), 1 config warn** (pre-existing unused allow launcher_cover x journal_plate) -> renders/attempt-2/cadcheck.json. FASTENERS 11 screws / 4 specs; PARTS 25 printed, 14 metal. Kept. Reprint: beam, jar_adapter, jar_gate.
