# Attempt 2 review: M&M launcher turret

Independent review. I re-ran `checks.py` (output in `review/checks_rerun.json`, same results as the designer's: 0 unintended interferences, all parts manifold and within the P1S, tip angle 41.5 deg, tracer 37/37 drops on the descending rear tape at every tilt). I also took my own measurements in Blender and rendered extra views into `review/`.

## Scores

| Metric | Score | Rationale |
|---|---|---|
| Functionality | **6** | The feed is now sound in principle. The undershot wheel with a hinged backplate means every drop lands on tape moving down into the nip, at tilts 0 to 45. The gap is adjustable from 5.5 to 12.5 mm, the tilt has hard stops, the encoder is coaxial by construction, and the cable plan is complete. Three problems would make it fail or need rework when built as documented. The documented feeder index drops two candies per fire command. The specified M3 x 16 pinch bolts stop 0.36 mm short of their nuts. The nip is a rigid 1 mm interference on a hard-shelled candy, with nothing to absorb thickness variation. |
| Manufacturability | **5** | Printing is good: no supports, every part fits the P1S, about 30 h and 1.46 kg. Assembly has a blocker: a 2.5 mm L-key cannot reach the flywheel pinch bolts through the web windows, so the wheel cannot be clamped to the shaft. Smaller items: the adapter through-bolts and nuts stick into the battery envelope, the right clamp screw is unreachable at tilt 0, and the lock nuts need a wrench. |
| Aesthetics | **6** | The pod reads as a designed object: nacelle capsule, one chamfer, flush or counterbored screws, consistent 1 mm edge breaks. Several things still look like a prototype. Jack screws and lock nuts hang under the pod. About 10 mm of feeder bus cable is bare above the left bonnet. A grey servo pocket dangles under an off-axis hopper. Taken together, the base box, the thin yoke, the outboard servo box and the large funnel don't share one form language. |

## Measurements (my own)

- **Nip** (ray casts at the wheel plane, tilt 0): backplate inner radius is 41.5 from psi -3 to 78 deg, so the gap is 6.5 bare or 6.0 over 0.5 mm tape. It is 7.1 at psi 85, 8.3 at 90, 12.6 at 100 and 19.3 at 110. The flange (R36) is inside the backplate width (x 8.5 to 31.0), so flange-to-plate is 5.5 mm.
- **Drop column**: a Ø13.5 vertical cylinder at the outlet is clear from the spout (z 250) down to z 215 at tilt 0, 15, 22.5, 30 and 45. Below that it meets the chute rear wall at 22.5 deg and above, which is intended (the candy slides).
- **Encoder**: IC top centre is (y 37.0, z 170.0) at x -77.0. Magnet centre is (37.0, 170.0) with its face at x -76.0, so the air gap is 1.0 mm and the model is coaxial. The tolerance stack is not controlled: can in bore ±0.2, jig in bore ±0.1, cap spigot ±0.15, pegs ±0.1.
- **Flywheel pinch bolts**: `FST_fw_bolt_0` shank ends at y 44.92 and `FST_fw_nut_0` starts at 45.28. The mirror pair ends at 29.08 against a nut ending at 28.72. **Zero thread engagement.**
- **L-key access** (ray-cast sweep, `review/flywheel_pinch_bolt_plane_lkey.png`, `review/flywheel_lkey_long_leg_vs_web.png`): along the bolt axis there are 21.1 mm of free run from the socket. With a standard 18 mm short leg, the long leg is clear only in directions 105 to 255 deg (toward the motor side), and those end at the body's left wall 4.5 to 7 mm away. Toward the web windows (+X) every direction is blocked. With a short leg ground down to 12 mm, only ±15 deg clears, which is less than the 60 deg swing a hex needs.
- **Feeder**: pockets sit at 90 + 60k deg about (21, -45). At the documented park (0 deg) **and** at fire (+60 deg) a pocket is over the outlet (`review/feeder_documented_park_0deg.png`, `..._fire_60deg.png`). The baffle covers only 69 to 111 deg.
- **Battery**: slides out +X by 120 mm with zero overlap with the shell or floor. Clearance is 2.0 mm all round and the pack stands 5 mm proud of the wall.
- **Adapter bolts**: `FST_adapter_0..3` tips reach z 60.0 and the nuts sit at z 60.1 to 62.5, below the adapter's battery face (z 62.6). Each overlaps `BUY_battery` by 12 triangles. `checks.py` skips fasteners against same-pivot purchased parts.
- **USB-C**: the plug overmold (x -91 to -84, y -150 to -81) is clear of the shell, floor and board, with a straight exit out the rear niche.
- **Journal end to bonnet**: 0.50 mm. **Tilt adapter**: the axial ray through the hex key is clear (Ø6.5 hole present).
- **Right clamp screw at tilt 0**: its head is about 2.5 mm from the right arm's inner face (`review/right_clamp_screw_vs_arm_tilt0.png`).

## Issues (most impactful first)

1. **[Manufacturability, blocker] The flywheel pinch bolts can't be driven.** The cup is open toward the body wall (4.5 mm away) and the web windows at r = 20 don't line up with an L-key elbow at r ≈ 27 to 28. *Fix:* put the web on the motor side (x 12.5 to 16.5) so the cup opens toward the cover. With the cover off at tilt 45, the key's long leg then exits +X past the rim. Otherwise, rotate the bolts so the heads face a Ø7 access hole drilled radially through the web at r = 20, on the bolt axis.
2. **[Functionality, major] The documented feeder index double-feeds.** With 60 deg pitch and a 0 to 60 deg stroke, both stroke ends put a pocket over the outlet. Pocket A drops at +60. The pocket that was over the outlet refills at 150 deg (outside the 69 to 111 baffle) and drops on the return. *Fix:* park at 30 deg so the disc is solid over the outlet. Fire by moving to 0 or 60 and back to 30, alternating sides, which is one pocket per cycle. Rewrite BOM section 0 and step 27.
3. **[Functionality, major] The pinch bolts are too short.** M3 x 16 from the counterbore floor ends 0.36 mm before the nut. *Fix:* use M3 x 20. The tip then ends at about 11.9 mm, inside the 13.5 mm trap. Update the BOM fastener table.
4. **[Functionality, major] The nip is rigid.** A 6.0 mm gap over tape against a 7 mm candy is 1 mm of interference between two rigid PLA surfaces. Hockey tape barely compresses. The backplate is held from opening by the jack-screw tips and both clamp screws. M&Ms vary by ±0.5 mm, so thin ones slip and thick ones crack and smear chocolate on the tape. *Fix:* turn the jack screws into a minimum-gap stop that the plate rests against, drop the clamp screws, and preload the plate closed with a printed PLA leaf spring (about 1.5 mm x 10 mm x 40 mm cantilever from the guard floor, roughly 10 to 20 N at the jack point) or two rubber bands. The plate can then yield 1 to 2 mm.
5. **[Manufacturability, minor] The DeWalt adapter bolts and nuts sit inside the battery envelope** (z 60 to 62.5 against the battery face at 62.6). *Fix:* use M3 x 25 so the tip stays inside the adapter, and check that the adapter's corner holes are counterbored at least 3 mm on the battery side for the nut. If they aren't, drive the screws from the battery side into Ø2.5 pilots in 10 mm deck bosses. Add same-pivot FST-vs-BUY overlap to `checks.py`.
6. **[Functionality, minor] The magnet jig references the nacelle bore, not the shaft.** The worst-case magnet-to-sensor stack is about 0.55 to 0.75 mm against the 0.3 mm limit. *Fix:* give `encoder_jig` a Ø7.8 spigot that enters the motor's Ø8 rear access hole (concentric with the bearing), with the Ø6.1 magnet pocket in it. Tighten the encoder-cap spigot to Ø36.2 with three crush ribs.
7. **[Manufacturability, minor] Gap adjustment needs a specific tilt, and the lock nuts need a wrench.** The right clamp screw is shadowed by the right arm at tilt 0. *Fix:* in BOM section 5, say "tilt to 45 deg before adjusting the gap". Add a 5.5 mm nut driver to the tool list, or use nyloc nuts in printed hex traps on the guard so no wrench is needed.
8. **[Aesthetics, minor] Exposed feeder bus.** About 10 mm of `CAB_bus_feeder` runs bare between the bonnet top (z 246) and the plate underside (z 251.5) at x -110 to -102 (`review/exposed_bus_above_left_bonnet.png`, also visible in `front.png` and `rear.png`). *Fix:* extend the bonnet's top up to z 252 so it meets the feeder plate, and add a matching notch in the plate edge so the cable passes inside.
9. **[Aesthetics, minor] Hardware hangs under the pod.** Two jack screws with lock nuts protrude below the guard (`review/pod_underside_jack_screws.png`, `rear.png`, `pan+90_*`). *Fix:* recess the jack bosses into a 10 mm pocket in the guard's underside with a terracotta snap cover or a flush printed thumbwheel. Use M3 x 16 set screws with knurled printed caps.
10. **[Aesthetics, minor] The pieces don't share a form language.** The square base, the Ø224 disc, thin grey trapezoid arms, a 54 x 45 x 76 terracotta box outboard on the right, and a 147 mm cone hopper offset 45 mm behind the pan axis on a hull-shaped plate all compete. The feeder servo pocket dangles grey under the plate. *Fix:* give the hopper skirt and feeder plate a terracotta shroud that wraps the feeder servo, and bring the hopper axis over the pan axis if the tilt sweep allows. Echo the 6 mm radius and the pod's chamfer angle on the arm tops and the servo housing. Frame the ortho renders so the whole machine is in view (`front.png`, `side.png` and `rear.png` crop the hopper and the base).

## Previous issues

| # | Previous issue | Status | Note |
|---|---|---|---|
| 1 | Feed delivers behind the hood | FIXED | Undershot wheel and hinged backplate. My tracer re-run: 37/37 drops first meet the descending rear tape at psi 66 to 85 deg, tilt 0 to 45, with no stalls. |
| 2 | Cap screw R-1 under the feeder disc | FIXED | Countersunk M3 x 45 sit flush. 0 cross-pivot fastener overlaps. |
| 3 | No real nip compression | FIXED | Jack screws, 5.5 to 12.5 mm at BDC, set at 6.0 over tape. The new problem is rigidity (issue 4). |
| 4 | Horn adapter can't be screwed on | FIXED | The Ø6.5 axial hole through the hex key is confirmed. The bench sequence is consistent. |
| 5 | No tilt margin or stop | FIXED | Printed stops at -3 and +46 deg. 3.26 mm to the feeder stack at 45 deg. |
| 6 | Service requires removing the launcher | PARTIAL | Journal plate added and the cover comes off in place at tilt 45. Re-tightening the flywheel is still impossible (issue 1). |
| 7 | Magnet centring uncontrolled | FIXED | `encoder_jig` exists and is in step 13. Its datum is weak (issue 6). |
| 8 | Pod looks unfinished | PARTIAL | Nacelle, single chamfer and servo housing added. Jack hardware and a bare cable are still visible. |
| 9 | Baffle shear and undocumented index | PARTIAL | 30 deg ramps added. The documented 0 to 60 index double-feeds (issue 2). |
| 10 | Outlet column hits the guard top at 40 to 45 deg | FIXED | Ø13.5 column clear to z 215 at every tilt. |
| 11 | Bullet joints at the bend | FIXED | Leads cut to 55 mm, joints in the straight bore, 10 mm bonnet with a chamfered exit. |
| 12 | Journal rubs the bonnet | FIXED | 0.50 mm measured. |
| 13 | No UART link | FIXED | `CAB_uart`, 230 mm, with floor clips. |
| 14 | Adapter fixing and battery clearance | PARTIAL | Bay is 2.0 mm per side with a lead-in, and the removal sweep is clear. The through-bolt nuts intrude on the battery face (issue 5). |
| 15 | Hard-to-reach screws | FIXED | No trunnion screws any more. The encoder note (tilt 45) is in the BOM. |
| 16 | Model and checks hide clashes | PARTIAL | Motor screws corrected, cross-pivot checks and a -5 to 50 sweep added. Same-pivot fastener-vs-purchased overlaps are still unchecked (adapter bolts into the battery). |
| 17 | Inconsistent detailing | FIXED | 1.0 mm edge breaks and 6 mm radii throughout, counterbored or flush screws, 4 mm muzzle flares. |
| 18 | Flywheel retention and balance, motor heat | PARTIAL | Point-symmetric two-bolt clamping hub on 12 mm of shaft, plus vents. The bolts are too short and can't be reached (issues 1 and 3). |
