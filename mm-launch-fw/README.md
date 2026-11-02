# mm-launch-fw

First-pass firmware for the M&M launcher turret, on a MotorGo Axis (ESP32-S3).

- **Flywheel:** the XTEAM XTI-3674 1900KV runs in voltage-mode FOC on motor channel 1 (`espp::BldcMotor`), with the Plink MT6701 on encoder port 1.
- **Turret:** pan, tilt and feeder are Hiwonder bus servos, driven through the Hiwonder bus servo controller board over a 9600-baud UART.
- **Link:** the browser talks to the board over WebUSB. The USB stack is the pace-racer `DemoLink`: espp `UsbDevice` + `DispatcherWorker` + `Telemetry` + `OtaService` + `CoreDumpService`.

## Layout

| Path | What |
|---|---|
| `main/main.cpp` | Boot, tasks, the console command table, and the IMU tip guard task |
| `main/tip_guard.hpp` | Base tilt from the onboard IMU against a stored "level" reference (pure math, host-tested) |
| `main/flywheel.hpp` | Encoder + FOC loop on a 4 kHz high-res timer, rpm ramp, calibration, at-speed detection |
| `main/turret.hpp` | Joint <-> servo-count mapping, limits, aim, the fire sequence with jam detection |
| `main/settings.hpp` | Everything tunable, persisted in NVS |
| `main/demo_link.hpp` | Copied from pace-racer-fw `atos-drive/main/demo_link.hpp` (WebUSB vendor + CDC, OTA, telemetry, core dump, console) |
| `components/hiwonder_bus/` | Hiwonder bus-servo **controller board** protocol (the 7-page PDF): packet builders, a resyncing parser, and a transport-agnostic driver |
| `test/host/` | Host unit tests (`make -C test/host`): the controller-board protocol, the joint map, the tip guard and latch, JSON number formatting, the stop rule, and (under node) the gamepad mapping |
| `main/stop_rule.hpp` | How a stop decelerates and when the drive is released (pure, host-tested) |
| `main/jsonf.hpp` | `null` instead of `nan` in `@json` lines, plus string escaping (host-tested) |
| `web/gamepad.js` | Gamepad-to-aim mapping and fire gating, pure and tested under node |
| `web/launcher.html` | WebUSB control panel, with a live 3D model of the v2 CAD |
| `web/model/` | Assembly-pose meshes per moving group plus `pivots.json`, exported by `tools/export_model.py` |
| `tools/export_model.py` | Blender (headless, read-only on the `.blend`) export of `web/model/` |

## Build and flash

ESP-IDF v6.0 (`~/esp/esp-idf`), espp components from the registry (>= 1.3.10).

```
. ~/esp/esp-idf/export.sh
idf.py set-target esp32s3      # first time only
idf.py build
idf.py -p /dev/cu.usbmodem* flash   # first flash over the ROM bootloader (hold BOOT, tap RST)
```

After the first flash, the native USB port belongs to TinyUSB, so later updates go over WebUSB OTA: use the **Update firmware** button in `web/launcher.html`, or `idf.py ota-usb`. The CDC port still carries a plain text console (`screen /dev/cu.usbmodem* 115200`).

Serve the panel over localhost, because WebUSB needs a secure context:

```
cd web && python3 -m http.server 8000   # then open http://localhost:8000/launcher.html in Chrome
```

## Wiring

| From | To | Notes |
|---|---|---|
| Hiwonder board `TX` | MotorGo **Qwiic SDA (GPIO1)** = ESP RX | **Measure the board's TX idle voltage first.** If it reads about 5 V, add a divider (for example 10k over 20k). The ESP32-S3 is not 5 V tolerant. |
| Hiwonder board `RX` | MotorGo **Qwiic SCL (GPIO2)** = ESP TX | 3.3 V logic into the board's RX |
| Hiwonder board `GND` | Qwiic GND | Common ground is required |
| Hiwonder board `5V` | **not connected** | Both boards run from the 12 V buck. Don't connect the Qwiic 3.3 V pin either. |

The servo UART uses the Qwiic connector because it is a keyed plug on a known pin pair. The firmware tears down the BSP's Qwiic I2C bus first. To use other header pins, change `MM_SERVO_UART_TX/RX` in `idf.py menuconfig` → *M&M launcher*.

Servo IDs: **pan 1, tilt 2, feeder 3**. Every servo ships as ID 1, so set the IDs one at a time with Hiwonder's PC tool before daisy-chaining them. The board protocol has no set-ID command.

## Console commands

Commands come in as text lines from the WebUSB console module (0x10) or the CDC terminal. Replies:

- `ok <what>`: the command was accepted.
- `! <reason>`: an error or refusal.
- `# <text>`: human-readable info.
- `@<kind> <json>`: machine-readable state for the panel.

### System

| Command | Effect |
|---|---|
| `help` | Command list |
| `status` | Prints one `@status {...}` line |
| `stop` | Stops the flywheel and aborts any fire sequence or calibration. Servos hold position. The stop takes **at most 4 s from any speed, whatever `fw ramp` is set to** (see [Stopping](#stopping)). A `stop` from the panel acts on the USB worker task, so it never waits behind a busy console command. |
| `clear` | Clears a latched fault. Refused, with a message, for the few seconds while a calibration that was aborted by the fault is still finishing. |
| `wd <ms>` | Host heartbeat watchdog. If no line arrives for `<ms>`, the firmware runs `stop`. `0` turns it off (the default). |
| `ping` | No-op that feeds the watchdog |
| `save` | Writes every setting to NVS |
| `cfg` | Prints `@cfg {...}` with every setting |

### Flywheel (launch-rig steps B2 to B6)

| Command | Effect |
|---|---|
| `fw enc [s]` | B2. Samples the raw encoder for `s` seconds (default 1) with the motor off. Prints `@enc {"deg":..,"std_deg":..,"rpm":..}`. |
| `fw cal` | B3. Starts the sensor-direction, pole-pair and electrical-zero alignment at `fw valign` volts. It runs in the background (about 3 s), so `stop` can abort it. Replies `ok fw cal started` right away. When it finishes, it saves to NVS and prints `@cal {...}`. **Use a current-limited supply.** |
| `fw cal clear` | Forgets the calibration (flywheel must be off) |
| `fw open <rpm>` | B4. Open-loop spin at the `fw vopen` voltage, no encoder in the loop |
| `fw spin <rpm>` | B5. Closed-loop velocity, ramped at `fw ramp` rpm/s. Needs a calibration. |
| `fw stop` | Same as `stop`: the stop decel band, then the drive is released, in at most 4 s |
| `fw gains <kp> <ki> [tf_s]` | Velocity PI gains (volts per rad/s, volts per rad) and the velocity low-pass time constant |
| `fw vlim <V>` | Closed-loop voltage limit |
| `fw vopen <V>` | Open-loop voltage |
| `fw valign <V>` | Alignment voltage (takes effect at the next `fw cal`) |
| `fw ramp <rpm_s>` | Setpoint slew rate for spin-up and speed changes. Stops ignore it (see [Stopping](#stopping)). |
| `fw pp <n>` | Pole pairs (takes effect at the next boot) |
| `fw sign <1/-1>` | Software direction, so a positive rpm turns the wheel clockwise seen from +X (B3) |
| `fw tol <rpm>` | At-speed band for `fire` |

### Turret

Joint angles are in degrees.

- Pan: ±90, 0 = forward.
- Tilt: 0 to 45, 0 = level.
- Feed: the disc angle, ±60, 0 = park.

| Command | Effect |
|---|---|
| `aim <pan> <tilt> [ms]` | Moves pan and tilt in one packet. Without `ms`, the move time comes from `turret speed`. |
| `pan <deg> [ms]` / `tilt <deg> [ms]` / `feed <deg> [ms]` | Moves one joint. Aiming is allowed during a fire sequence, so you can walk the shots across a target. A `feed` beyond ±15° can put a pocket over the outlet and drop a candy, so it is refused unless the flywheel is at speed. Calibrate the feeder with `servo unload` and hand placement, or bypass the check with `servo raw`. |
| `servo read` | Prints `@servo {...}`: counts and joint angles for all three |
| `servo unload [pan/tilt/feed/all]` | Servo goes limp (use it for hand calibration) |
| `servo zero <pan/tilt/feed>` | Stores the current read position as that joint's 0°. Unload it first and place it by hand. |
| `servo dir <joint> <1/-1>` | Joint direction (default pan -1, tilt +1, feed -1: the pan and feeder gears reverse) |
| `servo raw <id> <counts> [ms]` | Moves a servo by raw count (0 to 1000 = 0 to 240°), ignoring the limits |
| `turret speed <deg_s>` | Default aim speed |
| `vbat` | Prints the controller board's input voltage |

### Fire

| Command | Effect |
|---|---|
| `fire [n]` | Fires `n` shots (default 1). Refused unless the flywheel is at speed. Each shot is a feeder stroke to ±60 (alternating) and back to park, followed by a position read-back. If the read-back misses, it raises `FEED_JAM`, unloads the feeder and stops the flywheel. Each shot prints `@shot {"n","dir","rpm_set","rpm_before","dip_rpm","recover_ms","feed_err_deg"}`. |
| `feed timing <stroke_ms> <dwell_ms>` | Stroke time each way, and the dwell at the open position |
| `feed tol <deg>` | Jam threshold (disc degrees) |

### Base tip guard (onboard IMU)

The MotorGo Axis has an LSM6DS3TR IMU (the BSP drives it with espp's `Lsm6dso` driver), and the board sits in the base. The guard compares the accelerometer's gravity vector with a stored "level" reference. If the reference is unset (all zeros), it uses the first 0.5 s after boot in which the board holds steady: every sample must be within 3° of the first one, and handling the robot restarts the window. Run `imu level` and `save` once at bring-up anyway.

If the base leans more than the trip angle for 150 ms, the guard:

- aborts any fire sequence;
- latches the flywheel fault `TIPPED`, which releases the bridge immediately (a short brake on this board, see [Stopping](#stopping));
- refuses `fw spin`, `fw open`, `fw cal`, `fire`, `feed` and `clear` until the base is back within 8° (or half the trip angle, if smaller).

The refusal also lifts if `imu level` re-references the base where it now stands, or if the guard is turned off. Turning the guard back on while the base is already past the trip angle trips it straight away. The `TIPPED` fault itself always needs `clear`.

Samples far from 1 g (an impact, a drop) are ignored. The v2 CG check puts the static tip angle at about 30° with the jar full, so the default trip is 20°.

| Command | Effect |
|---|---|
| `imu` | Prints `@imu {"ok","base_tilt","tipped","guard","trip_deg","ref":[x,y,z]}` |
| `imu level` | Stores the current orientation as level. Run `save` to keep it. |
| `imu guard <on/off>` | Turns the guard on or off. Default on. |
| `imu trip <deg>` | Trip angle, 5 to 45° |

## Telemetry (module 3, 50 Hz while a host streams)

Channels, in order:

| Channel | Meaning |
|---|---|
| `rpm_set` | Ramped setpoint |
| `rpm` | Filtered encoder rpm, with sign |
| `uq` | q-axis voltage, V |
| `pan_cmd`, `pan` | Commanded and read-back pan, deg |
| `tilt_cmd`, `tilt` | Commanded and read-back tilt, deg |
| `feed_cmd`, `feed` | Commanded and read-back feeder disc angle, deg |
| `servo_v` | Controller-board input voltage, V |
| `state` | 0 off, 1 calibrating, 2 open loop, 3 spin-up, 4 at speed, 5 firing, 6 fault |
| `shots` | Shot counter since boot |
| `base_tilt` | Angle of the base from its level reference, deg (NaN without an IMU) |

espp's hosted Serial Plotter (`telemetry.html`) also reads this stream through discovery, which is handy for rig logs.

## State lines

Joint conventions:

- Pan: positive is counter-clockwise seen from above.
- Tilt: positive is muzzle up.
- Feed: the disc angle, 0 = park.

| Line | Shape |
|---|---|
| `@status` | `{"state","flywheel","rpm","rpm_set","target","uq","at_speed","calibrated","fw_ok","fw_fault","turret_fault","firing","shots","servo_v","bus_ok","enc_errors","foc_overruns","foc_lock_skips","wd_ms","foc_hz","imu","base_tilt","tipped","tip_guard"}` |
| `@cfg` | `{"pole_pairs","kv","vlim","vopen","valign","kp","ki","tf","ramp","max_rpm","tol","sign","calibrated","zero_electric","sensor_dir","ids":[pan,tilt,feed],"pan":{"zero","dir","min","max","fits"},"tilt":{..},"feed":{..},"aim_speed","feed_open","stroke_ms","dwell_ms","feed_tol","shot_gap_ms","wd_ms","imu":{"guard","trip_deg","ref"}}` |
| `@servo` | `{"pan":{"id","counts","deg","cmd","zero"},"tilt":{..},"feed":{..},"servo_v","timeouts"}` |
| `@enc` | `{"deg","std_deg","rpm","samples","errors"}` |
| `@cal` | `{"ok","aborted","kept_previous","zero_electric","sensor_dir","saved","why"}`, printed once when a `fw cal` finishes. A failed or aborted run keeps the previous calibration if there was one (`kept_previous`). A successful run saves only the calibration keys to NVS. |
| `@imu` | `{"ok","base_tilt","tipped","guard","trip_deg","ref":[x,y,z]}` |
| `@shot` | `{"n","dir","rpm_set","rpm_before","dip_rpm","recover_ms","feed_err_deg"}`. `recover_ms` is -1 if the wheel did not get back within the at-speed band within 1.5 s. |

An accepted `fire` sequence always ends with one `# fire done: <k> of <n> shots[, ended by stop|fault|FEED_JAM|flywheel left speed]` line. A failed or aborted calibration reports `! cal: ...` (not `! fw cal: ...`) followed by `@cal`.

Any value that isn't known yet prints as JSON `null`: an unloaded servo's command, a joint that hasn't answered, or base tilt without an IMU. Flywheel faults raised inside the FOC loop (overspeed, stall, encoder) are announced by the console task as `! flywheel fault: ...`, because the loop itself never prints.

## Stopping

A stop is any time the flywheel target goes to 0. That covers `stop` and `fw stop` (the panel's Stop button, Esc, gamepad B), the host watchdog, a `FEED_JAM`, and `fw spin 0`. The rule is in `main/stop_rule.hpp` and is host-tested.

1. **Ramp down in a fixed band.** The setpoint ramps down at `fw ramp` held inside 2000 to 3000 rpm/s. That is 3.0 s from 6000 rpm and 3.5 s from `max_rpm` 7000, however slow `fw ramp` is. A fast `fw ramp` is capped at 3000 for stops: a driven deceleration returns the wheel's roughly 9 J to the 12 V bus, about 0.3 to 0.4 A for 2 to 3 s, so going faster would mainly double the current pushed back into a bench supply.
2. **Release the drive.** The drive is released once the wheel is under 150 rpm, or **4 s after the stop began whatever the wheel is doing** (PI saturated, encoder wrong, open loop).

Faults (`TIPPED`, `OVERSPEED`, `STALL`, `ENCODER`) and OTA release the drive immediately instead.

**Released means short-braked on this board.** espp's `BldcDriver::disable()` stops the PWM timer without forcing the gates, and the MotorGo Axis has no driver enable pin, so the three low-side FETs stay on and the windings are shorted. The wheel brakes on its own back-EMF, and that energy goes into the windings, not the supply. Watch the first fault at speed during B5. A true free-wheel needs an upstream espp change.

## Gamepad aim

Tick **Gamepad aim** in the Aim panel and use any standard-layout pad (Xbox or PlayStation layout in Chrome).

| Input | Action |
|---|---|
| Left stick | Pan and tilt, up to 90°/s, with a cubic expo for fine aim |
| Right stick | The same at a quarter of the rate |
| Y | Center |
| B | Stop. This works even with gamepad aim unticked. |
| A while holding LB | Fire one shot. LB is the deadman. A without LB, or before the wheel is at speed, is refused. |

Spinning up stays a panel button on purpose. Aim moves go through the same 10 Hz throttle as the sliders. Fire goes through the Fire button, so the panel's at-speed gate and every firmware check still apply.

## Live model

The panel's **Live model** shows the v2 CAD moving.

- **Pose source:** read-back angles when the servos answer, commanded angles otherwise, and the aim sliders when no board is connected.
- **Gearing:** the pan and feeder pinions turn at their gear ratios.
- **Flywheel:** spins at the measured rpm, slowed down 50 times.
- **Aim ray:** a dashed line shows the muzzle direction.
- **Interaction:** click a part to jump to its control.

The meshes come from `mm-launch-hw/v2/blender/model.blend`. Each moving group is exported in world coordinates at the rest pose, decimated to about 25k triangles, and re-hinged in the browser on the pivots in `pivots.json`. To regenerate after a CAD change:

```
cd ../mm-launch-hw/v2/blender
/Applications/Blender.app/Contents/MacOS/Blender -b model.blend --python ../../../mm-launch-fw/tools/export_model.py -- ../../../mm-launch-fw/web/model
```

three.js loads from the jsDelivr CDN, the same as the style guide's examples, so the panel needs internet the first time.

## First bring-up order

1. Flash over USB with BOOT held, then open the panel and connect.
2. Run `fw enc` while turning the shaft by hand. The angle should climb smoothly (B2).
3. Put the board on a current-limited bench supply (1 to 2 A), then run `fw cal` and wait for `@cal`. Watch the console for `PP check: OK` (B3). If it reports a different pole-pair estimate, run `fw pp <n>`, `save`, reboot, and run `fw cal` again.
4. Run `fw open 300`, then `fw stop` (B4).
5. Run `fw spin 1000` and step up from there (B5). Check that the wheel turns clockwise seen from +X. If it doesn't, run `fw stop`, `fw sign -1` and `save`.
6. Servos: run `vbat` first, which proves the UART link.
   - For each joint: `servo unload <joint>`, set the joint to 0 by hand, `servo zero <joint>`.
   - Then `save`.
   - Check that `cfg` shows `"fits":true` for all three. If a joint shows false, the horn sits too far around the spline: move it one tooth and zero it again.
7. Stand the robot where it will work and run `imu level`, then `save`.
8. With the wheel at speed, `fire`.

## Why not the existing code

- **WebUSB, OTA, telemetry, console:** `main/demo_link.hpp` is pace-racer's `DemoLink`, copied with one change (a manufacturer field). The panel's framing, WebUSB transport and OTA flow are lifted from pace-racer's `dashboard.html`.
- **Flywheel FOC:** this is `espp::BldcMotor` with the MotorGo Axis BSP's driver, pin map and encoder settings. The BSP's `initialize_motor()` isn't used as-is, for one reason: it runs the MT6701 on its own fixed 1 kHz task.
  - At 6000 rpm with 2 pole pairs, 1 kHz is 72 electrical degrees between angle samples.
  - The firmware reads the encoder and runs FOC in the same tick at 4 kHz instead.
  - `FocMotor` is a 40-line subclass. It exists only to reach what `BldcMotor` keeps protected: live gains, voltage limits, `Uq`, and the calibration result, so the calibration can be saved to NVS.
  - pace-racer's own FOC (`foc_sampler.hpp`) isn't reused. It is built around the DRV8353 and phase-current shunts, which the MotorGo Axis doesn't have.
- **Known and left as is:** each encoder read in the FOC tick is espp's interrupt-driven `spi_device_transmit`, which waits on a semaphore for a few tens of µs on the esp_timer task. Switching to a polling transfer would mean replacing the BSP-proven read path just before first bring-up, so it is deferred. The SPI device's logger is silenced, so a failed read cannot print from the tick.
- **Tip guard:** this uses the MotorGo Axis BSP's own `initialize_imu()` and espp's `Lsm6dso` driver. The only new code is the angle and hysteresis logic in `tip_guard.hpp`.
- **Gamepad:** this is the browser's standard Gamepad API. The only new code is the mapping in `web/gamepad.js`, which feeds the panel's existing aim throttle and Fire button.
- **Live model:** this is the style guide's `ax-three.js` (`axScene`, with its STL loading and hover picking). The meshes come straight from the v2 `.blend`, so the robot isn't modelled a second time.
- **Hiwonder controller board:** neither espp nor any repo on this machine has a driver for it. `components/hiwonder_bus` follows the transport-injection pattern of espp's `Basicmicro`.
