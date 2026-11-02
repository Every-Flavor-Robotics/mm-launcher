tools: dea6536

## Tool issues
- Pin moved a20a4d7 -> dea6536. New: `prismatic=True` joints, `slide_out.flex`, `cable_chains`, `=EXPR` row values, the
  `M3_hex` fastener spec, `cad rows`, `cad bom`. The A4 deferrals that were tool limits (gate open state, hex stud) can now
  be closed.
- `cad check model.blend checks.json --only ... --out X` ignores `--out`. The wrapper takes OUT as the third positional and
  passes `--out <dir>/cadcheck.json` first, so the precheck overwrote blender/cadcheck.json. Restored it from
  renders/attempt-4/cadcheck.json. Use `cad check model.blend checks.json /path/out.json --only ...`.
- In `slide_out`, `step` is the sweep increment in mm. The A1-A4 gate rows carry `"step": 2`, which reads like an assembly
  step but sweeps every 2 mm. The gate open-stop row uses step 0.5 and at_mm [52.0, 53.0].
- `slide_out.flex` records nothing below `vol_tol` (0.5 mm3). The detent rides the blade at 0.43 mm3 (review probe), so
  `flexed` is {} and the riding overlap counts as contact. The row still proves that the detent no longer blocks the motion.

## Steps
checks | checks.json: 5 entry-arc rows PRT_hood-PRT_flywheel at full lift (psi 50/55/60/70/80, frame PIV_tilt, radial ray through R38, poses =HOOD_HI / 0 / =HOOD_STATIC_LO with PIV_nip_lift =-HOOD_LEAF_LIFT, min =NIP_PASS); BDC full-lift row moved to =NIP_PASS / =-HOOD_LEAF_LIFT; gate slide: ignore of PRT_gate_detent/FST_detent_* -> flex {PRT_gate_detent: 1.0}, min_clearance 0.05; new gate open-stop row (expect blocked by PRT_jar_adapter at 52.0..53.0, step 0.5); cable_chains encoder signal lead =ENC_LEAD - 5. Precheck on the A4 model (--only distances,slide,cables) -> precheck_a4_model.json, precheck_a4_model_slide.json | cadcheck 6F/1W on the A4 model (all 6 = A2-01 entry arc, matching the review exactly: min stop 7.943/7.719/7.496 at psi 60/70/80, home 7.933/7.665 at psi 70/80, max 7.954 at psi 80; psi 50/55 at the min stop already 8.117/8.031). Gate stop blocked at 52.5 by PRT_jar_adapter (pass), gate open slide passes with 0.08 to the detent, chain 514.3 / 545 (pass). Ray vs analytic (params) at the min stop: psi 50 8.117 vs 8.10, psi 60 7.943 vs 7.93 (ray +0.01..0.02)

## Plan
Attempt 5 closes the one major (A2-01, the nip entry arc at full leaf lift), both minors (A4-01, A4-02), and the A4 tool-limit
deferrals that the dea6536 tools now support: the gate as a prismatic joint, and the stud as `M3_hex`. It keeps everything
review 4 praised. That means the BDC full-lift rays (8.28..9.12), the 2.2 leaf travel with its modelled solid stack (4.288)
and home (6.500), the hood-to-body 0.54, the fork-to-nut 1.289, the sightlines 3/3, the pocket Ø13.75 with its payload
margins, the coupon, the detent at both ends, the encoder lead budget, the drops 31/31 at both stops (flattest >= 33), and
0 untriaged warns. Build order: params, launcher, feeder, finish. Each step is: edit one module, `cad build`, `cad check`,
append a line here. Rows are tagged v2-A4-NN.

0. **params (A2-01).**
   - Set `PSI_C` 78 -> 45, so the hood's entry taper starts at the jack line. Analytic values with PSI_C 45 (cad py, the
     probe below):
     - Full-lift minimum over psi -3..112: 8.138 at psi 50 at the min stop (A4 7.49 at psi 80), 8.417 at home, 8.884 at the
       max stop.
     - Rest gap over psi 0..45: unchanged at 6.18..7.00. The grip arc is 27.5 mm at R35.
     - Ray vs analytic on A4: +0.01..0.02, so the psi 50 row should read about 8.15.
   - Add `gap_arc(eps)`, the minimum radial gap of the rotated `gap_at` profile over psi BP_PSI0..PSI_TOP in 0.5 deg steps.
     - `HOOD_GAP_LIFT = gap_arc(solve_eps(HOOD_GAP_MIN) - LEAF_TRAVEL / jack_r())`, with the assert kept at
       `>= NIP_PASS + NIP_PASS_MARGIN` (8.1).
     - `gap_bdc` stays as the definition of the NIP_SET settings in `solve_eps`.
     - Add `HOOD_GAP_LIFT_HOME` and `HOOD_GAP_LIFT_MAX` for the report.
   - Put the review reason in the PSI_C comment. The rig's backplate must take PSI_C 45 too, because the brief requires the
     same params. This goes in the BOM rig-feedback note.
   - Fallback: if any entry-arc row reads < 8.05 after the launcher build, use PSI_C 40 (analytic 8.202 at the min stop,
     grip arc 24.4).
1. **launcher (A2-01, A3-02, A4-02).**
   - Rebuild. The hood band, the bay, the guard hull, the relief cuts, the tongue and the nip poly all derive from `gap_at`.
     The hood back face moves out by up to 1.58 at psi 78.
   - Predicted ripple (cad py on launcher_geom.Geo):
     - JACK_SURF/NIP_E move 0.25 outward along U, so the seat, leaf, cover and thumbwheel shift with them.
     - The stud tip at the 6.2 setting goes u 5.72 -> 5.47, still over the nut top at 3.2.
     - TONGUE_IN goes 1.068 -> 1.020. The JP and cover screw picks are unchanged.
   - Re-verify these (A4 values in brackets):
     - hood-body >= 0.5 at the static max with the leaf solid [0.54];
     - hard stop 4.2..4.4 and home 6.4..6.6 [4.288 / 6.500];
     - leaf-to-nut >= 1.0 [1.289];
     - rim to cover >= 1.0 at full lift [1.143];
     - sightlines 3/3 x 3 poses;
     - the tongue section at HOOD_LO, still shingled;
     - hood to wheel >= 4.0 one degree past the stop.
   - Run the 5 new entry-arc rows (min =NIP_PASS) and the BDC rows. Re-run the drop tests, both stops x tilt -3..46 x
     payloads 7.0 and 7.5: 31/31, flattest >= 33. The funnel now opens from psi 45, so gap_at(100) goes 9.22 -> 10.88.
   - `FST_nip_stud`: spec M3_cap -> `M3_hex` (ISO 4017 AF 5.5 x 2.0), with the same `at`/`into`. The hex pocket gets a
     measured fit, and the head-buried and engagement rows must pass. This closes the A3-02 tool-limit deferral.
   - `PRT_nip_cover` orient text: build the "finger slot" string from `P.FINGER_SLOT` (22 x 8.3), not a literal (A4-02).
   - `launcher_geom.leaf_numbers()` gains the operating stress at the lift each candy needs, from `gap_arc`. Predicted:
     - min stop: nominal 7.0 needs 0.66 of travel (27.8 MPa), the thickest 7.5 needs 0.93 (33.8 MPa);
     - home: 0.51 (24.3) / 0.78 (30.4);
     - max stop: 0.26 (18.5) / 0.52 (24.5);
     - solid: 35.5.
     `report()` prints the entry-arc minimum at every setting.
2. **feeder (A4-01; gate open state).**
   - Detent tab: section x 9.5 / 17 against BUY_jar_band. Replace the R37.25 band-relief step with one planar 45 deg chamfer
     across the full tab top that clears the band by >= 0.3, keeping EB 1.0 on its edges.
   - Head: move the tab back face below the chamfer 38.5 -> 39.9 and deepen the counterbore 1.0 -> 2.4. The bearing face
     stays at y 37.5, so the tip stays at y 27.5 and the head sits flush. If the band leaves no room, keep the 1.0 sink and
     record the band clearance.
   - Gate: `PIV_gate` prismatic, axis +X under PIV_jar, lo 0, hi GATE_TRAVEL 52 (open notch), home 0 (closed). Hang
     PRT_jar_gate on it. Overtravel 1.0 reaches 53 > the 52.35 stop, so the lug-adapter hit there is an accepted
     overtravel warn ("positive open stop at 52.35").
   - Add `allow` PRT_gate_detent x PRT_jar_gate: "detent rides the blade, 0.43 mm3 < vol_tol; slide flex row + flexures".
   - Add distances rows:
     - detent seated at PIV_gate 52 (clip to blade <= 0.15, as the closed row);
     - FST_detent_0 to gate >= 2.4 at PIV_gate 0 and 52;
     - stop lug to adapter at PIV_gate 52.35, max 0.1 (hard-stop row).
   - Interference must stay 0 F with the gate swept against tilt and pan (the open blade reaches x 86.5).
3. **finish (A4-02).**
   - Full check: 0 F, 0 untriaged.
   - `cad bom BOM_AND_ASSEMBLY.md manifest.json`: 0 mismatches.
   - BOM leaf numbers from leaf_numbers()/gap_arc: NIP_PASS asserted over the entry arc, the operating-stress table above,
     the PSI_C 45 rig note, and FST_nip_stud M3_hex.
   - DESIGN_LOG ## Attempt 5 with every v2-A4 row value.
   - Section the nip at x 21, min stop, full lift, with --lentil 13 x 7.5 at psi 50 and psi 80.
   - Section the detent tab at x 9.5.
   - Final view set, cg_grid.

Acceptance:
- 0 F, 0 untriaged.
- Entry-arc rows psi 50/55/60/70/80 >= NIP_PASS at all 3 settings, BDC rows >= 8.0, jam 8.8..9.3.
- Params assert on gap_arc >= 8.1.
- Drops 31/31, flattest >= 33.
- Hood-body >= 0.5, hard stop 4.2..4.4, home 6.4..6.6, sightlines 3/3.
- Gate open stop blocked by PRT_jar_adapter at 52.0..53.0, gate open slide clear with flex.
- Encoder chain <= 545.
- FST_detent_0 head flush (bbox y <= back face + 0.05) or the reason recorded.
- `cad bom` clean.

Deferred:
- Widening the static nip window (6.2..7.0) toward the rig's 5..12: still waiting on rig numbers (unchanged from A4).
- Calipering the candies and printing the coupon are physical user steps.
- post_R x journal_plate contact_normal: tool limit, the audit row stands.
- A wafer-head detent screw: cadlib has no wafer or button head spec. The flush counterbore gets the same result.
params | PSI_C 78 -> 45 (comment cites review A4 A2-01 + rig backplate PSI_C 45); gap_arc(eps) added; HOOD_GAP_LIFT = gap_arc(...) 8.138 (assert >= 8.1 passes), HOOD_GAP_LIFT_HOME 8.417, HOOD_GAP_LIFT_MAX 8.884; gap_bdc kept in solve_eps. Entry-arc rows all pass, min 8.144 (psi 50, min stop) -> no PSI_C 40 fallback. Rest gap psi 0..45 minima 6.180/6.500/7.002 (span 6.180..7.046), same as PSI_C 78. REGRESSION: 14 drop fails (the 7.0 candy now lands at psi 63-66, A4 87-93; stalls at tilt >= 40, and 8/31 at tilt 22.5/30) + 1 sightline fail (FST_nip_stud first at nip_lift -2.19). Experiment (reverted): lift-matched floor gap_at = max(A4 quadratic, 8.16 - full-lift rest offset) -> gap_arc 8.159, drop fails 14 -> 4 (home tilt 46 18/31 stall; max-setting tilt 22.5/45/46). The max-setting 7.0 drop conflicts with a full-lift entry arc >= 8.1 for any hood profile on HINGE at psi 112: the setting rotation is 0.885 deg against the 2.19 deg lift, so max-setting rest = rest_min + 0.40 x lift opening -> >= 7.4 at psi 80. Needs a design decision | cadcheck 15F/39W (12 untriaged)
launcher-1 | FST_nip_stud M3_cap -> M3_hex (STUD_POCKET_D 3.2 -> 2.2, spot face 1.6 -> STUD_SPOT_D 0.6 so the +v flats key the hex 1.6); PRT_nip_cover orient from P.FINGER_SLOT (22 x 8.3); leaf_numbers() operating stress per setting/candy from gap_arc + report() entry-arc minima; sightline origins +0.25 U with NIP_E. PSI_C 45 ripple confirmed by report(): TONGUE_IN 1.02, tip u 5.47 at 6.2, NIP_E (-6.26,-88.84). Sightline fail fixed; fasteners pass; drops still 14 F (PSI_C 45 conflict, see params line) | cadcheck 14F/39W (12 untriaged)
launcher-2 | DESIGN CHANGE vs plan (resolves the params-step conflict): gap_at = lift-matched profile (params GAP_PROFILE "lift": 6.5 to psi ~50; then the gap whose point, turned to the min stop with the leaf solid, sits LIFT_FLOOR 8.105 off the land, to psi ~94; then a funnel with taper angle <= psi - FUNNEL_PSI0 82 to G_IN 13 at 112; gap_quad keeps PSI_C 45 for reference). Flywheel tape modelled as BUY_tape (R35..35.5 on the land, PIV_flywheel, TAPE_T) and drop rows target [PRT_flywheel, BUY_tape] (A1-A4 ended on the bare land, 0.5 conservative; at the static max a 7.0 candy can only meet bare 7.0 at psi <= 55 with the arc >= 8.1). Flange relief PSI_RELIEF 92 -> 62 (the groove held x 29 rays 1.5 off the flange). checks.json: allow BUY_tape x flywheel, tape in step 6f + flywheel/pod slide_out rows + masses, accepted hood-tape overtravel clearance (5.674 at +0.327, 4.698 at +1.327, cad q), cable_junctions_ok CAB_phase_* (motor leads end in 4.0 bullets, components.json). Results: entry arc min stop psi 50/55/60/70/80 = 8.182/8.109/8.110/8.105/8.107, home 8.465..8.277, max 8.948..8.566; BDC full lift 8.346/8.657/8.846/9.188; jam 9.188; HOOD_GAP_LIFT 8.105 (assert >= 8.1), HOME 8.206, MAX 8.380; drops 31/31 all rows, flattest 34.5 at tilt 46; hood-body 0.54 / 0.532 (static max, leaf solid); hard stop 4.288 / home 6.5; leaf-nut 1.289, rim-cover 1.143 (cad q); hood-flywheel 4.723 at +1.327; sightlines 3/3 x 3; FST_nip_stud M3_hex standoff 0, engagement 2.4, hood fit 0.1 (cad q); leaf 35.5 MPa in plane; operating stress min 27.8/34.2, home 24.4/30.7, max 18.5/24.9 MPa; TONGUE_IN 1.08 (plan 1.020 was for the PSI_C 45 quadratic). Remaining untriaged: cables 9 junctions at the pan hub [0,0,76] (CAB_bus_* / CAB_launcher_base / CAB_launcher_bundle: base/finish) | cadcheck 0F/33W (1 untriaged, not launcher)
feeder | A4-01 detent tab: R37.25 band-relief step -> one planar 45 deg chamfer across the tab top (feeder.tab_chamfer; fall line radial through the screw axis x 9.5, plane 0.32 off the band's R36.75/z 300.5 lip corner, params GATE_DETENT tab_chamfer), EB 1.0 on its edges; band to detent 0.322 (row, A4 0.5). Plane-angle search (/tmp/feeder_a5/plane.py): a pure-Y fall line breaks into the Ø3.4 clearance hole (-0.08..-0.22), the radial one leaves 1.25 vertical over the hole top at the R34.05 inner edge (cad q ray 9.5,32.8 -> 297.445; ~0.9 normal), all-faces wall probe finds no tab sample < 1.55. Flush head: plate_y 38.5 -> 39.9, cbore 1.0 -> 2.4, bearing face y 37.5, tip y 27.5: cad q list FST_detent_0 bbox max y 39.9 = back face 39.9, standoff 0, engagement 4.0. Gate: PIV_gate prismatic +X under PIV_jar (0..52, home 0, step 13), PRT_jar_gate on it. checks.json: allow detent x gate; fits valve x gate and adapter x gate min 0.3 (0.35 slide clearances, were same-body before); distances detent seated at gate 52 = 0.10, FST_detent_0 to gate 2.652 / 14.867 at gate 0 / 52, lug-adapter 0.0 at 52.35 (max 0.1), blade-valve 0.0 at the -0.4 closed stop (max 0.1), band-detent 0.322 (min 0.3); accepted overtravel warns at gate 53 (adapter, open stop) and gate -1 (valve, closed stop); wall accept 55 -> 66 samples (plate 1.4 wider). Slide: open row clear 0.08 to the detent (flexed {} under vol_tol), open-stop row blocked by PRT_jar_adapter at 52.5. Detent rows unchanged: seated 0.10, to gate 2.652, to adapter 1.142, engagement 4.0. Interference with PIV_gate swept against jar/pan/tilt/feeder/flywheel/nip: 0 F (only the 2 accepted overtravel stops) | cadcheck 0F/35W (1 untriaged: 9 cable junctions at the pan hub, base/finish)
finish-1 | finish.py: nip_numbers() re-asserts NIP_PASS over gap_arc at 3 settings (min 6.180/8.105, home 6.500/8.206, max 6.983/8.380) and writes manifest PRT_hood.nip + PRT_nip_leaf.operating (min 0.68/28.1 0.94/34.2, home 0.53/24.7 0.79/30.8, max 0.27/18.8 0.54/24.9 MPa, solid 35.5); bom_item FST_nip_stud M3_hex, FST_detent_0 2.4 cbore flush, CAB_bus_* -> 3-way bus junction (BOM 14a). checks.json: 6 stale accepts removed (bridge/ray-gap rules no longer fire on dea6536); cable_junctions_ok + CAB_bus_* (3-way hub junction; bus x launcher pairs are distinct conductors on the axis point); cable_chains + phase conductors 492.7/700; encoder chain 514.3/545. Sections sec_nip_x21_minstop_fulllift_lentil13x7.5_psi50_80 (13x7.5 lens to hood 0.113 psi 50 / 0.100 psi 80, to tape 0.004/0.007), sec_detent_tab_x9.5; cg_grid worst 29.9 (64 poses) | cadcheck 0F/34W (0 untriaged, stale [])
finish-2 | BOM_AND_ASSEMBLY.md -> attempt 5 (evidence 0F/34W, entry-arc table + NIP_PASS over gap_arc, leaf operating-stress table, rig-feedback note (lift-matched gap_at, not PSI_C 45), FST_nip_stud M3_hex, FST_detent_0 flush 2.4 cbore, BUY_tape, item 14a bus junction, phase/encoder chains, prismatic gate rows, sections 6-8); DESIGN_LOG ## Attempt 5 with every v2-A4 row value; checks.json entry-arc why text; final 1800x1350 view set (11) + stl_sheet; cad bom 18 rows 0 disagree | cadcheck 0F/34W (0 untriaged, stale [])
