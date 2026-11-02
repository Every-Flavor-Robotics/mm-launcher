# M&M Launcher Turret v2: Design Brief

v2 is a fresh, modular design that builds on what we learned from v1 attempts 1-3. **Read the v1 brief `../DESIGN_BRIEF.md` first.** Its hard constraints (PLA only, P1S/H2D, drill + M3 + glue assembly, cable rules, power chain), component table, functional requirements, aesthetic goals and change notices all still apply. **This file overrides it** where they conflict.

## 1. Hopper = an upside-down glass mason jar (user decision)
The printed hopper is gone. The M&Ms live in the user's **Ball/Kerr regular-mouth pint (16 oz) mason jar**, hanging upside down over the feeder. It's one less part to print, a standard interface, and the visible glass jar full of M&Ms is the design's hero element. Don't hide it.

| Jar item | Nominal (mm) | Notes |
|---|---|---|
| Jar body | Ø77 x 130 tall, including the neck | Glass. Full mass about 750 g (about 350 g jar plus about 400 g M&Ms). Include it in the CG/tip check at every pan and tilt pose. |
| Glass thread (neck) | OD about 70, thread height about 12 | **Never print glass-mating threads.** |
| Metal screw band | OD about 73.5, height about 13, top-lip opening about Ø58 | Uses the jar's own band. |
| Flat lid disc | Ø about 69 x 0.6 | Replaced by a printed disc. |
| Glass mouth opening | ID about 60 | |

These are nominal values; mark them as params to confirm with calipers. Keep them in `params.py` as one `JAR_*` block.

**Interface:**
- A printed **jar adapter disc** (about Ø69, flange 1.6 mm or less so the band still engages its threads) replaces the flat lid. The jar's own metal band clamps it onto the glass.
- The disc carries a spout of Ø56 or less that passes through the band's top opening and mates to the feeder housing with a **bayonet or twist-lock**.
- A **printed slide gate (shutter)** in the adapter lets you lift the jar off and refill it without spilling: close the gate, twist off, flip upright, unscrew the band, refill.
- The jar rides on the pan stage. The full jar must not tip the machine, and nothing may rely on glass tolerances tighter than ±1 mm.

**The feeder** meters exactly **one** M&M per fire command from a Ø58 column of M&Ms pressing down on it. It needs agitation so they don't bridge, and an anti-shear lead-in for an M&M standing on edge. Turn the index timing into an `index_tests` check, not just prose (v1 A2: the documented index fed two candies).

## 2. Launcher pod = the test rig's geometry
A physical **launch test rig** is being printed now from the v1 attempt-3 launcher geometry (`../test-prints/launch-rig/`). Read its README when it exists. It covers: flywheel with D-shaft clamp hub and tape land, nip and backplate with continuous gap adjustment, motor mount, and rear-shaft encoder mount.
- v2's launcher module must use the **same parameters** (nip radius, gap range, wheel, motor and encoder mount), held in `params.py` as the single source of truth, so physical results can be fed back as parameter changes.
- Don't redesign the nip without a review reason.

## 3. Lessons from v1 (read the reviews; don't repeat them)
v1 scored 5/6/5, then 6/5/6, and attempt 3 is under review. All three attempts are in `../renders/attempt-{1,2,3}/`. Read `review.md` in each (review 3 when it exists) and `../DESIGN_LOG.md`.

**Carry forward, because reviewers praised it:**
- low CG and battery bay,
- vertical USB-C plugged straight through to a rear niche,
- pan cables through a hollow hub with a U-loop,
- rear-shaft encoder coaxial by construction,
- hinged backplate undershot nip,
- hard tilt stops,
- no-support prints that fit the P1S.

**Don't repeat these mistakes:**
- fasteners that miss their nuts or can't be reached with a key,
- adjustment or service claims that need disassembly,
- zero-clearance rubbing faces,
- a feeder that double-feeds,
- bolts poking into the battery envelope,
- exposed leads and dangling servo boxes,
- form languages that don't match.

## 4. Structure (the print-cad-blender skill)
- Use the template's modular project layout: `blender/build_assembly.py`, `blender/params.py`, and one module per subsystem in `blender/parts/`.
- Subsystems: `base` (battery, buck converter, MotorGo, servo controller, pan servo and drive), `pan_stage` (turntable, yoke, tilt servo, jar mount), `launcher` (pod), `feeder` (jar adapter, gate, indexer, servo #3).
- **Interfaces between subsystems** (mount points, bolt circles, cable pass-throughs, the drop axis) are defined once in `params.py`, in an `IF_*` block. A subsystem may only change another subsystem's interface through the planner.
- Every claim is backed by `cad check` / `cad q` evidence.

## 5. Aesthetic direction
One form language from base to pod: the same edge break, corner radii and chamfer family. The jar is the visual centre. The structure frames and supports it, like a product, not a fixture. Cables are fully concealed. Use two PLA colours, as in v1.

## Printer safety
**Hard rule (user, 2026-10-24):** never run Bambu Studio, OrcaSlicer or any slicer binary, never read ~/Library/Application Support/BambuStudio, and never contact a printer or any network service. Print time and filament are estimates computed from geometry only.

## Findings from the launch test rig (2026-10-24 23:00). They apply to every v2 subsystem.
- **MotorGo Axis mounting holes measure Ø2.5 in `reference/mg_axis.stl`, not the Ø3.4 stated in the v1 brief.** Use M2.5 clearance (Ø2.7) until the user confirms on the real board, and keep it a param.
- The attempt-3 motor-face screws (M3 x 10 socket heads) had **0 mm clearance to the spinning flywheel web**, because the model used a 2 mm head where the real one is 3 mm. Model real head heights, and keep at least 1.5 mm to anything rotating.
- Print leaf springs flat, so the bending stress runs in the layer plane. Gap adjustment must be reachable without removing covers (the rig uses an exposed thumbwheel, 5–12 mm). Below about 4.8 mm the backplate cuts into a 1.6 mm chute tongue, so add a hard stop.
- The attempt-3 nip frame was built mirrored, which inverts normals when reused. Build with right-handed frames.
- Feed drops reach the descending rear of the tape at gaps of 5–8 mm, and stall on the plate at 10–12 mm.
