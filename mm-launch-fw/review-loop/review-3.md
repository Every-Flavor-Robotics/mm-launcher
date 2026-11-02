# Review 3
VERDICT: DONE

Scope: `diff -ru /tmp/mml-snap-2 /tmp/mml-snap-3` (excluding dependencies.lock and sdkconfig). Changed: main/flywheel.hpp, main/main.cpp, main/turret.hpp, main/tip_guard.hpp, README.md, web/launcher.html, test/host/Makefile, test/host/test_tip_guard.cpp, .gitignore. New: main/stop_rule.hpp, test/host/test_stop_rule.cpp. Apart from build products, the working tree matches snap-3.

I read every changed file in full. I also read the espp code the changes call: `BldcMotor::initialize`, `init_foc` and `align_sensor` (bldc_motor.hpp:192-201, 683-830), `BldcDriver::enable` (bldc_driver.hpp:114-133), `Spi::Device` (a `BaseComponent`, spi.hpp:169, and its logger in spi.cpp:383-407), plus the wheel geometry in params.py:223-225.

Every review-2 finding is closed, including all the MINORs. No BLOCKER or MAJOR is open. The three new findings are MINOR. The bring-up watch list at the end is the gate for first power-up.

## Done criteria
D1 pass: a fresh build (`idf.py -B /tmp/mml-review3-build build`) exits 0. It compiles `main.cpp.obj` (log line 1437), and the whole log has 0 `warning:` lines and 0 `error:` lines.

D2 pass: `make -C test/host clean && make -C test/host` passes all six suites with 0 failures each: hiwonder protocol, joint map, tip guard, jsonf, stop rule, and gamepad (node). Each pure-logic module changed this round has a test, and I checked by mutation that the tests can fail:
- **stop_rule.hpp.** Removing the deadline fails 5 checks (test_stop_rule.cpp:54, 60). Making `rate()` return `fw ramp` unchanged fails 7 checks (36-51, 56).
- **tip_guard.hpp, the steady-window check.** Disabling it fails 3 checks (test_tip_guard.cpp:55, 59).

The fire-done bookkeeping (turret.hpp) and the tick wiring (flywheel.hpp) are not pure modules, so I verified them by reading the code (see S1 and R2-02).

D3 pass: zero open BLOCKER or MAJOR findings. R2-01, the only MAJOR, is fixed. The R3 findings are all MINOR.

D4 pass: S1–S7 are each verified below.

D5 pass:
- The panel's command set is unchanged since round 2. Every command it sends exists in `handle_line`.
- The only panel change is the Fire wait (launcher.html:740). It ends on `! fire:` (main.cpp:468 `err("fire: "+why)`, tipped refusal 459), on `! usage`, `! TIPPED` or `! watchdog`, on `# fire done` (turret.hpp:458, 570), or on the n-th `@shot`.
- The Cal button waits for `@cal`, which main.cpp:507 always prints after the new async `! cal:` line (505). It still ends on the synchronous `! fw cal: …` refusals (main.cpp:194).
- `replyTo()` heads cannot match `! cal:`, because no command's first word is a prefix of "cal:".
- The README documents `# fire done`, `! cal:`, the `clear` refusal and the stop bound (README.md:75-76, 91, 96, 187, 191-200). No command was added or removed.
- `node --check` passes on the classic script, both module scripts (as .mjs) and web/gamepad.js. The importmap parses as JSON.

D6 pass, under the fix-only clause. Round 3 was designated fix-first, and the review-2 fix list (R2-01 only) is fully closed. The improver added no new capability, and none was required.

## Safety invariants
S1 pass. Every stop path sets the target to 0, and the tick's stop rule bounds what follows. The bound does not depend on `fw ramp`.

**The rule.** `stopping = tgt == 0` (flywheel.hpp:683). The slew rate is `fw ramp` clamped into [2000, 3000] rpm/s (stop_rule.hpp:47-49, applied at flywheel.hpp:685). `stop_elapsed_s_` grows by dt on every tick that runs with target 0 and resets otherwise (684). The drive is released when `elapsed ≥ 4 s`, or when `set == 0` and either open loop or |rpm| < 150 (stop_rule.hpp:60-66, applied at flywheel.hpp:725-726). `max_rpm` is capped at 7000 (settings.hpp:144), so the setpoint reaches 0 within 3.5 s and the drive is off by 4.0 s.

**Paths, all checked:**
- `stop` (main.cpp:399-401) and `fw stop` (216-218) call `stop_all()` (136-139), which runs `abort_fire()` and `Flywheel::stop()` (flywheel.hpp:382-387). Both are lock-free.
- The panel's Stop button, Esc and gamepad B send `stop`. The DemoLink hook runs `stop_all()` on the USB worker (main.cpp:603-607).
- The watchdog runs `stop_all()` (main.cpp:662-666) and counts Calibrating and firing as moving.
- A jam calls `fw_.stop()` (turret.hpp:523).
- `fw spin 0`: `spin()` sets target 0 (flywheel.hpp:338). From Off it releases on the first tick (set 0, rpm < 150). From Closed it follows the stop band.
- Open-loop stop: target 0, slew in the band, release at set 0 (stop_rule.hpp:65).
- A stop while the wheel is still ramping UP: the slew starts from the current setpoint (flywheel.hpp:681-685), so a lower setpoint means a shorter stop. `stop_elapsed_s_` starts at 0, because it was reset on every non-stop tick.
- A wheel that does not follow (PI saturated, encoder misreading, lost sync) is released at 4 s (stop_rule.hpp:63; tested in test_stop_rule.cpp:53-54, 58-60).
- `before_ota` calls `coast()` (main.cpp:589-595, flywheel.hpp:390-401), which releases at once.
- A tip calls `fault()` (main.cpp:547, flywheel.hpp:407-426), which releases at once or aborts a calibration.
- A calibration is aborted by `driver_->disable()` and the tick's re-assert (flywheel.hpp:385-386, 558-562, 658-661).

None of these paths touches the servo bus or needs the USB link, apart from the panel delivering its line.

**Races with the try-lock tick:**
- "Stopping" is not a mode, only target 0 inside Closed or OpenLoop.
- Closed→Off happens only in `coast_locked()`, and only under `mutex_` (tick 725-726, coast 399-400, fault 419-425).
- `spin()` and `open_loop()` change the mode and reset `stop_elapsed_s_` under the same mutex (339-350, 367-375). So a `fw spin` cannot interleave with a release.
- The only lock-free writers of `target_rpm_` (`stop`, `coast`, `fault`) write 0. So a stop that lands inside `spin()` after its target write still wins on the next tick.
- `stop_elapsed_s_` is a plain float, but every access holds `mutex_`: tick lines 684 and 725 run after the try-lock at 665-669, and spin and open_loop hold the lock.
- A tick that skips on the lock does not advance the deadline. That stretches 4 s only by the skipped ticks; `foc_lock_skips` is in @status.

**Is the 4 s release worse than the old fault path?** No. It uses the same `coast_locked()` as OVERSPEED, STALL, ENCODER and TIPPED, at no higher speed: the setpoint is already at or near 0 by then, and the old fault paths release at up to 8400 rpm (flywheel.hpp:707). It fires at speed only when the wheel has not followed the decel. In that case the round-2 code kept driving indefinitely, which was worse. See R3-02 for what is not reported when it happens.

S2 pass: unchanged since round 2.
- `Turret::fire` refuses on a missing bus, a turret fault, a flywheel Fault, already firing, or not at speed (turret.hpp:299-320). `at_speed()` needs Closed mode (flywheel.hpp:503).
- `fire` refuses while tipped (main.cpp:459).
- Speed and fault are re-checked before every stroke (turret.hpp:474-479), and `cut()` ends a stroke (429, 494-501, 509-513).
- `stop()` clears `at_speed_` at once (flywheel.hpp:384), so no stroke starts after a stop.

S3 pass: a missing read-back counts as 999 (turret.hpp:518-519), which is a jam. The jam path:
- unloads the feeder (522);
- stops the flywheel, now bounded at 4 s (523);
- latches the fault (528);
- ends the sequence with `# fire done …, ended by FEED_JAM` (532, 570).

`fire` refuses while the fault is latched (304). `clear` resets it only after any calibration has finished (main.cpp:403-411).

S4 pass: unchanged since round 2 (JointMap clamps, `sanitize()` clamps on the NVS zero and dir, `servo raw` as the explicit bypass). Nothing in this diff touches joints.

S5 pass:
- ENCODER, OVERSPEED and STALL go through `fault_locked` → `coast_locked` and latch (flywheel.hpp:551-554, 674-676, 707-718).
- Setpoints are clamped to `max_rpm` (338, 366).
- The console ceilings are unchanged: vlim ≤ 0.5 × supply, vopen ≤ 4 V, valign ≤ 3 V (main.cpp:225-240), and `sanitize()` re-clamps them from NVS.
- The calibration hand-back now re-applies kp, ki, valign and vlim from the atomics (flywheel.hpp:618-620). Those values passed through the same console clamps, so no ceiling is bypassed.
- On this board, "coast" means a three-phase short brake. It is documented (flywheel.hpp:524-531, README.md:200) and is a watch item below.

S6 pass:
- The boot path still uses `initialize(zero≠0, dir)` with both values known, so `align_sensor` skips the motion (flywheel.hpp:213-222; bldc_motor.hpp:754, 806).
- An aborted re-calibration now restores through `restore_calibration()` (flywheel.hpp:100-104, 597). It only writes three fields and never calls `enable()`, so the bridge stays off.
- The IMU auto-reference only reads (tip_guard.hpp:77-96).
- Boot sends no servo move.

S7 pass: no new autonomous behaviour this round. The gamepad and the tip latch are unchanged since round 2, when they were verified.

## Previous findings
R2-01 fixed. Every stop to target 0 decelerates at a rate clamped into [2000, 3000] rpm/s and releases by 4 s (see S1). The round-2 scenario (`fw ramp 200`, 6000 rpm, Esc) now stops in 3.0 s instead of 30 s (test_stop_rule.cpp:45-46). Normal setpoint changes still use `fw ramp` (stop_rule.hpp:48; test 41-42). README rows and the Stopping section are updated (README.md:75, 91, 96, 191-200). The regen justification is weaker than written; see R3-01.

R2-02 fixed.
- **One closing line per accepted fire.** Every accepted `fire` ends with exactly one `# fire done` line. The paths:
  - abort before the fire task wakes: `firing_.exchange(false)` prints "0 of n" once (turret.hpp:457-458);
  - abort after it wakes but before the first stroke: the loop is skipped and `why_end = "stop"` is set (561-562);
  - stop in a gap: 561-562;
  - stop or fault mid-stroke: 498-499, 510-511;
  - left speed: 476-477;
  - FEED_JAM: 532;
  - normal completion: no suffix.
- **Exactly once.** The main path clears `firing_` under `fire_m_` before printing (563-567). A later wake-up's `exchange` therefore returns false, unless a new `fire` was accepted, and that one owns its own line. Refused fires print `! fire: …` and no done line, which matches the claim of "each accepted fire".
- **Async calibration result.** It prints `! cal: …` (main.cpp:505).

R2-03 fixed.
- `forget_calibration` refuses while `cal_running_` (flywheel.hpp:300-303).
- `clear_fault` returns false while `cal_running_` (431-434), and `clear` answers `! clear: a calibration is still finishing …` (main.cpp:406-407).
- `clear_fault` now resets `fault_code_` whatever the mode (437), which closes the `!ok_` leftover.

R2-04 fixed: `restore_calibration()` (flywheel.hpp:100-104) replaces `initialize()` in `restore` (597), so neither `enable()` nor the "Init FOC / Aligning" log runs. `init_foc` also samples the shaft angle and velocity, but `loop_foc` re-samples them on every tick, so nothing is lost.

What remains: the MCPWM comparators keep the last alignment vector until the next `fw spin` or `fw open` enables the driver. `BldcDriver::enable()` does not zero them (bldc_driver.hpp:114-133). So that first ≤250 µs tick drives up to `valign` at a command that asked for motion anyway. This is harmless and not a finding.

R2-05 fixed (as the documentation fix review 2 asked for). The comment is at flywheel.hpp:524-531, and the README covers it at 136 and 200. The behaviour is unchanged: release is still a short brake. It is the second item on the watch list.

R2-06 fixed: `apply_settings` stores kp and ki in atomics before its `cal_running_` early return (flywheel.hpp:245-246, 258-259). The hand-back applies kp, ki, valign and vlim (618-620) under `mutex_`.

R2-07 fixed (the optional half): the SPI device logger is set to NONE (flywheel.hpp:180). That is the logger that prints in `Spi::Device::transfer` (spi.cpp:396-407). The interrupt-driven `spi_device_transmit` is kept and documented (README.md:257). Its bounded semaphore wait remains; watch `foc_overruns`.

R1-11b fixed: the auto-reference needs 0.5 s in which every sample is within 3° of the window's first sample, and any motion restarts the window (tip_guard.hpp:81-95). It is host-tested and the test can fail (test_tip_guard.cpp:48-59). One residual is inherent to auto-levelling: a board powered up tipped and held still becomes "level". `imu level` + `save` at bring-up is still the instruction (README.md:131).

From review 1, by way of review 2: R1-01's residual is R2-04, fixed. R1-07's residual is R2-07, fixed as above. R1-10's residual is R2-02, fixed. R1-13's leftover is R2-03, fixed. R1-15 (the LSM6DS3TR part driven by `Lsm6dso`) still needs a hardware check; it is on the watch list.

## Findings
R3-01 [MINOR] main/stop_rule.hpp:15-23, 41, README.md:195: the regeneration argument for the 2000 rpm/s floor is weaker than written. There is also no longer any way to make a stop gentler than 2000 rpm/s.
  scenario: B5 on the launch rig, with a 12 V bench supply and the MotorGo as the main load on that rail (launch-rig README.md:143), wheel at 6000 rpm, and the operator presses Stop.
  - Braking power is I·α·ω. With the header's own I ≈ 4.5e-5 kg·m², that is ≈ 4.5e-5 × 209 × 628 ≈ 5.9 W at the start of a 2000 rpm/s stop, and 8.9 W at 3000 rpm/s.
  - The motor's iron and bearing losses and the wheel's drag absorb part of that.
  - The header says the rest is "less the board's own draw (MotorGo, servo board and buck …)" and that a non-sinking supply "sees at most a small rise". On the launch rig there is no servo board or buck on that rail. A supply that cannot sink current absorbs nothing, so any net regeneration goes into the bulk capacitance, and a few joules into a few hundred µF is a large voltage rise.
  - The real magnitude depends on losses and capacitances nobody has measured.
  - Round 2's "gentle `fw ramp`" let the operator stop below the wheel's free coast-down rate, with near-zero regeneration. That is now impossible without a rebuild.
  - Separately, `fw spin <lower rpm>` still decelerates at `fw ramp`, which goes up to 20000 rpm/s (main.cpp:243-246), with no regen cap.
  evidence: read stop_rule.hpp:15-34 and README.md:195; params.py:223-225 (wheel R35, 17 mm wide, so the guessed I is the right order of magnitude); launch-rig README.md:132, 143 (bench supply).
  fix (optional, after bring-up): measure VIN during the first stops (watch list item 1). If it rises, either lower kStopDecelMin toward the measured free coast-down rate (the 4 s deadline still bounds the stop), or add a sink. Apply the same cap to downward `fw spin` changes.

R3-02 [MINOR] main/flywheel.hpp:725-726, stop_rule.hpp:60-66, README.md:196: two gaps in how a release at speed is reported and documented.
  - **A deadline release is silent.** When the 4 s deadline releases a wheel that is still fast, the mode silently becomes Off. No `!` line is printed and no counter records it, so the operator does not learn that the wheel failed to follow the decel. On this board that release is also a full short brake (R2-05).
  - **Open-loop stops are documented wrongly.** An open-loop stop releases as soon as the setpoint reaches 0, whatever the wheel is doing. The README describes the release as "under 150 rpm, or 4 s" and lists open loop only under the deadline. In B4, the stop now ramps at ≥ 2000 rpm/s where it used to ramp at the operator's gentle `fw ramp`. At `vopen` the wheel can lose sync during the ramp, and it is then short-braked from whatever speed it still has.
  scenario: B4 at 2500 rpm open loop with `fw ramp 300`, then Stop. The field ramps down in 1.25 s. The rotor slips and is still at, say, 1500 rpm when `set` reaches 0. It is short-braked with no message, and the README says this should not happen above 150 rpm.
  evidence: code read; stop_rule.hpp:65 (the `open_loop ||` term).
  fix (optional): have the tick raise a notice flag when it releases at the deadline with |rpm| ≥ 150 (`poll_faults` can print it), and fix README item 2 for open loop.

R3-03 [MINOR] main/turret.hpp:475-477, 561-562 and web/launcher.html:740-742: some closing-line reasons are wrong, and the panel no longer surfaces jams or left-speed endings.
  - A stop that lands after the last shot has completed reports `# fire done: n of n shots, ended by stop`.
  - A turret fault that is latched during the recovery wait reports "flywheel left speed".
  - The Fire button now ends on `# fire done`, or on the n-th `@shot`, which comes after the `! FEED_JAM` line. It therefore no longer prints its red `fire: …` summary for a jam or a left-speed ending. The raw `!` line is still shown in the console by `handleLine`.
  scenario: `fire 1` jams. The console shows `! FEED_JAM …` in red, but the Fire button returns quietly with no summary, as it does for a good shot.
  evidence: code read.
  fix (optional): set `why_end` only when `pending_` was still above 0. Use "turret fault" when `has_fault_` is set. Have the panel print an error when the done line carries `ended by`.

## The three areas you flagged
- **Does the stop rule bound every stop path?** Yes: `stop`, `fw stop`, Esc, gamepad B, the watchdog, FEED_JAM, `fw spin 0`, an open-loop stop, and a stop during spin-up all reach target 0 and the same tick code (see S1). The 4 s release is the same short brake as the fault paths, at a lower speed, so it is not worse than them. It is strictly better than round 2's behaviour of driving indefinitely. The gaps are reporting and documentation only (R3-02).
- **Is the Closed → stopping → Off transition racy with the try-lock tick?** No. Every mode change and every `stop_elapsed_s_` access holds `mutex_`, and the lock-free writers only ever write 0 (see S1).
- **Does `# fire done` appear exactly once?** Yes, on every accepted path, including abort-before-wake, jam, fault and left speed. Refused fires get a `! fire:` line instead (see R2-02). The wording issues are R3-03.

## Verified improver claims
All of them are true, with the caveats noted:
- R2-01: true. The numbers are justified in the header, but the regen reasoning overstates its certainty (R3-01).
- R2-02, R2-03, R2-04, R2-05, R2-06 and R2-07: true.
- R1-11b: true.
- "No new capability": true.
- The build is clean, the six host suites pass, and `node --check` passes: all true (D1, D2, D5).

## Fix list for the improver (BLOCKER and MAJOR, in priority order)
None. R3-01 to R3-03 are optional MINORs, best done after the measurements below.

## First power-up watch list (the bring-up gate)
1. **Regeneration on stop.**
   - Put a DMM on the MotorGo VIN, or watch the bench supply's voltage readout.
   - Make the first stops from 3000 rpm (about ¼ of the 6000-rpm energy), then from 4500, then from 6000.
   - If VIN rises more than about 1 V, stop going higher. Add a sink first: a supply that can sink, a battery, or a clamp.
   - Keep `fw ramp` ≤ 3000, because downward `fw spin` changes are not capped (R3-01).
2. **The short brake on any release at speed.** It happens on:
   - any fault at speed (TIPPED, OVERSPEED at > 8400 rpm, STALL, ENCODER);
   - OTA while the wheel spins (`before_ota` → `coast()`);
   - an open-loop stop once the setpoint reaches 0;
   - a stop that hits the 4 s deadline.

   Rough estimate: back-EMF ≈ 6000 / 1900 KV ≈ 3.2 V into a few tens of mΩ, so expect tens of amps of peak phase current and a very hard deceleration. I am inferring this from the espp `disable()` code; it has not been measured. So:
   - never start an OTA with the wheel turning;
   - do the first deliberate tip-guard or fault test at ≤ 2000 rpm;
   - check the hub's set screw and the board's temperature afterwards.
3. **Stop timing.** After Stop, `state` should go to off within 4 s: 3.0 s from 6000 rpm, 2.0 s if `fw ramp` ≥ 3000.
   - If `rpm` is still well above 150 at the moment the mode goes to off, the wheel did not follow the decel. Check the gains and the encoder before the next run (R3-02).
4. **B4 open loop.** Keep open-loop tests at ≤ 1500 rpm. The stop ramps at ≥ 2000 rpm/s, and a wheel that loses sync is short-braked at setpoint 0.
5. **Calibration.** Run `fw cal` only on a current-limited supply (1–2 A), with `valign` ≤ 3 V, as the panel dialog says.
6. **IMU.** The tip guard does nothing until it has a reference. That means 0.5 s of stillness after boot, or a stored `imu level`.
   - First confirm that the part answers sensibly: `imu` should report about 1 g and a `base_tilt` near 0. The LSM6DS3TR is driven by `Lsm6dso`, which has not been checked on hardware.
   - Then run `imu level` and `save`.
7. **FOC tick health.** In `@status`, `foc_overruns` and `foc_lock_skips` should stay near 0, and `enc_errors` should be 0 at rest. Rising overruns would point at the interrupt-driven SPI read (R2-07).
