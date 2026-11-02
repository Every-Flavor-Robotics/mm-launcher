# Review notes, attempt 4

- start: copy at /tmp/rv4/model.blend, tools pin a20a4d7
- full cad check on copy (tools a20a4d7, 150 s): CADCHECK PASS 0 fail / 43 warn (0 untriaged, 40 accept keys), stale []. Every check section identical to designer's renders/attempt-4/cadcheck.json except runtime_s. -> review/cadcheck.json
- nip rows (checks.distances): BDC full-lift rays 8.282/8.593/8.782/9.124 pass, but nearest_mm 6.967/7.121/7.216/7.385 (no ray-vs-nearest warn: threshold near+max(1,0.3near))
- probe /tmp/rv4probe/gap_profile.py (radial rays from land R35.01 at x 15/21/27, psi 0..110 from BDC toward rear): x21 min stop full lift: psi0 8.16, 40 8.23, 60 7.93, 70 7.71, 80 7.48, 90 8.03. home full: 80 7.65. max full: 80 7.94. Rest: min 6.17..6.34 over psi 0..80 (hood concentric to PSI_C 78). => the full lift opens psi 80 only 1.14 (hinge at PSI_TOP 112). Thick candy (8.0 needed) rigid at psi 60..85 at every setting; nominal (7.5) rigid by 0.02 at min stop. params gap_bdc samples psi -2..+2 only.
- review_rows.json (3 distances rays at psi 60/70/80 x 3 hood settings, full lift) -> cadcheck_review.json: 6 FAIL: min stop 7.94/7.72/7.50, home -/7.93/7.67, max -/-/7.95 (need 8.0)
- analytic (/tmp/rv4probe/psi_c.py via cad py, matches the rays): PSI_C 78 -> full-lift min 7.49 @psi80 (min stop); PSI_C 60 -> 7.89; 50 -> 8.06; 45 -> 8.14 @psi50 (max setting 8.89)
- gate probe /tmp/rv4probe/gate_move.py: detent 0.10 @0, -0.43 mm3 riding 13..39, -0.2 @51, 0.10 @52 (open notch), 0.0 @52.35 (adapter stop); FST_detent_0 to gate >= 2.652 over the travel
- rotating clearance /tmp/rv4probe/rot_clear.py: FST_motor_*/FST_nacelle_* 1.6 to flywheel (>= 1.5 brief), body 1.594, cover 2.0; BUY_motor 0.05 = shaft in hub bore
- BOM fastener table vs manifest counts: all match. assembly_order labels match BOM steps 1..14. stl/tools has coupon + jig.
- renders: review/r01_nip_x21_minstop_fulllift_psi80_lentil.png, review/r02_gate_detent_closeup.png (head 1.4 proud: FST bbox y to 39.9 vs tab back face 38.5; band-relief step on tab top)
