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
