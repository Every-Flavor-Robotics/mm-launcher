tools: f039205

## Tool issues
- Pin moved 6b62667 -> f039205. The new cadcheck re-runs the attempt-2 model at 0 F / 49 W (A2 had 44 W): the 5 extra are new
  checks (drop coverage x4: the hood joints held at home; service removal x1: the FST_fhorn_ctr row removes the lobe cover with
  no matching slide). New features are used in the attempt-3 checks.json: `fits.contact_normal` (base_shell x turntable),
  `drop_tests.home_only_ok`, `accepted_warns` (target: 0 untriaged at the end), `--overlay`, missing-object rows fail instead of crash.
- A service op with no `pose` can never be "proved" by a slide_out row (cadcheck compares pose keys, None never matches). The
  FST_fhorn_ctr guard op now carries `"pose": {}` so the new lobe-cover slide row (home) proves the removal.
- `distances` without a ray is unsigned nearest distance, so a row cannot assert "these two overlap". The lentil-pair test (A1-03)
  therefore stays a pocket-diameter window (ray rows) plus the `cad q dist` lentil probe (negative = overlap mm3) as acceptance.
- `slide_out` cannot express a flexing detent (any detent overlaps its track mid-travel). The A1-09 detent is a separate flat-printed
  clip (PRT_gate_detent) that the gate slide row `ignore`s, with its own `flexures` and seated-bump `distances` rows.
- Line of sight still has no row type. The A2-03 fingertip access is expressed as ray_gap rows from PRT_turntable (behind the
  origin, home pose) to PRT_launcher_body along the approach line, against an R8 fingertip sphere resting on the rim crest.

## Steps
checks | checks.json: attempt-3 rows (v2-A2-NN) for A2-01/03/04/05, A1-03, A1-09, A2-02; fits/assembly/flexures/cable_leads/accepted_warns updated; precheck on the A2 model | cadcheck 11F/2W (--only drop,service,slide,distances,flexures,cables; every fail is a review issue: A2-01 nip stop x1, A1-03 pocket x4, A2-03 guard shelf x3, A1-09 detent x1, A2-02 launcher base lead x2)

Precheck notes (A2 model, new rows; files beside this one):
- precheck_a2_model_full.json was run on the first draft, where the gap-6.2 and gap-7.0 drop rows also held the leaf at full lift.
  Those poses stalled 13-31/31 rays on the opened plate. That is the rig's "stall at 10-12 mm" regime, and not an operating state: the
  leaf lifts only while a candy is in the nip, and the next candy drops with the leaf at rest. So the final rows put PIV_nip_lift
  under `home_only_ok` with that reason, and the full-lift case is checked by the gap rows.
- Full-lift bare gap on the A2 geometry (PIV_hood-framed y34 ray): 7.613 at hood +0.327 (gap 6.2), 7.928 at 0, 8.461 at -0.558.
  So HOOD_GAP_MIN 6.2 meets the 7.5 rule (margin 0.11). Static ray at +0.327 = 6.202.
- Leaf-solid rows: thumbwheel top to cover roof along the stud axis = 6.000 at home and 4.495 at PIV_nip_lift -1.493 (= LEAF_PAD_H +
  LEAF_T 4.5). The declared lift limit is the leaf going solid. The reviewer's "thumbwheel on the cover at -2.1" measured the cover
  without the leaf, which is modelled in its free state.
- Drops with the leaf at rest: gap 6.2 gives tilt -3/0/22.5/45/46 flattest 62.8/64.7/56.8/34.0/33.3 (stall 28 + 5 = 33: pass, A2-05 closes).
  Gap 7.0 gives 62.8/64.7/57.0/34.5/33.5.
- hood x nip_wheel min_clearance 0.5 (no longer contact) and base_shell x turntable contact_normal [0,0,1] / 0.1 both pass on A2.
- Only BUY_battery was unordered (A2-04's sleeve and valve-screw items were already in 6e/12); it now has step 14.

## Plan
Attempt 3 closes both majors (A2-01, A1-03) and every minor except where noted. It does not touch what review 2 praised: the
form language (EB 1.0/0.6, CR 6/30), the colour map, the jar glass, metering windows, the drop at both stops, rotating clearances
>= 1.5, 0 fastener fails, P1S fit and no supports. Build order: params, launcher, feeder, base (cables), finish. Each step: edit one
module, `cad build`, `cad check`, then append a line here. Rows are tagged v2-A2-NN in checks.json.

0. **params.**
   - HOOD_GAP_MIN 5.3 -> 6.2 and NIP_SET (6.2, 7.0), so HOOD_HI = +0.327.
   - Add MM_D = (12.5, 13.5) and MM_T = (6.3, 7.5) as "confirm with 20 calipered candies" params, plus NIP_PASS = MM_T_NOM 7.0 + TAPE_T.
     Add an assert that gap_bdc(solve_eps(HOOD_GAP_MIN) - lift) >= NIP_PASS.
   - Fix the HOOD_LO comment: the limit is the leaf going solid (pad + strip = 4.5 between the thumbwheel and the roof), not the stud.
   - POCKET_D 14.4 -> 13.9.
   - Gate detent params: GATE_DETENT, a clip 12 x 5 x 1.2 with an R1 x 0.5 bump. Notches at the closed position and at closed - 52.
   - CABLE_LEADS dict, same values as checks.json cable_leads.
1. **launcher (A2-01, A2-05, A1-08, A2-03).**
   - Rebuild. PRT_nip_stop follows HOOD_HI. The bay shrinks with EPS_BAY = HI + 1.1, which should close the 1.12 body wall.
     If it doesn't, step the bay hull 0.5 inboard above z 172.
   - Nip cover: a 45 deg chamfer on the slot-end underside, and a 45 deg skirt top. Target: no overhang warn.
   - Open the cover 0.3 over the rim, so thumbwheel to cover is >= 1.0 at full lift (A2: 0.83).
   - Finger scallop: an R8.5 cylinder along x (slot length 22 + EB 1.0), centred on the fingertip centre O0 + u(-1) + d(6.4), cut
     from the guard shelf.
2. **feeder (A1-03, A1-09).**
   - Pocket Ø13.9, keeping the 1 x 45 rim chamfer. Stack "pocket over outlet": limit = (16 - 13.9)/2 = 1.05.
   - Add tools/lentil_probe.py (from review/lentils.py, sizes from MM_D/MM_T).
   - Add PRT_gate_detent: a flat-printed clip on the +Y cheek top, 1 x M3 self-tap (FST_detent_0). Its bump sits in a blade notch
     at x of about 29.5 (between the spout OD and the tab). The open notch is 52 along -X.
3. **base / pan cables (A2-02).**
   - Add CAB_launcher_base: from the hub-bottom junction on the pan axis, through a >= 45 mm U-loop under the hub gear, to the
     MotorGo J6/J8 pads and its encoder JST. It is static, on step 3.
   - Add a 45 mm loop to CAB_bus_pan's hub end.
   - Pass lead_len from params to every A.cable.
4. **finish.**
   - Triage every remaining warn (accepted_warns with a reason, or fix it). Target: 0 untriaged.
   - The tilt-servo slide shows 0.10 against a row minimum of 0.25. Open the pocket 0.15 or accept it with a reason.
   - cg_grid, renders, sections (nip stop at +0.327, finger scallop x 19.5, pocket with --lentil), BOM and DESIGN_LOG.

Acceptance:
- 0 F, and every v2-A2 row passes.
- Lentil probe: a 12.5 x 6.3 edge-on pair overlaps the disc by >= 0.3 mm3 each. A flat 13.5 x 7.5 clears by >= 0.15.
- `cad q ray` along the finger approach at tilt 0 and tilt 45: the first hit is PRT_nip_wheel.

Deferred:
- PIV_nip_lift range. With the leaf solid at 1.493 deg and hood to body at 0.50 at the max setting, more lift would mean reworking
  the bay (review option B). Raising the minimum gap closes A2-01 with a parameter.
- post_R x journal_plate contact_normal. The stop-lug face normals aren't known yet; the 0.156 journal audit row stays.
params | HOOD_GAP_MIN 6.2 / NIP_SET (6.2,7.0) -> HOOD_HI +0.327, MM_D/MM_T + NIP_PASS 7.5 with assert (full-lift gap 7.548), HOOD_LO comment = leaf solid 4.5, POCKET_D 13.9, GATE_DETENT + notches (29.5, -22.5), CABLE_LEADS = checks.json; report() prints HI/full-lift line; A2-01 nip stop and A1-03 pocket rows now pass (remaining fails: A2-03 guard x3 launcher, detent part x1 feeder, CAB_launcher_base x2 base) | cadcheck 6F/39W
launcher | rebuilt on HOOD_HI +0.327 (nip stop at the gap-6.2 landing: hood/nip_stop 0.000; EPS_BAY = HI + 1.1 already in params, the bay shrink did not move the 1.12 wall because it sat under the FST_nipcover pilot tips: pilot now ends 0.5 past the tip (NIPCOVER_PILOT_OVER) instead of stepping the bay, which would have hit the hood at LO; body min wall 1.59, no thin samples); nip_cover: slot-end R4 arc -> 45 deg chamfer (kept 0.3 outside the leaf tip's path: leaf tip -3.5 -> -2.6 with a 0.5 chamfer), screw bores teardrops flattened at 1.0 r (td_bore), slot top +0.3 over the rim, slot shifted 0.3 off the +x end wall, roof step 0.4 before the leaf root: overhang 171 -> 19.5 mm2, cover min wall 1.35 -> 1.48; finger scallop R8.5 x 20 (+1.0 x 45 deg edge breaks) about nip (u 3.0, v -15.6) cut from the guard shelf: shelf rows 25.58/25.03/23.63 (>= 24.9/24.4/22.7), rim crest 24.511, seat contact 0.0 kept; thumbwheel to cover at full lift 0.827 -> 1.128; cad q ray along the finger line at tilt 0 and 45: first hit PRT_nip_wheel at 14.40; drops gap 6.2/7.0 x tilt -3..46 31/31 hit, flattest 33.3 (remaining fails: PRT_gate_detent x1 feeder, CAB_launcher_base x2 base) | cadcheck 3F/36W
feeder | pocket Ø13.9 + 1x45 rim chamfer (ray rows 13.9 x4); stack "pocket over outlet" renamed for 13.9, limit 1.05 (worst 0.67); tools/lentil_probe.py (review lens, MM_D/MM_T): `cad q dist` edge-on 12.5x6.3 pair -0.013 mm3 each (blocked by 0.05 radial only, NOT the >= 0.3 target: with this lens, 0.3 mm3 needs pocket R <= 6.835, which gives the flat 13.5 0.085 clearance and fails the 13.8 ray rows, so the targets conflict), flat 13.5x7.5 +0.198; PRT_gate_detent: the band lip (z 300.5, R36.75) covers the cheek top, so the clip is a tab on the +Y cheek's R34 outside face (FST_detent_0 M3x9 self-tap radial -Y at x 7.1 z 294.5, engagement 4.5, straight access 14) + a 1.2 plate at blade top +0.1 running +X to an R1x0.5 bump at (29.5, 25.5); blade notches R1.1x0.6 at x 29.5 and -22.5; printed on its +Y back face (R_PY_DOWN): flexures angle 0.0, 16.1 MPa; detent-to-gate 0.10; gate slide +X 52 0.35; index ±60 1 window each, column 0 at drift 0/5/10/15; jar-lift and pod-lift slide rows now carry/ignore the clip; accepted: detent 1.2 plate, gate 1.4 under the notches (remaining fails: CAB_launcher_base x2 base) | cadcheck 2F/36W
base (pan cables) | CAB_launcher_base (static, step 3, BUNDLE_R): pan-axis junction (0,0,76) -> hanging U under the hub gear (az 235, legs r 3/16, U centre z 48, riser top z 68 under the FST_hub_* band) -> z 77 across the base -> 12.5 slot between partition and MotorGo face -> 0.5 over encoder JST 1 (STEP 21.8,-50.8, measured on the STL) -> J6/J8 pads (STEP 34,-51, flat band between the JSTs; not in components.json); loop 69.3 vs chord 17.9 (+51.4), route 164.8/250; to BUY_motorgo_axis 0.722, to CAB_launcher_bundle 0.028/0.008/0.008 at pan 0/-90/90; FST_hub_1 sweep min 3.28, hub gear 4.48. CAB_bus_pan hub end: pocket exit -> riser r 14 az 35 -> arch -> U (legs r 9/3) -> junction: 127.1 vs chord 67.2 (+59.9), route 290.5/300. lead_len=P.CABLE_LEADS[...] on all 14 cables (base, pan_stage, launcher, feeder); manifest parts.<CAB>.loop {path_len, straight, added}; params HUB_JCT_Z, PAN_LOOP_ADD 45 (asserted), PAN_LOOP_ZC 48, MG_ENC_JST_STEP, MG_PHASE_PAD_STEP | cadcheck 0F/36W
finish triage | checks.json: 26 accepted_warns with measured reasons (parts x9 A1-08 locations, nip/tilt overtravel x13, overtravel clearances x3, tilt-servo slide 0.10 = M2 horn-screw tips at rest, not the clamp pocket); fits PRT_launcher_cover x PRT_hood 0.45 and PRT_nip_stop_sleeve x FST_tw_nut 0.5 (in-range 0.50 / 0.805); hood x nip_stop fit text gap 5.3 -> 6.2; untriaged 0, stale 0, unordered_solids [] | cadcheck 0F/34W
finish renders | cg_grid 64 poses worst 29.9 deg (jar 0 tilt 46 pan 180, 3936 g) -> cg_grid.txt; preview/ 8 views (960); sections sec_nip_stop_x19.75_hood+0.327 and sec_pocket_y18.19_lentil_pair (edge-on 12.5x6.3 pair from tools/lentil_probe.py, -0.013 mm3 each, flat 13.5x7.5 +0.198); finger scallop section reused from the launcher step; cad q ray finger line tilt 0/45 -> PRT_nip_wheel 14.4; final 1800 px view set (11) + stl_sheet; 12 preview renders total | cadcheck 0F/34W
finish docs | BOM attempt 3 (evidence summary, NIP_SET 6.2..7.0, leaf-solid lift stop, lead lengths + pan U-loops, detent clip + FST_detent_0 in step 12, battery step 14, 10a M2 x 8, gate_detent part, service rows, sections 6-8 rewritten with the triaged warns); DESIGN_LOG ## Attempt 3 with every v2-A2 row value; renders/attempt-3/cadcheck.json copied (05:42, 134 s) | cadcheck 0F/34W (0 untriaged, 0 stale, unordered_solids [])
