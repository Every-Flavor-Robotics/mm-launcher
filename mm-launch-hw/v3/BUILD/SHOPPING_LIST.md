# M&M launcher v3: shopping list

You already own:

- the MotorGo Axis, the Plink encoder(s) and the XTEAM 3674;
- the Hiwonder bus servos (3), with their round horns, and their controller;
- the DeWalt battery, its adapter and the 12 V buck converter;
- a regular-mouth pint mason jar with its band, and hockey tape;
- M3 machine screws and nuts, superglue and hot glue.

Everything else is below. Quantities come from the model (`../blender/manifest.json`, checked against the BOM by `cad bom`: 5
rows, 0 disagree, 0 modelled screws in no row, re-run for this list), from `checks.json` `cable_leads` and `cable_chains`,
and from the cable routes in `../blender/cadcheck.json` [cables].

**The screw list is much shorter than v2's.** v3 has **11 screws and 3 nuts in 4 specs**, all M3 (manifest
`fastener_summary`: M3 pan x 10 (6), M3 cap x 6 (2), M3 cap x 20 (2), M3 hex x 16 (1)). v2 attempt 7 had 103 screws and 4
nuts in 18 specs (DESIGN_LOG baseline table). Three things from v2's buy list are gone:

- the M2 x 8 horn screws: horns sit on printed pins;
- the M2.5 MotorGo screws: card guides;
- the M3 x 35 hinge axle: printed stubs.

So is the long 2 mm hex bit: the hinge axle was the screw that needed it. No screw in v3 holds two printed parts together
(BOM section 2).

## 1. Buy

| # | Item | Qty to buy | Used for | Notes |
|---|---|---|---|---|
| 1 | **Diametric magnet, Ø6 x 2.5 mm** (NdFeB, magnetised across the diameter, not through the thickness) | 1 (buy 3: the glue step can go wrong) | Glued to the motor's rear shaft end; the Plink MT6701 reads it (`BUY_magnet`, BOM item 4, step 6b) | Must be *diametric*. An axial magnet gives no angle signal. |
| 2 | **JST-SH 1.0 mm 5-pin lead, one piece, 550-600 mm**, twisted or shielded | 1 | Plink to the MotorGo encoder connector, unspliced across tilt and pan (BOM item 15) | The chain routes 504.6 against the 545 that a 550 lead leaves after its plugs [cables.chains: encoder signal]. Check the pin order against the Plink's own short cable before routing it: some leads arrive reversed end to end. |
| 3 | **16 AWG silicone wire, 3 colours** | 1 m of each colour | Motor phase extensions, journal-bore splice to the MotorGo J6/J8 pads: 700 per phase, 481.1 routed [cables.chains: phase conductors] | Silicone insulation, so it bends through the hollow journal and the U-loop. |
| 4 | **Expandable braided sleeve, 6 mm** | 1 m | Launcher bundle (350 lead, 262.6 routed) and base lead (250, 156.1 routed) [cables]: 3 phases + encoder | Leave it loose over the bundle/base hand-over (step 11a). |
| 5 | **Heat-shrink, 2:1** (an assortment covers it) | 3 x 25 mm of 4.8 mm; 3 x 15 mm of 4.8 mm; 1 x 20 mm of 12.7 mm | Phase solder joints in the journal bore (3); bus splice: three 3-to-1 joints (V+, GND, signal), then all three together | The finished bus splice must be **Ø10 x 20 or smaller** (`BUY_bus_junction`, BOM 14a). |
| 6 | **Hiwonder 3-pin bus servo leads**, at least 350, 300 and 500 long | 1 of each (skip any the servos came with at that length or longer) | Pan (350: 290.2 routed incl. the 12.7 tail [cables.chains: pan bus lead]), tilt (300: 203.7), feeder (500: 324.6) [cables] | The hub-end plugs are cut off at step 11a. |
| 7 | **4-wire UART lead, 300 mm**, with connectors to match the MotorGo UART header and the controller's TTL header | 1 | MotorGo to servo controller (213.8 routed [cables]) | Check both headers before buying; the model doesn't name the connectors. It presses into 2 printed floor clips (step 12). |
| 8 | **18 AWG silicone wire, red and black** | 1 m of each | 12 V runs [cables]: adapter to buck (200 lead, 119.4 routed), buck to MotorGo (100, 45.2), buck to controller (250, 168.8) | Terminate to suit the MotorGo power input and the controller's screw terminal. |
| 9 | **USB-C cable, straight plug** (not right-angle), overmold 12.5 x 7 mm or smaller, 1 m or longer | 1 | Plugs vertically into the MotorGo and leaves through the rear niche (`CAB_usb`, 1000 lead) | Unless you already have one that fits the niche. |
| 10 | **M3 x 16 hex head bolt** (ISO 4017 / DIN 933, 5.5 AF x 2.0 head, full thread) | 1 (buy 2) | Nip stud, captive in the hood's hex pocket (`FST_nip_stud`, step 6c) | A socket head won't key in the pocket. The only screw you may not have in stock. |
| 11 | **Small cable ties, 2.5 x 100 mm** | 10 | Strain relief at the shell's printed zip-tie anchor, the MotorGo and the controller | Not at the bundle/base hand-over: that one stays loose. |
| 12 | **Feeler gauges, 0.1 and 0.3 mm** (or shim stock) | 1 set | `MEASURE_FIRST.md` 3a (gate slots) and 3b (shoulder contact) | Tool. |

**Bullet connectors: none needed.** The motor's 80 mm leads are cut to about 55 and soldered to the 16 AWG extensions in the
journal bore, with the joints staggered (BOM item 13). The extensions are soldered to the MotorGo J6/J8 pads. Ø4 bullets and
their sleeves are too fat to stagger three in the Ø12 journal bore beside the encoder lead. Buy 3 female 4 mm bullets only if
you want to run the motor on the bench before cutting its leads.

**Optional:**

- a push gauge (0-20 N) for the leaf preload log (v2 BOM section 0, "Leaf creep");
- 4 self-adhesive rubber feet, Ø14 or smaller: the floor has 4 Ø14 x 1.0 recesses for them at (±100, ±100) (`parts/base.py`
  "rubber-foot recesses"; not in the manifest);
- a 1/2 in (12.7 mm) heat-shrink offcut as a strain-relief collar on the USB-C cable.

## 2. Already owned: check you have enough

### M3 screws and nuts (11 + 3)

| Size | Head | Qty | Objects | Where (step) |
|---|---|---|---|---|
| M3 x 6 | socket cap | 2 | `FST_pinion_ctr`, `FST_tilt_horn_ctr` | Pan pinion and tilt horn adapter centre screws into the servo splines (1a, 8a) |
| M3 x 10 | pan | 2 | `FST_adapter_0/1` | DeWalt adapter, into its own holes from the deck top, counterbored flush (1) |
| M3 x 10 | pan (machine) | 4 | `FST_motor_0..3` | Motor face, through the body and nacelle plate into the motor's M3 threads (6a) |
| M3 x 16 | hex head | 1 | `FST_nip_stud` | Nip stud: buy, item 10 above |
| M3 x 20 | socket cap (machine) | 2 | `FST_fw_bolt_0/1` | Flywheel pinch bolts, through nuts (6f) |
| M3 hex nut, 5.5 AF | - | 3 | `FST_fw_nut_0/1`, `FST_tw_nut` | The two pinch-bolt nuts, and the thumbwheel's nut in its side slot (6e, a drop of superglue) |

`cad bom ../BOM_AND_ASSEMBLY.md ../blender/manifest.json` (run for this list): `CADBOM PASS: 5 rows, 0 disagree, 0 modelled
screws in no row`.

### Other owned items

- **Superglue:** magnet to shaft, the thumbwheel nut.
- **Hot glue:** UART lead in its floor clips; Plink on its pegs once the air gap is checked (optional); cable strain relief.
- **Hockey tape, 1 in (25 mm) wide, cloth.** About 0.25 m. It is trimmed with a knife to the 13.8 land and must caliper 0.5 or
  less with a butt joint (step 6f). Half-inch tape is 1.1 narrower than the land the drop tests assume. (The manifest's
  `BUY_tape` source text still says 1/2 in; the BOM's item 12 and this list say 1 in.)
- **Mason jar:** Ball/Kerr regular-mouth pint, with its metal screw band. The flat lid disc isn't used.
- **PLA:** about 1.6 kg of colour A (warm grey) and 0.25 kg of colour B (terracotta), by the geometry estimate in
  `PRINT_PLAN.md` (A 1587 g, B 232 g, including the fit coupons and tools).

## 3. Tools for the build

- A 2.5 mm hex L-key: the two centre screws and the pinch bolts. cadcheck reaches the pinch bolts with a 15.5 L-key at tilt
  45 [service: v3-A1 tape / flywheel].
- A driver for your M3 pan heads.
- **A small flat screwdriver, blade 2.5 wide or less:** it releases the beam hooks through the posts' 2.8 release slots, and
  the crown hooks from under the beam (BOM section 5).
- Feeler gauges (item 12), calipers with a depth rod.
- Side cutters, wire strippers, soldering iron, solder, heat gun. Use card or foil to shield the PLA at step 11a.
- A stiff wire or nylon line to pull leads through the turntable's closed tunnels (steps 8, 9, 11).
- A knife for the tape and for cleaning slots.
