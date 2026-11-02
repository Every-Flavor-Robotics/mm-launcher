# M&M Launcher Turret v2: Design Log

## Attempt 1: architecture plan (written before modelling)

Inputs: `DESIGN_BRIEF.md` (v2) over `../DESIGN_BRIEF.md`; v1 reviews `../renders/attempt-{1,2,3}/review.md`; `../DESIGN_LOG.md`;
`components.json` (pinned tools 2197aac). `../test-prints/launch-rig/` does not exist yet, so the launcher block in
`blender/params.py` is the v1 attempt-3 geometry the rig is being printed from, plus four review-driven deltas
(marked `v2:`). All numbers below live in `blender/params.py`; this log names them.

### World frame and the big decision
- X right, Y forward (muzzle), Z up, mm; origin on the table under the pan axis.
- **The jar axis is the pan axis, and the feeder disc is concentric with the jar.** That gives the lowest pan inertia, keeps the 750 g
  jar's CG on the pan axis at every pan angle, and centres the visible jar on the machine.
- The outlet is on the 3-pocket circle (`FEED_RP` 21), so the drop axis sits at `IF_DROP_XY` = (21, 0). That is directly over the tilt
  axis in the wheel plane (`WHEEL_XW` 21), so all v1 attempt-3 pod coordinates carry over unchanged in world X.
- Height stack: deck 90, turntable 92-102, tilt axis 222, beam 252-260, disc 263.3-271.3, bayonet socket 274-286, gate plane 288-290.4,
  band lip 300.5, glass rim 302.6, jar top 432.6.
- Scaffold tip check: **32.2 deg** worst static tip angle with the full jar on stub geometry (`cadcheck.json` stability).

### Subsystems (one module each in `blender/parts/`)

**base** (static, `parts/base.py`). This is the v1 layout, which reviewers praised.
- Shell and deck: 240 x 240 x 90 (`BASE_HALF` 120, `IF_DECK_Z` 90), plan corners R30.
- Removable floor (`FLOOR_T` 3).
- Battery bay `BATT`: it slides out +X with 2 mm per side, behind a window cut to the pack outline + 2 (`BAY_WINDOW_Z1`). Two Ø30
  finger scallops.
- DeWalt adapter `ADAPTER`: M3 x 20 self-tap screws from the deck top go into its corner holes. Each tip stays at least 3 mm above the
  battery face (`ADAPTER_SCREW_L`). There are no nuts on the battery side (A3-M2).
- Buck at `BUCK_C`, with low and high louvres.
- MotorGo behind the rear partition (`MG_WALL_Y` -87, `MG_STANDOFF` 12.5). The vertical USB-C goes straight through into the rear niche,
  with a zip-tie anchor.
- Servo controller `CTRL` on drill-to-fit bosses with a +0.4 pocket. Its switch, terminal and ports are reachable through the wall notch.
- Pan servo, spline up, under the pinion at `IF_PINION_XY` (0, 54). The pinion meshes 1:1 with the hub gear (`IF_GEAR_M` 1.5, `IF_GEAR_N` 36).
- UART lead in floor clips.

**pan_stage** (`PIV_pan`, `parts/pan_stage.py`).
- Turntable R108 (`IF_TT_R`) on a 2 mm printed thrust ring, with a hollow hub (`IF_HUB_R` 20, bore R14). The hub journals in the deck
  hole R20.3 and carries the hub gear.
- **Yoke = a sliced drum.** Two posts whose outer faces are arcs of the R108 turntable cylinder:
  - left post x from the arc to `IF_ARM_L_IN` -88;
  - right post from `IF_ARM_R_IN` 40 to the arc;
  - both span y -26 to +22 (`IF_POST_Y`; the front face sits at 22 so the flywheel slides off +X at tilt 45).
- Post bores R15.2 are open U-slots at the top.
- The **beam** (x ±108, y ±30, z 252-260, R108 ends) bolts across the post tops. Its tongues close the U-slots over the journals, so
  there are no arm caps and no visible cap screws.
- The **tilt servo lives inside the right post.** Its spline is on the tilt axis pointing -X, with the tip at `IF_TILT_SPLINE_X` 52 and
  the body at x 56-96. The 12 AF hex horn adapter, with a Ø6.5 centre-screw hole, keys into the journal plate.
- The servo goes in and out along X through the post's outer cover (`PRT_post_R_cover`) without removing the pod.
- Cable channels: left post `IF_POST_L_CHANNEL` (launcher bundle + feeder bus), right post `IF_POST_R_CHANNEL` (tilt bus).

**launcher** (`PIV_tilt`, `parts/launcher.py`) = the launch test rig. Port the v1 attempt-3 functions (`gap_at`, `bp_band`,
`chute_poly`, `guard_profile`, the nip stud, thumbwheel and cover) from `../blender/build_assembly.py`, reading only params.py values.
- Wheel at `W_P, W_Q` = (37, -52) from the tilt axis. `WHEEL_R` 35, flange 36, 14 mm tape land, two-bolt clamping hub (`FW_*`, M3 x 20).
- Undershot hinged backplate (`PIV_hood`): concentric to psi 78 at `HOOD_GAP` 6.5 bare, funnel to psi 112.
- Nacelle around the motor with the hollow left journal (bundle on-axis). The rear encoder is coaxial by construction, with an air gap
  of `ENC_GAP` 1.0 and the magnet jig on the Ø8 access hole.
- Cover and journal plate (right journal, hex socket, stop lug at -3/+46).
- Review deltas (feed these back to the rig):
  1. `G_IN` 21 -> 13 (A3-F1).
  2. `NIP_SET` 5.5-12 with an M3 x 25 stud (A3-F3).
  3. `HINGE_AXLE_L` 35 into a nut trap (A3-F2).
  4. The leaf spring becomes a separate flat-printed `PRT_nip_leaf`: `LEAF_T` 2.5, `LEAF_PRE` 1.2 (≈9 N, ≈13 MPa), `LEAF_TRAVEL` 1.5,
     R2 root (A3-M1).
- Pod must stay inside x -86..37.5 with at least 2 mm to the posts at every tilt.

**feeder** (`PIV_pan`, `parts/feeder.py`).
- Housing on the beam (4 x M3 csk at `IF_FEED_BOLTS`). The floor top is at 263, and the floor spout (OD 22) reaches down through the
  beam hole to `IF_SPOUT_Z0` 245, 3 mm over the pod drum.
- Above the disc sits a chamber R31, whose lip covers the gear ring so no candy reaches the mesh. The bayonet socket (`IF_SOCKET_ID`
  68.6) has 3 L-slots for a 30 deg twist.
- **Disc** (`PIV_feeder`) on the jar axis:
  - 3 through-pockets Ø15 x 8 at r 21. At park they sit at ±60 and 180 from the outlet, 5.5 mm of solid from the outlet edge.
  - Agitator fins on the hub, and a 44T m1.5 gear ring.
  - Baffle over the outlet, ±28 deg, with 30 deg anti-shear ramps on both edges.
- **Pinion** 30T (`PIV_feeder_pinion`, coupled -1.467) at (-55.5, 0). It is driven by servo #3, spline down, standing above the beam in
  the crown's left lobe (`PRT_feeder_cover`). Disc ±60 = servo ∓88.
- **Index:** park 0, fire +60 then back to 0. The next shot is -60 then back to 0. Exactly one window per stroke (`index_tests`).
- **Jar group** (`PIV_jar`, 0 = locked, 30 = free):
  - `PRT_jar_adapter`: a Ø69 lid disc, 1.6 flange, spout OD 55 / ID 50 that passes the Ø58 band lip.
  - `PRT_jar_valve`: OD 68, bayonet lugs to R37, clamps the spout with 3 radial self-tappers, carries the gate guides.
  - `PRT_jar_gate`: a guillotine blade (`GATE_T` 2, `GATE_TRAVEL` 52). Pull +X to open. The model's home is CLOSED.
- The gate plane (288-290.4) is above the housing top (286), so the blade never passes a wall at any twist.
- Optional interlock: a slot in the crown that receives the open blade, so the jar cannot twist with the gate open.
- Nothing touches the glass or the band (at least 2 mm, `JAR_TOL` 1).

### IF_* interfaces (params.py, planner-owned)
| Interface | Value | Between |
|---|---|---|
| `IF_PAN_XY`, `IF_DECK_Z`, `IF_DECK_HOLE_R`, `IF_RING_H`, `IF_TT_Z0/Z1`, `IF_TT_R` | (0,0), 90, 20.3, 2, 92/102, 108 | base / pan_stage |
| `IF_HUB_R`, `IF_HUB_BORE_R`, `IF_GEAR_M/N`, `IF_PINION_XY` | 20, 14, 1.5/36, (0,54) | base / pan_stage |
| `IF_TILT_Z`, `IF_TILT_Y`, `TILT_LO/HI`, `TILT_STOP_LO/HI` | 222, 0, 0/45, -3/46 | pan_stage / launcher |
| `IF_ARM_L_IN`, `IF_ARM_R_IN`, `IF_JOURNAL_R`, `IF_BORE_R`, `IF_JOURNAL_BORE_R` | -88, 40, 15, 15.2, 6 | pan_stage / launcher |
| `IF_TILT_KEY_AF`, `IF_TILT_KEY_HOLE_D`, `IF_TILT_SPLINE_X` | 12, 6.5, 52 | pan_stage / launcher |
| `IF_BEAM_Z0/T/Z1`, `IF_BEAM_Y`, `IF_POST_Y` | 252/8/260, ±30, -26..22 | pan_stage / feeder |
| `IF_DROP_XY`, `IF_OUTLET_D`, `IF_BEAM_HOLE_D`, `IF_SPOUT_OD`, `IF_SPOUT_Z0` | (21,0), 16, 30, 22, 245 | feeder / pan_stage / launcher |
| `IF_FEED_BOLTS`, `IF_FEED_BUS_XY`, `IF_POST_L/R_CHANNEL` | see params | feeder / pan_stage |
| `IF_JAR_XY`, `IF_SOCKET_ID`, `IF_SOCKET_Z`, `IF_BAYO_*`, `IF_GATE_Z`, `IF_VALVE_Z1`, `IF_BAND_Z0`, `IF_GLASS_RIM_Z` | see params | feeder / jar |

### Joints (asm.joint, real ranges)
| Joint | Axis, pivot | Range | Parent |
|---|---|---|---|
| `PIV_pan` | Z at (0,0,90) | -90..90 | - |
| `PIV_pan_pinion` | Z at (0,54,90) | coupled -1 | - |
| `PIV_tilt` | X at (0,0,222) | 0..45 (stops -3/+46) | PIV_pan |
| `PIV_flywheel` | X at (21,37,170) | continuous | PIV_tilt |
| `PIV_nip_lift` (attempt 2) | X at the hinge (21,-14.9,191.0) | -1.493..0 deg (leaf lift: 1.5 at the stud) | PIV_tilt |
| `PIV_hood` (attempt 2) | X at the hinge | -0.558..+1.315 deg (thumbwheel gap 7.0..5.3; sum with the lift spans gap 8.35..5.3) | PIV_nip_lift |
| `PIV_feeder` | Z at (0,0,263) | -60..60 | PIV_pan |
| `PIV_feeder_pinion` | Z at (-55.5,0,263) | coupled -1.467 | PIV_pan |
| `PIV_jar` | Z at (0,0,274) | 0..30 (bayonet) | PIV_pan |

### Load path
- **Jar** (750 g):
  1. Band clamps the adapter flange on the glass rim.
  2. Spout to the valve body (radial screws).
  3. Bayonet lugs to the socket ledge.
  4. Housing to the beam (4 x M3).
  5. Beam to both post tops.
  6. Posts to the turntable.
  7. Thrust ring to the deck, then the shell, then the table.
- **Pod:** journals R15 sit in the post U-bores and are closed by the beam tongues. The tilt servo spline carries torque only. The hard
  stops are printed lugs on the journal plate against the right post.
- **Pan:** the hub journals in the deck hole (radial load). The servo pinion carries torque only.
- **Firing reaction:** wheel to the motor face, to the nacelle and body, to the journals.

### Payload path (jar to muzzle)
1. Jar mouth Ø60.
2. Adapter spout Ø50.
3. Gate (open).
4. Valve bore Ø50.
5. Chamber R31 (agitator fins break arches).
6. Pocket Ø15 x 8: one flat candy. The baffle's 30 deg ramps push an edge-standing candy down or back.
7. Disc stroke ±60 puts the pocket over the outlet Ø16 at (21,0).
8. Floor spout to the beam hole.
9. Drum on the tilt axis.
10. Chute: front fin, rear wall, tongue shingled into the backplate top.
11. Backplate funnel (`G_IN` 13). The candy slides at 28 deg or more at tilt 46.
12. It meets the descending rear tape at psi 0-112.
13. Nip 6.0 over tape, compliant via the leaf.
14. Exit along the fixed floor at BDC.
15. Muzzle with 4 mm flares.

Checked by `drop_tests` (slide, stall 28, tilts 0-46) and `index_tests`.

### Cable plan (all concealed; `exposure` max 5 mm)
- **Phase leads** (cut to about 55 mm, staggered joints in the straight journal bore) and the encoder JST: through the hollow left journal,
  down the left post channel, through the turntable groove under the posts, through the hub bore Ø28 with a U-loop below the deck, to the
  MotorGo.
- **Feeder bus:** from the servo lobe down through the beam at `IF_FEED_BUS_XY` into the left post channel, then the same route.
- **Tilt bus:** from the right post channel to the turntable groove, then the hub.
- **Base:** pan bus, UART (MotorGo to controller, floor clips), 12 V (adapter to buck to MotorGo and controller), USB-C straight out of
  the rear niche.

### Assembly order (mirrored in checks.json `assembly_order`)
1. Base shell upside down: adapter screws from the deck, pan servo and pinion.
2. Floor on the bench: buck, partition with MotorGo, controller.
3. Floor into the shell, cables.
4. Thrust ring, turntable and hub.
5. Posts onto the turntable.
6. Pod on the bench: motor, encoder with the jig, flywheel, backplate, hinge, stud, thumbwheel, leaf and nip cover, journal plate, cover.
7. Pod drops into the post U-slots.
8. Tilt servo and horn adapter slide in -X through the right post (horn fixed to the adapter on the bench, centre screw through the
   key). Post cover on.
9. Beam closes the U-slots.
10. Feeder on the bench: disc, pinion and servo, lobe cover.
11. Feeder onto the beam.
12. Jar on the bench: adapter in the band, valve on the spout, gate.
13. Jar drops in at +30 and twists to 0.

### Service (each is a checks.json `service` / `slide_out` row)
| Task | How |
|---|---|
| Nip gap | Remove the nip cover. The thumbwheel turns by hand. No tilt dependence. |
| Tape, flywheel | Tilt 45. Remove the cover (4 screws). L-key on the pinch bolts. The wheel slides off +X. |
| Encoder | Tilt 45. The cap comes off -X. |
| Tilt servo | Remove the right post cover. The servo slides out +X. |
| Feeder servo | Remove the lobe cover. |
| Refill | Close the gate, twist the jar 30, lift, flip, unscrew the band. |
| Battery | Slides out +X. |

### Form language
- One edge break (`EB` 1.0), one corner radius (`CR` 6), and one chamfer (`CH`: 45 deg x 4) on the top outer edges of the posts, beam,
  crown and pod.
- The yoke and turntable read as one R108 drum with the pod's slot cut out. The crown (feeder housing, servo lobe, valve) is a collar
  at the jar's base.
- Colours: grey `pla_a` for the base, turntable, posts and beam; terracotta `pla_b` for the pod, crown, valve and adapter. The jar's
  glass and candy are the hero.
- No outboard servo boxes (tilt servo inside the post, feeder servo inside the crown) and no hardware hanging under the pod.

### v2 naming (checks.json depends on these exact names)
| Subsystem | Names |
|---|---|
| base | `PRT_base_shell`, `PRT_base_floor`, `PRT_base_partition`, `PRT_pan_servo_*`, `PRT_pan_pinion`, `BUY_battery`, `BUY_dewalt_adapter`, `BUY_buck_12v`, `BUY_motorgo_axis`, `BUY_servo_controller`, `BUY_servo_pan`, `BUY_horn_pan`, `BUY_usbc_plug`, `FST_adapter_0..3` (0, 1 = +X side), `FST_floor_*`, `FST_buck_*`, `FST_mg_*`, `FST_ctrl_*`, `FST_panservo_*`, `FST_pinion_*`, `CAB_usb`, `CAB_uart`, `CAB_12v_*`, `CAB_bus_pan` |
| pan_stage | `PRT_thrust_ring`, `PRT_turntable` (hub included), `PRT_post_L`, `PRT_post_R`, `PRT_post_R_cover`, `PRT_beam`, `PRT_tilt_horn_adapter` (PIV_tilt), `BUY_servo_tilt`, `BUY_horn_tilt` (PIV_tilt), `FST_tt_*`, `FST_post_*`, `FST_beam_*`, `FST_postcover_*`, `FST_tilt_horn_*`, `CAB_bus_tilt`, `CAB_launcher_bundle` |
| launcher | `PRT_nacelle`, `PRT_launcher_body`, `PRT_launcher_cover`, `PRT_journal_plate`, `PRT_encoder_cap`, `PRT_hood` (PIV_hood), `PRT_nip_wheel`, `PRT_nip_cover`, `PRT_nip_leaf`, `PRT_flywheel` (PIV_flywheel), `BUY_motor`, `BUY_magnet` (PIV_flywheel), `BUY_plink_encoder`, `FST_motor_*`, `FST_nacelle_*`, `FST_jp_*`, `FST_fw_bolt_*`, `FST_fw_nut_*`, `FST_hinge`, `FST_hinge_nut`, `FST_nip_stud`, `FST_tw_nut`, `FST_leaf_*`, `FST_nipcover_*`, `FST_cover_*`, `FST_enc_*`, `CAB_phase_*`, `CAB_encoder`; tool STL `encoder_jig` |
| feeder | `PRT_feeder_housing`, `PRT_feeder_disc` (PIV_feeder), `PRT_feeder_pinion` (PIV_feeder_pinion), `PRT_feeder_cover`, `BUY_servo_feeder`, `BUY_horn_feeder` (PIV_feeder_pinion), `FST_feedmount_*`, `FST_fservo_*`, `FST_fhorn_*`, `FST_fcover_*`, `CAB_bus_feeder`; jar group on PIV_jar: `BUY_jar`, `BUY_jar_band`, `BUY_mm_fill`, `PRT_jar_adapter`, `PRT_jar_valve`, `PRT_jar_gate`, `FST_valve_*` |

### v1 lessons -> v2 (each row closes in a work item and a check)
| v1 issue | v2 answer | Check |
|---|---|---|
| A1-1 feed lands outside the nip; A3-F1 stall at tilt 46 | Undershot nip kept; `G_IN` 13 | drop_tests slide, stall 28, tilts 0-46, psi 0-112 |
| A1-2 / A2-4 no or rigid squeeze | Thumbwheel stop + flat leaf | distances ray 5.5-7.0, payload 7, compliant |
| A1-3 screw head under the disc | Housing screws outside the disc, countersunk | interference across PIV_feeder |
| A1-4 horn adapter order | Bench sequence, Ø6.5 key hole, servo inserted -X | assembly_order step 8 access |
| A1-5 tilt margin | Stops -3/+46; beam and spout at least 2.5 from the pod | overtravel 2.5; distances at -3/46 |
| A1-6 service teardown | Cover off at tilt 45; servo out through the post | service + slide_out |
| A1-7 / A2-6 magnet centring | Jig on the Ø8 access hole | stacks (RSS 0.17, worst case 0.40 warn) |
| A1-16, A2-10, A3-A1 form language | Drum yoke, servos inside, one chamfer | exposure, standoff; renders |
| A2-1 L-key on the pinch bolts | v1 a3 web side + bolt plane | fastener access + service |
| A2-2 double feed | 3 pockets, park solid, ±60 strokes | index_tests (1 window each) |
| A2-3 short bolts | M3 x 20 through nuts | bolt-to-nut engagement |
| A2-5 / A3-M2 bolts in the battery | Self-tap from the deck top, no nuts | slide_out battery 120 mm at 1.0 clearance; distances to FST_adapter_0/1 at 3.0 or more |
| A2-7 gap adjust access | Thumbwheel by hand | service |
| A2-8 / A3-A2 bare cable | Channels in posts, turntable groove, hub | exposure 5 mm |
| A2-9 hardware under the pod | Nip cover, flush | head stand-off 2 mm |
| A3-M1 leaf across layers | Separate flat-printed leaf, about 13 MPa | print_rot R_ID flat (stress not geometric: noted) |
| A3-F2 hinge axle 2.5 mm thread | M3 x 35 into a nut trap | bolt-to-nut engagement |
| A3-F3 thumbwheel stops at 10 | Stud M3 x 25, 5.5-12 | PIV_hood range; log arithmetic |
| A3-A3 battery window shows hardware | Window to pack + 2 | render |

### Open questions / confirm with calipers
- All `JAR_*` (thread OD, band lip ID, band height): the adapter flange and valve depend on `JAR_BAND_LIP_ID` 58 and `JAR_BAND_LIP_T`.
- Launch rig results: feed back `HOOD_GAP`, `G_IN`, `LEAF_*` and the tape thickness into params.py.
- Gate closing force through a packed column: the blade has a 30 deg chamfered leading edge. Test it physically.

## Attempt 1

Result: **cadcheck 0 fails / 34 warns** (`renders/attempt-1/cadcheck.json`, tools 2197aac, full run including `distances`).
Per-step history is in `renders/attempt-1/progress.md`. BOM, assembly and service are in `BOM_AND_ASSEMBLY.md`; every claim there
cites a cadcheck row or a `cad q` line.

### Coverage and not_checked (quoted from cadcheck.json)
- **coverage:**
  - parts: 33 printed objects (33 unique STLs). Manifold, bed fit ['P1S', 'H2D'], overhang, wall probe, bed contact.
  - interference/clearance: 170 objects in ['Printed', 'Purchased', 'Fasteners', 'Cables'], 4082 pair-pose tests. Joints swept: ['PIV_feeder', 'PIV_flywheel', 'PIV_hood', 'PIV_jar', 'PIV_pan', 'PIV_tilt'], with 2.5 deg overtravel.
  - fasteners: 102 screws, 4 nuts. Checks: head-buried, thread engagement (bolt-to-nut pairing), shanks/nuts inside purchased parts, head stand-off, protruding thread. Access: Ø6 bit to 14 mm hand clearance, else an 18/56 mm L-key with a 60 deg swing, at 14 poses, with parts present per assembly_order (28 steps).
  - service: 7 ops, 24 screw accesses with the built assembly present.
  - drop: 1 test (fall + slide on walls, no bounce or rolling).
  - index: 3 indexer timing tests (probe through the moving parts over the motion sequence).
  - slide: 8 slide-out sweeps.
  - stacks: 3 tolerance stacks (declared terms only).
  - stability: CG and tip angle over 1 pose, footprint from the static parts' lowest faces.
  - cables: 13 routes, 13 with path length; exposure (>= 8 of 26 rays escape) at the home pose.
  - The `distances` block ran (26 rows, 0 fails), but `coverage` has no line for it.
- **not_checked:**
  - fasteners: pilot/clearance hole diameters (use cadlib.features for those); wrench access to nuts.
  - stability: dynamic loads (recoil, pan acceleration), friction/sliding.
  - cables: bend radius, slack across joints, connector positions (review by section render).
  - not geometric: teardown step count, alignment-jig datums (declare stacks), aesthetics, BOM correctness.

### Key results (row -> value)
- **drop `outlet_to_descending_rear_tape`:** at tilt 0, 15, 22.5, 30, 40, 45 and 46, 31/31 rays land on PRT_flywheel with 0 stalls.
- **index:**
  - +60 stroke: 1 window (48..60).
  - -60 stroke: 1 window (-60..-48).
  - column-to-outlet: 0 windows over 0/+60/0/-60/0.
- **distances:**
  - nip ray 6.493 (5.5..7.0), squeeze 1.01;
  - adapter screws to battery 4.562;
  - spout to pod: 3.009 / 3.0 / 4.537 / 2.985 / 2.705 at tilt -3 / 0 / 22.5 / 45 / 46;
  - beam to pod 4.875 or more;
  - post_L to encoder cap 3.75 or more;
  - flywheel to guard 1.594;
  - disc to valve 1.6;
  - band to crown 14.5;
  - jar to crown 16.6;
  - jar to feeder cover 7.486.
- **slide:**
  - battery 120 mm, min 1.6;
  - flywheel off +X at tilt 45, 140 mm, min 1.59;
  - gate +X 52, min 0.64;
  - tilt servo +X 60, min 0.10 (warn);
  - pod cover, encoder cap, nip cover and jar lift: not blocked, 0.00 at the start contact (warn).
- **stacks:**
  - jar band 2.4 worst case vs 3.0;
  - pocket over outlet 0.67 vs 1.0;
  - magnet centring 0.40 vs 0.30 (warn).
- **stability:** 3936 g, tip 33.5 deg at the single sampled pose.
  - Supplementary `blender/tools/cg_grid.py` (same mass model; pan 0..315/45 x tilt -3/0/22.5/46 x jar 0/30, 64 poses): worst 29.8 deg at
    jar 30, tilt 46, pan 180. Output in `renders/attempt-1/cg_grid.txt`.
- **parts:** all 33 fit the P1S, with no supports. Estimated 1500 g and 31.3 h.

### Finish-step changes (planner)
- `IF_FEED_BOLTS[2:4]`: (40, ±18) -> (34, ±20). At x 40 the screws sat on PRT_post_R's inner face, and the driver was blocked at 1.1 mm
  in all 14 poses (2 fails). Now all four FST_feedmount pass with the L-key, engagement 4.5.
- **MotorGo screws M3 -> M2.5,** following the v2 brief rig finding (holes measure Ø2.5 in `REF/mg_axis.stl`). New params:
  - `MG_SCREW` "M2.5_cap", registered in `asm.FASTENER_SPECS` from base.py;
  - `MG_HOLE_D` 2.7, opened in the BUY envelope;
  - `MG_PILOT_D` 2.1, in the partition standoffs.

  FST_mg_* engagement 8.0, 0 fails. components.json still lists Ø3.4: confirm on the board.
- Renders: final view set and STL sheet. Four sections: x 21 drop axis + nip, x 21 feeder/bayonet/gate, z 277 bayonet lugs, y 0
  tilt/encoder axis.

### Deltas from the architecture plan (made by the subsystem work items)
- **base:**
  - MotorGo moved to `MG_X0` -10, so the USB niche sits on the straight rear wall.
  - Adapter on 4 x M3 x 20 csk self-tap screws.
  - `IF_GEAR_Z` (77.5, 85) added.
  - Assembly steps split into 1a-1c and 2a-2b.
- **pan_stage:**
  - Hub gear is a separate part (`PRT_hub_gear`, R28.5 > deck hole R20.3). It is screwed up into the hub from below, with the floor off (step 2d).
  - Posts go onto the turntable on the bench (2c).
  - Groove cap stands 3 proud.
  - Tilt drive bench steps 8a/8b.
- **launcher:**
  - `STUD_L` 20, not 25, with `SEAT_H` 3.2 (an x 25 stud ended 5.4 proud at gap 12).
  - `HUB_X0` 9.6, `FIN_R0/R1` 37.6/39.2: wheel to guard 1.59.
  - `JP_R` 23.8: flywheel slide-off 1.59.
  - The v1 chute vertex pw(R+8, 104) was dropped (every drop stalled on it at tilt 15-46).
  - Nip-cover screws are M3 x 14 cap.
  - Pod bench steps 6a-6g.
- **feeder:**
  - New `PRT_feeder_crown`. The Ø69 disc cannot pass the Ø68.6 socket, so the disc and pinion go in from below. The housing is now just the floor plate and spout.
  - Bench steps 10a-10d.
  - The baffle moved onto `PRT_jar_valve`, so it covers the outlet only when the bayonet is locked at 0.
  - Baffle ramps are 45 deg from horizontal, not 30 (30 gave 325 mm² of overhang needing support).
- **Naming additions:** `PRT_feeder_crown`, `PRT_hub_gear`, `PRT_groove_cap`, `FST_fplate_*`, `FST_fhorn_ctr`, `FST_gcap_*`, `FST_hub_*`,
  `FST_mg_*` (M2.5). `FST_ctrl_*` is not modelled.

### Tool issues found
- `cad check`: a `distances` row naming a missing object crashes (KeyError, cadcheck.py:1456) instead of failing the row.
- `cad check` stability: `pose_grid(..., cap=27)` with 5 driven joints thins every joint to [lo-overtravel, mid, hi+overtravel], then
  drops every overtravel combo. Only the all-mid pose survives, so the brief's "every pan and tilt pose" needs `tools/cg_grid.py`.
- `cad check` coverage: there is no line for `distances`.
- `cad q section` / `render.section`: the EXACT boolean inverts on `PRT_jar_valve` and `PRT_journal_plate` (the frame fills with the cut
  colour) and leaves `PRT_base_shell` uncut at y 0. `tools/section_precut.py` pre-cuts the named objects with the Manifold solver.
- cadlib has no M2.5 fastener spec or hole helper. Both were added locally in base.py.

### Not met / deferred (needs a planner or user decision)
1. **Nip gap adjustment needs the nip cover off** (2 x M3 x 14). The thumbwheel is enclosed: `cad q ray` at r 7 from the stud hits
   PRT_nip_cover first. The v2 brief asks for adjustment without removing covers. Fix options:
   - a thumbwheel window in the nip cover, with the leaf re-anchored;
   - the rig's exposed thumbwheel layout.

   A `service` row without `remove` would pass trivially, because cadcheck tests screw access, not finger access to a wheel. The check
   needs a ray/exposure row on PRT_nip_wheel.
2. The hub-bore U-loop and the base end of the launcher bundle and buses are not modelled. CAB_bus_pan stops at z 75.5.
3. `FST_ctrl_*` is not modelled (controller holes unconfirmed).
4. Bayonet detent nub, optional open-gate interlock.
5. Warns accepted for now:
   - thin walls: valve 0.02 at chamfer edges, gate knife 0.77, hood 0.91, crown 0.94, journal plate 0.95;
   - bridges: flywheel 72, journal plate 48, nacelle 39;
   - beam csk overhang 205 mm²;
   - FST_hinge 104 mm reach;
   - nip stud 17 mm stand-off;
   - magnet stack 0.40;
   - the -3 tilt stop is never reached in the sweep, which ends at -2.5.
6. Confirm with calipers: `JAR_*`, `MG_HOLE_D`, `ADAPTER_HOLE_INSET`, `BATT_STEM_INSET`, `BUCK_HOLE_Y`.

## Attempt 2: launcher work item (A1-01, A1-02, A1-08; A1-07 was the params step)

Evidence: `blender/cadcheck.json` after this step (4 F / 47 W, none on a launcher object) and the `cad q` lines in
`renders/attempt-2/progress.md`.

- **Joint split (A1-01).** The leaf lift and the thumbwheel setting are separate joints. `PIV_nip_lift` (-1.493..0) carries
  `PRT_nip_wheel` and `FST_tw_nut`. `PIV_hood` (-0.558..+1.315, its child) carries the hood, the stud and the stop sleeve. The thumbwheel
  therefore lifts off its seat only under a jam, and the sleeve meets it only at the gap-7.0 stop. With a single joint, either the
  sleeve went 1.5 mm into a static thumbwheel, or a carried thumbwheel sank into the seat. The seat is declared as a `fits` contact
  (body x nip_wheel).
- **Min-gap stop `PRT_nip_stop` (A1-01).** It is a 20 x 7 x 6.5 pad in a pocket under the muzzle floor, with its top flush with the
  floor. Its face lies on the plane of the hood's free-end face at `HOOD_HI`. A `HOOD_LUG` (2.5 radial, 6 deg) on the hood's front end
  makes the end face reach 3.4 below the floor, which gives a 3.4 x 20 land, far from the chute entry. The pocket's front wall takes the
  load. One `FST_nipstop` M3 x 6 runs up from the skin and only retains the pad (4.3 in the pad, tip 2.2 under the floor). The pocket
  also floor-cuts 3 mm behind the face, so the lug's swept envelope meets a flat floor instead of leaving a 0.2 sliver.
  `cad q dist PRT_hood PRT_nip_stop` at +1.315: 0.000. At +0.815: 0.603.
- **Max-gap stop `PRT_nip_stop_sleeve` (A1-01).** It is an R3.8 / R1.7 tube, 8.86 long, standing on the stud head's bearing face. The
  thumbwheel underside bottoms on it at gap 7.0. Its OD passes the AF 5.7 nut trap, so it bears on the wheel, not on the nut. `STUD_L`
  20 -> 16: the tip sits at u 5.2 / 7.1 / 8.6 at gaps 5.3 / 7.0 / 8.35, under the cover roof (11). `STUD_HOLE_R` 3.6 -> 4.4: the guard slot
  clears the sleeve by 0.59 (sweep). `cad q dist` sleeve/wheel at -0.558: 0.000, and 0.107 at -0.458.
- **Bay (A1-01).** It is swept to +2.415 (`BAY_OVER` 1.1). The grow is a true normal offset of 0.55: on the funnel slope, the A1 radial
  0.5 grow was 0.46 normal. The boss is a 48-gon. The tongue envelope is recomputed over the same range (`TONGUE_IN` 1.05 -> 1.26). Over
  the whole range, hood to body is >= 0.5 (the x-wall, 0.55 by `x0`).
- **Hood flange relief (A1-01 row hood/flywheel >= 4 at +2.315).** Over each R36 track the hood face is cut 1.5 deep. Beside each track,
  the cut follows a R4.1 circle about the flange corner (`relief_cuts`). A step-sided groove left 5/31 drop rays stalling in it, and the
  arc keeps every ray within 7 of the wheel. Result: 4.094 at +2.315; drops 31/31 at both stops.
- **Finger slot (A1-02).** The nip cover's -v end wall moves to v -6.5, so the R8.5 thumbwheel rim stands 2.0 proud through a 22 x 7.5
  slot. The extra 0.5 over the review's 7 is there because at full lift the rim's -v edge rises 1.72, and wheel to cover is 0.83 there.
  The leaf tip is cut back to -3.5, which makes an open fork round the stud. The 6 x 22 land at v -12..-6.5 stays as a finger shelf.
  Rays through the slot are in progress.md.
- **Thin and bridge items (A1-08).** In the hood, the hex pocket's -v half becomes a U-slot through the 26 deg back face. That was the
  0.91 lip, and the min wall is now 2.25. The spot face is 1.6 under the head's bearing face. The journal plate / cover lap is now 1.6
  vertical, then 45 deg, then 1.6 vertical, instead of the flat 2 mm step. The journal is re-added after the top chamfer, because the
  chamfer cutter's 1 mm overshoot had notched its base at the chute-entry chord. The journal-plate bridge goes from 47 to 11.4.
- **Flywheel flange ring (A1-08, declared).** The flywheel's "72 mm bridge" warn is the 1 mm R36 flange ring over the rim's 45 deg
  underside, a 33 mm2 ceiling. It prints as perimeter loops on the cone, so it is benign. It stays a warn, and the note is on the
  part (`notes`).
- **Moved by the bigger hull.** Cover screw `(81,-69)` is now at `(52,-101)` (`pick_screws`, still in front of the right post at tilt 45).

## Attempt 2

Result: **cadcheck 0 fails / 44 warns** (`renders/attempt-2/cadcheck.json`, tools 6b62667, full run including `distances`, 126 s).
Per-step history is in `renders/attempt-2/progress.md`. BOM, assembly and service are in `BOM_AND_ASSEMBLY.md`. Every attempt-2 row in
`checks.json` is tagged `v2-A1-NN` with the review-1 item it closes. The precheck of these rows on the attempt-1 model gave 12 F / 36 W
(progress.md, "checks" step), so the rows catch the A1 geometry they were written for.

### Coverage and not_checked (quoted from cadcheck.json)
- **coverage:**
  - parts: 35 printed objects (35 unique STLs): manifold, bed fit ['P1S', 'H2D'], overhang, wall probe, bed contact.
  - interference/clearance: 172 objects in ['Printed', 'Purchased', 'Fasteners', 'Cables'], 4430 pair-pose tests, joints swept
    ['PIV_feeder', 'PIV_flywheel', 'PIV_hood', 'PIV_jar', 'PIV_nip_lift', 'PIV_pan', 'PIV_tilt'] with 2.5 deg overtravel.
  - fasteners: 102 screws, 4 nuts; access at 15 poses, parts present per assembly_order (28 steps).
  - service: 8 ops, 26 screw accesses. drop: 3 tests. index: 6 tests. slide: 10 sweeps. stacks: 3. stability: 1 pose.
    cables: 13 routes, exposure at home. (`distances`: 39 rows, all pass; still no coverage line.)
- **not_checked (verbatim):**
  - "fasteners: pilot/clearance hole diameters (use cadlib.features for those); wrench access to nuts"
  - "flexures: no springs or snap arms declared (print orientation vs bending stress)"
  - "stability: dynamic loads (recoil, pan acceleration), friction/sliding"
  - "cables: bend radius, slack across joints, connector positions (review by section render)"
  - "not geometric: teardown step count, alignment-jig datums (declare stacks), aesthetics, BOM correctness"

### v2-A1 rows -> value (closes review 1)
- **A1-01 nip stops.**
  - [distances: v2-A1-01 nip ray at the printed min-gap stop] 5.294 (5.1..5.5) at hood +1.315, squeeze 2.21.
  - [distances: v2-A1-01 nip ray at the thumbwheel static max] 7.003 (6.8..7.2) at hood -0.558.
  - [distances: v2-A1-01 hood keeps 0.5 to the body] 0.541 at +1.315 and +2.315 (A1: 0.46, contact at +3.5).
  - [distances: v2-A1-01 hood never nears the wheel] 4.094 at +2.315 (A1: 2.17).
  - [drop: v2-A1-01 at the min-gap stop / at the thumbwheel max] 31/31 on PRT_flywheel at tilt 0 / 22.5 / 46; warn: 32.8 deg slide at
    gap 5.3, tilt 46.
  - `cad q dist PRT_hood PRT_nip_stop --pose PIV_hood=1.315` 0.000; `cad q dist PRT_nip_stop_sleeve PRT_nip_wheel --pose PIV_hood=-0.558` 0.000.
- **A1-02 finger slot.** [service: v2-A1-02 replace the nip leaf] reach 18 / 14 straight at tilt 45 (the gap itself needs no screw).
  `cad q ray 19.5,-2.33,111.274 0,-0.316,0.949` -> PRT_nip_wheel at 14.4 (tilt 0); `cad q ray 19.5,77.315,143.401 0,-0.895,0.445
  --pose PIV_tilt=45` -> PRT_nip_wheel at 14.4. 9/9 rays per tilt in progress.md. Section `sec_finger_slot_x19.5.png`.
  The "gap set with the cover on" claim rests on these `cad q ray` lines, not a cadcheck row: cadcheck has no outside-to-printed-part
  line-of-sight test (`service` tests only `FST_` objects, `exposure` only cables and nuts), so it is outside `coverage`.
- **A1-03 pocket.** [distances: v2-A1-03 pocket diameter along y / along x] 14.40 / 14.40 (13.6..14.5). [stacks: pocket over outlet at
  fire: v2-A1-03] 0.67 vs 0.8. Lentil pair at x 7.2 / 14.4 overlaps the disc 0.073 / 8.439 mm3 (`cad q dist` on the probe blend), so two
  edge-on candies cannot share a pocket. Section `sec_pocket_y18.19_lentil_pair.png`.
- **A1-04 feeder servo.** [service: v2-A1-04 feeder servo swap] reach 44 straight at every pose; [slide: v2-A1-04 feeder servo lifts +Z]
  60 mm, not blocked. `FST_fhorn_ctr` deleted.
- **A1-05 crown pilots.** [distances: v2-A1-05 FST_feedmount_0/1 to PRT_feeder_pinion] 3.517 / 3.517 (>= 2.35).
- **A1-06 pod install.** [slide: v2-A1-06 step 7 reversed] 150 mm, not blocked, min 0.2 to post_L.
- **A1-07 jig / pegs.** [stacks: magnet centring] 0.30 vs 0.30 (A1 0.40, a warn), with the v2-A1-07 spigot 7.9 and peg 2.4 terms.
- **A1-09 gate.** [slide: v2-A1-09 gate opens +X 52] min 0.35, valve present, not blocked; the lug meets the spout shoulder at 52.35.
- **A1-11 controller + glass.** [distances: v2-A1-11 +X wall closed over the controller PCB at y 32 / 50 / 68] 0.5 / 0.5 / 0.5 (0.3..6.0).
  BUY_jar is a transmissive material (`params.JAR_GLASS_RGBA`, alpha 0.25, set in `parts/finish.py`); Workbench honours the alpha, and
  the fill shows through the glass in `iso.png` and the rest of the view set.
- **A1-12 colours.** `params.COLOUR_B` is applied by `parts/finish.py`, the last subsystem, so modules cannot drift: B (terracotta) is
  the candy path and the touch points (jar adapter, valve, gate, feeder housing, disc, launcher body, hood, flywheel, thumbwheel), A
  (grey) the static structure and drivetrain. The table is in BOM section 3. No check covers colour (`not_checked`: aesthetics).
- **Unchanged rows still pass:** drop outlet_to_descending_rear_tape 31/31 at tilt 0..46; index +60 window [50, 60], -60 [-60, -50],
  column 0 windows incl. jar drift 5/10/15; battery slide 120 min 1.6; spout to pod >= 2.705; wheel to guard 1.594.

### Stability with the full jar
- [stability] 3935 g, tip 33.5 deg at the one sampled pose.
- `blender/tools/cg_grid.py` (same mass model; BUY_jar 350 + BUY_mm_fill 400 + band 15 g; pan 0..315/45 x tilt -3/0/22.5/46 x jar
  0/30, 64 poses): **worst 29.9 deg** at jar 0, tilt 46, pan 180, CG (8.7, -21.4, 169.8), edge 97.6. Output
  `renders/attempt-2/cg_grid.txt`. Acceptance (>= 20 deg) holds with 9.9 deg to spare.

### Finish-step changes
- New `parts/finish.py` (last in `SUBSYSTEMS`): owns the colour map (moved out of `build_assembly.py`) and the jar glass material. It
  adds no geometry, so the check counts are unchanged (0 F / 44 W before and after).
- `params.JAR_GLASS_RGBA` (0.80, 0.90, 0.95, 0.25).
- Renders (960 px previews, 12 in total for this step): the 6-view set plus the `pan+90_tilt45` pose, one jar test view, and three sections:
  `sec_nip_stop_x19.75_hood+1.315.png`, `sec_finger_slot_x19.5.png`, `sec_pocket_y18.19_lentil_pair.png`.

### Close-out (final renders, labels)
- `checks.json` assembly labels: 6c now reads "1 x M3 x 6 up from the skin" (matches `FST_nipstop`, `params.NIP_STOP_SCREW_L` 6.0);
  7 now reads "pod drops into the post U-slots, held nose-up about 20 deg (v2-A1-06)". Label text only, no geometry change.
  The re-run gives the same result: **0 F / 44 W**, `summary.pass: true` (`renders/attempt-2/cadcheck.json`, generated 2026-10-25 03:13,
  126 s).
- Final view set at 1800 x 1350 (`CAD_RENDER_FINAL=1`): iso, iso_front_left, front, side, top, rear, pan-90_tilt0, pan+90_tilt45, tilt45,
  jar_unlocked, exploded. `renders/attempt-2/stl_sheet.png` shows all 35 STLs in print orientation.
- BOM section 4 lists the 28 `assembly_order` steps in the same order and with the same labels (2 and 6 are group headings only).

### Not met / deferred
1. Stability is 1 pose in cadcheck (tool cap); the 64-pose cg_grid remains the evidence.
2. Gate detent bumps; base_shell x turntable per-region fits (see the plan in progress.md).
3. Not modelled: hub-bore U-loop, `FST_ctrl_*`, bayonet detent nub, open-gate interlock, Plink pegs (`PLINK_PEG_D` is used only in
   the magnet stack terms).
4. `flexures` has no `PRT_nip_leaf` entry, so leaf bending vs print orientation is in `not_checked`.
5. Base: the controller's 2-pole terminal faces the +X wall 1.5 mm away and `CAB_12v_ctrl` ends at the board's -Y corner; moving the
   board about 5 mm -X would leave room to land the wire, but would put the v2-A1-11 ray gap near its 6.0 limit. Not changed.
6. Confirm with calipers: `JAR_*`, `MG_HOLE_D`, `ADAPTER_HOLE_INSET`, `BATT_STEM_INSET`, `BUCK_HOLE_Y`, `CTRL_SW` / `CTRL_TB`.

## Attempt 3

Result: **cadcheck 0 fails / 34 warns, 0 untriaged, 0 stale accepts** (`renders/attempt-3/cadcheck.json`, tools f039205, generated 2026-10-25 05:42, 134 s, full
run including `distances`). `assembly.unordered_solids_assumed_present` is `[]`. Per-step history is in
`renders/attempt-3/progress.md` (checks, params, launcher, feeder, base, finish). Rows added in attempt 3 are tagged `v2-A2-NN` (the
review-2 item they close). The precheck of these rows on the attempt-2 model gave 11 F / 2 W (progress.md "checks"), so the rows
catch the A2 geometry they were written for.

### Coverage and not_checked (quoted from cadcheck.json)
- **coverage:**
  - parts: 36 printed objects (36 unique STLs): manifold, bed fit ['P1S', 'H2D'], overhang, wall probe, bed contact.
  - interference/clearance: 175 objects in ['Printed', 'Purchased', 'Fasteners', 'Cables'], 4562 pair-pose tests, joints swept
    ['PIV_feeder', 'PIV_flywheel', 'PIV_hood', 'PIV_jar', 'PIV_nip_lift', 'PIV_pan', 'PIV_tilt'] with 2.5 deg overtravel.
  - fasteners: 103 screws, 4 nuts; access at 15 poses, parts present per assembly_order (29 steps).
  - service: 8 ops, 26 screw accesses. drop: 3 tests. index: 6 tests. slide: 11 sweeps. stacks: 3. flexures: 2 declared springs or
    snap arms. stability: 1728 poses. cables: 14 routes, 14 with path length, exposure at home. (`distances`: 57 rows, all pass;
    still no coverage line.)
- **not_checked (verbatim):**
  - "fasteners: pilot/clearance hole diameters (use cadlib.features for those); wrench access to nuts"
  - "stability: dynamic loads (recoil, pan acceleration), friction/sliding"
  - "cables: bend radius, slack across joints, connector positions (review by section render)"
  - "not geometric: teardown step count, alignment-jig datums (declare stacks), aesthetics, BOM correctness"
  - (A2's "flexures: no springs or snap arms declared" is gone: the leaf and the detent clip have rows.)

### v2-A2 rows -> value (closes review 2)
- **A2-01 nip window 6.2..7.0 (major).** `HOOD_GAP_MIN` 5.3 -> 6.2, `NIP_SET` (6.2, 7.0), `HOOD_HI` +0.327; params asserts the
  full-lift gap at the min stop (`HOOD_GAP_LIFT` 7.548) >= `NIP_PASS` 7.5.
  - [distances: v2-A2-01 nip ray at the printed min-gap stop (gap 6.2)] 6.202 (6.0..6.4) at hood +0.327.
  - [distances: v2-A1-01 nip ray at the thumbwheel static max (gap 7.0), PIV_hood frame] 7.007 (6.8..7.2) at hood -0.558.
  - [distances: v2-A2-01 the hood lug lands on PRT_nip_stop at 6.2] 0.000 (<= 0.05) at +0.327.
  - [distances: v2-A2-01 bare gap at FULL leaf lift] 7.613 / 7.928 / 8.461 (>= 7.5) at hood +0.327 / 0 / -0.558, lift -1.493
    (A2: 6.685 at the min stop).
  - [distances: v2-A2-01 the PIV_nip_lift limit is real] 4.495 (4.4..4.6) at lift -1.493; [same ray at home] 6.000 (5.9..6.1):
    the lift ends with the leaf solid (pad 2.0 + strip 2.5) between the thumbwheel and the cover roof.
  - [drop: v2-A2-01/A2-05 drop at the min-gap stop (gap 6.2)] 31/31 hit PRT_flywheel, 0 stalls, at tilt -3 / 0 / 22.5 / 45 / 46;
    flattest 62.8 / 64.7 / 56.8 / 34.3 / 33.3.
  - [drop: v2-A2-01 drop at the thumbwheel max (gap 7.0)] 31/31, 0 stalls; flattest 62.8 / 64.7 / 57.0 / 34.5 / 33.5.
  - `PIV_nip_lift` is `home_only_ok` in all three drop tests, reason in the row: the leaf lifts only while a candy is in the nip.
  - `cad q dist PRT_hood PRT_nip_stop --pose PIV_hood=0.327143` 0.000; `cad q dist PRT_nip_stop_sleeve PRT_nip_wheel --pose
    PIV_hood=-0.558139` 0.000; `cad q dist PRT_nip_wheel PRT_nip_cover --pose PIV_nip_lift=-1.493` 1.128 (A2 0.83).
  - Section `sec_nip_stop_x19.75_hood+0.327.png`.
- **A2-02 lead lengths and pan slack.** `cable_leads` in checks.json = `params.CABLE_LEADS`, passed to all 14 `A.cable`.
  - [cables] path / lead: usb 89.6/1000, 12v_in 119.4/200, 12v_mg 45.2/100, 12v_ctrl 168.8/250, uart 213.8/300, bus_pan 290.5/300,
    launcher_base 164.8/250, launcher_bundle 265.4/350, bus_tilt 217.9/300, phase_0/1/2 62.4/80, encoder 84.1/150, bus_feeder 325.5/500.
  - [distances: v2-A2-02 the launcher lead reaches the MotorGo] 0.722 (<= 3.0).
  - [distances: v2-A2-02 bundle and base lead meet on the pan axis] 0.008 / 0.028 / 0.008 (<= 1.0) at pan -90 / 0 / +90.
  - Loops (manifest `parts.<CAB>.loop`): CAB_launcher_base 69.3 vs a 17.9 chord (+51.4), CAB_bus_pan 127.1 vs 67.2 (+59.9), both
    >= `PAN_LOOP_ADD` 45 (asserted).
- **A2-03 finger access.** R8.5 scallop cut from the guard shelf beside the slot.
  - [distances: v2-A2-03 thumbwheel rim crest on the finger approach line] 24.511 (24.0..25.0).
  - [distances: v2-A2-03 R8 fingertip clears the guard shelf at u -4.5 / -6 / -8] 25.578 / 25.032 / 23.634 (>= 24.9 / 24.4 / 22.7;
    A2 shelf at 10.0 + 11.29).
  - `cad q ray 19.5,-2.33,111.274 0,-0.316,0.949` -> PRT_nip_wheel at 14.4 (tilt 0); `cad q ray 19.5,77.315,143.401 0,-0.895,0.445
    --pose PIV_tilt=45` -> PRT_nip_wheel at 14.4. Section `sec_x19p5_finger_scallop.png`.
- **A2-04 config gaps.**
  - assembly_order: `PRT_nip_stop_sleeve` in 6e, `FST_valve_*` and the detent clip in 12, `BUY_battery` in 14; 10a reads "M2 x 8".
    `unordered_solids_assumed_present` [].
  - [flexures: nip leaf spring] 2.2 deg to the bed, 30.7 MPa in the layer plane (row passes: the beam lies in the bed plane).
  - Nip rays are in the PIV_hood frame (rows above); [distances: v2-A2-04 jam lift at the thumbwheel max] 8.461 (8.0..8.7).
  - [fits: v2-A2-04 PRT_hood x PRT_nip_wheel] min_clearance 0.5 instead of contact: 3.694 at the closest swept pose.
  - [fits: v2-A2-04 PRT_base_shell x PRT_turntable] `contact_normal` [0, 0, 1] with min 0.1: the R20/R20.3 journal now measures
    0.258 at pan 15 (A2: hidden by `contact: true`).
- **A2-05 drop margin at +46.** Closed by A2-01: flattest 33.3 (gap 6.2) and 33.5 (gap 7.0) at tilt 46, against 28 + 5.
- **A1-03 pocket (A2 PARTIAL).** `POCKET_D` 14.4 -> 13.9.
  - [distances: v2-A2-A1-03 pocket diameter along y / x at z 267.3 and 269.3] 13.90 x 4 (13.8..14.0).
  - [stacks: pocket over outlet at fire, limit (16 - 13.9) / 2] 0.67 vs 1.05 (RSS 0.37).
  - Lentil probe (`tools/lentil_probe.py`, sizes from `MM_D` / `MM_T`): edge-on 12.5 x 6.3 pair -0.013 mm3 each (overlap, cannot
    seat); flat 13.5 x 7.5 +0.198 (clears). The plan's >= 0.3 mm3 target is not met: 0.3 mm3 needs R <= 6.835, which gives the flat
    13.5 candy 0.085 and fails the 13.8 ray rows. Section `sec_pocket_y18.19_lentil_pair.png`.
- **A1-08 thin walls and overhang (A2 PARTIAL).** launcher_body 1.12 -> no thin samples (the `FST_nipcover_*` pilots end 0.5 past
  the screw tips, `NIPCOVER_PILOT_OVER`); nip_cover overhang 171 -> 19.5 mm2 (no warn), min wall 1.35 -> 1.48. Every remaining
  parts warn is located and accepted with its reason (below).
- **A1-09 gate detent (A2 PARTIAL).** `PRT_gate_detent`, a flat-printed clip on the +Y cheek with `FST_detent_0` (M3 x 9 pan ST).
  - [distances: v2-A2-A1-09 detent clip bump seated in the gate's closed notch] 0.10 (<= 0.15).
  - [flexures: gate detent clip] 0.0 deg to the bed, 16.1 MPa (`GATE_DETENT_STRESS`).
  - [slide: v2-A1-09/A2 gate opens +X 52] not blocked, min 0.35 to PRT_jar_adapter, clip ignored in the sweep (a detent overlaps its
    track mid-travel by design; the flexures row covers it).
  - [slide: v2-A2 feeder lobe cover lifts +Z] not blocked (0.00 is the seat); with the `FST_fhorn_ctr` op's `"pose": {}` it proves the
    lobe-cover removal.
- **Unchanged rows still pass:** drop outlet_to_descending_rear_tape 31/31 at tilt 0..46 (flattest 33.3 at 46); index +60 window
  [50, 60], -60 [-60, -50], column never open incl. jar drift 5/10/15; battery slide min 1.60; spout to pod 2.705 at 46; wheel to
  guard 1.594; magnet stack 0.30 vs 0.30; jar band stack 2.4 vs 3.0.

### Stability
- [stability] worst 31.2 deg over 1728 poses (feeder -60, hood -0.558, jar 0, nip_lift -1.493, pan -90, tilt 45; 3936 g, CG (16.1,
  -13.9, 169.7), edge 102.9). The tool now samples every driver joint at lo / home / hi, so the A2 "1 pose" limit is gone.
- `blender/tools/cg_grid.py` (64 poses, reaches the -3 / +46 hard stops): worst 29.9 deg at jar 0, tilt 46, pan 180 (3936 g, CG
  (8.7, -21.4, 169.9), edge 97.6). `renders/attempt-3/cg_grid.txt`.

### Finish-step changes (warn triage)
- 26 new `accepted_warns`, each with the measurement behind it (`cad q dist` / `sweep` lines, or a probe of the cadcheck rule):
  - Parts (A1-08): beam 205 mm2 = loft-seam facets at the four R6 plan corners where the top chamfer ends, 4.0-4.5 above the bed
    (the A2 BOM's "csk cones" was wrong); feeder_cover 1.40 = idler-boss recess roof; feeder_crown 26 = the three bayonet leg floors,
    5.1 wide (inscribed circle), 26.4 is an arc's bbox; jar_valve 1.29 = roof over the `FST_valve_*` counterbores; journal_plate 1.29
    = the `FST_hinge_nut` trap floor; nacelle 39 = duct roof, inscribed 15.0; nip_cover 1.48, nip_leaf 1.51, nip_wheel 1.50 located.
  - Overtravel: 13 collide / touch warns and 3 clearance warns, all 2.5 deg past a printed stop; each accept quotes the in-range value.
  - Tilt servo slide 0.10: the four M2 x 8 horn-screw tips (x 45.5) 0.10 from the journal plate's counterbore floor (x 45.4) at rest,
    same body (PIV_tilt). After that the 12 AF key leaves its 12.3 AF socket at 0.15 per flat for 6.5 mm, then 0.72. Probe: vertex
    sweep of each slide member against PRT_journal_plate at 0..60 mm. The 0.3 clamp pocket in post_R is not involved, so opening it
    (the plan's option) would change nothing, and opening the socket would add tilt backlash.
- Two in-range clearance warns became declared `fits` instead: PRT_launcher_cover x PRT_hood 0.45 (0.50 over the whole hood range,
  `cad q sweep PIV_hood -3.06..2.83`) and PRT_nip_stop_sleeve x FST_tw_nut 0.5 (0.805 at the gap-7.0 stop).
- The PRT_hood x PRT_nip_stop fit text said "gap 5.3"; it now says 6.2 (+0.327).
- No geometry change in this step; check counts 0 F / 36 W (28 untriaged) -> 0 F / 34 W (0 untriaged).
- Renders: 12 preview renders (8-view 960 px set in `preview/`, two new sections, one re-render of the pocket section with the probe
  lenses moved into the Purchased collection so they draw), then the 1800 px final set (11) and `stl_sheet.png`.

### Not met / deferred
1. Lentil overlap target (>= 0.3 mm3) not met; conflicts with the flat 13.5 candy and the 13.8 ray rows (above). Needs calipered `MM_D` / `MM_T`.
2. `FST_detent_0` is M3 x 9, not a stock length; M3 x 10 would reach 1.0 further into the gate slot (now 0.9 off the spout). Feeder step to resolve.
3. `CAB_bus_pan` uses 290.5 of its 300 lead.
4. Plan deferrals kept: more `PIV_nip_lift` range (bay rework, review option B); `post_R x journal_plate` `contact_normal` (the 0.156
   journal audit row stays).
5. Not modelled: `FST_ctrl_*`, the bayonet detent nub, the open-gate interlock.
6. Confirm with calipers: `MM_D` / `MM_T` (20 candies), `JAR_*`, `MG_HOLE_D` and the J6/J8 pad position, `ADAPTER_HOLE_INSET`,
   `BATT_STEM_INSET`, `BUCK_HOLE_Y`, `CTRL_SW` / `CTRL_TB`.

## Attempt 4

Result: **cadcheck 0 fails / 43 warns, 0 untriaged, 0 stale accepts** (`renders/attempt-4/cadcheck.json`, tools a20a4d7,
generated 2026-10-25 07:10, 150 s, full run). `assembly.unordered_solids_assumed_present` is `[]`. Per-step history is in
`renders/attempt-4/progress.md` (checks, params, launcher, feeder detent, feeder coupon, cables, finish). Rows added in attempt 4
are tagged `v2-A3-NN` (the review-3 item they close). The precheck of these rows on the attempt-3 model gave 7 F / 13 W
(`renders/attempt-4/precheck_a3_model.json`): every fail was a planned change (hard-stop rays x2, pocket rays x4, hood-body at
-2.19 x1), so the rows catch the A3 geometry they were written for.

### Coverage and not_checked (quoted from cadcheck.json)
- **coverage:**
  - parts: 36 printed objects (36 unique STLs): manifold, bed fit ['P1S', 'H2D'], overhang, wall probe, bed contact.
  - interference/clearance: 175 objects in ['Printed', 'Purchased', 'Fasteners', 'Cables'], 4727 pair-pose tests, joints swept
    ['PIV_feeder', 'PIV_flywheel', 'PIV_hood', 'PIV_jar', 'PIV_nip_lift', 'PIV_pan', 'PIV_tilt'] with 2.5 deg overtravel.
  - fasteners: 103 screws, 4 nuts; access at 15 poses, parts present per assembly_order (29 steps).
  - service: 8 ops, 26 screw accesses. drop: 4 tests. index: 6 tests. slide: 12 sweeps. payload: 4 payload-fit probes (rigid
    probe, no settling). sightlines: 3 first-hit ray rows. assembly: 29 steps, 175 objects placed, 0 in no step. stacks: 3.
    flexures: 2. stability: 1728 poses. cables: 14 routes, 14 with path length, exposure at home. (`distances`: 62 rows, all pass.)
- **not_checked (verbatim):**
  - "fasteners: pilot/clearance hole diameters (use cadlib.features for those); wrench access to nuts"
  - "stability: dynamic loads (recoil, pan acceleration), friction/sliding"
  - "cables: bend radius, slack across joints, connector positions (review by section render)"
  - "not geometric: teardown step count, alignment-jig datums (declare stacks), aesthetics, BOM correctness"

### v2-A3 rows -> value (closes review 3)
- **A2-01 leaf runs out of travel before the declared max candy passes (major).** params: `LEAF_TRAVEL` 1.5 -> 2.2, `LEAF_T`
  2.5 -> 2.3, `LEAF_PRE` 1.2 kept; cover roof `SHELL_U0` 11.0 -> 11.5; `PIV_nip_lift` lo -1.493 -> -2.190, `HOOD_LO` -2.051 ->
  -2.748; `NIP_PASS` = `MM_T[1]` + `TAPE_T` = 8.0, asserted `HOOD_GAP_LIFT` 8.181 >= 8.1.
  - [distances: v2-A3-A2-01 bare gap at FULL leaf lift, min 8.0] 8.282 / 8.593 / 8.782 / 9.124 at hood +0.327 / 0 / -0.2 / -0.558,
    lift -2.19 (A3 7.613 / 7.928 / - / 8.461; predicted from gap_bdc 8.181 / 8.479 / 8.662 / 8.991, the ray reads about 0.1 over).
  - [distances: v2-A3-A2-01 BOM claim "a jam lifts the hood to gap ~9.0"] 9.124 (8.8..9.3) at hood -0.558, lift -2.19.
  - [distances: v2-A3-A2-01 hard stop, thumbwheel top to cover roof along the stud] 4.288 (4.2..4.4) at lift -2.19; [same ray at
    home] 6.500 (6.4..6.6). Travel 2.2 = 6.5 - 4.3 (pad 2.0 + strip 2.3). The ray origin moved +1.5 along U in the launcher step (it
    sat inside the lifted thumbwheel and read 9.29).
  - [distances: v2-A3-A2-01 fix step 3, hood to body at the static max] 0.54 at hood -0.558 with lift 0 and with lift -2.19 (>= 0.5);
    `cad q dist PRT_hood PRT_launcher_body --pose PIV_hood=0.327143,PIV_nip_lift=-2.18977` 0.542. The derived bay (BAY_EPS from
    EPS_OPEN) was enough: no 0.5 outboard step.
  - [drop: v2-A3-A2-01 thick candy (MM_T max 7.5) drop at both hood stops] 31/31 hit PRT_flywheel, 0 stalls, at hood +0.327 and
    -0.558 x tilt -3 / 0 / 45 / 46; flattest 62.8 / 64.7 / 35.2 / 34.2 at both stops (>= 28 + 5).
  - [flexures: nip leaf spring] 2.2 deg to the bed, 35.5 MPa at the solid stop, in the layer plane (A3 30.7). `leaf_numbers`: 21.9 x
    34.0 x 2.3, 5.93 N/mm, preload 7.1 N (12.5 MPa), 20.2 N solid; thickest candy at the min stop 30.4 MPa, nominal 26.9.
  - Launcher step (progress.md): leaf fork half width 2.6 -> 4.0, so leaf x `FST_tw_nut` at lift -2.19 went 0.35 (fail) -> 1.289;
    `FST_leaf` pilot through the root block (wall min 1.49); `FST_nipcover` counterbore follows the roof (thread >= 4.2).
  - `cad q dist PRT_nip_wheel PRT_nip_cover --pose PIV_nip_lift=-2.18977` 1.143 (A3 1.128); stud tip at the 7.0 setting + full lift
    u 8.80, 2.70 under the roof plane (target >= 2.0); chute tongue at `HOOD_LO`: shingled inside the backplate, hood face 2.6
    outboard of the tongue face (`launcher_tongue_hood_lo_x22.png`).
  - Unchanged A2 rows still pass: nip ray 6.202 at +0.327, 7.007 at -0.558; hood to `PRT_nip_stop` 0.000; drops at both stops 31/31,
    flattest 33.3 / 33.5 at tilt 46.
  - Section `sec_nip_x21_hood+0.327_lift-2.19.png`.
- **A2-03 finger access (A3 FIXED; now a row type).**
  - [sightlines: v2-A3-A2-03 fingertip line reaches the thumbwheel rim first] 3/3 at home (13.75 / 14.4 / 13.75), 3/3 at tilt 45
    (same), 3/3 at nip_lift -2.19 (15.48 x 3). `FINGER_SLOT` u 7.5 -> 8.3 keeps the rim's -v edge >= 1.0 to the cover at full lift
    (1.143 above).
  - [distances: v2-A2-03 rim crest / fingertip vs shelf] 24.511; 25.160 / 24.637 / 22.999 (>= 24.9 / 24.4 / 22.7).
- **A1-03 pocket (A3 PARTIAL).** `POCKET_D` 13.9 -> 13.75.
  - [distances: v2-A3-A1-03 pocket diameter along y / x at z 267.3 and 269.3] 13.75 x 4 (13.65..13.85).
  - [payload: v2-A3-A1-03 pocket blocks an edge-on MIN pair 12.5 x 6.3, pair across x] blocked, 0.253 mm3, margin 0.06; [same,
    across y] blocked, 0.253 mm3, margin 0.06 (A3 precheck at Ø13.9: margin 0.00).
  - [payload: v2-A3-A1-03 pocket blocks an edge-on NOMINAL pair 13 x 7] blocked, 17.553 mm3, margin 0.34.
  - [payload: v2-A3-A1-03 pocket seats one flat MAX 13.5 x 7.5] fits, margin 0.14 (A3 0.20).
  - [stacks: pocket over outlet at fire, limit (16 - 13.75) / 2] 0.67 vs 1.125 (RSS 0.37).
  - Lentil probe (`tools/lentil_probe.py`): `cad q dist ZMM_pair_a PRT_feeder_disc` -0.134 mm3, `ZMM_pair_b` -0.134 (A3 -0.013),
    `ZMM_flat` +0.123 (A3 0.198). Section `sec_pocket_y18.19_lentil_pair_12.5x6.3.png`.
  - Test coupon `blender/tools/pocket_coupon.py` -> `stl/tools/test_pocket_coupon.stl`: 8 mm disc, OD 51.1, Ø13.6 / 13.75 / 13.9 /
    14.1 through pockets with the 1 x 45 rim chamfer, 1..4 rim notches as labels; bores ray 13.600 / 13.750 / 13.900 / 14.100 at
    z 1 and 6. Procedure in BOM section 8. Moved from `stl/` to `stl/tools/` in the finish step, because `cad build`
    (`export_stls clean=True`) deletes top-level `stl/*.stl`.
- **A3-01 gate detent clip.** Tab EB 1.0, plate EB 0.4 (0.6 meets in a knife edge on the 1.2 plate), R3 plan end; `FST_detent_0`
  M3 x 10 pan self-tap with the head in a Ø6.6 x 1.0 counterbore; back face 36.5 -> 38.5, screw x 7.1 -> 9.5 (the review's sink-only
  fix put the tip 0.77 mm3 into the adapter spout).
  - [distances: v2-A3-A3-01 FST_detent_0 to the gate] 2.652 (>= 2.4); [FST_detent_0 to PRT_jar_adapter] 1.142 (>= 0.5).
  - [fasteners: FST_detent_0] engagement 4.0, straight access 16. [distances: v2-A2-A1-09 detent bump seated] 0.10 (<= 0.15).
  - [flexures: gate detent clip] 0.0 deg, 16.1 MPa. Section `sec_detent_cbore_x9.5.png`.
- **A2-02 encoder lead and pan bus.** `ENC_LEAD` 550; `parts/finish.py` `encoder_budget()` writes `CAB_encoder` `lead_len` = 550 -
  265.4 (bundle) - 164.8 (base) - 5 = 114.8 after every subsystem is built, asserts it covers the route and matches checks.json
  `cable_leads` (115) within 1 mm.
  - [cables] CAB_encoder 84.1 / 114.8 (30.7 spare); CAB_bus_pan 290.5 / 350 (A3 300, 9.5 spare); bundle 265.4 / 350; base
    164.8 / 250; others unchanged; no cable findings.
  - BOM item 15: one-piece twisted 5-wire JST-SH lead >= 550, routed on the far side of the sleeve from the phases. The route inside
    the sleeve is not modelled (one route per cable).
- **A3-02 nip stud.** BOM and step 6c: M3 x 16 hex head ISO 4017 (AF 5.5 x 2.0). `manifest parts.FST_nip_stud.bom_item` carries it.
  cadlib has no hex-head spec, so the model keeps `M3_cap` x 16 (same bearing face, shank and `STUD_L`); [fasteners: FST_nip_stud]
  thread 2.4 in `FST_tw_nut`, protrusion 2.8. Section `sec_stud_hex_pocket_y4.83.png` shows the AF 5.7 pocket (three +v flats key
  the head; the -v half is the U-slot through the 26 deg back face).
- **A3-03 config gaps.**
  - [slide: v2-A3-A3-03 base floor plate with its electronics drops -Z after the 8 floor screws] members floor, partition,
    MotorGo, buck, controller and their 8 screws; 40 mm, `blocked_at_mm` null, min 0.00 (the seat), closest `PRT_base_shell`.
  - The full-lift row asserts 8.0 (A2-01 above).
  - The detent open notch has no posed row: cadlib `asm.joint` is rotary only, so the gate's +52 cannot be posed (deferred, tool).
- **Unchanged rows still pass:** drop outlet_to_descending_rear_tape 31/31 at tilt 0..46 (flattest 33.3 at 46); index +60 window
  [50, 60], -60 [-60, -50], column never open incl. jar drift 5/10/15; battery slide min 1.60; gate slide +52 min 0.35; spout to pod
  2.705 at 46; wheel to guard 1.594; magnet stack 0.30 vs 0.30; jar band stack 2.4 vs 3.0; launcher lead reaches the MotorGo 0.722;
  bundle and base meet on the pan axis 0.008 / 0.028 / 0.008.

### Stability
- [stability] worst 31.2 deg over 1728 poses (feeder -60, hood -0.558, jar 0, nip_lift -2.19, pan -90, tilt 45; 3937 g, CG (16.1,
  -13.9, 169.8), edge 102.9).
- `blender/tools/cg_grid.py` (64 poses, reaches the -3 / +46 hard stops): worst 29.9 deg at jar 0, tilt 46, pan 180 (3937 g, CG
  (8.7, -21.5, 169.9), edge 97.5). `renders/attempt-4/cg_grid.txt`.

### Finish-step changes
- `parts/finish.py` `bom_items()`: writes `bom_item` on the object and in the manifest for `FST_nip_stud`, `FST_detent_0`,
  `CAB_encoder` and `CAB_bus_pan`, so the reviewer reads the purchased item next to the modelled spec.
- checks.json label texts: the three leaf `compliant` strings read 7.1 N preload / up to 2.2 lift (they said ~9 N / 1.5); step 6c
  names the ISO 4017 stud. No row values changed.
- `tools/pocket_coupon.py` default output `stl/tools/test_pocket_coupon.stl`.
- Warns: 43 (A3 34). The 9 new ones are the a20a4d7 ray-vs-nearest rule on rows that are rays on purpose (hard stop x2, pocket
  rays x4, fingertip rows x3), accepted in the checks step. Re-triaged launcher accepts quote the -2.19 / -4.69 numbers.
- Renders: 5 preview renders at 960 px (the 4 sections above and one discarded nip framing at x 19.5); no 960 view set this time;
  the final 1800 x 1350 set (11) and `stl_sheet.png`.

### Not met / deferred
1. Detent open-notch posed row (A3-03): no prismatic joint in cadlib. The closed notch row (0.10), the review's +52 probe and the
   flexures row stand.
2. Hex-head stud pocket fit (A3-02): no hex-head fastener spec in cadlib; section only.
3. `PRT_nip_cover` manifest orient text still says "finger slot 22 x 7.5" (`parts/launcher.py` string); geometry is 22 x 8.3.
4. Static nip window 6.2..7.0 vs the rig's 5..12: waits for rig numbers.
5. `post_R x journal_plate` `contact_normal`: tool limit, the 0.156 audit row stays.
6. Physical steps for the user: caliper 20 candies (`MM_D`, `MM_T`), print the coupon, set `POCKET_D` (BOM section 8).

## Attempt 5

Result: **cadcheck 0 fails / 34 warns, 0 untriaged, 0 stale accepts** (`renders/attempt-5/cadcheck.json`, tools dea6536, full
run). `assembly.unordered_solids_assumed_present` is `[]`. `cad bom BOM_AND_ASSEMBLY.md blender/manifest.json`: 18 rows, 0
disagree. Per-step history is in `renders/attempt-5/progress.md` (checks, params, launcher-1, launcher-2, feeder, finish). Rows
added in attempt 5 are tagged `v2-A4-NN` (the review-4 item they close). The precheck of the new rows on the attempt-4 model gave
6 F / 1 W (`renders/attempt-5/precheck_a4_model.json`): all six were the A2-01 entry arc, matching the review exactly, so the rows
catch the A4 geometry they were written for.

### Coverage and not_checked (quoted from cadcheck.json)
- **coverage:**
  - parts: 36 printed objects (36 unique STLs): manifold, bed fit ['P1S', 'H2D'], overhang, wall probe, bed contact.
  - interference/clearance: 176 objects in ['Printed', 'Purchased', 'Fasteners', 'Cables'], 5122 pair-pose tests, joints swept
    ['PIV_feeder', 'PIV_flywheel', 'PIV_gate', 'PIV_hood', 'PIV_jar', 'PIV_nip_lift', 'PIV_pan', 'PIV_tilt'] with 2.5 deg overtravel.
  - fasteners: 103 screws, 4 nuts; access at 16 poses, parts present per assembly_order (29 steps).
  - service: 8 ops, 26 screw accesses. drop: 4 tests. index: 6 tests. slide: 13 sweeps. payload: 4 payload-fit probes (rigid
    probe, no settling). sightlines: 3 first-hit ray rows. assembly: 29 steps, 176 objects placed, 0 in no step. stacks: 3.
    flexures: 2. stability: 3456 poses. cables: 14 routes, 14 with path length, 2 chains; junctions on 14 routes with known ends;
    exposure at home. (`distances`: 83 rows, all pass.)
- **not_checked (verbatim):**
  - "fasteners: pilot/clearance hole diameters (use cadlib.features for those); wrench access to nuts"
  - "stability: dynamic loads (recoil, pan acceleration), friction/sliding"
  - "cables: bend radius, slack across joints, connector positions (review by section render)"
  - "not geometric: teardown step count, alignment-jig datums (declare stacks), aesthetics, BOM correctness"

### v2-A4 rows -> value (closes review 4)
- **A2-01 the nip entry arc at full leaf lift (major).**
  - params: `gap_arc(eps)` = minimum radial gap of the rotated hood profile over psi -3..112 (0.5 deg). `HOOD_GAP_LIFT` =
    gap_arc(min stop, leaf solid) = **8.105**, asserted >= `NIP_PASS` 8.0 + 0.1; `HOOD_GAP_LIFT_HOME` 8.206, `_MAX` 8.380.
    `parts/finish.py nip_numbers()` re-asserts all three and writes manifest `parts.PRT_hood.nip`.
  - Profile: the plan's `PSI_C` 78 -> 45 passed the arc (8.144 by ray) but stalled 14 drop rows (the 7.0 candy met the tape at psi
    63-66). Shipped: `GAP_PROFILE` "lift" (`LIFT_FLOOR` 8.105, `FUNNEL_PSI0` 82, `G_IN` 13); `PSI_C` 45 feeds `gap_quad` only.
    Home-pose gap_at: 6.5 to psi 45, 6.503 / 6.674 / 6.887 / 7.137 / 7.417 / 8.704 / 13.0 at psi 50 / 60 / 70 / 80 / 90 / 100 / 112
    (`cad py`, params.gap_at).
  - [distances: v2-A4-A2-01 bare gap at FULL leaf lift on the candy's ENTRY ARC, min 8.0], lift -2.19 (`=-HOOD_LEAF_LIFT`), frame
    PIV_tilt, radial ray through R38:

    | psi | min stop (+0.327) | home (0) | max stop (-0.558) |
    |---|---|---|---|
    | 50 | 8.117 | 8.400 | 8.884 |
    | 55 | 8.105 | 8.373 | 8.832 |
    | 60 | 8.110 | 8.361 | 8.791 |
    | 70 | 8.105 | 8.319 | 8.684 |
    | 80 | 8.107 | 8.277 | 8.566 |

    (A4 7.94 / 7.72 / 7.50 at psi 60 / 70 / 80 at the min stop.)
  - BDC rows unchanged: [distances: v2-A3-A2-01 bare gap at FULL leaf lift] 8.282 / 8.592 / 8.781 / 9.123; jam 9.124 (8.8..9.3);
    hard stop 4.288 (4.2..4.4), home 6.500 (6.4..6.6); nip rays 6.202 (min stop) / 7.007 (max stop) / 6.493 (home).
  - Drops (tape now `BUY_tape`, R35..35.5; targets [PRT_flywheel, BUY_tape]): [drop: outlet_to_descending_rear_tape] 31/31 at tilt
    0 / 15 / 22.5 / 30 / 40 / 45 / 46, flattest 64.7 / 65.5 / 58 / 50.5 / 40.5 / 35.5 / 34.5; [drop: v2-A2-01/A2-05 min-gap stop]
    and [drop: v2-A2-01 thumbwheel max] 31/31 at tilt -3 / 0 / 22.5 / 45 / 46, flattest 62.8 / 64.7 / 58 / 35.5 / 34.5; [drop:
    v2-A3-A2-01 thick candy] 31/31 at both stops x tilt -3 / 0 / 45 / 46, flattest 34.5. Flattest anywhere 34.5 (>= 33).
  - Hood: [distances: hood keeps 0.5 to the body] 0.54 at +0.327, 0.541 at +1.327; [hood never nears the wheel] 4.723 at +1.327;
    [v2-A3-A2-01 fix step 3] 0.54 at -0.558 lift 0, 0.532 at -0.558 lift -2.19. Accepted overtravel: hood to tape 0.79 only at hood
    +2.83 with lift +2.5; 5.674 at +0.327 and 4.698 at +1.327 (cad q dist, launcher-2).
  - Section `renders/attempt-5/sec_nip_x21_minstop_fulllift_lentil13x7.5_psi50_80.png` (pose PIV_hood 0.327143, PIV_nip_lift
    -2.18977; script `/tmp/finish_a5/sec_nip.py`, cadlib `R.marker_lentil(d=13, t=7.5)` centred on R39.25 = tape + 3.75 at psi 50
    (21, 6.933, 144.771) and psi 80 (21, -1.654, 163.184), thin axis radial). BVH nearest: marker to `PRT_hood` 0.113 (psi 50) /
    0.100 (psi 80), to `BUY_tape` 0.004 / 0.007, 0 overlapping triangles. The 7.5 candy passes the solid leaf with about 0.1 on
    each side of the arc minimum, as the rays say (8.117 / 8.107 - 8.0).
- **A4-01 detent tab (minor).** Feeder step: one planar 45 deg chamfer across the tab top (fall line radial through the screw
  axis x 9.5), EB 1.0 on its edges; back face y 38.5 -> 39.9, counterbore Ø6.6 x 1.0 -> 2.4, bearing face y 37.5, tip y 27.5.
  - [distances: v2-A4-01 band to detent] 0.322 (>= 0.3; A4 step 0.5).
  - `cad q list FST_detent_0`: bbox y 27.5..39.9, back face 39.9: head flush (stand-off 0). [fasteners: FST_detent_0] engagement 4.0.
  - [distances: FST_detent_0-PRT_jar_gate] 2.652 at home / gate 0, 14.867 at gate 52 (>= 2.4); [FST_detent_0-PRT_jar_adapter]
    1.142 (>= 0.5).
  - Wall accept: `PRT_gate_detent` 66 samples, min 1.18, all on the 1.2 plate (A4 55).
  - Section `renders/attempt-5/sec_detent_tab_x9.5.png` (`cad q section x 9.5 ... 400,33,295 34`): chamfer under the band lip,
    head flush in the counterbore, shank into the valve cheek, tip above the blade.
- **A4-02 BOM / manifest numbers (minor).**
  - `launcher_geom.leaf_numbers()["operating"]` (manifest `parts.PRT_nip_leaf.notes` and `.operating`): lift fraction of 2.2 /
    root stress at which gap_arc reaches candy + tape: min stop 0.68 / 28.1 MPa (nominal 7.0), 0.94 / 34.2 (thickest 7.5); home
    0.53 / 24.7, 0.79 / 30.8; max stop 0.27 / 18.8, 0.54 / 24.9; solid 35.5 [flexures: PRT_nip_leaf 35.5 MPa, 2.2 deg]. (The
    launcher-2 progress line quoted 27.8 / 34.2 from a probe; the build's numbers above are the ones in the manifest and BOM.)
  - `PRT_nip_cover` orient text from `P.FINGER_SLOT`: manifest reads "finger slot 22 x 8.3".
  - BOM: `NIP_PASS` asserted over `gap_arc`, the entry-arc table, the operating-stress table, the rig-feedback note (the rig
    backplate takes the lift-matched `gap_at` table, not `PSI_C` 45), `FST_nip_stud` `M3_hex`.
- **A3-02 tool-limit deferral (stud).** `FST_nip_stud` spec `M3_cap` -> `M3_hex` x 16 (`STUD_POCKET_D` 3.2 -> 2.2, `STUD_SPOT_D`
  0.6 so the +v flats key the hex). [fasteners: FST_nip_stud] stand-off 0, engagement 2.4 in `FST_tw_nut`; hood pocket fit 0.1
  (cad q, launcher-2).
- **Gate open state (A3-03 / A4 tool-limit deferral).** `PIV_gate` prismatic +X under PIV_jar, 0..52, home 0.
  - [distances: v2-A4 detent bump seated in the open notch] 0.10 at gate 52 (<= 0.15); closed notch 0.10.
  - [distances: v2-A4 hard stop] lug to `PRT_jar_adapter` 0.000 at 52.35; blade to `PRT_jar_valve` 0.000 at -0.4 (max 0.1).
  - [slide: v2-A1-09/A2 gate opens +X 52] min 0.08, closest `PRT_gate_detent` (flex, <= 1.0 mm3; `flexed` {} below vol_tol 0.5).
  - [slide: v2-A4 gate open stop] blocked at 52.5 by `PRT_jar_adapter` (expect blocked, 52.0..53.0).
  - [fits] `PRT_jar_valve` > `PRT_jar_gate` 0.35 at gate 0, `PRT_jar_adapter` > `PRT_jar_gate` 0.35 at gate 52 (min 0.3).
  - Accepted overtravel: gate 53 (adapter, open stop), gate -1 (valve, closed stop).
- **A2-02 encoder lead (tool now has cable_chains).** [cables.chains: encoder signal (BOM item 15)] 514.3 / 545 (`=ENC_LEAD - 5`).
  `finish.py` still writes `CAB_encoder` lead_len 114.8 (path 84.1).
- **Sightlines** [v2-A3-A2-03 fingertip line] 3/3 at home (13.75 / 14.4 / 13.75), tilt 45 (same), nip_lift -2.19 (14.58 / 14.84 /
  14.58); origins moved +0.25 along U with NIP_E. Finger rows: rim crest 24.511 (24.0..25.0); shelf 25.160 / 24.637 / 22.999 (>=
  24.9 / 24.4 / 22.7).
- **Unchanged rows still pass:** payload_fit margins 0.06 / 0.06 / 0.34 / 0.14; pocket rays 13.75 x 4; index windows; battery
  slide 1.60; flywheel off 1.59; spout to pod 3.009 / 3.0 / 4.524 / 2.985 / 2.705 at tilt -3 / 0 / 22.5 / 45 / 46; wheel to guard
  1.594; stacks 0.30 / 0.30, 2.4 / 3.0, 0.67 / 1.125; launcher lead to the MotorGo 0.722; bundle and base meet on the pan axis
  0.008 / 0.028 / 0.008.

### Stability
- [stability] worst 31.2 deg over 3456 poses (feeder -60, hood -0.558, jar 0, nip_lift -2.19, pan -90, tilt 45, gate 0; 3940 g,
  CG (16.1, -13.9, 169.8), edge 102.9).
- `blender/tools/cg_grid.py` (64 poses, reaches the -3 / +46 hard stops): worst 29.9 deg at jar 0, tilt 46, pan 180 (3940 g, CG
  (8.7, -21.5, 169.9), edge 97.5). `renders/attempt-5/cg_grid.txt`.

### Finish-step changes
- `parts/finish.py`: `nip_numbers()` (entry-arc assert at 3 settings, manifest `PRT_hood.nip` and `PRT_nip_leaf.operating`, two
  FINISH lines in the build log); `BOM_ITEM` texts for `FST_nip_stud` (M3_hex), `FST_detent_0` (2.4 counterbore, flush) and
  `CAB_bus_tilt` / `CAB_bus_feeder` (new), `CAB_bus_pan` (hub-end junction).
- checks.json:
  - 6 stale accepts removed (flywheel / feeder_crown / nacelle bridges, three ray-gap rows): dea6536 no longer raises them.
  - The pin's new junction rule warned (untriaged) on the pan-axis point (0, 0, 76), where all five hub-crossing routes end. Triage:
    `cable_junctions_ok` += `CAB_bus_*` (the three bus leads end in one 3-way bus junction, new BOM item 14a; the bus x launcher
    pairs are different conductors drawn to the same axis point), and a second `cable_chains` row, phase conductors
    `CAB_phase_2` + bundle + base = 492.7 / 700 (BOM item 13: one 16 AWG wire per phase, unspliced at the hub). The
    bundle / base pair is in both chains.
  - `_about` notes attempt 5 (prismatic gate, junction triage); the five entry-arc rows' `why` text names the shipped lift-matched
    profile (it still said "PSI_C 45 ... 8.14"). No row values changed.
- Renders: 2 preview sections at 960 px (nip x 21 with 13 x 7.5 markers at psi 50 / 80; detent tab x 9.5); the final 1800 x 1350
  set (11: iso, iso_front_left, front, side, top, rear, pan-90_tilt0, pan+90_tilt45, tilt45, jar_unlocked, exploded);
  `stl_sheet.png`; `cg_grid.txt`.
- Warns: 34 (A4 43): 12 thin walls, 1 overhang, 19 overtravel (12 collide, 2 touch, 5 clearance; +2 for the gate stops, +1 hood to
  tape), 1 fastener, 1 slide. The A4 bridge (3) and ray-vs-nearest (9) warns no longer fire under dea6536.

### Not met / deferred
1. Bus junction (BOM item 14a) is a triage decision made in the finish step, not a modelled part. It needs the user's choice
   (3-way splice / hub board in the hub bore, or a daisy chain through the tilt servo) and a size check in the R14 bore.
2. Static nip window 6.2..7.0 vs the rig's 5..12: waits for rig numbers. With the hood on a hinge at psi 112, the static-max rest
   gap is tied to the min-stop full-lift gap by a fixed turn (params step), so a wider window costs entry-arc margin.
3. `post_R x journal_plate` `contact_normal`: tool limit, the 0.156 audit row stays.
4. Wafer- or button-head detent screw: no cadlib spec; the 2.4 counterbore makes the pan head flush instead.
5. Physical steps for the user: caliper 20 candies (`MM_D`, `MM_T`), print the coupon, set `POCKET_D` (BOM section 8).

## Attempt 6

Result: **cadcheck 0 fails / 35 warns, 0 untriaged, 0 stale accepts, `poses_past_limits` []** (`renders/attempt-6/cadcheck.json`,
tools 36189b8, full run, 167 s). `assembly.unordered_solids_assumed_present` is `[]`. `cad bom BOM_AND_ASSEMBLY.md
blender/manifest.json`: 18 rows, 0 disagree, 0 modelled screws in no row. Per-step history is in `renders/attempt-6/progress.md`
(checks, feeder, pan_stage + base, finish). Rows added in attempt 6 are tagged `v2-A5-NN` (the review-5 item they close). The
precheck of the new rows on the A5 model gave 5 F (`renders/attempt-6/precheck_a5_model.json`): band to detent 0.322 (A5-01) and
four `BUY_bus_junction` rows with no object (A5-03). The swept rows reproduced review 5 exactly (8.099 at psi 90).

### Coverage and not_checked (quoted from cadcheck.json)
- **coverage:**
  - parts: 36 printed objects (36 unique STLs): manifold, bed fit ['P1S', 'H2D'], overhang, wall probe, bed contact.
  - interference/clearance: 177 objects in ['Printed', 'Purchased', 'Fasteners', 'Cables'], 5126 pair-pose tests, joints swept
    ['PIV_feeder', 'PIV_flywheel', 'PIV_gate', 'PIV_hood', 'PIV_jar', 'PIV_nip_lift', 'PIV_pan', 'PIV_tilt'] with 2.5 deg overtravel.
  - fasteners: 103 screws, 4 nuts; access at 16 poses, parts present per assembly_order (29 steps).
  - service: 8 ops, 26 screw accesses. drop: 4 tests. index: 6 tests. slide: 13 sweeps. payload: 4 payload-fit probes.
    sightlines: 3 first-hit ray rows. assembly: 29 steps, 177 objects placed, 0 in no step. stacks: 4. flexures: 2. stability:
    3456 poses. cables: 14 routes, 14 with path length, 2 chains; junctions on 14 routes with known ends; exposure at home.
    (`distances`: 83 row-poses, all pass.)
- **not_checked (verbatim):**
  - "fasteners: pilot/clearance hole diameters (use cadlib.features for those); wrench access to nuts"
  - "stability: dynamic loads (recoil, pan acceleration), friction/sliding"
  - "cables: bend radius, slack across joints, connector positions (review by section render)"
  - "not geometric: teardown step count, alignment-jig datums (declare stacks), aesthetics, BOM correctness"

### v2-A5 rows -> value (closes review 5)
- **A5-01 detent tab under the jar band (major).** `GATE_DETENT` `tab_z1` 301.5 -> 299.5, chamfer deleted, flat top with EB 1.0;
  the tab is a 6-chord plan prism (A5's n=768 cylinder cut clamped every tab EB to about 0.1).
  - [distances: v2-A5-01 BUY_jar_band > PRT_gate_detent, min 1.0] **1.000** (A5 0.322); `cad q dist` 1.0 at (4.8, 36.44, 300.5).
  - [stacks: v2-A5-01 jar band lip over the capped detent tab] worst case 0.8, RSS 0.418, limit 1.0.
  - [fasteners: FST_detent_0] engagement 4.0, stand-off 0; `cad q list FST_detent_0` bbox y 27.5..39.9 (back face 39.9: flush).
  - [distances: FST_detent_0 > PRT_jar_gate] 2.652 at gate 0, 14.867 at gate 52 (>= 2.4); [> PRT_jar_adapter] 1.142 (>= 0.5).
  - [distances: detent bump seated] 0.10 at gate 0 and at gate 52 (<= 0.15).
  - Wall accept `PRT_gate_detent: 64 wall samples` (min 1.20, all on the 1.2 plate; A5 66). Counterbore rim at x 9.5: top z 297.8,
    1.65..1.7 under the flat top, 0.7 at the back-face edge (feeder step `cad q ray` lines in the accept).
  - Sections `renders/attempt-6/sec_detent_tab_x9.5_band.png` (band in view) and `sec_detent_tab_x9.5_feeder_step.png`.
- **A5-02 entry-arc margin and the tape seam (minor).** Five point rows (psi 50..80 x 3) -> three swept rows, psi 0..104 step 2,
  at hood +0.327 / 0 / -0.558, leaf solid (lift -2.19) for the first two:

  | Row (min) | min stop +0.327 | home 0 | max stop -0.558 |
  |---|---|---|---|
  | bare gap at full lift (`NIP_PASS` 8.0) | **8.099 @ psi 90** | 8.211 @ 92 | 8.397 @ 92 |
  | hood to `BUY_tape` at full lift (`MM_T[1]` 7.5) | **7.599 @ 90** | 7.711 @ 92 | 7.897 @ 92 |
  | rest gap, leaf at rest (`HOOD_GAP_MIN` - 0.1 = 6.1) | 6.176 @ 18 | 6.493 @ 0 | 6.987 @ 50 |

  Min-stop full-lift profile: 8.169 (psi 0), 8.325 (24), 8.241 (40), 8.117 (50), 8.105 (54), 8.110 (60), 8.105 (70), 8.107 (80),
  8.102 (88), 8.099 (90), 8.101 (92), 8.183 (94), 8.426 (96), 9.198 (100), 10.219 (104). `gap_arc` (analytic) reads 8.105 /
  8.206 / 8.380 (FINISH line); the mesh ray is 0.006 lower at the min stop. At home and max the psi 0 station reports no hit
  (`missed_deg [0]`, not investigated), so those minima come from psi 2..104; the min stop has all 53 stations.
  - BOM: 6f butt-joins the tape with no overlap and calipers it <= 0.5; item 12 repeats it; section 8 adds the rule "calipered
    `MM_T` max over 7.3 -> run at home or above" (min-stop margin 0.099 at psi 90; home 0.211; a 7.3 candy at the min stop 0.299).
  - Geometry margin not added (deferred, as planned): +2.4 leaf travel would add about 0.07 for +2 MPa (review A5).
- **A5-03 bus junction (minor).** `BUY_bus_junction`, Ø10 x 25 envelope on `PIV_pan`, (5.73, 4.02) z 74..99 (`params.BUS_JCT`),
  8 g (`masses_g`), assembly step 10d; `bom_item` written by `finish.py` from `BUS_JCT`.
  - [distances: v2-A5-03] to `PRT_turntable` 1.945, `PRT_hub_gear` 1.000 (`cad q dist` 1.0 at (10.69, 7.4, 82.5)),
    `CAB_launcher_bundle` 2.846 (all >= 1.0); to `CAB_launcher_base` 3.548 / 5.130 / 4.206 at pan -90 / 0 / 90 (>= 1.0).
  - [interference.min_clearance] junction to `CAB_launcher_base` 3.536 at pan -92.5 (overtravel), to `PRT_base_shell` 8.264, to
    `PRT_pan_pinion` 13.625.
  - Cables: 0 junction warns (`cables.junctions` []); `cable_junctions_ok` = [`CAB_phase_*`]. Bus routes 287.7 / 206.5 / 319.6 of
    350 / 300 / 500. Chains: encoder 511.8 / 545, phases 490.2 / 700. `CAB_encoder` budget 117.2 (path 84.1). Loops:
    `CAB_bus_pan` +61.1, `CAB_launcher_base` +50.3 (>= 45). Bundle/base meet 0.133 / 0.002 / 0.097 at pan -90 / 0 / 90 (<= 1.0).
  - Section `renders/attempt-6/sec_hub_bore_z88_bus_junction.png`.
- **A5-04 leaf creep (minor).** BOM: print 2 leaves (one spare, 3.1 g each by the cadcheck estimate; review said 1 g); preload
  log on day 0 and after 1 week (lift-start force, 7.1 N nominal, and free set against the unused spare, `LEAF_PRE` 1.2), and
  `LEAF_L` 34 -> 40 (x0.72 stress) if either drops by more than about 10 %. Not modelled; the cover length is unchecked for 40.
  [flexures: PRT_nip_leaf] 35.5 MPa at solid, 2.2 deg to the bed (unchanged).
- **A5-05 drift (minor).**
  - Item 12: 1 in (25 mm) cloth hockey tape trimmed to the 13.8 land; `cad q list BUY_tape` x 14.1..27.9 (13.8), unchanged, so
    the drops are unchanged: [drop] 31/31 at every row (4 tests: 7 tilts, both stops x 5 tilts, thick candy at both stops x 4
    tilts), flattest 34.5 at tilt 46 (>= 33); `first_hit` `BUY_tape` 23..27, `PRT_flywheel` 4..8.
  - `side.png` (and `front.png`) re-framed by `finish.elevations()`: z 0.0..432.6 in a 467.2 tall window (ortho 622.9), 17.3
    margin above the jar top and under the base. A5's view_set window was 0.94 x the height (ortho 1.25 x 432.6 at 4:3 = 405.6).
- **A5-06 detent x gate (minor).** The `allow` is deleted; `fits` rule detent x gate, contact accepted on faces within 20 deg of Z,
  `min_clearance` 0.05: [interference.min_clearance PRT_jar_gate > PRT_gate_detent] 0.10 at gate 39. [slide: gate opens +X 52] min
  0.08, `flexed` {}. Accepted touch only at gate -1 (past the -0.4 closed stop).

### Stability
- [stability] worst 31.2 deg over 3456 poses (feeder -60, hood -0.558, jar 0, nip_lift -2.19, pan -90, tilt 45, gate 0; 3948 g,
  CG (16.1, -13.8, 169.6), edge 102.9).
- `blender/tools/cg_grid.py` (64 poses, tilt -3 / 46): worst 29.9 deg at jar 0, tilt 46, pan 180 (3948 g, CG (8.6, -21.4, 169.8),
  edge 97.6). `renders/attempt-6/cg_grid.txt`.

### Finish-step changes
- `parts/finish.py`: `BOM_ITEM` text for `CAB_bus_pan` / `CAB_bus_tilt` / `CAB_bus_feeder` (plug cut off, which face of the junction
  each enters); `BUY_bus_junction` text built from `params.BUS_JCT` in `bom_items(P)`; `elevations(outdir)` re-renders front and
  side fitted to the scene bounds + 8 % (`ELEV_MARGIN` 1.08). `build_assembly.py` calls it right after `render.view_set`.
- BOM_AND_ASSEMBLY.md: attempt 6 evidence; section 0 quotes the swept profiles in place of the 15 point rays, plus the leaf
  creep note; item 12 (1 in tape, trimmed, butt-joined, <= 0.5), 13/14/15 numbers, 14a modelled; U-loop text with the off-axis
  meeting point; printed parts: gate_detent (flat top, 1.5 g) and 2 x nip_leaf; steps 3, 6f (tape), 10d (junction); refill row
  cites the v2-A5-06 fits rule; section 6 renders; section 7 warns 35; section 8 resolved list and the thickest-candy rule.
- Renders (`renders/attempt-6/`): 2 sections at 960 px (`sec_detent_tab_x9.5_band`, `sec_hub_bore_z88_bus_junction`); the final
  1800 x 1350 set (iso, iso_front_left, front, side, top, rear, pan-90_tilt0, pan+90_tilt45, tilt45, jar_unlocked, exploded,
  with front and side re-framed); `stl_sheet.png`; `cg_grid.txt`.
- Warns 35 (A5 34): 12 thin walls, 1 overhang, 20 overtravel (12 collide, 3 touch, 5 clearance; +1 the detent touch at gate -1,
  now visible because the allow is gone), 1 fastener, 1 slide.

### Not met / deferred
1. `LEAF_L` 34 -> 40 (A5-04) waits on the rig preload log; the 40 leaf and its cover are not modelled.
2. More entry-arc margin by geometry (A5-02): the BOM's thickest-candy rule stands in for it; raising the lift floor broke the
   max-setting drops in A5.
3. Static nip window 6.2..7.0 vs the rig's 5..12: waits for rig numbers.
4. `post_R x journal_plate` `contact_normal`: tool limit, the 0.156 audit row stays.
5. Physical steps for the user: caliper 20 candies (`MM_T`, `MM_D`), print the pocket coupon, caliper the tape, log the leaf
   preload (BOM section 8).
6. psi 0 station of the swept full-lift rows reports `missed_deg [0]` at home and at the max stop, so those minima come from
   psi 2..104 (logged above, not investigated; launcher/checks scope).

### Close-out
- checks.json text only: `_about` gains an Attempt 6 note (BUY_bus_junction modelled, CAB_bus_* out of `cable_junctions_ok`,
  bundle/base point at (-2.29, -3.28, 70)); the v2-A2-02 and phase-chain `why` strings no longer say "on the pan axis". No row
  changed. Final `cad check` (renders/attempt-6/cadcheck.json, generated 10:09:27): PASS 0 fail, 35 warn (0 untriaged), stale
  accepts [], poses past limits [], 167.2 s.
- Coverage (cadcheck.json `coverage`): 36 printed objects; 177 objects, 5126 pair-pose tests over 8 joints with 2.5 deg
  overtravel; 103 screws / 4 nuts at 16 poses over 29 assembly steps; 8 service ops / 26 accesses; 4 drop, 6 index, 13 slide,
  4 payload, 3 sightline rows; 4 stacks; 2 flexures; stability over 3456 poses; 14 cable routes, 2 chains.
- Not checked (cadcheck.json `not_checked`): pilot/clearance hole diameters and wrench access to nuts; dynamic loads and
  friction/sliding; cable bend radius, slack across joints and connector positions; teardown step count, alignment-jig datums,
  aesthetics, BOM correctness.

## Attempt 7

Result: **cadcheck 0 fails / 37 warns, 0 untriaged, 0 stale accepts, `poses_past_limits` []** (`renders/attempt-7/cadcheck.json`,
tools 6025133, full run, generated 2026-10-25 10:56:59, 184 s). `cad bom BOM_AND_ASSEMBLY.md blender/manifest.json`: 18 rows,
0 disagree, 0 modelled screws in no row. Per-step history is in `renders/attempt-7/progress.md` (checks, pan_stage groove cap
step, base + pan_stage pan-lead tail, finish). Rows added in attempt 7 are tagged `v2-A6-NN` (the review-6 item they close). The
precheck on the A6 model (`renders/attempt-7/precheck_a6_model.json`) gave 4 F, all "CAB_bus_pan_tail not in the scene".

### Coverage and not_checked (quoted from cadcheck.json)
- **coverage:**
  - parts: 36 printed objects (36 unique STLs): manifold, bed fit ['P1S', 'H2D'], overhang, wall probe, bed contact.
  - interference/clearance: 178 objects in ['Printed', 'Purchased', 'Fasteners', 'Cables'], 5046 pair-pose tests, joints swept
    ['PIV_feeder', 'PIV_flywheel', 'PIV_gate', 'PIV_hood', 'PIV_jar', 'PIV_nip_lift', 'PIV_pan', 'PIV_tilt'] with 2.5 deg overtravel.
  - fasteners: 103 screws, 4 nuts; access at 16 poses, parts present per assembly_order (30 steps).
  - service: 9 ops, 32 screw accesses. drop: 4 tests. index: 6 tests. slide: 16 sweeps. payload: 4 payload-fit probes.
    sightlines: 3 first-hit ray rows. assembly: 30 steps, 178 objects placed, 0 in no step. stacks: 4, 0 with a measured limit.
    flexures: 2. stability: 3456 poses. cables: 15 routes, 15 with path length, 3 chains; junctions on 15 routes with known
    ends, 2 waived (cable_junctions_ok); exposure at home. (`distances`: 90 row-poses, all pass.)
- **not_checked (verbatim):**
  - "fasteners: pilot/clearance hole diameters (use cadlib.features for those); wrench access to nuts"
  - "stability: dynamic loads (recoil, pan acceleration), friction/sliding"
  - "cables: bend radius, slack across joints, connector positions (review by section render)"
  - "not geometric: teardown step count, alignment-jig datums (declare stacks), aesthetics, BOM correctness"

### v2-A6 rows -> value (closes review 6)
- **A6-01 the splice goes into a bore that is already closed (major).** Order change, no geometry change: `pan_stage.build`
  labels `FST_gcap_*` "11a" (was "2c"); checks.json step 2c is the posts only and a new step **11a** (after 11, feeder on the
  beam) holds `BUY_bus_junction`, `CAB_bus_pan_tail`, `PRT_groove_cap`, `FST_gcap_*`. 10d keeps only the feeder cover.
  - [assembly: 11a (v2-A6-01)] 0 findings; 30 steps, 178 objects placed, 0 in no step.
  - [service: v2-A6-01 groove cap off for the bus splice (BOM 11a / 14a): pod at tilt 45, 6 x M3 x 10 csk with a straight bit]
    **6/6 `tilt=45:straight 14`** (FST_gcap_0..5).
  - [fasteners: FST_gcap_*] engagement 6.5, stand-off 0.5, protrusion 0; best access straight 14 (gcap_0/1/4 at home, gcap_2/3/5
    at tilt 45); at home gcap_2/3 need the L-key (15.5) and gcap_5 is BLOCKED -> accepted warn `FST_gcap_5 reachable only at
    tilt=45`.
  - [slide: v2-A6-01 groove cap lifts +Z off the turntable at tilt 45 after its 6 screws] 40 mm, **min 0.2 to `PRT_post_L`**,
    not blocked (overlapping at rest: `PRT_turntable`, the seat).
  - [slide: v2-A6-01 bus splice lowered into the hub bore to its seat (z 74, az 35) with the groove cap off, pod at tilt 45]
    +Z 40, **min 1.000 to `PRT_hub_gear`**, not blocked.
  - [slide: v2-A6-01 the refitted groove cap keeps the splice captive] **blocked at 3.5 by `PRT_groove_cap`** (expect blocked,
    window 2.0..4.5). `cad q dist BUY_bus_junction PRT_groove_cap` -> 3.0 at (9.73, 4.02, 99.0) (splice top z 99, cap
    underside z 102).
- **A6-02 the static pan lead ended under an orbiting splice (minor).** `params.BUS_PAN_AX` (0, 0, 63); `CAB_bus_pan` (static)
  ends there; `CAB_bus_pan_tail` (PIV_pan, step 11a, 14.641) runs from it to `BUS_JCT_BOT` (5.73, 4.02, 74). The launcher base
  lead's inner leg moved r 3 -> `LB_LEG_R` 6.5, U radius 4.75 at r 11.25, `LB_LOOP_ZC` 46.5 (the axis between z 48 and 66 was
  inside its sleeve). `BUS_PAN_END_GAP` deleted.
  - [distances: v2-A6-02 CAB_bus_pan > CAB_bus_pan_tail, max 1.0] 0.011 / 0.008 / 0.013 at pan -90 / 0 / +90.
  - [distances: v2-A6-02 CAB_bus_pan_tail > CAB_launcher_base, min 1.0] 1.362 / 2.789 / 2.430 at pan -90 / 0 / +90;
    `cad q sweep CAB_bus_pan_tail CAB_launcher_base PIV_pan -92.5 92.5 2.5` -> 75 stations, min **1.236 at -92.5** (at
    (0.67, -3.16, 66.67)), 2.41 at +92.5.
  - [distances: v2-A6-02 CAB_bus_pan_tail > PRT_hub_gear, min 1.0] 5.825.
  - [cables.chains: pan bus lead (BOM item 14, CAB_bus_pan 350)] route 292.1 (277.5 + 14.6) / lead 350: 57.9 spare (the plan
    said 62; that was A6's 287.7 route).
  - Loops [manifest `parts.*.loop`]: `CAB_bus_pan` 114.1 vs chord 55.9, **+58.2**; `CAB_launcher_base` 60.6 vs 12.2, **+48.4**
    (both >= 45, asserted). `cad q dist CAB_bus_pan CAB_launcher_base` -> 2.585.
  - Unchanged rows that moved: [distances: v2-A2-02 base > bundle] 0.916 / 0.006 / 0.760 (A6 0.133 / 0.002 / 0.097, max 1.0),
    base > MotorGo 0.722; [distances: v2-A5-03 splice > launcher base] 3.286 / 6.979 / 5.203 (A6 3.548 / 5.130 / 4.206); splice
    to turntable 1.945, hub gear 1.000, bundle 2.846 (unchanged). Chains: encoder 510.0 / 545 (A6 511.8), phases 488.3 / 700
    (A6 490.2). `CAB_encoder` lead budget 119.1 (A6 117.2; checks.json `cable_leads` 119).
  - Accepted warn `no lead length: CAB_bus_pan_tail`: the tail is part of the 350 lead; the chain row is its length check.
- **A6-03 the swept rows missed psi 0 (minor).** The 3 swept rows (x 3 settings) run psi **1..105** step 2 (53 stations; A6 0..104).
  `missed_deg` is `[]` on all 9 row-poses.

  | Row (min) | min stop +0.327 | home 0 | max stop -0.558 |
  |---|---|---|---|
  | bare gap, full lift (8.0) | **8.098 @ 63** (8.099 @ 81) | 8.222 @ 91 | 8.415 @ 91 |
  | hood to tape, full lift (7.5) | 7.598 @ 63 | 7.722 @ 91 | 7.915 @ 91 |
  | rest grip (6.1) | 6.175 @ 27 | 6.494 @ 27 | 6.986 @ 49 |

  The min-stop minimum moved from A6's psi 90 (8.099) to psi 63 (8.098) because the odd stations sample other facets; the
  `gap_arc` assert (8.105, analytic) is unchanged. The max-stop psi 1 station reads 14.26 (the ray meets the hood's entry
  chamfer, not the land); every other station is on the land.

### Stability
- [stability] worst 31.2 deg over 3456 poses (feeder -60, hood -0.558, jar 0, pan -90, tilt 45; 3948 g, CG (16.1, -13.8, 169.6),
  edge 102.9), as in A6. `cg_grid.py` not re-run (mass model unchanged): `renders/attempt-6/cg_grid.txt`, worst 29.9 deg.

### Finish-step changes
- `parts/finish.py`: `bom_item` for `CAB_bus_pan_tail` ("the last 14.6 of the CAB_bus_pan 350 lead ... soldered into
  BUY_bus_junction at step 11a") and a new `CAB_bus_pan` text (ends on the pan axis at `BUS_PAN_AX`). The `BUY_bus_junction`
  text says "made above the turntable and seated at step 11a"; the label comes from checks.json `assembly_order`
  (`assembly_step()`), and the build asserts that the splice and the tail are both at 11a.
- BOM_AND_ASSEMBLY.md: attempt-7 evidence; section 0 swept profiles psi 1..105; items 13/14/14a/15 numbers, item 14 split into
  the static lead + tail with the 350 chain, item 14a at step 11a with the three v2-A6-01 slide rows; U-loop text (inner leg
  r 6.5, pan lead to the axis); fastener table `FST_gcap_*` (11a); steps 2c (posts only), 3 (pan lead fed up, plug on), 10d
  (feeder cover only), new 11a (9 sub-steps, each citing a v2-A6-01 row); service row "Bus splice: groove cap off at tilt 45";
  sections 6, 7 (37 warns), 8.
- Renders (`renders/attempt-7/`): 2 sections at 960 px, `sec_hub_bore_x5.73_pan-90.png` and `sec_hub_bore_x5.73_pan+90.png`
  (`cad q section x 5.73 ... 300,0,78 70 --pose PIV_pan=-90 / 90`: the tail on the pan axis, the launcher leg, the splice cut at
  -90 and whole behind the plane at +90); the final 1800 x 1350 set (iso, iso_front_left, front, side, top, rear, pan-90_tilt0,
  pan+90_tilt45, tilt45, jar_unlocked, exploded); `stl_sheet.png`.
- Warns 37 (A6 35): +1 `FST_gcap_5 reachable only at tilt=45`, +1 `no lead length: CAB_bus_pan_tail`; both accepted with reasons.

### Not met / deferred
1. The optional 2 mm tie slot in the hub-gear bore (A6-01 fix item 3): the cap stops the splice rising (3.5); it would need a
   radial window through the gear's bore ring (z 77.5..85), and the splice's lower 3.5 (z 74..77.5) hangs below the gear anyway.
2. Launcher bundle/base meeting point (A6-02, second half): kept at r 4 / az 235; the two Ø6 ends are 0.916 apart at pan -90
   (row max 1.0), under one sleeve diameter.
3. Carried from A6: `LEAF_L` 40 (rig log), entry-arc margin by geometry (thickest-candy rule stands in), nip window 6.2..7.0 vs
   the rig's 5..12, `post_R x journal_plate` `contact_normal` (tool limit), and the user's calipering steps (BOM section 8).
4. checks.json `why` text of the v2-A6-02 rows says the axis joint is at "z 64" and the launcher leg at "r 6"; the model has
   z 63 (`BUS_PAN_AX`) and r 6.5 (`LB_LEG_R`). Text only, checks scope; the rows measure the built geometry.

## Print freeze after review 7 (9/8/9, no blockers), 2026-10-25

**Freeze.** The loop was stopped as an attempt-8 planner started (11:12-11:14). Nothing in `blender/` (params.py, parts/*.py,
checks.json), `stl/` or BOM_AND_ASSEMBLY.md had an mtime after review 7 began (`find -newer review/cadcheck.json`). The
only attempt-8 artefact was `renders/attempt-8/progress.md` ("tools: 6025133"); it was deleted. A rebuild reproduced all 38
STLs (36 machine parts, encoder jig, pocket coupon) and `manifest.json` byte for byte. `cad check` came back 0 F / 37 W, with
every check section identical to `renders/attempt-7/cadcheck.json` apart from runtimes.

**Review-7 fixes that change no printed geometry:**
- A7-01: step 11a.0 (post cover off, tilt servo +X about 10 out of the socket, pod onto a printed 45 deg prop).
  - `blender/tools/tilt45_prop.py` writes `stl/tools/tilt45_prop.stl`, 49 x 30.7 x 50.9, 24.6 cm3.
  - The pad top is the nip cover's underside plane at tilt 45, fitted by 4 rays on the built model: z = 168.975 - 0.4967 y,
    26.4 deg, flat to 0.000.
  - A foot runs to the right post's front face (y 22.000 by ray), 0.3 off it. The pod pushes the pad -Y as well as down, and
    the foot reacts that push.
  - The pad starts at y 31.5. At y 28, cadcheck's 14 mm hand radius at `FST_gcap_5` fell back to the L-key (15.5).
  - Scratch blend with the prop (`--blend`), measured by `cad q dist`:
    - nip cover -1.0 mm3 (face contact) at tilt 45, 1.036 at 46;
    - groove cap 8.519, `FST_gcap_5` 12.3, post_R 0.3, thumbwheel 8.495, leaf 5.395.
  - `cad check --only service,slide` on the scratch blend: 0 F, 0 W from the service rows; all 12 cap accesses straight 14.
  - The prop is not in the model: at tilt < 45 the pod would sweep through it, and cadcheck has no fixture concept.
  - New rows: [service: v2-A7-01 groove cap screws at tilt 45 with the right post cover off] 6/6 straight 14; [slide: v2-A7-01
    right post cover off +X] min 0.3 (closest `BUY_servo_tilt`).
- A7-02: BOM text only.
  - Trim the tilt and feeder leads to route + 70. Service-loop homes: tilt in the groove at x 10..60 (`CAB_bus_tilt` is the
    only route with x > 7.1 there), feeder back up the left-post channel. Splice Ø10 x 20 or smaller.
  - Model change not made. A scratch build with `BUS_JCT` `l` 20 (params only) left all 36 printed STLs identical but failed
    1 row: the captive-splice slide stopped at 8.5 (window 2.0..4.5). The lead offsets need per-lead hub lists in
    pan_stage.py / feeder.py.
  - The pan lead is not trimmed. Its 57.9 spare returns to the U-loop (not modelled).
- A7-03:
  - the reviewer's forward-up cap exit is adopted as [slide: v2-A7-03 groove cap leaves the machine forward-up], min 0.2 to
    `PRT_post_L`;
  - the v2-A6-02 `why` strings now say z 63 / r 6.5.
- A6-02 (skipped by decision): the 5.66 chord swing of the bundle hand-over is documented in the BOM U-loop paragraph; no
  model change.
- Final `cad check`: **PASS, 0 fail, 37 warn (0 untriaged, 0 stale)**; service 10 ops / 38 accesses, slide 18. `cad bom`: 18
  rows, 0 disagree.

**Print package `BUILD/`:**
- `PRINT_PLAN.md`, `plates.json`, `print_estimate.json`, `plates/<plate>/`, `SHOPPING_LIST.md`, `ASSEMBLY.md`,
  `MEASURE_FIRST.md`, and 7 step renders.
- Times and grams come from the launch rig's layer model, loaded by AST from `test-prints/launch-rig/build.py`
  (`blender/tools/print_estimate.py`). It reproduces the rig's six published numbers exactly. 3 walls: 27.9 h, 1705 g.
- Not a slicer.
- Found while packaging: the v2 flywheel is not the rig's.
  - `HUB_X0` is 9.6 against the rig's attempt-3 9.0, so the web is 4.5 thick, not 5.1 (33.2 vs 35.4 cm3).
  - The thumbwheel nut trap is 0.3 deeper.
  - The hood profile (lift-matched) and the separate leaf differ from the rig's backplate and integral leaf.
