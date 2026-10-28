# Attempt 2 hotfix review (v3-A1-01, v3-A1-03)

Independent reviewer, 2026-10-28. All measurements were taken on a copy of `blender/model.blend` (in `/tmp/v3h`) with
`cad q` and `cad check --only slide,distances,flexures`: **PASS, 0 fail, 14 warn (all accepted)**.

| Issue | Verdict |
|---|---|
| v3-A1-01 beam-hook barb vs release slot | **FIXED** |
| v3-A1-01 valve key rib vs adapter | **FIXED** |
| v3-A1-03 gate not held open | **FIXED** (light detent; print risk below) |

## v3-A1-01: beam hooks

- `cad q dist PRT_beam PRT_turntable`: **0.0** (A1: -0.531 mm³).
- `inside` at z 233.5, right post: y 16.55 / 19.45 → [turntable] (the jambs); 16.95 / 18.0 / 19.05 → [beam] only;
  16.75 / 19.25 → [] (air). The left post reads the same at x -90.7. The 2.2 barb sits in the 2.8 window with air on both sides.
- Catch: `inside 42.7,18,233.7` → [beam], `42.7,18,233.9` → [turntable]. The barb is under the ledge.
- Slide `A2 hotfix (v3-A1-01) beam hooks hold`: **blocked at 0.1** by PRT_turntable (0.22 mm³ over the 0 bound).
- **Still holds:** the catch face is square (profile in `pan_stage.py`, flat at zh + 1.8), so the hold doesn't depend
  on barb width. The 27 % narrower barb lowers the snap-in force, not the hold. Beam y is located by the tongue in the
  journal U-slots (0.142), well inside the 0.3 a side.
- **Still comes off:** the release window (2.8 x the post inner face) and the 1.0 back gap are unchanged, so the
  screwdriver path and the A1 sightlines still apply. Slide `beam + feeder lift +Z` passes (flexed 5.84 mm³ at 16 mm).
  The 2.2 barb is easier to reach through the 2.8 window than the 3.0 one was.

## v3-A1-01: valve key rib

- `cad q dist PRT_jar_valve PRT_jar_adapter`: **+0.028** at (-10.58, 25.55, 336.0) (A1: -0.485 mm³).
- Distances row (rib top → groove end): 1.0, passes.
- **Notch through the shoulder (3.4 x 1.0):** probes at x -7, z 336.5 are empty for r 26.9 to 28.6, so the notch is
  open to the outside. The wall to the bore is intact (adapter from r 25.0 to the groove floor, about 1.65 thick), and
  the lid disc is above z 337. **No candy leak:** the only path is bore → 0.35 gap under the spout tip → groove →
  notch. That passes dust, not a 7 mm candy, and the groove-to-cheek path already existed in A1.
- **Shoulder strength:** it is not weakened in any way that matters. But the measurement shows something the notes
  don't say. The shoulder underside is a 45° chamfer: at x -3 the adapter reaches r 27.6 at z 336.03, r 28.0 at 336.3
  and r 28.3 only at 336.6. So the jar weight bears on a **line at the pad's inner top edge (r 27.65)**, not on a flat.
  Flat overlap in a z 335.95 / 336.05 grid: +Y pad 0.14 mm², -Y pad 0.22 mm². The notch removes 3.4 of the +Y pad's
  12 mm of that line (x -8.7..-5.3; the -Y pad has a continuous row of bearing samples). See N1.

## v3-A1-03: gate held open

- Slide `A2 hotfix (v3-A1-03) gate held open`: **blocked at 0.2** by PRT_jar_adapter (A1: free over 10 mm).
- My sweep, `cad q sweep PRT_jar_gate PRT_jar_adapter PIV_gate -0.4 53 0.25` (214 poses): clearance is 0.35
  everywhere except 50.35 (0.137), the ride from 50.6 to 51.85 (max **-0.087 mm³** at 51.35), seated **0.05** at
  52.1, hard stop 0.0 at 52.35, and overtravel past it (-1.23 at 52.6). The bump clears the widened closed notch
  (0.35 from -0.4 to 2.1).
- **Does the 0.02 mm³ allow hide a real collision? No.** Apart from the intended ride and the hard stop, the 0.25 mm
  sweep finds no contact. The allow is below the ride (0.087), so the interference check would flag the ride if it
  ever sampled it.
- Gate x valve sweep (-0.4..52.4, 0.4 step): only the existing closed-finger ride (max 0.704 at 1.6, under the 1.0
  allow). The new finger touches nothing on the valve.
- **Finger is real and flexes in the layer plane:** `inside` at x -20, z 325.3: y 1.25 and 3.6 are empty (slots);
  y 0.5, 2.25 and 4.6 are gate. The root is solid at x -10.8 and the slot is open at x -11.3. Section
  `/tmp/v3h/out/sec_gate_z325.3.png` shows both slots cut through and open at the blade's -X edge. Flexures row:
  beam_print_dir [-1,0,0], angle to bed 0, 10.2 MPa. Out-of-plane stiffness (I = 1.0) is above in-plane (I = 0.56),
  so it bends in y as intended. `cad q printcheck PRT_jar_gate`: no findings.
- **Hold force (hand calc):** k = 3·3500·(2·1.5³/12)/15.25³ ≈ 1.67 N/mm. That gives 0.5 N normal at 0.3, so about
  **0.4-0.5 N** to walk out over the R0.6 flank (μ 0.3). That is roughly 5 g on the 8.9 g blade. It is enough for
  vibration, but the click is lighter than the closed detent (about 0.7 N).

## New problems

**N1 (minor, functionality / pre-existing, made a little worse): the jar weight bears on a line, and the notch cuts
28 % of the +Y pad's line.** The shoulder's 45° underside meets the pads only at their inner top edge (profile above).
The vertical load also pushes the cheeks apart radially. A 0.1-0.2 print error on the pad face or the chamfer moves
the contact. If the contact is lost, the adapter's weight goes onto the valve snap fingers, the cross-layer path that
v3-A1-02 already flags. Fix: give the shoulder a flat underside 0.5 wide over r 27.65..28.3 at the pads (or end the
chamfer at r 27.65). Optionally stop the key groove at the pad top and lower the rib 0.6 instead (the review's
alternative), which leaves the shoulder whole.

**N2 (minor, manufacturability): the open-detent finger has small print features under the candy column.** The inner
relief slot is 0.5 wide (the finger needs 0.3 of it), and the gap from the bump apex to the outer slot wall is 0.55.
Both are at about 1.2 line widths for a 0.4 nozzle, so first-layer squish can bridge them and lock the finger. The R0.6
bump is under 3 line widths, so it will print rounded, and the 0.3 engagement may come out at 0.15-0.2. With the gate
closed, both slots (x -27..-11) sit inside the R25 bore footprint, open to the candy column, where shell chips can
lodge. Fix: widen the inner slot to 0.8 (there is room toward y 0.7), and print a coupon with
`blender/tools/pocket_coupon.py` before the gate reprint. The A1 closed finger uses the same 0.5 slots and is just as
unproven.

**Carried, not hotfix scope:** v3-A1-01 fix step 3 (distances rows for every same-body snap pair) was done for 2 of 5
pairs. `cad q dist PRT_encoder_cap PRT_nacelle` is still **-0.183 mm³** at rest. Crown x beam measures 0.0 and hub
gear x turntable 0.05. v3-A1-02 and -04..-07 are unchanged, as the designer says.
