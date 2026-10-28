# M&M Launcher Turret v3 (min-hardware): Design Brief

v3 is the **minimal-hardware, minimal-part-count** branch of v2. It starts from v2 attempt 7 (scores 9/8/9, frozen for print)
copied into this folder. **Read `../v2/DESIGN_BRIEF.md` and `../DESIGN_BRIEF.md` first.** Everything there still applies
(PLA only, P1S/H2D, the mason-jar hopper, the launch test rig's nip/flywheel geometry, cable rules, printer-safety hard rule,
no-support prints) **except where this file overrides it.** v2 history and reviews: `../v2/renders/attempt-*/review.md`,
`../v2/DESIGN_LOG.md`.

## 1. The goal (user, 2026-10-28)
> Assemble the robot with as little metal hardware as possible and as few parts as possible. We still need metal hardware
> for mounting motors, but for assembling the overall robot I want more elegant solutions: fewer nuts and bolts, more
> 3D-printer solutions.

### Baseline (v2 attempt 7, measured by `cad build`)
- **103 screws, 4 nuts, 18 distinct spec x length** (the build's `FASTENERS` line).
- **36 printed parts.**

### Targets for v3
| Metric | v2 A7 | v3 target | Stretch |
|---|---|---|---|
| Metal screws + nuts + pins, total | 107 | **<= 24** | <= 16 |
| Distinct screw spec x length | 18 | **<= 4** | <= 3 |
| Printed parts (STLs, not counting spares / jigs) | 36 | **<= 26** | <= 22 |
| Review F / M / A | 9 / 8 / 9 | **>= 9 / 9 / 9** | |

The build prints `FASTENERS ...`; add a `PARTS <n> printed, <n> metal` line to the build output so every attempt reports both counts.

### Metal that is allowed (motor mounting and purchased-part interfaces)
- BLDC motor face screws into the motor (4), the flywheel's D-shaft clamp (pinch screw(s) + nut(s)), as the test rig has it.
- Servo **centre screws** into the servo splines (pan, tilt). Servo horn-to-part M2 screws are **not** required: capture the
  horn in a horn-shaped pocket (the centre screw clamps the part onto the horn) or print the spline coupling.
- Anything else must justify itself in the design log: what printed joint was tried, and why it fails (load, creep, service).

### Joining toolbox (prefer, in this order)
1. **Part consolidation**: merge parts that only exist because of a screw joint (covers, plates, sleeves, caps) when the merged
   part still prints without supports on the P1S (256 mm cube) and still assembles.
2. **Bayonets / twist-locks / quarter-turns** with a printed detent (the jar already uses one): for round interfaces
   (turntable to hub, feeder to beam, encoder cap, motor nacelle).
3. **Cantilever snap hooks and snap-fit lids**: the beam lies in the layer plane (a `flexures` row each, stress under the
   PLA limit with margin), releasable by finger or a flat screwdriver slot if the part is serviced.
4. **Dovetail / T-slot slides with a snap detent at the end of travel**: for boards (MotorGo, buck, servo controller),
   the DeWalt adapter, the floor, the post covers.
5. **Printed pins / press-fit pegs, printed axles and print-in-place-free hinges** (pin pressed into a printed boss) for
   hinges such as the nip backplate.
6. **Printed coarse threads** (pitch >= 2 mm, OD >= 12) between printed parts only, e.g. a printed thumbwheel nut on a
   printed screw for the nip gap. Never thread into glass.
7. **Captive geometry**: parts locked by the next part in the assembly order (the last part in the stack carries the one
   snap or bayonet that holds the whole stack).

Load paths that see impact or sustained preload (flywheel, nip spring, pan/tilt drives under a 750 g jar) still need
evidence: a `flexures` row, a `stacks` row, or a `distances` row that shows the joint holds. PLA creeps under sustained load:
don't hold a preloaded spring with a snap.

### Still required (don't regress v2)
- Every service op v2 had (refill, nip leaf swap, tape/flywheel, encoder, tilt/feeder servo swap, base floor, bus splice)
  still works, and now uses snaps/bayonets/slides instead of screws. Each has a `service` or `slide_out` row.
- Snaps that must come off for service release without breaking (flexures row at the release deflection too).
- Assembly order: every snap/bayonet/slide has an insertion path (`assembly_order` insertion checks) at its step.
- No-support prints (`cad printcheck` 0 fails), bed fit, all cadcheck fails at 0.
- Same form language; the jar stays the hero; no visible screw heads is now an aesthetic goal.

## 2. Process
- Keep the modular layout: `blender/build_assembly.py`, `blender/params.py`, `blender/parts/<subsystem>.py`.
  Subsystems: base, pan_stage, feeder, launcher (+ finish).
- The design log gets a **joint table**: every v2 joint (by fastener group, e.g. `FST_floor_*`), the v3 replacement, and the
  evidence row. Each attempt updates it.
- Tool repo: the pinned alex-3d-skills worktree tracks the **`next`** branch and is re-synced before every attempt; read
  its `SKILL.md` / `reference/` each attempt because new features land during the run.
