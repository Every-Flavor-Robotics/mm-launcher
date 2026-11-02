# Review 2
VERDICT: CONTINUE

Scope: `diff -ru /tmp/mml-snap-1 /tmp/mml-snap-2` (excluding dependencies.lock and sdkconfig). Changed: main/flywheel.hpp, main/main.cpp, main/demo_link.hpp, main/settings.hpp, main/tip_guard.hpp, main/turret.hpp, README.md, web/launcher.html, test/host/Makefile, test/host/test_tip_guard.cpp, .gitignore. New: main/jsonf.hpp, web/gamepad.js, test/host/test_jsonf.cpp, test/host/test_gamepad.mjs. Apart from build products, the working tree matches snap-2.

I read every changed file in full. Where the changed code calls into espp, I also read it: `bldc_driver.hpp` (enable/disable/set_pwm, generator actions, dead time), `bldc_motor.hpp` (initialize, init_foc, align_sensor, loop_foc, move), `logger.hpp` (atomic level, checked before formatting), `pid.hpp`, `spi.cpp` (`Device::transfer`), the `motorgo-axis` BSP (`gpio_enable = -1`, `initialize_imu`) and `lsm6dso.hpp` (WHO_AM_I 0x6A accepted).

The one finding that blocks DONE is R2-01: `stop` is a driven ramp whose length is set by `fw ramp`. Everything round 1 asked for is fixed.

## Done criteria
D1 pass: a fresh build (`idf.py -B /tmp/mml-review2-build build`) exits 0. It compiles `main.cpp.obj` (log line 1437), and the whole log has 0 `warning:` and 0 `error:` lines.

D2 pass: `make -C test/host clean && make -C test/host` passes all five suites with 0 failures each: hiwonder protocol, joint map, tip guard, jsonf, and gamepad (node). Each pure-logic module changed this round has a test of its new behaviour, and the tests can fail:
- `TipLatch` (test_tip_guard.cpp:85-122) covers trip, the `level_here` clear (R1-02), guard-on-while-tipped (R1-11) and guard-off.
- `jsonf::num` and `jsonf::str` cover NaN, ±inf, -0 and escaping.
- `gamepad.js` covers deadzone and expo, sign conventions, clamps, the dt cap, edges, and the deadman and at-speed gate.

`Settings::sanitize()` is pure logic inside a module that includes NVS, so it has no host test. I checked its ranges by hand against every console clamp (main.cpp:221-251, 368, 451, 471-476), and they match.

D3 fail: one MAJOR is open (R2-01).

D4 fail: S1 fails (R2-01). S2–S7 pass.

D5 pass:
- Every README command exists in `handle_line` / `cmd_*`.
- The panel sends nothing new except `stop` on Disconnect.
- Every key the panel reads is emitted, including the new `kept_previous`. `fw_ok` is emitted and not read, which is harmless.
- The importmap is valid JSON. `node --check` passes on the classic script, both module scripts (as .mjs) and `web/gamepad.js`.
- The 13 telemetry channels match: main.cpp:584-585 against the panel's `DEFAULT_CH`.
- The firmware now prints `null` for unknown values, and every panel handler guards for it (`onImu` uses `Number.isFinite`, `onServo` checks for null).

D6 pass: gamepad aim works end to end. The panel's rAF poll goes through `stepAim` and `decide` (web/gamepad.js), then the existing `aimThrottled()` (an `aim` command), the Fire button (a `fire 1` command) and the Stop button (`stop`), and from there to the firmware's existing `aim`, `fire` and `stop` handlers. The firmware's DemoLink stop fast path and the `@cal`/`@status` changes are also live.

## Safety invariants
S1 fail. The calibration abort race (R1-01) is closed, but `stop` is still a driven ramp whose duration the operator can set (R2-01).

What holds:
- **Calibration abort.** The tick re-asserts the abort every 250 µs while a calibration runs: `if (cal_running_ && cal_abort_ && driver_->is_enabled()) driver_->disable();` (flywheel.hpp:627-630). It runs before the try-lock, so a lock skip cannot delay it. `cal_running_` is set in `start_calibration` (267) and cleared under `mutex_` only after `motor_->disable()` and `restore()` (562-592).
- **Panel Stop and Esc.** They send `stop` (launcher.html `stopBtn.onclick`, the keydown handler). The DemoLink hook runs `stop_all()` on the USB worker before the line is queued (demo_link.hpp:266-267, main.cpp:598-604). The queued `stop` still runs on the console afterwards. So a `fw spin` already in the queue cannot outlive the stop. It can only run briefly between the two.
- **`stop_all()`** (main.cpp:136-139) is lock-free:
  - `abort_fire` writes two atomics (turret.hpp:331-334);
  - `Flywheel::stop` writes atomics, plus `driver_->disable()` when a calibration is running (flywheel.hpp:363-368, 528-532);
  - the driver's logger is at WARN or ERROR, and espp checks the atomic level before formatting, so nothing prints on the USB worker.
- **Watchdog.** It runs `stop_all` and counts Calibrating as moving (main.cpp:655-664).
- **`before_ota`.** It runs `coast()`: it aborts a running calibration, otherwise `coast_locked` (flywheel.hpp:371-382). With `!ok_` it is a no-op, so the round-1 null dereference is gone.
- **Tip trip.** It runs `fault()`, which coasts or aborts at once (flywheel.hpp:388-407).
- **Independence.** No stop path touches the servo bus or needs the USB link, apart from the panel delivering the line.

What fails: in closed loop and in open loop, `stop` slews the setpoint at `ramp_` (flywheel.hpp:648-653). The bridge is released only at `set == 0` and |rpm| < 150 (691-692). `fw ramp` accepts 50–20000 rpm/s (main.cpp:243-247, settings.hpp:143), so a Stop/Esc/watchdog stop keeps the bridge driving the wheel for up to 7000/50 = 140 s (R2-01).

S2 pass:
- `Turret::fire` refuses when the bus is missing, on a turret fault, on a flywheel Fault, while already firing, or when not `at_speed()` (turret.hpp:298-329). `at_speed()` needs Closed mode (flywheel.hpp:481).
- `fire` refuses while tipped (main.cpp:458).
- Speed and fault are re-checked before every stroke (turret.hpp:470).
- `cut()` now ends a stroke on abort, on a turret fault, or on a flywheel Fault raised by the tick, and then parks the feeder (428, 488-492, 502-505).
- The R1-05 stuck-`firing_` path is fixed under `fire_m_` (452-458).
- Manual feed beyond ±15° still needs `at_speed` (204).
- The gamepad's A only clicks the Fire button. It does that only with LB held and telemetry state 4, and only when the button is enabled (`decide`, launcher.html gamepad module). The firmware re-checks everything.

S3 pass: a missing read-back counts as 999, which is a jam. The jam path:
- unloads the feeder (turret.hpp:514);
- calls `fw_.stop()` (515);
- latches the fault (520).

`fire` refuses while the fault is latched (303), and only `clear` resets it. The flywheel stop on a jam is the same ramp as R2-01.

S4 pass: unchanged since round 1. `JointMap::to_counts` clamps. `sanitize()` now also clamps the NVS joint `zero` to 0..1000 and `dir` to ±1 (settings.hpp:151-154). `servo raw` is the explicit, range-checked bypass (main.cpp:320-330). The gamepad clamps to ±90 and 0..45 before sending, and the firmware clamps again.

S5 pass:
- ENCODER, OVERSPEED and STALL run `fault_locked`, which calls `coast_locked` and sets the fault state (flywheel.hpp:521-524, 643-645, 674-684). The fault latches until `clear_fault` (409-417).
- Setpoints are clamped to `max_rpm` (321, 348).
- The console ceilings are unchanged: vlim ≤ 0.5 × supply, vopen ≤ 4 V, valign ≤ 3 V.
- NVS values are now re-clamped to the same ceilings (settings.hpp:130-160), which closes R1-12.
- Caveat: on this board "coast" is a three-phase low-side short, not a float (R2-05).

S6 pass:
- A stored calibration still uses `initialize(zero≠0, dir)`, which makes no motion (flywheel.hpp:202-211).
- `sanitize()` now drops `calibrated` when `sensor_dir == 0` or the zero is non-finite (settings.hpp:148-149). That closes the round-1 corrupt-NVS residual that could run the direction sweep at boot.
- Boot sends no servo move. The poll and IMU tasks only read. A TipLatch trip at boot only latches a fault.

S7 pass:
- The gamepad cannot spin the wheel up; it has no spin binding.
- It fires one shot only on a new A press with LB held and state 4. Holding A does nothing more.
- B stops even while gamepad aim is unticked.
- The TipLatch only aborts and faults.
- Nothing new fires on its own.

## Previous findings
R1-01 fixed: the tick re-disables the driver while `cal_running_ && cal_abort_` (flywheel.hpp:627-630). It keys on `cal_running_`, which stays true after a mid-run fault sets the mode to Fault (401-404, 590-592), so a missed abort lasts at most one 250 µs tick. Residual: on an aborted re-calibration, `restore()` briefly re-enables the bridge (R2-04, MINOR).

R1-02 fixed: `TipLatch::step(guard_on, guard.tipped())` is level-based (tip_guard.hpp:140-157). `level_here()` clearing `tipped_` now yields `Clear`, and `g_tipped` is reset (main.cpp:538-553). Host-tested (test_tip_guard.cpp:102-107).

R1-03 fixed: `jsonf::num` prints `null` for non-finite values and `jsonf::str` escapes. They are used in @status (main.cpp:118-132), @imu (340-344), @enc (177-179), @cal (504-507) and @servo (turret.hpp:358-369; `counts` is null until a joint has answered). @shot never carries a NaN, because 999 is substituted. Host-tested.

R1-04 fixed: `fault()` during a calibration only aborts and latches, without touching `motor_` (flywheel.hpp:401-404). `cal_loop` keeps a Fault mode (590-591). `clear_fault` waits for `!cal_running_` (413). See R2-03 for a leftover.

R1-05 fixed: turret.hpp:452-458.

R1-06 fixed: `cut()` is used in `sleep_sampling`, after each stroke and in the recovery loop (turret.hpp:428-432, 488, 502, 527).

R1-07 fixed: the tick no longer formats or prints. Faults are a code plus two floats in atomics (flywheel.hpp:514-520), announced by `poll_faults` on the console (main.cpp:512-515). The driver's logger is at WARN from `init` (flywheel.hpp:150), so `disable()`'s "Disabling" does not print. The encoder's logger is NONE (180). Residual blocking: `spi_device_transmit` waits on a semaphore for each encoder read (R2-07, MINOR, pre-existing).

R1-08 fixed:
- `fw cal clear` refuses unless the mode is Off or Fault (flywheel.hpp:281-294).
- A failed or aborted run restores the previous calibration (563-587), and `kept_previous` keeps `s.calibrated` (main.cpp:497-503).
- The auto-save writes only `cal`, `zel` and `sdir` (settings.hpp:168-182), with the same keys and types as `save()` and `load()`.

R1-09 fixed: Disconnect sends `stop` and then `wd 0` (launcher.html `disconnect`).

R1-10 fixed, with a residual: `replyTo()` now matches the command's first word. I checked every `ok`/`err` site in main.cpp against every command the panel sends, and all of them start with the command's first word or match the usage/unknown/too-long regex. The residual is R2-02 (MINOR).

R1-11 partly fixed:
- Guard-on while tipped now trips (TipLatch, tested).
- Still open (MINOR): the boot auto-reference averages whatever pose the board has for the first 0.5 s (tip_guard.hpp, unchanged).

R1-12 fixed: `sanitize()` (settings.hpp:130-160).

R1-13 fixed:
- `ok_` guards every Flywheel entry point (flywheel.hpp:256, 282, 298, 338, 374, 395).
- `apply_settings` and `coast_locked` check `motor_`.
- Every `bus_->` use is guarded (turret.hpp:172, 193, 223, 230, 250, 289, 300, 355, 416).
- `fw_ok` is in @status.
- Leftover (MINOR, folded into R2-03): `fault()` with `!ok_` sets a fault code that `clear` can never reset.

R1-14 fixed for the panel: the DemoLink hook (main.cpp:598-604). A `stop` typed on CDC still queues, as the README says.

R1-15 fixed: README now says LSM6DS3TR driven by `Lsm6dso`, and the test row is updated. espp's `Lsm6dso` accepts WHO_AM_I 0x6A, and the 2 g full-scale bits are 00 on both parts, so the tip guard's 1 g magnitude gate should see sane values. This is still untested on hardware.

R1-16 fixed: three.js is now loaded with a dynamic `import()` inside the `try`. `v.onFrame` is guarded with `if (v)`. The offline message is clear.

## Findings
R2-01 [MAJOR] main/flywheel.hpp:648-653, 691-692 with main/main.cpp:243-247: `stop` (panel Stop, Esc, gamepad B, host watchdog, FEED_JAM) decelerates at `fw ramp`, which accepts down to 50 rpm/s. A stop can therefore keep the bridge actively driving the wheel for up to 140 s (7000/50), or 120 s from 6000 rpm.
  scenario: in B5 the operator follows the launch-rig protocol's "gentle ramp" (mm-launch-hw/test-prints/launch-rig/README.md:155) and applies `fw ramp 200` from the panel's Ramp field. The wheel runs at 6000 rpm, starts to wobble, and the operator hits Esc. `stop_all()` sets the target to 0. The tick then slews the setpoint down at 200 rpm/s with the PI loop tracking it, so the motor holds the wheel on the slow setpoint for 30 s before `coast_locked()`. Any ramp below the wheel's free coast-down rate makes Stop keep the wheel spinning longer than cutting power would. A watchdog trip from a dead host behaves the same way, unattended. Only the tip guard and OTA cut the bridge at once. The firmware README documents the ramp (README.md:74), but that does not satisfy S1: Stop and the watchdog are the operator's emergency controls, and their stop time must not depend on a tuning value.
  evidence: code read (tick slew 648-653, release condition 691-692, `stop()` 363-368, ramp clamp main.cpp:244 and settings.hpp:143). Arithmetic: 6000/200 = 30 s, 7000/50 = 140 s, default 6000/1500 = 4 s.
  fix: bound the stop, independent of `fw ramp`. For example, have `stop()` set a stop flag and its own decel floor (a stop never takes longer than about 3 s from `max_rpm`), or coast once a stop has been in effect for N s. Keep the plain `fw ramp` slew for `fw spin <lower rpm>`. Pick with R2-05 in mind: a faster driven decel pushes more energy back into a bench supply that may not sink current, while `coast_locked` on this board short-brakes the windings instead.

R2-02 [MINOR] web/launcher.html `replyTo()` with main/main.cpp:502: a pending `fw ...` command still completes on an unrelated asynchronous `! fw cal: ...` line. Separately, a multi-shot `fire` stopped between shots ends without a terminating line, so the Fire button stays busy until its timeout.
  scenario 1: during a failing or aborted calibration the operator presses Apply (`fw gains ...`). The gains wait rejects with "fw cal: alignment failed", the real `ok fw gains` is orphaned, and the console shows the wrong error.
  scenario 2: `fire 5`, then Stop during the gap after shot 1. `fire_loop` leaves its `while (... && !abort_)` silently (turret.hpp:469), so the Fire button stays "Firing" for up to 4 + 5 × 3 = 19 s. This is pre-existing, and the gamepad fires n = 1 so it is not affected.
  fix: print `# fire stopped` when the loop exits on `abort_`. For calibration, prefix the async result with something other than the command word, for example `! cal:`.

R2-03 [MINOR] main/flywheel.hpp:286-292, 409-417: while a calibration with a latched fault is still running, `fw cal clear` and `clear` misbehave.
  scenario: the base tips during `fw cal`. `fault()` sets the mode to Fault while the cal task is still in espp's ~3 s alignment sleeps. Two things then go wrong:
  - `fw cal clear` passes the Off/Fault check and calls `motor_->forget_calibration()` while the cal task owns `motor_`, which is a data race. `restore()` then reinstates the previous calibration. Settings ends up saying uncalibrated while the flywheel says calibrated, and `fw spin` works on the "cleared" calibration.
  - `clear` in the same window answers `ok clear`, but the fault stays latched (`!cal_running_` is false).

  Also: `fault()` with `!ok_` (395-398) sets a fault code that `clear_fault` never resets, because the mode is not Fault, so `fw_fault` stays non-empty in @status.
  fix: require `!cal_running_` in `forget_calibration`. Make `clear` say "calibration still finishing" when it does nothing. Reset the fault code in `clear_fault` when the mode is not Fault.

R2-04 [MINOR] main/flywheel.hpp:563-576: after an aborted re-calibration (`had_cal`), `restore()` calls `motor_->initialize(prev_zero, prev_dir)`. espp's `initialize()` calls `enable()` (bldc_motor.hpp:196-200), which restarts the MCPWM timer with the comparators still at the last alignment vector, because every `set_pwm` after the abort was a no-op. So the phases are driven at up to `valign` (3 V) until the tick's R1-01 check disables them, at most 250 µs later. It also prints "Init FOC / Using provided ... / Aligning sensor" right after the abort.
  scenario: `fw cal` with a stored calibration, then `stop` mid-sweep. A sub-millisecond pulse reaches the motor at `valign`, and the console shows an apparent second alignment start. The pulse is harmless, but it contradicts "aborted".
  fix: restore the three fields directly in `FocMotor` (mirroring `forget_calibration()`: set the zero and direction, and `status_ = READY`) instead of calling `initialize()`.

R2-05 [MINOR] main/flywheel.hpp:502-511 (`coast_locked`) and README "coasts the bridge": on the MotorGo Axis, `BldcDriver::disable()` stops the MCPWM timer at its peak and does not force any gate level (its doc comment says it does, but the code doesn't), and the BSP has `gpio_enable = -1`. With the actions "up-compare → LOW, down-compare → HIGH" and the low side inverted by the dead-time block, all three low-side FETs stay on. Every "coast" (tip, OTA, OVERSPEED, STALL, ENCODER) is therefore a three-phase short brake.
  scenario: an ENCODER fault at 6000 rpm short-brakes the wheel. The current is about BEMF / |Z|, roughly 3.2 V of back-EMF, which is no more than the stall current a 4 V `vlim` already allows. It is probably safe for the FETs, but the wheel and its hub see a hard deceleration torque, and the behaviour is not "coast" as documented.
  evidence: bldc_driver.hpp:139-150, 494-539; motorgo-axis.cpp:70.
  fix: none needed for bring-up. Document it, and watch the first fault at B5. A true float would need `mcpwm_generator_set_force_level(..., 0, true)` on all six generators (an upstream espp fix).

R2-06 [MINOR] main/flywheel.hpp:245-246: `apply_settings` during a calibration returns before `set_velocity_gains` and `set_align_voltage`, and `cal_loop` re-applies only `vlim` (589). `fw gains` sent during the ~3 s calibration answers ok, but the PI keeps the old gains until the next `fw gains`/`fw vlim`. This is pre-existing (snap-1 had the same early return on Calibrating).
  fix: call `apply_settings` again after a calibration finishes, or store the gains in atomics and apply them in `cal_loop`'s hand-back.

R2-07 [MINOR] main/flywheel.hpp:171-174, 614: the tick's encoder read is espp `Spi::Device::transfer`, which calls `spi_device_transmit` (spi.cpp:288). That is an interrupt-driven transaction with a semaphore wait on the esp_timer task, and `Spi::Device`'s own logger prints on a transmit error. The wait is bounded at a few tens of µs, and `.log_level = NONE` on the encoder does not silence the SPI device logger. The tick is otherwise free of printing and allocation: atomics, try-lock, `Pid`'s uncontended recursive mutex, and MCPWM register calls. This is pre-existing and does not contradict the "never blocks indefinitely" intent.
  fix (optional): use `polling_transmit` for the 3-byte SSI read, and set the SPI device's log level to NONE.

R1-11b [MINOR] main/tip_guard.hpp auto-reference: carried over. With no stored reference, whatever pose the board has in the first 0.5 s after boot becomes "level". Run `imu level` and `save` once at bring-up.

## The three areas you flagged
- **DemoLink `on_console_line` hook.** It runs on the USB worker with no DemoLink lock held, before `push_bytes` takes `rx_mutex_` (demo_link.hpp:263-271). The lambda only trims and compares a `string_view`, then calls `stop_all()`, which touches only atomics and possibly `driver_->disable()` (MCPWM API, no print at WARN/ERROR). It never takes `Flywheel::mutex_`, `fire_m_` or `rx_mutex_`, so it cannot deadlock against the console, the tick or the cal task. It cannot lose a stop: the line is still queued, and the console's `stop` runs after any command already in the queue. A concurrent `fire()` on the console could overwrite `abort_`, but the same `stop_all` clears `at_speed_` and the tick cannot set it again while the target is 0, so `fire_loop`'s at-speed check (turret.hpp:470) refuses the first stroke. A formal nit: the hook reads `g_fw` and `g_turret` (plain `unique_ptr`s) while `app_main` may be assigning them (main.cpp:609-612). It is benign on Xtensa, and no failure scenario follows from it.
- **Is `stop` fast enough?** Only at sensible ramps; see R2-01.
- **FOC tick.** It is free of printing and allocation; see R1-07 and R2-07.

## Verified improver claims
- R1-01, R1-02, R1-03: true, as above.
- R1-04 to R1-16: true, with the residuals noted (R2-02, R2-03, R2-04, R1-11b).
- Gamepad: true. The left stick aims, the right stick fine-aims, B always stops (even unticked), and A fires only with LB held and state 4, through the existing Fire button. The pad has no spin binding.
- The known gaps you flagged:
  - the ramped stop is real, and I rate it MAJOR (R2-01);
  - the `! fw cal:` misattribution is real, and I rate it MINOR (R2-02);
  - IMU compatibility looks right on paper (WHO_AM_I 0x6A accepted, matching FS bits) but is unverified on hardware.
- The build is clean, all five host suites pass, and `node --check` passes: all true.

## Fix list for the improver (BLOCKER and MAJOR, in priority order)
1. R2-01: make `stop` (panel Stop, Esc, gamepad B, watchdog, FEED_JAM) finish in a bounded time, a few seconds from `max_rpm`, whatever `fw ramp` is set to. Keep `fw ramp` for setpoint changes. Update the README's `stop` / `fw stop` rows to match, and add a host-testable helper for the stop-decel rule if you factor one out.
