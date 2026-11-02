# Review 1
VERDICT: CONTINUE

Scope: `diff -ru /tmp/mml-snap-0 /tmp/mml-snap-1` (excluding dependencies.lock and sdkconfig). Changed files: main/flywheel.hpp, main/main.cpp, main/settings.hpp, main/turret.hpp, test/host/Makefile, README.md, web/launcher.html, .gitignore. New files: main/tip_guard.hpp, test/host/test_tip_guard.cpp, tools/export_model.py, web/model/*, web/vendor/ax-three.js. The working tree matches snap-1 apart from build products. I also read espp `bldc_motor.hpp`, `bldc_driver.hpp`, the `motorgo-axis` BSP, `lsm6dso`, and `main/demo_link.hpp` where the changed code calls into them.

## Done criteria
D1 pass: a fresh build into `/tmp/mml-review1-build` (`idf.py -B ... build`) exits 0. `main.cpp.obj` is compiled (log line 1437), and the log has 0 `warning:` and 0 `error:` lines anywhere. The incremental build in `build/` also exits 0.
D2 pass: `make -C test/host clean && make -C test/host` gives `PASS: hiwonder protocol`, `PASS: joint map` and `PASS: tip guard` (0 failures each). The only pure-logic module changed or added this round is `tip_guard.hpp`. Its test covers trip, hold time, hysteresis, the 1 g magnitude gate, auto-reference and `level_here`, and its assertions can fail. The glue bug in R1-02 lives in main.cpp, not in the module.
D3 fail: 1 BLOCKER (R1-01) and 2 MAJOR (R1-02, R1-03) are open.
D4 fail: S1 fails (R1-01). S2–S7 pass.
D5 fail: every README command exists in `handle_line` / `cmd_*`, every command the panel sends exists (`fw cal|enc|open|spin|stop|gains|vlim|ramp|tol`, `aim`, `servo read|unload|zero`, `vbat`, `fire`, `feed timing|tol`, `imu`, `imu level`, `imu guard on|off`, `wd`, `ping`, `save`, `cfg`, `status`, `stop`), and every key the panel reads is printed. But `@servo`, `@status` and `@imu` print `nan` for unset floats. That makes the whole JSON line fail to parse, so in those states the panel reads nothing from it (R1-03).
D6 pass: the tip guard works end to end: the `imu*` console commands, the panel's Level here and Tip guard buttons, the Base tilt tile, the `base_tilt` channel (13 channels in the same order in main.cpp:560-561 and launcher.html DEFAULT_CH), and the firmware imu task. The live 3D model is a new panel capability fed by the existing telemetry.

## Safety invariants
S1 fail: what works:
- `stop` / `fw stop` call `stop_all()` (main.cpp:133-136). That calls `Turret::abort_fire()` (atomics only) and `Flywheel::stop()` (flywheel.hpp:327-332, lock-free). The tick then ramps down and calls `coast_locked()` (flywheel.hpp:586-587).
- `before_ota` calls `coast()` (main.cpp:562-569, flywheel.hpp:335-344).
- The watchdog counts Calibrating as moving (main.cpp:620-629).
- The panel's Stop button and Esc send `stop` (launcher.html:639-640).
- Tip trip calls `fault()` (main.cpp:524).
- Neither the servo bus nor the USB link is on the stop path.

The failure is in calibration: a stop that lands just before espp's `BldcDriver::enable()` is lost, and the alignment then drives the bridge for about 3.1 s (R1-01).

Two smaller points:
- `stop` is a ramp at `fw ramp`, which can be as low as 50 rpm/s (main.cpp:237). From 6000 rpm that is a 120 s driven ramp-down, not a coast.
- A `stop` queues behind any blocking console command (R1-14).

S2 pass:
- `Turret::fire` refuses on a turret fault, a flywheel fault, while already firing, or when not at speed (turret.hpp:282-299).
- `at_speed()` requires Closed mode (flywheel.hpp:406).
- `fire` refuses while tipped (main.cpp:451).
- Speed and fault are re-checked before every stroke (turret.hpp:439).
- An abort mid-stroke parks the feeder (turret.hpp:457-462).
- A manual `feed` beyond ±15° needs at_speed (turret.hpp:195). From the geometry (pockets Ø15 on r21, outlet Ø16, pockets at ±60/180 at park; DESIGN_LOG lines 72 and 133), a pocket first overlaps the outlet at |disc| ≈ 16.7°. The margin is only 1.7°, but an M&M cannot drop through a sliver of overlap.
- The fire task's first-time park goes to 0°, which is closed.

Caveat: a fault raised by the tick does not cut short a stroke already in progress (R1-06).

S3 pass: a missing read-back becomes 999 and counts as a jam (turret.hpp:478-480). The jam path:
- unloads the feeder (481-482);
- stops the flywheel with `fw_.stop()` (483);
- latches the fault with `latch_fault` (488).

`fire` refuses while the fault is latched (283). Only `clear_fault` (316-320, called from `clear` at main.cpp:400) resets it.

S4 pass:
- `JointMap::to_counts` clamps to the soft limits and then to 0..1000 (joint_map.hpp:33-37).
- The limits are pan ±90, tilt 0..45 and feed ±60 (settings.hpp joint defaults). Nothing in the console or in NVS can change min/max; the turret's copy comes from `init`/`set_joint` (turret.hpp:95-98, 160-163).
- `servo raw` is the explicit bypass and is range-checked to 0..1000 (main.cpp:313-322).

S5 pass:
- ENCODER, OVERSPEED and STALL go through `fault_locked` (flywheel.hpp:538-541, 569-579), then `coast_locked` and `motor_->disable()` (427-435).
- The fault latches until `clear_fault` (357-366).
- Setpoints are clamped to `max_rpm` (288-289, 311-312).
- Console voltage ceilings: vlim ≤ supply × 0.5, vopen ≤ 4 V, valign ≤ 3 V (main.cpp:222, 227, 232).
- Caveat: values loaded from NVS are not re-clamped (R1-12, MINOR).

S6 pass:
- With a stored calibration, `init` passes a known direction and a non-zero zero to `motor_->initialize` (flywheel.hpp:192-201). Exactly 0 is nudged to 1e-6.
- espp then skips both alignment motions (bldc_motor.hpp:693-698, 806).
- `enable()` with zero duty does not move the motor.
- Turret init sends no move (turret.hpp:94-151). The poll task only reads. The IMU task only reads.
- Residual risk, reachable only through corrupt NVS: `calibrated=true` with `sensor_dir=0` would run the direction sweep at boot.

S7 pass: none of the new behaviours can fire on its own. The tip guard only aborts and coasts (main.cpp:521-525). Firing still comes only from the `fire` command, bounded to 1..20 shots (turret.hpp:304). Aiming during a burst is an operator command.

## Previous findings
none (round 1)

## Findings
R1-01 [BLOCKER] main/flywheel.hpp:449-453, 467-473: an abort can be lost (stop, watchdog, OTA or tip). `abort_calibration()` relies on `driver_->disable()`, which returns early when the driver is not enabled yet (bldc_driver.hpp:140-143). The cal task has already passed its `!cal_abort_` check.
  scenario: `fw cal`, then `stop` (or the watchdog, or a tip) lands after line 467 and before `BldcDriver::enable()` sets `enabled_` (bldc_driver.hpp:114-129, inside `BldcMotor::initialize` at bldc_motor.hpp:197). `disable()` is a no-op. `enable()` then turns the bridge on, and the full alignment runs: about 3.1 s at FREERTOS_HZ=1000 (2 × 501 × 2 ms sweeps + 200 + 700 + 20 + 200 ms) at `valign` (up to 3 V). Only after that is the result reported as aborted. The improver acknowledged this gap, but it is still an S1 break. The window is microseconds wide, but no path closes it.
  evidence: read flywheel.hpp:327-353, 447-503; espp bldc_motor.hpp:168-201, 740-830; bldc_driver.hpp:114-147.
  fix: in `tick()`, which runs at 4 kHz in every mode, add `if (mode_ == Mode::Calibrating && cal_abort_ && driver_->is_enabled()) driver_->disable();` before the early return at line 526. That bounds a missed abort to one tick (250 µs).

R1-02 [MAJOR] main/main.cpp:338-351 with main/tip_guard.hpp:103-113: `imu level` while TIPPED clears the guard's internal `tipped_` without emitting `Cleared`, so `g_tipped` stays true until reboot or `imu guard off`.
  scenario: the guard trips, for example because the boot-time auto-reference caught the robot being handled. The operator sets it down and presses the panel's Level here button (`imu level`). It answers `ok`, and `base_tilt` reads about 0. But `g_tipped` is never reset: only a `Cleared` event resets it (main.cpp:526), and `level_here` has just made that event impossible. From then on `clear`, `fw spin`, `fw open`, `fw cal`, `fire` and `feed` all answer `! ...: base is tipped 0 deg (stand it up, then 'clear')`. The README's recovery steps do not work.
  evidence: read tip_guard.hpp:76-113 (`level_here` sets `tipped_=false`, and `update` only emits `Cleared` from `tipped_==true`) and main.cpp:139-144, 396-398, 519-528.
  fix: in `imu_step`, when `level_here()` succeeds, set `g_tipped = false` and print the "base level again" line. Add a host test, for example by having `level_here` return or record a Cleared event.

R1-03 [MAJOR] main/turret.hpp:340-342, main/main.cpp:122/127 and main/main.cpp:332-335: non-finite floats print as `nan`, which makes the `@servo`, `@status` and `@imu` lines invalid JSON. The panel swallows the parse error (launcher.html:341), so `onAt` never runs for that line.
  scenario 1: right after boot, or after `servo unload <joint>` (turret.hpp:225 sets cmd to NaN), `servo read` prints `"cmd":nan`. A joint that has not answered a read also prints `"deg":nan`. The panel's servo table then never updates during the hand-zeroing flow (unload, place, `servo zero`, `servo read`, launcher.html:705).
  scenario 2: on a board where the IMU is absent, or before the auto-reference settles, `@status` prints `"base_tilt":nan`. The whole status table and the tip readout stop updating. `@imu` behaves the same way.
  evidence: `std::format("{:.1f}", NAN)` gives `nan`, and `JSON.parse` rejects it ("Unexpected token 'a'"), checked with a scratch test in /tmp/mml-review1-nan. espp's format.hpp is fmt, which prints NaN the same way. The `@servo` case was already present in snap-0. The `@status` and `@imu` cases are new this round.
  fix: one helper that prints `null` for non-finite values, used in `print_status`, `cmd_imu` and `servo_json`.

R1-04 [MINOR] main/flywheel.hpp:348-355 vs 476-497: a `fault()` during calibration is overwritten. `cal_loop` sets `mode_ = Mode::Off` unconditionally (line 496). `fault_locked`'s `motor_->disable()` also runs while the cal task is inside `motor_->initialize()`, which contradicts the comment at line 465.
  scenario: the base tips during `fw cal` (main.cpp:524). The calibration aborts correctly, but the TIPPED latch is lost. Once the base is level, `g_tipped` clears itself (main.cpp:526-527) and `fw spin` works without `clear`, contrary to the README ("latches the flywheel fault TIPPED").
  evidence: code read.
  fix: `if (mode_ != Mode::Fault) mode_ = Mode::Off;` in `cal_loop`, and in `fault()` while Calibrating, set the fault without touching `motor_`.

R1-05 [MINOR] main/turret.hpp:300-307, 311-314, 423-428: an abort that lands between `fire()` and the fire task waking leaves `firing_ = true` forever.
  scenario: `fire 3`, then a watchdog, tip or OTA `abort_fire()` (pending_=0) arrives before the fire task evaluates its predicate. `fire_loop` returns at line 427 without clearing `firing_`. After that, `fire` answers "already firing", `feed` answers "firing", the servo poll stays paused, and the state reads 5 until reboot. `clear` does not reset it.
  fix: clear `firing_` (under `fire_m_`) on the early-return path.

R1-06 [MINOR] main/turret.hpp:403-413, 456: faults raised by the tick (OVERSPEED, STALL, ENCODER at flywheel.hpp:538-579) do not abort a stroke in progress. `sleep_sampling` only watches `abort_`. The stroke opens and dwells over a wheel that is already coasting. The fault is only noticed before the next shot (439).
  fix: have `sleep_sampling` also stop on `fw_.mode() == Flywheel::Mode::Fault` and park.

R1-07 [MINOR] main/flywheel.hpp:437-445, 586-587: the esp_timer task (the FOC tick) does blocking and allocating work:
- `fault_locked` calls `fmt::format` and `fmt::print`, which takes newlib's stdout lock and does a UART `::write` in `demo_link` `vfs_write` (demo_link.hpp:322-327).
- Every normal ramp-down ends in `coast_locked`, which calls `BldcDriver::disable()`, which calls `logger_.info("Disabling")` (bldc_driver.hpp:144). That runs at INFO level until a `fw cal` in the same boot sets WARN (flywheel.hpp:474).

This was already present in snap-0. fix: set the driver's log level to WARN in `init`, and post fault text to the console task instead of printing from the tick.

R1-08 [MINOR] main/flywheel.hpp:260-263, 479-483 and main/main.cpp:177-182, 482-491: calibration bookkeeping has three problems.
- `fw cal clear` during a running calibration answers ok but does nothing, and then `poll_calibration` sets and auto-saves `calibrated=true`.
- An aborted re-calibration forgets the good in-RAM calibration and sets `s.calibrated=false`, so a later `save` erases the NVS calibration.
- The auto-save in `poll_calibration` also persists any unsaved tweaks, such as `fw pp`.

R1-09 [MINOR] web/launcher.html:595: Disconnect sends `wd 0` and not `stop`. If the operator disconnects with the wheel spinning, it keeps running with the watchdog disarmed. This was already present in snap-0.

R1-10 [MINOR] web/launcher.html:310-323, 584: `cmd()` resolves on the first `ok` or `!` line after it is sent. That includes the `ok ping` reply to a ping sent 500 ms earlier, and the asynchronous `! TIPPED`, `! fw cal: ...` and `! watchdog` lines. This round adds more asynchronous `!` lines, so more results get pinned on the wrong command.

R1-11 [MINOR] main/main.cpp:353-358, main/tip_guard.hpp:98-107: `imu guard on` while the guard is already tripped internally never trips, because `Tripped` is only emitted on the transition.
  scenario: guard off, the robot is tipped, then guard on: there is no TIPPED and the wheel can spin. A related issue: the auto-reference captures whatever pose the board is in for the first 0.5 s after boot (tip_guard.hpp:70-79).
  fix: in `imu_step`, latch when `g_imu_guard_on && guard.tipped() && !g_tipped`.

R1-12 [MINOR] main/settings.hpp `load()`: `vlim`, `vopen`, `valign`, `max_rpm` and `imu_trip_deg` from NVS are not re-clamped to the console's hard ceilings. Only firmware writes NVS today, so S5 holds, but it should not depend on that.

R1-13 [MINOR] main/flywheel.hpp:228-233, 316, 428 with main/main.cpp:576-577 and 566-567: if `Flywheel::init` fails, `motor_` and the cal task are null.
- `fw vlim` and `fw open` dereference null.
- `before_ota` → `coast()` → `coast_locked()` dereferences null, so an OTA would crash.
- `fw cal` leaves the mode stuck at Calibrating.

That contradicts the log line "turret and console still run".

R1-14 [MINOR] main/main.cpp:166-174: a `stop` from the panel queues behind a blocking console command. `fw enc 5` while the wheel spins delays `stop` by up to 5 s. This was already present in snap-0. A fast path for `stop` in the USB RX handler would remove the dependency on the console task.

R1-15 [MINOR] README.md "Base tip guard": says LSM6DS3, but the BSP driver is `espp::Lsm6dso` (motorgo-axis.hpp:51). The file-table row for `test/host/` still says "for the protocol", but it also covers the joint map and the tip guard now.

R1-16 [MINOR] web/launcher.html:79, 818-896: the live model is not worth much risk on an un-powered robot, and it takes none, because it runs in its own module script. But if the jsDelivr import fails (offline), the module never runs and the "Loading model" spinner stays forever: the static `import` fails before the try/catch can catch it. The model also adds 4.8 MB of STLs to the repo. The pivots and gear couplings match DESIGN_LOG "Joints" (pan pinion -1, feeder pinion -44/30 = -1.467, flywheel and tilt about X).

## Verified improver claims
- One mutex, try-lock tick, `foc_lock_skips` in `@status`: true (flywheel.hpp:529-533, main.cpp:121, 126).
- Calibration on its own task, aborted by stop, watchdog, OTA and faults: true, except the race in R1-01. The result arrives as `@cal`: true (main.cpp:494-496).
- Fault strings behind a mutex, Settings only on the console task, cached atomics, locked joint maps, FireParams snapshot: true.
- Stop mid-stroke parks the feeder, fire refuses on a flywheel fault, at_speed cleared on faults and stops: true.
- `feed` beyond ±15° gated on at_speed: true.
- Zero nudge: true.
- 3D model and tip guard present and reachable: true, with bugs R1-02, R1-03 and R1-11.
- Build clean, tests pass, `node --check` passes: true. Both extracted scripts pass, the module one checked as .mjs.

## Fix list for the improver (BLOCKER and MAJOR, in priority order)
1. R1-01: close the calibration abort race. Re-assert `driver_->disable()` from `tick()` while `mode_ == Calibrating && cal_abort_`.
2. R1-02: reset `g_tipped` when `imu level` succeeds, and add a host test of that hand-off.
3. R1-03: print `null` instead of `nan` in `@servo`, `@status` and `@imu`. Re-check the panel's servo table after `servo unload`.
