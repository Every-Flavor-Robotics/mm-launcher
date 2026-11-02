tools: 2197aac

## Tool issues
- `cad check`: a `distances` row whose `a`/`b` object does not exist yet crashes cadcheck (KeyError in check_distances, cadcheck.py:1456) instead of reporting a fail. Workaround until every named object exists: `cad check model.blend checks.json cadcheck.json --only parts,interference,fasteners,service,drop,index,slide,stacks,stability,cables` (skips distances). Do not drop rows from checks.json.
- `../test-prints/launch-rig/` does not exist yet (no README/build.py). Launcher parameters come from v1 attempt-3 `../blender/build_assembly.py` (the geometry the rig is printed from), with the review-driven deltas marked `v2:` in params.py.
- Template build_assembly.py defaulted CAD_SKILL to the unpinned ~/code-stuff/alex-3d-skills; the v2 copy points at the pin.

## Steps
scaffold | template copied, params.py (JAR_/IF_/launcher), stub modules base/pan_stage/launcher/feeder, checks.json (distances skipped: tool issue) | cadcheck 12F/10W
scaffold | IF_POST_Y front face 26 -> 22 (flywheel slide-off at tilt 45 had 0.94 mm to the post) | cadcheck slide+stability only: 2F/1W (stub fails: battery bay and post servo pocket not cut yet); tip angle 32.2 deg with the 750 g jar at z 302-433
base | parts/base.py ported onto IF_*: shell R30 + floor + partition + pan servo mount/clamp + pinion (PIV_pan_pinion); adapter on 4 x M3x20 csk self-tap from the deck (no nuts), stem-modelled battery, window to pack+2 (z<=76.6) + 2 x Ø30 scallops; MotorGo moved to MG_X0 -10 so the V-floor USB niche sits on the straight rear wall; params: IF_GEAR_Z (77.5,85) added, base block; checks.json assembly_order steps 1/2 split into bench steps 1a-1c, 2a-2b | cadcheck 10F/11W (0 base fails; distances FST_adapter_0/1 run separately 4.56 mm, 0F/0W)

## Plan
Architecture is in ../../DESIGN_LOG.md ("Attempt 1: architecture plan"), and the numbers are in blender/params.py. Build order:
base -> pan_stage -> launcher -> feeder. For each one: edit parts/<name>.py, `cad build`, `cad check` (use --only without
distances until every named object exists), fix the fails, then append a line here.

1. **base.** Port the v1 base onto the IF_* values.
   - Shell 240x240x90 with R30 corners, removable floor.
   - Battery bay slides out +X with 2/side, window to the pack + 2, Ø30 scallops.
   - Adapter on 4 x M3x20 self-tap screws from the deck top. No nuts. Tips >= 3 above the battery face.
   - Buck, MotorGo partition + vertical USB-C niche, controller on drill-to-fit bosses.
   - Pan servo + 36T pinion at (0,54), deck hole R20.3, cables (usb, uart, 12v, pan bus).
   - Acceptance: 0 fails in base pairs; slide_out battery 120 mm at >= 1.0 mm clearance including FST; distances FST_adapter_0/1 to
     BUY_battery >= 3.0; USB plug clear.
2. **pan_stage.**
   - Thrust ring, R108 turntable + hollow hub gear (bore R14), turntable cable groove.
   - Posts as R108 drum slices (L: arc..-88, R: 40..arc, y -26..22) with U-bores R15.2 and the cable channels.
   - Beam 216x60x8 with journal tongues, drop hole Ø30 at (21,0), feeder bolts.
   - Tilt servo inside the right post (spline tip x 52), hex 12AF horn adapter with a Ø6.5 hole, post cover, hard-stop lugs (-3/+46).
   - Acceptance: fits declared and no other cross-joint contact; slide_out of the tilt servo +X; service on FST_postcover_*;
     distances beam/post to pod >= 2.5 at -3..46.
3. **launcher.** Port the v1 attempt-3 pod (nacelle, body + chute + muzzle, cover, journal plate, encoder cap, hood on PIV_hood,
   flywheel) reading params.py.
   - Deltas: G_IN 13, stud M3x25 (gap 5.5-12), hinge M3x35 + nut trap, separate flat PRT_nip_leaf (2.5 thick, 1.2 preload,
     1.5 travel, R2 root).
   - Acceptance: drop_tests slide passes at every tilt 0-46 with stall 28; nip ray 5.5-7.0 with compliant; L-key access to
     FST_fw_bolt_* at tilt 45; bolt-nut engagement for the fw bolts and the hinge; flywheel, cover and encoder slide_out;
     magnet stack; exposure <= 5 mm.
4. **feeder.**
   - Housing on the beam: floor spout OD 22 to z 245, chamber R31 with a lip over the gear ring, 3-slot bayonet socket (30 deg),
     servo lobe + cover.
   - Disc: 3 x Ø15 through-pockets at r 21, park solid, 44T ring, agitator fins, baffle ±28 with 30 deg ramps.
   - Pinion 30T + servo #3 spline-down at (-55.5,0).
   - Jar group: adapter (Ø69 x 1.6 flange, spout 55/50), valve (lugs R37, gate guides, 3 radial screws), guillotine gate
     (travel 52, home closed).
   - Acceptance: index_tests 1 window for both ±60 strokes; jar lift slide_out at PIV_jar 30; gate slide_out +X 52;
     distances band/housing >= 2, jar/cover >= 2, disc/valve >= 1.5; stability tip angle >= 20 deg; P1S fit, no supports.
5. **Renders** (after all four have 0 fails): view_set + sections through the nip, drop axis, bayonet/gate and encoder axis.
pan_stage | parts/pan_stage.py written: thrust ring, R108 turntable (revolved, CH at the foot) + integral hub R20/bore R14, 36T hub gear screwed up into the hub, groove + cap, drum-slice posts with U-bores/channels/cavity, beam with tongues + R108 ends + CH, tilt servo in the right post, post cover, horn adapter (12 AF key, 6.5 hole), stop lugs; params IF_JOURNAL_*/IF_TILT_ADAPTER/IF_TILT_KEY_X/IF_STOP_* + pan-stage block; checks.json fits thrust_ring + hub_gear, assembly steps 2c/2d (posts on the turntable on the bench, gear from below with the floor off) and 8a/8b/8 | cadcheck (no distances) 13F/21W (5 pan_stage: cover x servo idler boss, 4 FST_post heads buried by an internal face)
pan_stage | turntable as one revolve and beam chamfer by frustum intersection (coincident side faces had left internal faces: parity misread), cover clears the servo idler boss, teardrop R13.5 | cadcheck (no distances) 8F/19W (0 pan_stage fails)
pan_stage | tongues end flat at tilt axis +9 (no slivers), groove cap proud 3 mm on a flat top (rebate needed a 36 mm bridge), gear bore R13, post_L bus drop-in as a box, notch wall, cover screws counterbored cap (csk on the arc left a knife edge), groove end -100.5, beam screws moved; slide_out row declares its 0.25 guide clearance | cadcheck (no distances) 8F/11W; pan_stage 0F/2W (beam csk cones on the bed face 205 mm2; hub gear tooth tips 1.54, same as the pan pinion). Remaining fails: feeder stub (housing x servo_feeder), drop test on the launcher stub (7)
launcher | parts/launcher.py + launcher_geom.py ported from v1 a3 (pod profiles, chute/tongue for G_IN 13, nip stud/thumbwheel/flat leaf/nip cover, hinge M3x35 + nut trap, flywheel 2 bolts through nuts, nacelle hollow journal Ø12, encoder cap, jig STL); dropped the v1 chute vertex pw(R+8,104) (ledge where every drop stalled at tilt 15-46); stud M3x20 + SEAT_H 3.2 (x25 ends 5.4 proud at gap 12); pod bench split 6a-6g; allow rows for the free-state leaf and the stud in the thumbwheel nut; slide rows take screws out first | cadcheck (no distances) 2F/31W (launcher: nip cover slide hits the groove cap at tilt 0)
launcher | HUB_X0 9.6 + FIN_R0/R1 37.6/39.2 (wheel to guard 1.59), JP_R 23.8 (flywheel slide-off 1.59), top-chamfer cutter fixed (keep cone both sides of the face; it had sliced the right journal), right plates CH-1.6 (1.6 land), hood stud spot face, nip-cover screws M3x14 cap counterbored at v 44, leaf block 3.6 (pilot through), encoder cable via the slot, stud slot as +X teardrops; nip-cover slide row at tilt 45 | cadcheck (no distances) 1F/29W, launcher 0F (only fail: feeder stub housing x servo_feeder); distances run separately on existing objects 0F/0W (hood-wheel ray 6.49, squeeze 1.01; wheel-body 1.59; beam 4.9 at 46; spout 2.7 at 46; post_L-cap 3.75)
feeder | parts/feeder.py written: housing = floor plate 260-263 + outlet Ø16 + spout OD22 to 245 (printed top down); new PRT_feeder_crown (band cavity R35, lip + land journal R31.35, pinion chamber, bayonet socket 68.6 with 3 L-slots entry +30 / 30 deg / end stops, 47.5 deg socket cone, servo pocket, bus channel to IF_FEED_BUS_XY; printed upside down) because the Ø69 disc cannot pass the Ø68.6 socket and the disc/pinion must go in from below; disc = 44T band at the bottom + R31 land journal + 3 x Ø15 pockets + hub fins; pinion 30T + horn recess, servo spline down face 276.2; cover R4 corners + CH by frustum intersection, idler pocket; jar group: adapter (Ø69 x 1.6, spout 55/50, 3 pads), valve (skirt + BAFFLE moved onto the valve, 45 deg underside ramps (30 needs support), 35 deg roof, lugs R37 275-279, three cheeks with FST_valve_*), gate 2 x 56, 30 deg leading edge, travel 52; checks.json: crown fits, bench steps 10a-10d, index 'feeder_column_never_open_to_outlet' (0 windows), band/jar-to-crown distances, pocket stack term; params FEEDER block | cadcheck 2F/34W (feeder: index +60/-60 1 window each, column 0; fits disc/pinion 0.142, crown/disc 0.349, housing/disc 0.30; disc/valve 1.6; band/crown 14.5; jar/cover 7.6; spout/pod 2.705 at 46; tip 33.5 deg; remaining 2F = FST_feedmount_2/3 at IF_FEED_BOLTS x 40 sit on PRT_post_R's inner face, driver blocked at 1.1 mm: planner item; trial with (34, +/-20) gave 0 fastener fails, reverted)
finish | IF_FEED_BOLTS[2:4] (40,±18) -> (34,±20) (planner change from feeder trial); full check incl. distances runs (all named objects exist) | cadcheck 0F/34W
finish | MotorGo screws M3 -> M2.5 per v2 brief rig finding (MG_SCREW/MG_HOLE_D 2.7/MG_PILOT_D 2.1 params; FST_mg_* engagement 8.0) | cadcheck 0F/34W
finish | renders (final view set, 4 sections via tools/section_precut.py, stl_sheet), cg_grid 64 poses worst 29.8 deg, cadcheck.json copied, BOM_AND_ASSEMBLY.md + DESIGN_LOG 'Attempt 1' written | cadcheck 0F/34W
