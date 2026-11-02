tools: 6025133

## Tool issues
- Pin moved 36189b8 -> 6025133. No tool misbehaved. Subsets run as `cad check model.blend checks.json OUT.json --only ...`.

## Steps
checks | checks.json (A6 copy: renders/attempt-7/checks_attempt6.json; edit script renders/attempt-7/checks_edit_a7.py): A6-01 groove cap + FST_gcap_* moved 2c -> new step 11a with BUY_bus_junction + CAB_bus_pan_tail (10d keeps the feeder cover only; step 3 "CAB_bus_pan*" -> "CAB_bus_pan"), service "v2-A6-01 groove cap off" at tilt 45, 3 slide rows (cap +Z 40 at tilt 45; splice +Z 40 out of its seat with the cap ignored at tilt 45; splice +Z expect blocked by PRT_groove_cap at 2.0..4.5), accepted warn "FST_gcap_5 reachable only at tilt=45"; A6-02 distances CAB_bus_pan<->CAB_bus_pan_tail max 1.0 and tail<->CAB_launcher_base min 1.0 at pan -90/0/90, tail<->PRT_hub_gear min 1.0, cable_chains "pan bus lead" 350; A6-03 the 3 swept entry-arc rows psi 0..104 -> 1..105. Precheck on the A6 model (--only assembly,fasteners,service,slide,distances,cables -> precheck_a6_model.json): cap service 6/6 straight 14 at tilt 45; cap slide min 0.2 (post_L); splice seat slide min 1.0 (hub gear); captive row blocked at 3.5 by PRT_groove_cap; assembly 0 fail with the cap at 11a; swept rows from psi 1: 0 missed stations, 8.098 @ 91 / 8.222 / 8.415, tape 7.598 / 7.722 / 7.915, rest 6.175 / 6.494 / 6.986 | cadcheck 4F/3W (1 untriaged, now accepted): the 4 fails are CAB_bus_pan_tail not in the scene (3 distances + the chain), expected until the base/pan_stage step

## Plan
Attempt 7 fixes the one major from review 6 (A6-01: the bus splice is placed in a hub bore that the groove cap and the
floor have already closed) and both minors (A6-02: the static pan lead ends under an orbiting splice; A6-03: the swept rows
miss psi 0). Keep everything review 6 praised:
- full-lift entry arc >= 8.0 at all 3 settings (now 8.098 @ psi 91 with the psi 1..105 sweep);
- drops 31/31 at both stops, flattest >= 34;
- band to detent 1.000 and stack v2-A5-01; the flush detent head; the flat-topped tab; one EB 1.0 / CR 6 set;
- splice clearances: turntable 1.945, hub gear 1.000, bundle 2.846, base lead >= 3.5 over pan;
- 0 untriaged warns; `cad bom` clean; no PCB, wire or motor can visible in iso / iso_front_left.

checks.json is already updated (step "checks" above). The A6 model gives 4F against it, all "CAB_bus_pan_tail not in the
scene", planned in step 2. Build order: pan_stage (cap step label), base + pan_stage (pan-lead tail), finish (BOM, log,
renders). Each step: edit one module, `cad build`, `cad check`, append a line here.

1. **pan_stage: groove cap goes on last (A6-01, major).** Order change only, no geometry change.
   - Every bus lead reaches the turntable groove only after step 8 (tilt), 9 (bundle) or 11 (feeder), and the cap closes that
     groove and the hub bore. So the cap moves from bench step 2c to a new step **11a**, after the feeder is on the beam.
   - `pan_stage.build`: change the `FST_gcap_*` screw step label "2c" -> "11a". Nothing else in the cap or turntable changes.
   - Acceptance: assembly 0 fail with the cap, its 6 screws, the splice and the tail in 11a; the service row "v2-A6-01 groove
     cap off" passes with a straight bit (14) at tilt 45 for all 6; the slide rows pass: cap +Z 40 at tilt 45 (min 0.2,
     post_L), splice +Z 40 from its seat with the cap off (min 1.0, hub gear), splice captive (blocked by PRT_groove_cap at
     3.5, inside 2.0..4.5); the only new warn is `FST_gcap_5 reachable only at tilt=45` (accepted).
2. **base + pan_stage: pan-lead tail on PIV_pan (A6-02).** Measured in `renders/attempt-7/tail_feasibility.py` (capsule
   model): with the launcher inner leg at r 3, any point near the pan axis between z 48 and 66 is inside the launcher sleeve
   (gap -1.4), so the launcher leg moves out first.
   - params: `BUS_PAN_AX = (0, 0, 63)`, the joint between the static loop and the moving tail, on the pan axis.
     `LB_LEG_R = 6.5` (was 3), `LB_LOOP_ZC = 46.5` (was `PAN_LOOP_ZC` 48), and the launcher U arc centre r 11.25, radius
     4.75, so the outer leg stays at r 16 into the existing riser `vl(16, 68)`.
   - base.py `CAB_launcher_base`: `lb = [BUS_LB_JCT, vl(LB_LEG_R, 66)] + _arc(vl, 11.25, LB_LOOP_ZC, 4.75, 180, 360, 10) +
     [vl(16, 68)] + ...`. The meeting point with the bundle is unchanged: (-2.29, -3.28, 70). Estimated `added` 50.3 - 5.5 +
     3.0 = about 47.8 (must stay >= 45; the `_note_loop` assert enforces it). The U bottom centreline is at 41.75 (it was
     41.5).
   - base.py `CAB_bus_pan`: replace the last three points `[vb(3, 64), vb(7, 69), vb(7, 72.8)]` with
     `[vb(3.0, 59.0), BUS_PAN_AX]`. The static lead now ends on the axis. `_note_loop` added must stay >= 45 (it was 61.1).
   - pan_stage.py: `A.cable("CAB_bus_pan_tail", [BUS_PAN_AX, vb(3.5, 66), vb(7, 68), BUS_JCT_BOT], P.BUS_R, "cable_wht",
     joint="PIV_pan", step="11a")`, about 14.6 long. No `lead_len`: the chain row "pan bus lead" (350) covers it. Delete
     `BUS_PAN_END_GAP`, because the tail now ends on the splice face (same body).
   - Feasibility model (capsules): static bus to static launcher 2.1; tail to launcher 1.17 at pan -90 and 1.04 at -92.5
     overtravel, 2.1 at 0 / +90; tail to the bus arch 3.9 at pan 0. If cadcheck reads under 1.0, raise the tail's mid point
     (`vb(3.5, 66)` -> `vb(3.0, 66.5)`), or take `LB_LEG_R` to 7 (U radius 4.5, `LB_LOOP_ZC` 46). Re-measure with
     `cad q sweep CAB_bus_pan_tail CAB_launcher_base PIV_pan -92.5 92.5 2.5`.
   - Acceptance:
     - `distances` CAB_bus_pan<->CAB_bus_pan_tail <= 1.0 at pan -90/0/90 (coaxial, so expect overlap / 0);
     - tail<->CAB_launcher_base >= 1.0 at pan -90/0/90; tail<->PRT_hub_gear >= 1.0;
     - the v2-A2-02 launcher rows are unchanged (base to bundle <= 1.0 at pan ±90, base to MotorGo <= 3.0);
     - the v2-A5-03 splice rows still pass (base lead >= 1.0 over pan);
     - interference 0 F, with no new moving-clearance warn under 0.5 on the tail;
     - cables: "pan bus lead" chain <= 350, encoder chain <= 545, phase chain <= 700, both `_note_loop` asserts hold,
       0 junction warns (the tail/static pair is declared by the chain).
3. **finish: BOM, log, renders (A6-01 text, A6-02 / A6-03 evidence).**
   - BOM_AND_ASSEMBLY.md:
     - **2c**: posts only. Add the note "groove cap at 11a".
     - **10d**: feeder cover only; the feeder bus hangs free until 11a.
     - **New 11a**, after the feeder is on the beam:
       1. Tilt the pod to 45.
       2. Lay the tilt and feeder bus leads and the launcher bundle in the turntable groove.
       3. Pull the pan lead up the hub bore (62 spare), and bring the tilt / feeder ends down to it (93.5 / 180.4 spare).
       4. Cut the plugs off, solder 3-to-1 above the turntable, heat-shrink each splice, and sleeve the three.
       5. Lower the splice into the bore at az 35 until its bottom is at z 74 (24.5 under the turntable top). Tie it to the
          bundle sleeve. Push the spare pan lead back down into its U-loop.
       6. Fit the groove cap: 6 x M3 x 10 csk, straight bit, at tilt 45.
       7. Retention: the cap is 3.0 over the splice top and stops it at 3.5 [slide_out v2-A6-01 captive].
     - Fastener table: `FST_gcap_*` (2c) -> (11a).
     - Item 14: the pan lead ends on the pan axis (static loop + PIV_pan tail, chain 350).
     - Item 14a: step 11a, plus the three A6-01 rows.
     - Service: "bus splice: groove cap off at tilt 45".
     - Evidence table: swept rows psi 1..105.
   - finish.py `bom_items`: add `CAB_bus_pan_tail`; change the splice text to "step 11a".
   - DESIGN_LOG: one A7 section citing each new row.
   - `cad bom` clean.
   - Renders: preview set, then `sec` x 5.73 through the hub bore at pan -90 / +90, showing the tail, the launcher leg and
     the splice. Then the final 1600 px set.
   - Run the full `cad check` last: 0 F, every warn accepted.

Deferred:
- The optional 2 mm tie slot in the hub-gear bore (A6-01 fix item 3). The cap stops the splice from rising (blocked at 3.5).
  Downward, it hangs from the tilt and feeder leads, which are pinned in the groove, and it is tied to the bundle. The review
  marks the slot optional. It would need a radial window through the gear's bore ring (z 77.5..85), and the splice's lower
  3.5 mm (z 74..77.5) hangs below the gear in any case.
- Launcher bundle/base meeting point (A6-02, second half): kept at r 4, az 235. The two Ø6 ends are 5.66 apart at pan ±90,
  less than one sleeve diameter, so that joint never opens. The bus case was a real one: a Ø2.8 lead with a 9.9 swing.
pan_stage: groove cap step | FST_gcap_* screw step '2c' -> '11a' (pan_stage.py build, comment too); no geometry change. assembly 0 findings, cap/6 screws/splice at 11a; service 'v2-A6-01 groove cap off' 6/6 straight 14 at tilt 45; slides: cap +Z 40 min 0.2 (post_L), splice +Z 40 min 1.0 (hub gear), captive blocked 3.5 by PRT_groove_cap; warns 35 -> 36, the new one FST_gcap_5 tilt=45 (accepted); the 4 fails are CAB_bus_pan_tail not in the scene (step 2) -> check_step1.json | cadcheck 4F/36W
base + pan_stage: pan-lead tail | params BUS_PAN_AX (0,0,63), LB_LEG_R 6.5, LB_LOOP_ZC 46.5, LB_U_RC/LB_U_R 11.25/4.75, BUS_PAN_END_GAP deleted; base CAB_bus_pan ends [vb(3,59), BUS_PAN_AX] (loop added 58.2), CAB_launcher_base inner leg r 6.5 + U r 11.25 R 4.75 (added 48.4, meeting point unchanged); pan_stage CAB_bus_pan_tail on PIV_pan step 11a (14.64); checks.json cable_leads CAB_encoder 117 -> 119 (finish budget 119.1, base path 156.1) + accepted warn "no lead length: CAB_bus_pan_tail" (chain row covers it). Rows: bus_pan<->tail 0.011/0.008/0.013 at pan -90/0/90; tail<->launcher_base 1.362/2.789/2.43 (cad q sweep -92.5..92.5 min 1.236 @ -92.5); tail<->hub_gear 5.825; A2-02 base<->bundle 0.916/0.006/0.76 (max 1.0; was 0.133/0.002/0.097), base<->MotorGo 0.722; A5-03 splice<->base 3.286/6.979/5.203 (was 3.548/5.13/4.206), splice hub gear 1.000, turntable 1.945, bundle 2.846; static bus<->launcher 2.585 (cad q dist); chains pan bus 292.1/350, encoder 510.0/545, phase 488.3/700; 0 junctions; interference 0 F -> check_step2.json | cadcheck 0F/37W (0 untriaged)
finish: bom_items | finish.py: bom_item for CAB_bus_pan_tail (last 14.6 of the 350 lead, chain row), CAB_bus_pan text ends on the pan axis (BUS_PAN_AX), splice text 'seated at step 11a' with the label read from checks.json assembly_order (assert 11a for splice + tail) -> check_step3a.json (--only assembly,cables,parts) | cadcheck 0F/14W
finish: BOM, log, renders | BOM: header/evidence A7; sec 0 swept psi 1..105 (8.098@63 / 8.222@91 / 8.415@91); items 13/14/14a/15 + U-loop numbers; FST_gcap_* (11a); 2c posts only, 3 pan lead fed up, 10d feeder cover only, new 11a (9 sub-steps citing v2-A6-01 rows: service 6/6 straight 14 @ tilt 45, cap slide 0.2 post_L, splice slide 1.0 hub gear, captive blocked 3.5, cad q cap-splice 3.0); service row 'bus splice: groove cap off at tilt 45'; sec 6/7/8. DESIGN_LOG A7 section. Renders: sec_hub_bore_x5.73_pan-90/+90 (960), final 1800x1350 set + stl_sheet; cad q sweep tail/base min 1.236 @ -92.5. cad bom 18 rows 0 disagree -> renders/attempt-7/cadcheck.json | cadcheck 0F/37W (0 untriaged)
