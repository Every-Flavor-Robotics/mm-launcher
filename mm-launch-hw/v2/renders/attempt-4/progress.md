tools: a20a4d7

## Tool issues
- Pin moved f039205 -> a20a4d7. New: `payload_fit`, `sightlines`, and a ray-vs-nearest warn on `distances`. The warn fires on
  the A3 rows that are rays on purpose (pocket diameter a = b, fingertip-vs-shelf, leaf-solid along the stud): 9 new warns on the
  A3 model, accepted in checks.json with reasons.
- A `distances` pose past a joint limit is taken silently: the new full-lift rows at PIV_nip_lift -2.19 PASS on the A3 model,
  whose limit is -1.493 (they read the hood posed through the solid leaf). The hard-stop ray rows (thumbwheel to cover 4.2..4.4)
  are what catch it there (3.79, fail). Keep both.
- `payload_fit` "blocked" is an overlap volume > 0.01 mm3. A lens rim touching the pocket wall reads margin 0.00 at A3 Ø13.9
  (overlap 0.023 mm3), matching the review's -0.016 mm3 probe.
- No prismatic joint in `asm.joint` (rotary only), so the gate detent's open-notch claim cannot be a posed `distances` row (A3-03).
- No hex-head fastener spec (`M3_cap`, `M3_pan`, `M3_csk`, `M3_selftap_pan`, `M2_pan`, `M2.5_*`), so FST_nip_stud cannot be
  modelled as ISO 4017 AF 5.5 x 2.0 for a measured pocket fit (A3-02).

## Steps
checks | checks.json: v2-A3 rows (full-lift >= 8.0 at hood +0.327/0/-0.2/-0.558 lift -2.19; jam claim 8.8..9.3; leaf-solid hard stop 4.2..4.4 and home 6.4..6.6; hood-body 0.5 at the static max with the leaf solid; pocket rays 13.65..13.85; FST_detent_0 to gate >= 2.4; 4 payload_fit rows; finger sightlines at tilt 0/45/full lift; review thick-candy drop; review base-floor slide; leaf flexure 35.5 MPa; pocket stack limit 1.125; cable_leads CAB_encoder 115 (budget of the 550 lead) and CAB_bus_pan 350; 3 accepted ray-vs-nearest warns); precheck on the A3 model (--only distances,payload,sightlines,drop,slide,flexures,stacks,cables) -> precheck_a3_model.json | cadcheck 7F/13W (every fail is a planned change: hard-stop rays x2 (A2-01 leaf travel), pocket rays x4 (A1-03 13.9 -> 13.75), hood-body at -2.19 x1 (A2-01 bay relief); payload margin 0.00 x2 = A1-03; thick drop, floor slide and sightlines pass; the 9 ray-vs-nearest warns are accepted after this run)

## Plan
Attempt 4 closes the one major (A2-01) and every minor that is cheap. It keeps what review 3 praised: the two printed nip stops,
the leaf-solid lift bound, one window per stroke at every drift, the gate stop and detent, drops 31/31 at both stops with >= 5 deg
margin, 0 untriaged warns, the bench floor and battery slides, and the pan U-loops. Build order: params, launcher, feeder, cables
(finish.py), then finish. Each step: edit one module, `cad build`, `cad check`, then append a line here. Rows are tagged v2-A3-NN.

0. **params (A2-01, A1-03, A3-01, A2-02).**
   - `LEAF_TRAVEL` 1.5 -> 2.2 and `LEAF_T` 2.5 -> 2.3, with `LEAF_PRE` 1.2 unchanged. The cover roof (SHELL_U0) rises a net 0.5.
     PIV_nip_lift lo goes -1.493 -> -2.190 and HOOD_LO -2.051 -> -2.748. The bay (BAY_EPS from EPS_OPEN) and the stud slot follow.
     Predicted full-lift bare gap (cad py, gap_bdc): 8.181 / 8.479 / 8.662 / 8.991 at hood +0.327 / 0 / -0.2 / -0.558. The ray
     read about 0.065 over gap_bdc in A3. Leaf (leaf_numbers): preload 7.1 N (A3 9.1; this is a rig-feedback param), 35.5 MPa
     solid, 30.4 for the thickest candy at the min stop, 26.9 for a nominal candy.
   - `NIP_PASS = MM_T[1] + TAPE_T` (8.0). Assert `HOOD_GAP_LIFT >= NIP_PASS + 0.1`.
   - `FINGER_SLOT` u 7.5 -> 8.3. At full lift the rim's -v edge now rises about 2.5 (A3 1.72), and it must keep >= 1.0 to the cover.
   - `POCKET_D` 13.9 -> 13.75. This balances the two payload margins (lens pair at about 0.08-0.1, flat 13.5 at 0.125). The
     A3 precheck gave 0.00 / 0.20.
   - `GATE_DETENT`: tab EB 1.0, plate EB 0.6, R3 plan round on the plate's free end, screw length 9 -> 10. Add a counterbore
     Ø6.5 x 1.0 (sink=1.0, head pan).
   - `ENC_LEAD = 550`, `CABLE_LEADS["CAB_bus_pan"]` 350, and `CAB_encoder` = ENC_LEAD - bundle - base path - 5.
1. **launcher (A2-01).** Rebuild.
   - Check hood to body >= 0.5 at -0.558 / lift -2.19. If the derived bay is not enough, step its hull 0.5 outboard over that
     arc (review fix 3).
   - Check the stud tip stays >= 2.0 under the roof at the 7.0 setting at full lift (A3 2.4, predicted 2.2), and the rim stays
     >= 1.0 to the cover.
   - Section the chute tongue at HOOD_LO. It must stay shingled inside the backplate top end (brief: 1.6 tongue).
   - Re-triage the leaf and cover thin-wall and overtravel accepts. Their texts quote -1.493.
2. **feeder (A1-03, A3-01).**
   - Pocket Ø13.75: 4 payload_fit rows and 4 ray rows.
   - Detent clip per params, FST_detent_0 as M3 x 10 pan self-tap in the counterbore. Optionally colour B as a gate touch point.
   - tools/pocket_coupon.py: an 8 mm test disc with Ø13.6 / 13.75 / 13.9 / 14.1 pockets and the 1 x 45 chamfer, exported to
     stl/test_pocket_coupon.stl, plus a BOM note: caliper 20 candies and set MM_D, MM_T and POCKET_D from the coupon.
3. **cables (A2-02).** finish.py sums the CAB_launcher_bundle and CAB_launcher_base path_len and writes CAB_encoder["lead_len"]
   = 550 - sum - 5, asserting it is >= the CAB_encoder path. checks.json cable_leads CAB_encoder 115 is the same budget.
   CAB_bus_pan uses lead 350.
4. **finish.**
   - Full check: 0 F, 0 untriaged.
   - BOM:
     - FST_nip_stud "M3 x 16 hex head, ISO 4017 (AF 5.5 x 2.0)" (A3-02).
     - Detent "M3 x 10 pan self-tap".
     - New row: "5-wire JST-SH encoder lead >= 550, one piece, twisted, routed on the far side of the sleeve from the phases".
     - Pan bus lead 350.
     - NIP_SET table plus the leaf numbers.
   - DESIGN_LOG ## Attempt 4 with every v2-A3 row value.
   - cg_grid, previews, sections:
     - nip at hood +0.327 with lift -2.19,
     - pocket with --lentil 12.5 x 6.3 pair,
     - detent counterbore.
   - Final view set.

Acceptance (all checks.json rows):
- 0 F, 0 untriaged.
- Full-lift ray >= 8.0 at 4 hood settings, jam row 8.8..9.3.
- Hard stop 4.2..4.4 and home 6.4..6.6.
- Hood-body >= 0.5 at the static max with the leaf solid.
- payload_fit: MIN pair blocked, margin >= 0.05 both ways; nominal pair margin >= 0.3; flat MAX fits, margin >= 0.05.
- Sightlines 3/3 at tilt 0, tilt 45 and full lift.
- Thick-candy drop 31/31 at both stops, flattest >= 33.
- Floor slide clear.
- FST_detent_0 to gate >= 2.4.
- Leaf flexure in plane.
- CAB_encoder path <= its lead budget.

Deferred:
- Widening the static nip window (6.2..7.0) toward the rig's 5..12. The gap-7.0 row notes that drops stall from 7.4 in this
  geometry, and the rig's own result is that drops stall at 10-12. Wait for rig numbers. With the leaf, the nip now opens
  dynamically 6.2..9.0.
- The detent open-notch posed row (A3-03). There is no prismatic joint type, so the gate's +52 pose cannot be posed. It stays
  as the review's moved-gate probe, plus the flexures and seated rows.
- The FST_nip_stud hex-head pocket fit (A3-02). There is no hex-head fastener spec. The BOM is corrected, and a section through
  the hex pocket shows the AF 5.5 head.
- Calipering the candies and printing the coupon (A1-03) are physical steps for the user. The geometry ships with Ø13.75 and
  the coupon STL.
- post_R x journal_plate contact_normal: unchanged from A3 (tool limit, audit row stands).
params | blender/params.py: LEAF_T 2.3 / LEAF_TRAVEL 2.2 (PRE 1.2), SHELL_U0 11.0 -> 11.5, HOOD_LEAF_LIFT 2.190, HOOD_LO -2.748, HOOD_GAP_MAX 8.991; NIP_PASS = MM_T[1] + TAPE_T 8.0 with assert HOOD_GAP_LIFT (8.181) >= 8.1; FINGER_SLOT u 8.3; POCKET_D 13.75; GATE_DETENT screw L 10, cbore (6.5, 1.0), tab_eb 1.0, plate_eb 0.6, plate_end_r 3 (feeder step consumes the new keys; "edge" 0.3 kept until then); ENC_LEAD 550, enc_budget(), CAB_encoder 115, CAB_bus_pan 350. cad py: leaf_numbers 7.1 N preload, 35.5 MPa at stop; full-lift rays 8.282/8.593/8.782/9.124, hood-body 0.54, pocket rays 13.75 x4, payload margins 0.06/0.06/0.34/0.14, CAB_encoder 84.1 <= 115, bus_pan 290.5 <= 350 | cadcheck 2F/45W (5 untriaged; both fails launcher-owned: leaf x FST_tw_nut 0.35 at nip_lift -2.19, hard-stop ray origin now inside the lifted thumbwheel reads 9.29 (home row 6.5 passes))
launcher | launcher.py rebuilt on LEAF_T 2.3 / TRAVEL 2.2 (roof u 11.5, bay to HOOD_LO -2.748): FST_nipcover counterbore follows the roof (head stays at u 9.8, thread 3.5 -> >= 4.2, no warn); FST_leaf pilot runs through the root block (0.30 floor gone, wall min 1.49); leaf fork half width 2.6 -> 4.0 (nut corner + 0.7): leaf x FST_tw_nut 0.35 F -> 1.289 at lift -2.19; checks.json hard-stop/home ray origin moved +1.5 along U (it sat inside the lifted thumbwheel): 4.288 / 6.500. Hood-body 0.54 at -0.558 lift 0 and -2.19 (no bay step needed; lift-0 sweep 0.54 to -2.558, 0.485 at -2.808). Full-lift rays 8.282/8.593/8.782/9.124, jam 9.124. Stud tip at 7.0 + full lift: u 8.80 = 2.70 under the roof plane, 2.936 nearest to the cover (window); rim to cover 1.143 at lift -2.19 (1.549 home). Tongue at HOOD_LO (radial ray chains x 14/22/30): tongue 43.25..45.07 at psi 106, hood face 46.36 behind it, below the tongue end hood at 45.84 (psi 104) = 2.6 outboard of the tongue face (min stop: 45.24 / 45.86), shingled. Drops thick 31/31 x8 flattest 34.2; sightlines 3/3 x3; leaf flexure 35.5 in plane. Re-triaged 9 launcher accepts to -2.19/-4.69 numbers, removed 3 stale | cadcheck 0F/43W (0 untriaged)
feeder (detent) | feeder.py: pocket Ø13.75 kept with the 1 x 45 rim (comments to A3-A1-03); detent clip: tab EB 1.0 and plate EB 0.4 (0.6 on the 1.2 plate meets in a knife edge) with R3 plan end, FST_detent_0 M3 x 10 pan self-tap in screw_hole sink 1.0 (Ø6.6 cbore). The sink-only fix put the tip at y 25.5, 0.77 mm3 into the adapter spout, so params GATE_DETENT: back face 36.5 -> 38.5 (tip y 27.5, 1.142 off the spout), screw x 7.1 -> 9.5, tab z 288.4..301.5 with a band relief R37.25 above z 300 (counterbore keeps >= 2.7 to every tab edge; first pass read 0.29), tab clearance run to its curved face (0.42 sliver gone). checks.json: detent wall accept re-texted (55 samples, min 1.19 on the plate), new row FST_detent_0 x PRT_jar_adapter >= 0.5. Rows: payload MIN pair 0.06 / 0.06 blocked, nominal 0.34 blocked, flat 13.5 fits 0.14; pocket rays 13.75 x4; FST_detent_0 x gate 2.652; detent seated 0.10; engagement 4.0 (min 4.0); stack 0.67 <= 1.125; index 1/1 windows, column 0 at drift 0..15; flexure 16.1 MPa 0.0 deg | cadcheck 0F/43W
feeder (coupon) | blender/tools/pocket_coupon.py (cad py, not in the assembly): 8 mm disc OD 51.1 with Ø13.6/13.75/13.9/14.1 through pockets in the disc profile (1 x 45 top rim chamfer), 1..4 R1 rim notches as labels, EB 1.0, print flat chamfer up -> stl/test_pocket_coupon.stl (1903 tris; bores ray 13.600/13.750/13.900/14.100 at z 1 and 6). Caveat: cad build (export_stls clean=True) deletes top-level stl/*.stl, so re-run the tool after the final build or move it to stl/tools/ (finish step) | cadcheck 0F/43W (assembly unchanged)
cables (finish.py) | parts/finish.py encoder_budget(): after every subsystem is built, reads CAB_launcher_bundle 265.4 + CAB_launcher_base 164.8 path_len, writes CAB_encoder lead_len = enc_budget() = 550 - 430.2 - 5 = 114.8 on the object and the manifest (P.CABLE_LEADS too), asserts it >= the CAB_encoder path (84.1, spare 30.7) and within 1 mm of checks.json cable_leads CAB_encoder 115; CAB_bus_pan lead 350 (params, already in) reads path 290.5 / 350. cadcheck cables rows: CAB_encoder 84.1 / 114.8, CAB_bus_pan 290.5 / 350, no cable findings | cadcheck 0F/43W
finish (baseline) | rebuild + full cad check, no edits: 0 untriaged, stale_accepts [], unordered_solids_assumed_present []; base floor + electronics slide -Z 40 blocked_at null (min 0.00 = seat, closest PRT_base_shell) | cadcheck 0F/43W
finish (bom items) | finish.py bom_items(): manifest/object bom_item for FST_nip_stud (M3 x 16 hex ISO 4017 AF 5.5 x 2.0), FST_detent_0 (M3 x 10 pan self-tap), CAB_encoder (one-piece twisted 5-wire JST-SH >= 550, far side of the sleeve from the phases), CAB_bus_pan (350); checks.json label texts: leaf 'compliant' 7.1 N / 2.2 lift, step 6c names the ISO 4017 stud; tools/pocket_coupon.py default out stl/tools/ (survives cad build clean), coupon re-exported | cadcheck 0F/43W
finish (renders) | cg_grid 64 poses worst 29.9 deg (jar 0 tilt 46 pan 180, 3937 g) -> renders/attempt-4/cg_grid.txt; 4 sections (960): sec_nip_x21_hood+0.327_lift-2.19, sec_pocket_y18.19_lentil_pair_12.5x6.3 (tools/lentil_probe.py lenses, cad q dist pair -0.134 mm3 each, flat 13.5x7.5 +0.123), sec_detent_cbore_x9.5 (head 1.0 into the tab), sec_stud_hex_pocket_y4.83; 1 discarded nip framing at x 19.5 = 5 previews; no 960 view set (final set instead); final 1800x1350 set (11) + stl_sheet; checks.json: the 3 leaf 'compliant' texts now 7.1 N / 2.2 | cadcheck 0F/43W (0 untriaged, stale [], unordered [])
finish (BOM) | BOM_AND_ASSEMBLY.md -> attempt 4: evidence summary (0F/43W, coverage incl. payload/sightlines/assembly, 62 distances rows), payload_fit + lentil numbers, NIP_PASS 8.0, leaf numbers (7.1 N, 35.5 MPa solid, 30.4 thick / 26.9 nominal), NIP_SET table, jam gap about 9.0 (ray 9.124), FST_nip_stud M3 x 16 hex ISO 4017 AF 5.5 x 2.0, FST_detent_0 M3 x 10 pan self-tap in the Ø6.6 x 1.0 counterbore, new item 15 one-piece twisted 5-wire JST-SH >= 550 far side of the sleeve from the phases, pan bus 350, base-floor slide row, coupon + caliper procedure, sections 6-8 rewritten | cadcheck 0F/43W
finish (log) | DESIGN_LOG ## Attempt 4: coverage/not_checked quoted, every v2-A3 row value (A2-01 x9 rows + drop + flexure, A2-03 sightlines x3, A1-03 rays x4 + payload x4 + stack, A3-01 x2, A2-02 cables, A3-02, A3-03 slide), stability, finish changes, deferred | cadcheck 0F/43W (0 untriaged, stale [], unordered_solids [])
