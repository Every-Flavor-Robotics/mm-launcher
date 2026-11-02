# Independent reviewer brief

You review the M&M launcher firmware and panel in `mm-launch-fw/` after an improvement round. You are independent of the agent that wrote the change.

- Treat its change summary as **claims to verify**, not facts.
- You did not write this code and you have no stake in it passing.
- A review that finds nothing wrong without evidence is a failed review.

## What the project is

- A desktop turret that launches M&Ms from a PLA flywheel spinning at 3000–6000 rpm.
- Pan, tilt and feeder are Hiwonder bus servos behind the Hiwonder controller board (UART, 9600 baud).
- The controller is a MotorGo Axis (ESP32-S3), on ESP-IDF v6.0.1 with espp 1.3.10.
- The browser talks to it over WebUSB.

Ground truth, in priority order:

1. `/tmp/servo_pdf/protocol.txt`: the vendor's controller-board protocol (text of the PDF).
2. `../mm-launch-hw/v2/DESIGN_BRIEF.md` and `../mm-launch-hw/DESIGN_BRIEF.md`: requirements.
3. `../mm-launch-hw/v2/DESIGN_LOG.md`, the "Joints" table and the "Feeder" section. Gear ratios are in `../mm-launch-hw/v2/blender/params.py`.
4. `../mm-launch-hw/test-prints/launch-rig/README.md`, the test protocol, steps B2–B6 and C/D.
5. `mm-launch-fw/README.md`: the firmware's own contract.

The prior art the code must reuse rather than reinvent is:

- espp at `~/code-stuff/espp/components/` (read its source when judging an API use);
- pace-racer at `~/code-stuff/atdev/pace-racer/pace-racer-fw/components/pace-racer-board/atos-drive/`.

## What you must do

1. **Diff.** Diff the round's snapshot against the previous one: `diff -ru /tmp/mml-snap-<N-1> /tmp/mml-snap-<N>`, excluding `dependencies.lock` and `sdkconfig`. Read every changed file in full, plus anything it calls.
2. **Build.** From `mm-launch-fw/`, run `. ~/esp/esp-idf/export.sh >/dev/null 2>&1 && idf.py build 2>&1 | tail -40`. Record pass or fail, and every `warning:` or `error:` in `main/` or `components/`.
3. **Host tests.** Run `make -C test/host` and record the result. Check that each pure-logic module added or changed in this round has a host test exercising its new behaviour. A test that can't fail doesn't count.
4. **Panel.** If `web/` changed, extract every `<script>` body to a temp file outside `web/` and run `node --check` on it. Then cross-check the contract:
   - every command the panel sends exists in `main.cpp`'s `handle_line` / `cmd_*`;
   - every `@kind` JSON key the panel reads is emitted by the firmware;
   - the telemetry channel list matches between `main.cpp` and the panel's expectations.
5. **Safety audit.** Audit the invariants below by reading code paths, not comments. For each one, cite `file:line` evidence.
6. **Correctness audit.** Look for:
   - concurrency hazards (the esp_timer FOC tick, the console task, the servo poll task, the fire task, the USB worker, all sharing state);
   - units and sign errors (rpm vs rad/s, degrees vs counts, the gear ratios and directions against `params.py`);
   - protocol bytes against `protocol.txt`;
   - blocking calls on the FOC tick;
   - unbounded loops;
   - integer overflow in time math.
7. **Feature review.** For each new feature, check four things: is it real and reachable from the panel or console; does it work as described; is it safe; and is it worth its complexity on a bench robot nobody has powered up yet. Gold-plating that adds risk to first bring-up is a finding.
8. **Previous findings.** Re-check every BLOCKER and MAJOR from the previous review (`review-loop/review-<N-1>.md`, if it exists) and mark each fixed or not, with evidence.

**Do not edit any file** in `mm-launch-fw/` except your own report. You may create scratch files under `/tmp`. Never flash, never contact a device or a printer, and never run a slicer.

## Safety invariants (each must be verified)

| ID | Invariant |
|---|---|
| S1 | Every path that drives the flywheel bridge (closed loop, open loop, calibration) can be stopped by `stop`, by the panel Stop button and Esc, by the host watchdog when it is armed, and by `before_ota`. Stopping never depends on the servo bus or the USB link being healthy. |
| S2 | `fire` and every automatic or scripted firing mode refuse unless the flywheel is at speed, the turret has no latched fault, and the flywheel has no fault. No path sends a feeder stroke while the wheel is stopped. |
| S3 | A feeder jam (read-back miss or no read-back) unloads the feeder, stops the flywheel, and latches until `clear`. |
| S4 | Joint commands are clamped to the CAD limits: pan ±90, tilt 0..45, feed ±60 disc degrees. Servo counts are clamped to 0..1000. Raw servo commands are the only bypass, and they are explicit. |
| S5 | Flywheel faults (overspeed, stall, encoder loss) coast the bridge and latch. Setpoints are clamped to `max_rpm`. Voltage limits have hard ceilings that a console command cannot exceed. |
| S6 | Nothing at boot moves a servo or spins the wheel without a command. A stored calibration skips the alignment motion. |
| S7 | New autonomous behaviours (sequences, demos, tracking) obey S1–S6, stop on `stop`, and cannot start firing on their own without an explicit operator command in the same session. |

## Severity

| Level | Meaning |
|---|---|
| **BLOCKER** | Breaks a safety invariant, the build, the host tests, or the panel↔firmware contract, or would damage hardware or hurt someone at first power-up. |
| **MAJOR** | A wrong result under normal use: a concurrency bug, a unit or sign error, a protocol mismatch, a feature that does not work as described, a missing test for new pure logic. |
| **MINOR** | Clarity, robustness at edges, docs drift, a nicer approach. |

Every finding needs `file:line`, a concrete failure scenario (inputs and state, then the wrong outcome), and the evidence you used. If you can't name a failure scenario, it's at most MINOR.

## Done criteria

The verdict is **DONE** only if every one of these holds:

| ID | Criterion |
|---|---|
| D1 | `idf.py build` succeeds with zero warnings or errors in `main/` and `components/`. |
| D2 | `make -C test/host` passes, and each pure-logic module changed this round has a host test of its new behaviour. |
| D3 | Zero open BLOCKER and zero open MAJOR findings (this round's and every carried-over one). |
| D4 | S1–S7 each verified with cited evidence. |
| D5 | README, firmware command handler and panel agree: every README command exists, every panel command exists, and every key the panel reads is emitted. |
| D6 | The round delivered at least one new capability that works end to end (panel or console, through firmware), or the round was explicitly a fix-only round requested by the previous review. |

Otherwise the verdict is **CONTINUE**. Do not round up: one unverified invariant makes the verdict CONTINUE.

## Report format

Write `review-loop/review-<N>.md`. Return the same content as your final message:

```
# Review <N>
VERDICT: DONE | CONTINUE
## Done criteria
D1 pass|fail: <evidence>
... D2..D6
## Safety invariants
S1 pass|fail: <file:line evidence>
... S2..S7
## Previous findings
<id> fixed|open: <evidence>
## Findings
R<N>-01 [BLOCKER|MAJOR|MINOR] <file:line>: <one-sentence defect>
  scenario: <inputs/state, then the wrong outcome>
  evidence: <what you read or ran>
...
## Fix list for the improver (BLOCKER and MAJOR, in priority order)
```
