tools: 36189b8

## Tool issues
- Pin moved dea6536 -> 36189b8. New: swept ray rows (`ray.sweep`), `cad build` exits non-zero on a failed build, a stale
  blend warns, poses past a joint limit are listed in the summary (`past_limit_ok` drops a row from the list).
- Baseline: the unchanged A5 model and A5 checks.json give 0F/34W on 36189b8 (165 s), same as dea6536, plus a
  poses-past-limits list (distances 8/9/10 tilt -3/46, 14/15 hood 1.327, 48/49 gate 52.35/-0.4). All are on purpose and
  now carry `past_limit_ok`.
- No tool misbehaved. Run subsets as `cad check model.blend checks.json OUT.json --only ...` (positional OUT), as in A5.

## Steps
checks | checks.json (A5 copy: renders/attempt-6/checks_attempt5.json): band->detent min 0.3 -> 1.0 (A5-01) + stacks row "v2-A5-01" (vertical, 4 terms, RSS 0.418 / WC 0.8 vs 1.0); five entry-arc point rows -> one swept row psi 0..104 step 2 at 3 settings (min =NIP_PASS) + swept hood->BUY_tape (min =MM_T[1]) + swept rest-gap row (min =HOOD_GAP_MIN - 0.1) (A5-02); BUY_bus_junction rows (turntable, hub gear, bundle >= 1.0; launcher base >= 1.0 at pan -90/0/90), masses_g 8, step 10d, CAB_bus_* out of cable_junctions_ok (A5-03); allow detent x gate deleted -> fits contact, contact_normal [0,0,1], min_clearance 0.05 + accepted overtravel warn gate=-1 (A5-06); past_limit_ok on 7 rows. Precheck on the A5 model -> precheck_a5_model.json. Swept rows reproduce the review exactly: full lift 8.099 @ psi 90 (min stop) / 8.211 @ 92 (home) / 8.397 @ 92 (max); hood->tape 7.599 / 7.711 / 7.897; rest 6.176 @ psi 18 / 6.493 / 6.987. Gate pair without the allow: contact rule passes, seated 0.125 at gate 52, one overtravel contact at gate -1 (0.2 mm3, accepted) | cadcheck 5F/36W (1 untriaged): band->detent 0.322 < 1.0 (A5-01) + 4 BUY_bus_junction rows not in the scene + the hub junction warn (A5-03), all expected until the feeder and base/pan steps

## Plan
Attempt 6 fixes the one major from review 5 (A5-01: the detent tab sits 0.322 from the jar band) and all five minors (A5-02..06).
Keep everything review 5 praised:
- full-lift entry arc >= 8.0 at all 3 settings (swept row min 8.099);
- drops 31/31 at both stops, flattest >= 34;
- hood-body 0.532, leaf hard stop 4.288 and home 6.500;
- the prismatic gate with stops and seated rows (0.10 / 0.000);
- the flush detent head (standoff 0, engagement 4.0) and the one EB 1.0 / CR 6 form language;
- 0 untriaged warns and `cad bom` clean.

Build order: params, feeder, pan_stage + base, finish. Each step is: edit one module, `cad build`, `cad check`, append a
line here. Rows are tagged v2-A5-NN. checks.json is already updated (step "checks" above). The A5 model gives 5F against it,
and every one of those fails is planned below.

1. **feeder: detent tab (A5-01, major).**
   - params `GATE_DETENT`: set `tab_z1` 301.5 -> **299.5**, so the tab top sits 1.0 under the band lip's lower face
     (`IF_BAND_Z0` 300.5).
   - Delete `tab_chamfer` from params, and delete `feeder.tab_chamfer()` and its use in `build_detent`. The top is flat, with
     EB 1.0 on every tab edge (`tab_eb`). Update the comments: the old one claims ">= 2.6 to every tab edge" for the
     counterbore.
   - These stay as they are: screw (9.5, 294.5, M3 x 10 pan), counterbore Ø6.6 x 2.4 (head flush), plate, bump and notches.
     The counterbore top is z 297.8, so there is 1.7 of material under the flat top and 0.7 at the back-face edge under the
     EB. Measure that rim with `cad q section` at x 9.5. Re-triage the `PRT_gate_detent: 66 wall samples` accept to the new
     count, and give the reason.
   - Acceptance:
     - `distances` BUY_jar_band > PRT_gate_detent >= 1.0 (A5: 0.322);
     - stacks "v2-A5-01" passes (WC 0.8 against 1.0);
     - FST_detent_0: standoff 0, engagement 4.0, head flush (bbox y max = 39.9);
     - FST_detent_0 to gate >= 2.4 at gate 0 and 52 (2.652 / 14.867);
     - detent seated <= 0.15 at gate 0 and 52;
     - the new fits rule (detent x gate contact on Z faces only) passes in every PIV_gate sweep;
     - gate slide rows pass, with flex 1.0 mm3.
2. **pan_stage + base: bus junction (A5-03).** Model the 3-way splice in the BOM 14a as `BUY_bus_junction`.
   - Envelope: a Ø10 x 25 cylinder with its axis along Z, on PIV_pan, mass 8 g. Its src is "3 x 3-to-1 solder splices under
     heat shrink, sleeved".
   - Position: in the hub bore, in the bus loop's az-35 half, at r 7 from the pan axis, centre (5.73, 4.02). The z span is
     about 74..99, which keeps 1.0 under the groove cap with the bus leads entering from above. That gives 1.0 to the R13
     hub-gear bore and 2.0 to the R14 turntable bore.
   - Add params `BUS_JCT` with d, l, r, az, z0.
   - CAB_bus_tilt / CAB_bus_feeder: the hub lists end at the junction's top face, not at (0, 0, 76).
   - CAB_bus_pan: the static U-loop riser ends at the junction's bottom face centre, in the az-35 plane. `_note_loop` must
     still add >= 45.
   - Move the launcher bundle/base meeting point off the axis to the az-235 half at r 4, which is (-2.29, -3.28, 76): the
     pan_stage hub list and `lb[0]` in base. The bundle (Ø6) and the junction are then 3.0 apart. The bus ends no longer
     share a point with the launcher pair, so the 9-pair junction warn clears. The bus ends are within 3 mm of a BUY part,
     and the bundle/base pair stays covered by the two `cable_chains` rows.
   - Acceptance:
     - `distances` junction to PRT_turntable, PRT_hub_gear and CAB_launcher_bundle >= 1.0;
     - junction to CAB_launcher_base >= 1.0 at pan -90 / 0 / 90;
     - interference 0 F with the junction swept over pan against the base and the U-loops;
     - cables: 0 junction warns;
     - encoder chain <= 545 and phase chain <= 700;
     - bus leads within their stock lengths (350 / 300 / 500);
     - assembly: the junction is in step 10d.
3. **finish: docs and renders (A5-02, A5-04, A5-05).** finish.py bom_item text for `BUY_bus_junction` / `CAB_bus_*`. Then
   update BOM_AND_ASSEMBLY.md:
   - 6f / item 12: butt-join the tape with no overlap at the seam, and caliper it at 0.5 or less (A5-02).
   - Item 12: buy 1 in (25 mm) cloth hockey tape and trim it to the 13.8 land against the flanges. The model stays at 13.8
     wide, so the drop rows are unchanged (A5-05).
   - Section 8: if the calipered `MM_T` max is over 7.3, run at home or above, not at the min stop. The min-stop margin is
     0.099 at psi 90 (A5-02).
   - Item 14a: modelled, with its position and checks (A5-03).
   - Printed parts: a spare PRT_nip_leaf (1 g). The rig-feedback note: log the leaf preload after 1 week in the rig, and if
     it relaxes, `LEAF_L` 34 -> 40 (A5-04).
   - The evidence table: quote the swept-row profiles in place of the five point rows.

   Then the other finish items:
   - DESIGN_LOG ## Attempt 6, with every v2-A5 row value.
   - Section the detent tab at x 9.5 with the band in view, and section the hub bore at z 88 with the junction.
   - Re-frame side.png so the jar top and the base bottom are inside the frame, like front.png (A5-05).
   - Final 1600 px+ view set, stl_sheet, cg_grid, and `cad bom` clean.

Acceptance (whole attempt):
- 0 F, 0 untriaged, stale [].
- Swept entry arc >= 8.0 at 3 settings, hood to tape >= 7.5, rest >= 6.1.
- Drops 31/31, flattest >= 34.
- Band to detent >= 1.0.
- Bus junction rows pass, and 0 cable junction warns.
- `cad bom` 0 disagree.

Deferred:
- `LEAF_L` 34 -> 40 (A5-04): the review makes it conditional on rig creep data. The spare leaf and the preload log go in the
  BOM.
- More entry-arc margin by geometry (A5-02): in A5, raising the lift floor broke the max-setting drops (the 0.885 deg setting
  rotation against the 2.19 deg lift). The review prefers the BOM instruction: 2.4 of leaf travel would add 0.07 for +2 MPa.
- Review A5's radial band stack (RSS 1.26 against 0.455): it no longer applies once the tab sits under the lip. The vertical
  stack replaces it.
- These stand from A5: the static nip window toward the rig's 5..12 (waiting on rig numbers), and calipering the candies and
  printing the coupon (physical steps). The post_R x journal_plate audit row also stands.
feeder: gate detent tab | params GATE_DETENT tab_z1 301.5 -> IF_BAND_Z0 - 1.0 = 299.5, tab_chamfer param + feeder.tab_chamfer() deleted (flat top); tab rebuilt as a 6-chord plan prism (chord midpoints on R34.05) instead of box minus n=768 cylinder, because the 0.28 facets made the bevel's overlap clamp shrink every tab EB to ~0.1 (A5 too) -> real EB 1.0 (ray 9.5,39.89 down 298.51); comments updated; accept "PRT_gate_detent: 66" -> 64 wall samples (plate only, min 1.20). Band->detent 1.000 (min 1.0), stack v2-A5-01 WC 0.8 pass, FST_detent_0 standoff 0 / eng 4.0 / bbox y max 39.9, screw->gate 2.652 / 14.867, seated 0.10 / 0.10, detent x gate fit min 0.10 (>= 0.05), gate slide rows pass. Counterbore rim at x 9.5: top z 297.8, 1.65-1.7 under the flat top, 1.1 along the EB normal, 0.7 at the back-face edge (sec_detent_tab_x9.5_feeder_step.png) | cadcheck 4F/36W (1 untriaged): 4 BUY_bus_junction rows + the 9-pair bus junction warn, all A5-03 (pan_stage + base step)
pan_stage + base: bus junction | params BUS_JCT {d 10, l 25, r 7, az 35, z0 74} + BUS_JCT_XY/TOP/BOT, BUS_HUB / LB_HUB hub lists, BUS_LB_JCT, BUS_PAN_END_GAP 1.2; pan_stage.build_bus_junction: BUY_bus_junction Ø10 x 25 (n=128, EB 1.0) on PIV_pan at (5.73, 4.02) z 74..99, 8 g, src "3 x 3-to-1 solder splices under heat shrink, sleeved"; hub-gear bore R13 n=256 (default facets read 0.969); CAB_bus_tilt + CAB_bus_feeder (feeder.build_bus) hub lists cross at z 100.5 and end on the splice top (5.73, 4.02, 99); CAB_bus_pan riser r 3 -> r 7 -> ends 1.2 under the splice bottom (73.8 z; ending on the face rubbed across PIV_pan: zero clearance at 6 poses), loop adds 61.0; bundle/base meeting point az 235 r 4 but z 70 not 76 (-2.29, -3.28, 70): at z 76 the static base end overlapped the swept splice (-5.09 mm3 at pan -90), and az 215 r 6.5 cleared it (1.46) but broke the v2-A2-02 base<->bundle <= 1.0 rows (3.38 / 3.29 at pan -/+90); base loop adds 56+; checks.json cable_leads CAB_encoder 115 -> 117 (finish.py budget 117.2). Junction->turntable 1.945, ->hub gear 1.000, ->bundle 2.846, ->launcher base 3.548 / 5.130 / 4.206 at pan -90/0/90 (swept min 3.536 at -92.5), ->bus_pan swept min 1.2; base<->bundle 0.133 / 0.002 / 0.097; encoder chain 511.8/545, phase 490.2/700; bus leads 287.7/350, 206.5/300, 319.6/500; 0 cable junction warns; BUY_bus_junction in step 10d | cadcheck 0F/35W (0 untriaged)
finish: BOM, log, renders | finish.py: BOM_ITEM CAB_bus_pan/tilt/feeder text (plug cut, junction face each enters), BUY_bus_junction bom_item built from params.BUS_JCT in bom_items(P); elevations(outdir) re-renders front/side fitted to scene bounds + 8 % (z 0..432.6 in a 467.2 window, ortho 622.9; view_set's 1.25 x size gave a 405.6 window), called from build_assembly.py after view_set (A5-05). BOM: attempt-6 evidence; section 0 quotes the swept profiles (8.099 @90 / 8.211 @92 / 8.397 @92; tape 7.599 / 7.711 / 7.897; rest 6.176 / 6.493 / 6.987) in place of the 15 point rays + leaf-creep note (spare leaf 3.1 g, 1-week preload log, LEAF_L 34 -> 40 if it relaxes) (A5-04); item 12 1 in hockey tape trimmed to the 13.8 land, butt-joined, calipered <= 0.5 (A5-02/05), step 6f the same; item 14a modelled + step 10d; section 8 thickest-candy rule (MM_T max > 7.3 -> home or above; min-stop margin 0.099 @ psi 90); cable/loop numbers (bus 287.7/206.5/319.6, chains 511.8/490.2, loops +61.1/+50.3, meet 0.133/0.002/0.097); warns 35. DESIGN_LOG ## Attempt 6 with every v2-A5 row value. Renders: sec_detent_tab_x9.5_band, sec_hub_bore_z88_bus_junction (2 previews), final 1800 px set (side.png shows the jar top and base bottom), stl_sheet, cg_grid worst 29.9 (3948 g). Drops 25 rows all 31/31, flattest 34.5. cad bom 18 rows 0 disagree | cadcheck 0F/35W (0 untriaged, stale [], poses_past_limits [])
finish attempt 6 | checks.json text only: _about gains an Attempt 6 note (BUY_bus_junction modelled, CAB_bus_* out of cable_junctions_ok, bundle/base point off the axis at (-2.29, -3.28, 70)); the v2-A2-02 and phase-chain 'why' strings no longer say 'on the pan axis'. Full re-check, copied to renders/attempt-6/cadcheck.json | cadcheck 0F/35W
