# Attempt 3: independent review

**Scores:** Functionality **6** · Manufacturability **6** · Aesthetics **6**

## What I checked

- **Deliverables are current.** `build_assembly.py` is newer than the saved .blend (21:24 vs 21:20). I rebuilt it in a scratch copy, and all 32 STLs came out byte-identical to the shipped `stl/`.
- **checks.py re-run** on the shipped .blend (`review/checks_rerun_reviewer.json`). `all_pass` is true:
  - 0 interferences;
  - 0 cross-pivot and same-pivot fastener-vs-purchased overlaps;
  - L-key 10/10 positions clear;
  - min tip angle 41.3 deg;
  - 1505 g of PLA and 31.3 h of printing.
- **Independent measurements** (scripts in /tmp/mmrev/scripts, renders in `review/`):

| Item | Measured | Verdict |
|---|---|---|
| Backplate gap, bare, wheel plane, tilt 0 | 6.50 mm from psi -3 to 78. Opens to 6.96 at 84, 10.6 at 96 and 20.2 at 111 | Matches the doc. 6.0 over tape is about 1 mm squeeze on a 7 mm candy |
| Encoder | IC top centred at (y 37.00, z 170.00), exactly on the motor axis. Magnet face to IC is 1.00 mm. Can crush ribs are r 17.95 at x -72 to -62. Cap spigot is r 17.89 with ribs to r 18.17, in an r 18.14 bore | Nominal coaxial. Tolerance stack is about 0.24 mm RSS and about 0.5 mm worst case (PCB pegs Ø2.3 in Ø2.5 are unchanged) |
| Chute width along the traced paths, at candy-centre x 17, 21 and 25, more than 9 mm from the rim | At least 9.5 mm in-plane, and 18.5 mm in X | A 7 x 13 mm candy fits. The 6.6 mm reading at tilt 22.5 to 45 is the tracer passing the shingled tongue tip, not a real choke |
| **Slide slope on the backplate funnel** (last sliding segment before tape contact) | **36.1 deg at tilt 30, 26.1 at 40, 21.0 at 45, 19.9 at 46** (the hard stop) | **Marginal.** See F1 |
| Hopper to disc | 1.0 mm under the baffle (75 to 105 deg). The disc rim is inside the R58 bore with a 2 mm annulus. Pockets are 8 deep, through to the plate | OK |
| Feeder index | Park 0 is solid over the outlet (7.5 mm edge to edge). ±30 puts exactly one pocket over the outlet | OK |
| USB-C | Partition cutout 9.0 x 14.5 mm against a 7 x 12.6 mm plug overmold, so 1 mm all round. The cable runs straight out of a 36 x 36 niche | OK |
| **Battery slid +X 10 to 70 mm** | BVH overlap with FST_adapter_nut_1 and _3. The stem (y -98.5 to -55.5) passes through the nut corners (y -56.2 to -50.8) | **Fails.** See M2 |
| Nip cover STL in print orientation | 2 mm leaf, 34 mm long, standing vertical off the screw block on the bed (`review/nip_cover_print_orientation_section.png`) | **Root bending goes across layer lines.** See M1 |

## Previous issues

1. **L-key can't reach the pinch bolts: FIXED.**
   - The web is now on the motor side (x 9 to 14.1), so the cup opens toward +X.
   - The bolt plane is at x 19.5, and the short-leg elbow lands at r ≈ 27.8, inside the rim's r 31.5.
   - A ±30 deg swing keeps the elbow under r 30. The check gives 10/10 clear.
2. **Feeder double-drop: FIXED.** Park 0 is solid. ±30 is one pocket. The baffle covers about 75 to 105 deg and is ramped at both ends.
3. **Pinch bolts too short: FIXED.** M3 x 20, with the tip 0.54 mm past the nut and 0.36 mm inside the hub surface.
4. **Rigid nip: FIXED in concept.** There's now a thumbwheel minimum-gap stop plus a leaf preload of about 9 N, with 2.5 mm of overtravel. The leaf as printed is a new major issue (M1).
5. **Adapter bolts in the battery envelope: PARTIAL.** The rest-pose clearance and the FST-vs-BUY check are fixed. But the battery's slide path runs through the +X nuts (M2), and checks.py never sweeps the pack along its rail.
6. **Magnet jig coaxiality: FIXED.** There's a Ø7.8 spigot in the Ø8 access hole, a Ø6.1 pocket, cap crush ribs and can crush ribs. The PCB peg fit still adds about ±0.1.
7. **Gap adjustment needs a wrench: FIXED.** The nip cover's 2 screws are reachable from behind at tilt 0 along a clear path angled about 20 deg down, and the thumbwheel turns by hand (`review/nip_thumbwheel_cover_off_tilt0.png`).
8. **Bare feeder bus above the bonnet: FIXED.** The bonnet now butts against the plate (`review/bonnet_top_feeder_bus_closeup*.png`). A new, smaller exposure is at the bonnet foot (A2).
9. **Jack screws under the pod: FIXED.** They're replaced by the terracotta nip cover.
10. **Form language and cropped renders: PARTIAL.** The renders are re-framed and the feeder servo now has a chamfered terracotta shroud. The machine still reads as a set of separate boxes (A1).

## Issues (most impactful first)

### F1 (functionality, major): feed stalls likely near full tilt
- **Problem:** At tilt 45 the candy lands near the hinge and slides down the backplate funnel at **21.0 deg**. At the 46 deg stop it's **19.9 deg**, below checks.py's own 20 deg stall limit. A sugar shell on printed PLA has μ of about 0.35 to 0.45, a friction angle of 19 to 24 deg.
- **Consequence:** The candy can stop 2 to 3 mm short of the tape, about psi 90 to 100 where the gap is 8 to 10 mm. The next candy then stacks on it.
- **Cause:** It's the funnel flare (G_IN 21 with the s² profile) that flattens the surface at high tilt. The concentric zone stays at 50 deg or more.
- **Fix:** Reduce `G_IN` from 21 to 12 or 13 mm. My estimate is about 40 deg of slide at tilt 45 and psi 100. Alternatively, extend the rear-wall tongue so the candy is released at psi 92 or less. Raise `STALL_DEG` in the tracer to 28 deg and require a pass at tilt 46.

### M1 (manufacturability, major): nip-cover leaf spring printed with its bending stress across layers
- **Problem:** `nip_cover` is printed screw-block-down with the leaf's length vertical (Z = v), so the root bending stress acts across layer bonds.
- **Load:** checks.py's own numbers are 20.9 MPa at the 9 N preload and 43.6 MPa at the over-travel stop. PLA's Z (interlayer) strength is about 20 to 30 MPa.
- **Consequence:** The leaf will crack or creep at the root after limited cycling. Then preload is lost, the plate falls open at tilt 0, and there's no grip.
- **Fix:**
  - Print the cover on an end wall, X vertical, so the leaf lies in the layer plane.
  - Add an R2 fillet at the root.
  - Keep preload stress at or below 15 MPa: for example, a 2.5 mm leaf at 1.2 mm preload is about 13 MPa.
  - Cut overtravel to about 1.5 mm, so the stop is at about 28 MPa.
  - Or make the leaf a separate flat-printed strip screwed under the cover.

### M2 (manufacturability, major): battery can't slide past the +X adapter nuts in the model
- **Problem:** Sliding BUY_battery along +X makes its rail stem overlap FST_adapter_nut_1 and _3 from dx = 10 to 70 mm, by 0.7 mm per side in Y.
- **Consequence:** If the real channel is as wide as the placeholder, a Ø6.5 x 5.5 counterbore at the +X corners breaks into it and the nut blocks the pack.
- **Fix:**
  - Drop the battery-face counterbores and nuts. Drive self-tapping M3 x 20 from the deck top into Ø2.5 pilots in the adapter's corner holes, with the tip at least 3 mm above the battery face.
  - Add a sweep of the battery along its rail (0 to 120 mm) against all FST and PRT parts to checks.py.
- **Also:** Only 5 mm of the pack protrudes, with 2 mm side clearance, so it's hard to grip. Add two Ø30 finger scallops at the top and bottom of the bay opening (`review/battery_bay_side.png`).

### A1 (aesthetics, major): no shared form language
The machine reads as separate boxes:
- a square grey base;
- an oversized plain Ø224 turntable disc;
- thin grey plate arms;
- a terracotta pod;
- a boxy terracotta tilt-servo housing;
- a terracotta feeder-servo box hanging behind;
- a grey hull plate carrying an offset cone hopper that sits up to 118 mm behind the pan axis (iso.png, rear_cable_side.png, `review/iso_rear_left_tilt45.png`).

Fix:
- Give the arms, the servo housing and the feeder shroud one section and corner treatment (the pod's chamfer plus R6), for example closed terracotta-capped arms.
- Step the turntable down to about Ø180 with a chamfered edge.
- Pull the hopper and feeder stack forward to within about 60 mm of the pan axis, or fair the shroud into the plate.

### F2 (functionality, minor): backplate hinge axle threads only 2.5 mm into PLA
- **Problem:** FST_hinge spans x 4 to 34 and engages x 31.5 to 34 of the journal plate. At 6,000 rpm, vibration can back it out.
- **Fix:** Add a 6 mm boss or nut trap on the journal-plate side and use M3 x 35 into it, or at least a drop of superglue. Keep the tip clear of the right arm at x 36.9.

### F3 (functionality, minor): thumbwheel range stops at 10 mm
- **Problem:** The thumbwheel reaches 10 mm. The brief asks for about 9 to 12 mm before tape.
- **Context:** The deviation is reasonable: a flat 7 mm candy needs about 6 mm. But it isn't flagged as a deviation, and edge-on experiments aren't possible.
- **Fix:** Lengthen the stud to M3 x 25 so the thumbwheel reaches 12. State the deviation in BOM section 0.

### A2 (aesthetics, minor): launcher bundle visible at the left bonnet foot
- **Problem:** The turntable groove is open where it leaves the bonnet footprint, and about 8 mm of yellow and white wire shows there (`review/bonnet_foot_turntable_closeup.png`, side_left.png, iso_front_left.png).
- **Fix:** Extend the bonnet skirt 3 mm down into a matching rim notch, or add a 14 x 10 mm groove cap under the bonnet.

### A3 (aesthetics, minor): battery bay window exposes the adapter and nut hardware
- **Problem:** The +X wall opening runs from z 0 to 89, which exposes the yellow adapter, the screw tips and the nuts above the pack (`review/battery_bay_side.png`).
- **Fix:** Cut the window to the pack outline plus 2 mm (to about z 77) and add a chamfered lead-in frame.

## Scores
- **Functionality 6.** The core is sound and well engineered:
  - the feeder index is correct;
  - the nip is compliant and force-limited at about 9 N;
  - the wheel clamp is fully engaged and balanced;
  - the encoder is nominally coaxial;
  - USB, cables and stability are good.

  But feeding is marginal over the top 5 to 10 deg of the required 0 to 45 tilt range. The nip's only compliance element (M1) is likely to fail in service, which takes the grip with it.
- **Manufacturability 6.**
  - In its favour: all 32 STLs fit the P1S with no supports, the fastener access problems from attempt 2 are solved, and about 31 h / 1.5 kg is reasonable.
  - Against it: two likely reworks. The leaf orientation (cheap reprint) and the battery-face nuts against the stem path, plus an awkward step 2 (nuts in an inverted shell).
- **Aesthetics 6.** It's tidy, with consistent 1 mm edge breaks and a two-colour palette, and it's mostly enclosed. But it's still a kit of boxes with no unifying form. There are small visible wire and hardware exposures.
