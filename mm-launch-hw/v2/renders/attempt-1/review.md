# Review: M&M Launcher Turret v2, attempt 1

Checks re-run: `CADCHECK PASS: 0 fail, 34 warn` on a /tmp copy (tools 2197aac). This matches the designer's cadcheck.json warn for warn (set difference empty).
- Coverage: parts 33, interference/clearance 170 objects in all four collections (4082 pair-poses, 2.5 deg overtravel), fasteners 102 + 4 nuts at 14 poses / 28 steps, service 7 ops, drop 1, index 3, slide 8, distances 26, stacks 3, stability 1 pose, cables 13.
- Not checked: pilot/clearance hole diameters and wrench access to nuts; dynamic loads; cable bend radius, slack and connectors; teardown count, jig datums, aesthetics, BOM correctness.
- Review-added rows (`review/checks_review.json` gives `review/cadcheck_review.json`) produced **25 fails, 11 warns**. Those fails back issues A1-01, A1-02, A1-04 and A1-06.

| Metric | Score | Anchor matched | One-line reason |
|---|---|---|---|
| Functionality | 7 | "Works, but has 3 or more majors" | No blockers. The feed path, index and drop pass at the home pose. The nip adjustment has no hard stops, setting the gap needs the cover off at tilt 45, and the Ø15 pocket admits two edge-on candies. |
| Manufacturability | 7 | "3 or more majors / a fix needing redesign" (rounded down from 8) | 0 fastener fails and everything fits the P1S. A feeder servo swap needs the feeder torn down, the crown wall next to the self-tap pilots is 0.94 mm, and the pod drops in only at an undocumented tilt. |
| Aesthetics | 6 | "unfinished element in a hero view caps at 6" | The gate is a bare 2 mm sheet sticking out of the valve in iso. Three rubric items fail: the feeder has no edge break, a PCB is exposed through a base notch, and the colours carry no meaning. |

## Previous issues
This is the first review of v2 attempt 1, so there are no previous v2 issues. The v1 lessons the brief lists are re-checked under the issues below (double feed: A1-03; adjustment without covers: A1-02; service without teardown: A1-04).

## Measurements

| Item | Value | Source |
|---|---|---|
| Full check | 0 F / 34 W, identical to the designer's | `review/cadcheck.json` |
| Index: +60 stroke, -60 stroke, full sequence | 1 window at 48..60, 1 at -60..-48, 0 windows | `checks.index` |
| Index with the jar drifted to 5 / 10 / 15 deg (no bayonet detent) | 0 column windows; +60 still 1 window | `cadcheck_review` index rows "REVIEW column never open, jar drifted" |
| Nip ray at home / hood hi (thumbwheel min) | 6.493 (squeeze 1.01) / 5.498 (squeeze 2.0) | `checks.distances`; review row "nip ray at hood hi" |
| Nip ray at hood -0.55 / -1.0 / -1.5 | 6.996 / 7.396 / 7.842 (not gripped) | `cadcheck_review` distances |
| Drop at hood +1.09 (gap 5.5) and -0.55 (gap 7.0), tilt 0/22.5/46 | 31/31 hit the flywheel | review drop rows |
| Drop at hood -1.0 (gap 7.4), tilt 0 | **8/31 stall** at (21.5..23.5, 18.2, 132.0) | review drop "top of working window" |
| Drop at hood -1.5 (gap 7.84) | **13/31 stall** at tilt 0, **23/31** at tilt 46 | review drop "threshold" |
| Drop at hood -3 .. -6.51 (to gap 12.5) | 18/31 stall at tilt 0, **31/31 stall** at tilt 46 | review drop rows |
| Hood to body past the thumbwheel minimum | 0.46 at hood 1.0, 0.29 at 2.0, 0.09 at 3.0, contact at 3.5, 1.2 mm³ overlap at 4.0, at (13.0,-6.25,180.8) and x 8.5..31 | `cad q sweep PRT_hood PRT_launcher_body PIV_hood 1 4 0.5` |
| Hood to wheel at hood +3.4 | 2.17 nearest | `cad q dist PRT_hood PRT_flywheel --pose PIV_hood=3.4` |
| Two edge-on 13 x 7 lentils side by side in the +60 parked pocket | true lentil 0.081 mm from the pocket wall; ellipsoid marker overlaps 3.13 mm³ | `cad q dist ZMM_lenA PRT_feeder_disc` on `/tmp/rv1/model_mm.blend` (built by `review/add_mm_probe.py`) |
| Pocket radius at z 268 | 7.386 (y, faceted) / 7.5 (x) | `cad q ray 10.5,18.187,268 0,1,0` |
| FST_fhorn_ctr (feeder servo centre screw) access, cover off | **blocked by PRT_feeder_housing at 8.0** (straight bit and L-key) at all 9 poses | review service rows |
| Feeder servo lift +Z after the cover is off | clear over 60 mm (0.00 resting contact) | review slide row |
| Nip cover + leaf off at tilt 0 | **blocked by PRT_groove_cap at 14 mm** | review slide row |
| Encoder cap off -X 45 mm | clear at tilt 45; blocked by PRT_post_L at 4 mm at tilt 0 | review slide rows |
| Pod lift-in (step 7 reversed, +Z 150) | **blocked by PRT_post_R at 2 mm** at tilt -3/0/46 (journal-plate lug); hinge head at 14 mm; clear at tilt 10/22.5/35 (min 0.14-0.2) | review slide rows |
| Feeder lift off the beam (step 11 reversed) | clear | review slide row |
| Gate +X 52 with the valve present | clear, min 0.20 to PRT_jar_valve (the designer's row ignored the valve) | review slide row |
| Gate +X 110, valve ignored | nothing retains it (min 0.64 to the adapter) | review slide row |
| Crown wall at the (-36, ±18) pilots | 0.94 at (-37.6, ±16.5, 266.2); pinion chamber R24.35 | `checks.parts` PRT_feeder_crown thin_wall_where |
| Magnet centring stack | worst case 0.40 against the 0.30 limit, RSS 0.17 | `checks.stacks` |
| Stability | 1 pose in cadcheck (33.5 deg); 64-pose grid worst 29.8 deg at jar 30, tilt 46, pan 180 | `checks.stability`, `cg_grid.txt` |
| Servo controller exposed in the +X wall | rays at (200, 30..70, 10..18) heading -X hit BUY_servo_controller at x 111-116.5 | `cad q ray` |

## Issues (ranked)

**A1-01 (major, functionality): the nip adjustment has no hard stops at either end.**
- The thumbwheel range is 5.5..12. The joint actually runs to 12.5, not the 12 the BOM states.
- Past the 5.5 setting nothing stops the hood. It swings on to hood +3.5, where it hits the body at the chute entry (13,-6.25,180.8). The hood is then 2.17 from the wheel. The rig finding asked for a stop below 4.8.
- At the open end, the drop stalls from a 7.4 bare gap (8/31 at tilt 0). At 7.84 it is 13/31 at tilt 0 and 23/31 at tilt 46. From hood -3 it is 31/31 at tilt 46.
- The feedable window is therefore 5.5..7.0, with 0.4 mm of margin. The thumbwheel offers 5.5..12.5 and gives no indication of where feeding stops.
- At the thumbwheel minimum the hood is 0.46 from the body (the moving minimum is 0.5).

Fix:
- Add a printed min-gap stop: a 3 x 20 land on the guard under the hood's back face, contacting at hood +1.3 (gap 5.3) on a broad face, away from the chute entry. Open the bay so the hood keeps ≥ 0.5 to the body down to that stop.
- Limit the thumbwheel's static travel to gap 7.2 (hood about -0.8) with a stop collar on the stud, or with STUD_L / SEAT_H. Dynamic lift through the leaf (1.5) stays free.
- Set PIV_hood to those stops, declare them as `fits` contact, and add `distances` ray rows and `drop_tests` at both stops.

**A1-02 (major, functionality/service): setting the gap needs the nip cover and the leaf spring off, and only at tilt 45.**
- The brief requires adjustment without removing covers. The BOM states this requirement is not met.
- At tilt 0 the cover is blocked by PRT_groove_cap at 14 mm.
- The leaf comes off with the cover, so the gap is set without its preload.
- The `service` row has no pose, and the BOM service table does not say "tilt 45".

Fix:
- Expose the thumbwheel rim (TW_R 8.5) through a 22 x 7 finger slot in the nip cover over the rim, with ≥ 2 mm of rim proud of the slot.
- Alternatively, move the leaf root onto the guard so the cover is cosmetic.
- Prove access with a `cad q ray` or `service` row at tilt 0 and tilt 45 with the cover on. Put `pose: {PIV_tilt: 45}` on any cover-off row.

**A1-03 (major, functionality, plausible): the Ø15 x 8 pocket admits two edge-on candies side by side.**
- Two true 13 x 7 lentils standing on edge sit 0.081 from the pocket wall. The conservative ellipsoid marker pair overlaps by 3.1 mm³.
- Any candy under nominal size fits.
- The baffle ramp starts 5.5 above the disc, so both candies pass under it. The result is either a double feed or a jam under the 45 deg ramp. This is the v1 failure mode the brief names.

Fix:
- Set POCKET_D 15 to 14.4 and add a 1 x 45 rim chamfer.
- Re-run the lentil-pair probe (`review/add_mm_probe.py`); it must overlap.
- Re-run `stacks: pocket over outlet` (the outlet stays 16) and the three index rows.

**A1-04 (major, manufacturability/service): swapping the feeder servo needs a feeder teardown.**
- FST_fhorn_ctr is driven up through the pinion. It is blocked by PRT_feeder_housing at 8 mm, for both the straight bit and the L-key, at all 9 poses with the lobe cover off.
- The BOM service row ("remove the lobe cover, 2 screws") is an overclaim. The real path is jar off, then 4 feed-mount screws with the L-key, then flip, then 2 floor-plate screws, then the disc out. checks.json had no row for this.

Fix (either one):
- Add a Ø6 access hole on the pinion axis (-55.5, 0) through the housing floor and the beam, for a straight 2 mm hex bit from below, and check the reach at tilt 45.
- Or retain the pinion on the horn with the 4 M2 screws only and drop the centre screw. The servo already lifts +Z clear for 60 mm.

Then add a `service` row for FST_fhorn_ctr.

**A1-05 (major, manufacturability): the crown wall at the (-36, ±18) self-tap pilots is 0.94 mm.**
- The wall sits between the pilots and the pinion chamber (R24.35).
- An M3 self-tapper (r 1.5) leaves about 0.65 mm. It will bulge into the chamber, where the pinion tips run at 0.35.

Fix: move IF_FEED_BOLTS (-36, ±18) to (-36, ±21). That leaves a 2.8 mm wall after threading. Re-run the `fasteners` access (L-key arc) and the `parts` wall row.

**A1-06 (minor, manufacturability): the pod (step 7) drops into the U-slots only at a tilt of 10..35 deg.**
- At tilt 0, -3 and 46 the journal-plate stop lug hits PRT_post_R at 2 mm, and the hinge head hits it at 14 mm.
- Neither the BOM nor `assembly_order` gives a pose.

Fix: write "lower the pod nose-up about 20 deg" in step 7. Add a `slide_out` row with `pose: {PIV_tilt: 20}`.

**A1-07 (minor, functionality): the magnet centring stack's worst case is 0.40 against a 0.30 limit.**

Fix: jig spigot 7.9 (tol 0.05) and Plink pegs 2.4 in 2.5 holes (tol 0.05). The worst case becomes 0.30.

**A1-08 (minor, manufacturability): several functional edges are knife-thin, and one large bridge is unexplained.**
- Knife edges: jar_valve 0.02 at the baffle bottom (16.6,-4.4,272.9); jar_gate 0.77 at its leading knife; hood 0.91 at the nip (20,6.3,134.4); journal_plate 0.95 at (34.2,29.7,222.2).
- journal_plate has a 48 mm bridge (153 mm² ceiling) with no explanation.
- The flywheel's "72 mm bridge" is its 1 mm flange ring (33 mm² ceiling). That one is benign but should be declared.

Fix: give the ramp and blade edges a 0.8 flat so every wall is at least 1.2; make the hood nip edge at least 1.6; turn the journal-plate ceiling into a 45 deg roof.

**A1-09 (minor, aesthetics/function): the gate looks unfinished, and its running state is never modelled.**
- In iso and r03 it is a bare 2 mm grey sheet with a ridge tab, 8 mm proud of the valve when closed.
- Open, it hangs about 60 mm out with 17 mm left in its guides, and nothing holds it at either end. With the valve ignored it slides 110 mm free.

Fix:
- Make the pull tab R6-cornered with EB 1.0 and flush with the valve OD to within ±1.
- Add detent bumps at 0 and 52.
- Model `PIV_gate` (prismatic 0..52) so interference and renders cover the open (running) state.

**A1-10 (minor, aesthetics): the feeder doesn't share the form language.**
- `parts/feeder.py` has no `bevel` calls: the adapter, valve, gate, crown and disc all have sharp edges.
- The crown and cover use R4 plan corners, which are not in the declared set (CR 6, BASE 30).

Fix: apply EB 1.0 to every feeder part, and use R6 corners or add R4 to the declared set.

**A1-11 (minor, aesthetics): the servo-controller PCB is exposed through a 52 x 24 notch in the +X base wall.**
- It is visible in side.png and iso.png.
- The jar is also rendered as an opaque grey solid, which hides the brief's glass "hero" element.

Fix: replace the notch with port-only cutouts (switch and terminal) plus a printed bezel. Give BUY_jar a transmissive material in the view set.

**A1-12 (minor, aesthetics): the two colours don't encode anything.**
- Grey (A) covers the structure plus the flywheel, disc, pinion, gate and hood.
- Terracotta (B) covers the pod, feeder, valve and every gear.

Fix: B for every moving part and A for the static structure, or B for the whole payload path. Reassign the parts accordingly.

## Check-config audit
- **allow** (10 entries): all agreed. The free-state leaf and the stud in the thumbwheel nut are both physical.
- **fits**, agreed with notes:
  - `PRT_post_R x PRT_journal_plate contact:true` covers both the stop lugs and the R15/R15.2 journal, so a journal rub would be hidden. Prefer min_clearance 0.1 plus a separate stop row.
  - `PRT_base_shell x PRT_turntable contact:true` hides the R20/R20.3 hub journal in the same way.
- **slide_out "gate opens"** is disputed. It ignores PRT_jar_valve, which is the gate's own guide. With the valve present, the minimum is 0.20, under the row's own 0.3.
- **service "set the nip gap"** is disputed. It has no pose, but the cover only comes off at tilt 45 (at tilt 0 it is blocked by the groove cap at 14 mm).
- **drop_tests** is missing rows. It covers only the home hood pose; the PIV_hood extremes had no rows. Review rows: the drop passes from 5.5 to 7.0 and stalls from 7.4.
- **distances (nip ray)** is missing rows at both ends of the adjustment. The fixed ray origin also misses the hood at hood ≤ -3; use a PIV_hood-framed origin.
- **service** is missing the feeder servo swap the BOM claims. Added; it fails (A1-04).
- **assembly_order step 7** needs a pose (A1-06).
- **index_tests** match the documented 0/+60/0 and 0/-60/0 motion, so they are agreed. The added jar-drift rows (5/10/15 deg) pass.
- **stability** is a tool limitation. `pose_grid(cap=27)` with 5 driven joints leaves only 1 non-overtravel pose. The designer's 64-pose cg_grid (worst 29.8 deg) is accepted as the evidence.
- **Overclaims in the BOM**:
  - the "Feeder servo: remove the lobe cover" service row;
  - "NIP_SET 5.5..12 = PIV_hood -6.51..+1.09" (the joint runs to 12.5);
  - the drop claim, which is true only at the home hood pose.

## What is good
- 0 fails, reproduced exactly. All four collections are included in interference, and 102 screws pass access at their steps.
- Index logic is sound:
  - park is solid over the outlet;
  - each stroke opens exactly one window;
  - the baffle keeps the column off the outlet even with the jar 15 deg unlocked;
  - the gear ratio is coupled in the joints.
- The drop lands on the descending rear tape at every tilt from 0 to 46, with 0 stalls across the whole 5.5..7.0 working window.
- Jar handling:
  - the band and glass never touch print (14.5 / 16.6 / 7.49 mm);
  - the band stack is 2.4 against 3.0;
  - the jar and feeder lift off cleanly;
  - the tip angle is 29.8 deg or more over 64 poses with a full jar.
- Service:
  - the tilt servo slides out +X with the pod in place;
  - the flywheel comes off +X at tilt 45 with 1.59 clearance;
  - the battery slides 120 mm at 1.6 clearance;
  - the adapter screw tips sit 4.56 above the battery.
- The BOM is honest about the gap-adjust shortfall and the unmodelled U-loop. Every claim cites a row.
