# Improver brief

You improve the M&M launcher firmware and panel in `mm-launch-fw/`. The goal is the coolest robot that someone can safely bring up on the bench next week.

**Cool means things you can see and do:**

- the turret visibly doing something clever;
- the panel making the robot feel alive;
- shots that are more accurate or more repeatable.

**Cool does not mean** abstraction layers, or features that need hardware nobody has bought.

An independent reviewer checks your work against `review-loop/REVIEWER.md`. Read it first: its safety invariants (S1–S7) and done criteria (D1–D6) are the bar you're held to.

## Each round

1. **Fix first.** If `review-loop/review-<N-1>.md` exists, fix every BLOCKER and MAJOR in its fix list before anything else. Fix the MINORs where it's cheap.
2. **Then add one or two capabilities** that work end to end: console command → firmware → panel control, with README rows. Pick by impact on how cool and how useful the robot is, weighed against the risk at first power-up.

Candidates (you choose, or propose better):

- **Live 3D view in the panel.** The design brief requires the browser to show the CAD moving live. Use `alex-style`'s `web/ax-three.js` (`axScene`) and the pivots in `../mm-launch-hw/v2/DESIGN_LOG.md` "Joints" (`PIV_pan` Z at (0,0,90), `PIV_tilt` X at (0,0,222), `PIV_feeder` Z at (0,0,263)).
  - The STLs in `../mm-launch-hw/v2/stl/` are in print orientation, so they can't be assembled directly.
  - Either export assembly-pose meshes per moving group with Blender, headless: `/Applications/Blender.app/Contents/MacOS/Blender -b ../mm-launch-hw/v2/blender/<the .blend> --python <script>`, writing only into `mm-launch-fw/web/`, with the source `.blend` left untouched.
  - Or build a clean low-poly stand-in from the documented dimensions.
- **Onboard IMU.** The Axis has an LSM6DS3 reachable through the BSP's `initialize_imu()`. Use it for base-tilt / level compensation, a recoil and shot-detect signal, or a "picked up / knocked over" safety stop.
- **Ballistics.** Given target distance and height, solve tilt and rpm from a calibration table of exit speed against rpm, recorded on the rig with `@shot` plus a measured value. Pure math belongs in a host-tested header.
- **Gamepad aiming in the panel** (Gamepad API), with a deadman button for fire.
- **Scripted motion.** Sweep / scan / "look around" idle motion, and aim presets stored in NVS. Never auto-fire (S7).
- **Shot analytics.** Rolling rpm-dip and recovery stats, and a CSV export for the rig's gap sweep.
- **Feeder robustness.** Unjam with a reverse wiggle before latching, and an agitation stroke.

## Rules

- Only edit files under `mm-launch-fw/`. Don't modify `../mm-launch-hw/`. Don't commit, flash, contact devices or printers, or run slicers.
- Reuse before writing: espp (`~/code-stuff/espp/components/`), pace-racer (`~/code-stuff/atdev/pace-racer/pace-racer-fw/components/pace-racer-board/atos-drive/`), and the style guide's `web/` helpers. If you add a component, add a line to the README's "Why not the existing code" section.
- **Panel style:** follow `/Users/alxchunlin/code-stuff/alex-style-guide/SKILL.md`. Copy any helper you use into `web/vendor/`.
- **Pure logic** (math, parsers, state machines without hardware) goes in headers with host tests in `test/host/`, wired into its Makefile.
- **Commands:** every console command answers with exactly one `ok ...` or `! ...` line. Update the README tables and `@kind` shapes for anything you add.
- **Before you finish:**
  - `idf.py build` from `mm-launch-fw/` is clean (zero warnings in `main/` and `components/`);
  - `make -C test/host` passes;
  - `node --check` passes on the panel script.
- Keep the code style of the surrounding files (comment density, naming, `fmt::print`, `espp::Task`).

## Report (final message)

1. **What you fixed:** one line per review finding ID.
2. **What you added**, and how to use it: command or panel control.
3. **Files changed.**
4. **Commands you ran** and their results: build, tests, `node --check`.
5. **Known gaps or risks** you're leaving for the reviewer to judge.
