# M&M launcher v2: shopping list

You already own:

- the MotorGo Axis, the Plink encoder(s) and the XTEAM 3674;
- the Hiwonder bus servos (3) and their controller;
- the DeWalt battery, its adapter and the 12 V buck converter;
- a regular-mouth pint mason jar with its band, and hockey tape;
- M3 machine and self-tapping screws, superglue and hot glue.

Everything else is below. Quantities come from the model (`../blender/manifest.json`, checked against the BOM by `cad bom`: 18
rows, 0 disagree) and the cable routes (BOM section 1). "ST" means the screw cuts its own thread in a printed Ø2.5 pilot; an
M3 machine screw does this in PLA, and a thread-forming screw for plastic holds better.

## 1. Buy

| # | Item | Qty to buy | Used for | Notes |
|---|---|---|---|---|
| 1 | **Diametric magnet, Ø6 x 2.5 mm** (NdFeB, magnetised across the diameter, not through the thickness) | 1 (buy 3: the glue step can go wrong) | Glued to the motor's rear shaft end; the Plink MT6701 reads it (BOM item 4, step 6b) | Must be *diametric*. An axial magnet gives no angle signal. |
| 2 | **JST-SH 1.0 mm 5-pin lead, one piece, 550-600 mm**, twisted or shielded | 1 | Plink to the MotorGo encoder connector, unspliced across tilt and pan (BOM item 15) | The 545 chain row needs at least 550. Check the pin order against the Plink's own short cable before routing it: some leads arrive reversed end to end. |
| 3 | **16 AWG silicone wire, 3 colours** | 1 m of each colour | Motor phase extensions: journal-bore splice to the MotorGo J6/J8 pads, 700 per phase (488 routed) (BOM item 13) | Silicone insulation, so it bends through the hollow journal and the U-loop. |
| 4 | **Expandable braided sleeve, 6 mm** | 1 m | Launcher bundle (350) and base lead (250): 3 phases + encoder | Leave it loose over the bundle/base hand-over (A6-02). |
| 5 | **Heat-shrink, 2:1** (an assortment covers it) | 3 x 25 mm of 4.8 mm; 3 x 15 mm of 4.8 mm; 1 x 20 mm of 12.7 mm | Phase solder joints in the journal bore (3); bus splice: three 3-to-1 joints (V+, GND, signal), then all three together | The bus splice, finished, must be **Ø10 x 20 or smaller** (BOM 14a). |
| 6 | **Hiwonder 3-pin bus servo leads**, at least 350, 300 and 500 long | 1 of each (skip any the servos came with at that length or longer) | Pan (350: 292 routed), tilt (300: 207), feeder (500: 320) (BOM item 14) | The hub-end plugs are cut off at step 11a. |
| 7 | **4-wire UART lead, 300 mm**, with connectors to match the MotorGo UART header and the controller's TTL header | 1 | MotorGo to servo controller (214 routed) | Check both headers before buying; the model doesn't name the connectors. |
| 8 | **18 AWG silicone wire, red and black** | 1 m of each | 12 V runs: buck to MotorGo (100), buck to controller (250); adapter to buck (200) if the adapter's own leads are short | Terminate to suit the MotorGo power input and the controller's screw terminal. |
| 9 | **USB-C cable, straight plug** (not right-angle), overmold 12.5 x 7 mm or smaller, 1 m or longer | 1 | Plugs vertically into the MotorGo and leaves through the rear niche | Unless you already have one that fits the niche. |
| 10 | **M2.5 x 10 socket cap screws** | 4 (pack of 10) | MotorGo to the partition standoffs, ST into Ø2.1 pilots (step 2a) | Only if the board's holes measure about Ø2.5 (`MEASURE_FIRST.md` item 3). If they're Ø3.2 or more, use M3 x 10 cap instead and change params. |
| 11 | **M2 x 8 pan head screws** | 12 | Horn to printed part: pan pinion, tilt horn adapter and feeder pinion, 4 each (steps 1a, 8a, 10a) | Skip if the servo horns came with M2 screws 6-8 long. |
| 12 | **M3 x 16 hex head bolt** (ISO 4017 / DIN 933, 5.5 AF, full thread) | 1 (buy 2) | Nip stud, captive in the hood's hex pocket (step 6c) | A socket head won't key in the pocket. |
| 13 | **M3 x 35 countersunk** | 1 (buy 2) | Hood hinge axle into its trapped nut (step 6d) | Skip if it's in your M3 stock. |
| 14 | **Small cable ties, 2.5 x 100 mm** | 10 | Bus splice to the bundle sleeve (11a.6), strain relief at the MotorGo and controller | |
| 15 | **2 mm hex bit with 104 mm or more of reach** (or a long 2 mm driver) | 1 | `FST_hinge` (M3 x 35 csk) is driven from 94 mm deep (accepted warn, step 6d) | Tool. |

**Bullet connectors: none needed.** The motor's 80 mm leads are cut to about 55 and soldered to the 16 AWG extensions in the
journal bore, with the joints staggered (BOM item 13). The extensions are soldered to the MotorGo J6/J8 pads. Ø4 bullets and
their sleeves are too fat to stagger three in the Ø12 journal bore beside the encoder lead, and the model has no room for them
anywhere else on that route. Buy 3 female 4 mm bullets only if you want to run the motor on the bench before cutting its leads.

**Optional:**

- a push gauge (0-20 N) for the leaf preload log (BOM section 0, "Leaf creep");
- a 1/2 in (12.7 mm) heat-shrink offcut as a strain-relief collar on the USB-C cable.

## 2. Already owned: check you have enough

### M3 screws (91)

| Size | Head | Qty | Where (step) |
|---|---|---|---|
| M3 x 6 | socket cap | 3 | Pan pinion and tilt horn centre screws into the servo splines (1b, 8b); nip stop retainer, ST (6c) |
| M3 x 8 | pan, ST | 2 | Buck converter flange (2b) |
| M3 x 8 | pan, ST | 4 | Servo controller, drill-to-fit (2b). Not modelled; 8 mm gives about 6 of thread under a 1.6 PCB. |
| M3 x 8 | countersunk, ST | 2 | Feeder floor plate (10c) |
| M3 x 10 | countersunk, ST | 10 | Partition (2a), nip leaf (6e), groove cap (11a) |
| M3 x 10 | pan (machine) | 4 | Motor face, into the motor's M3 threads (6a) |
| M3 x 10 | socket cap, ST | 3 | Jar valve, radial (12) |
| M3 x 10 | pan, self-tapping | 1 | Gate detent clip, head flush in its counterbore (12) |
| M3 x 12 | socket cap, ST | 9 | Pan servo clamp (1b), pan drive to the deck (1c), hub gear (2d) |
| M3 x 12 | countersunk, ST | 19 | Floor (3), encoder cap (6b), journal plate (6d), pod cover (6g), feeder lobe cover (10d) |
| M3 x 12 | pan, ST | 2 | Nacelle to body (6a) |
| M3 x 14 | socket cap, ST | 6 | Nip cover (6e), right post cover (8) |
| M3 x 16 | countersunk, ST | 18 | Posts to the turntable (2c), beam (9), feeder to the beam (11) |
| M3 x 16 | hex head | 1 | Nip stud: buy, item 12 above |
| M3 x 20 | countersunk, ST | 4 | DeWalt adapter from the deck top (1) |
| M3 x 20 | socket cap (machine) | 2 | Flywheel pinch bolts, through nuts (6f) |
| M3 x 35 | countersunk (machine) | 1 | Hinge axle: item 13 above if you don't have it |

### Other owned items

- **M3 hex nuts, 5.5 AF: 4.** Two flywheel pinch-bolt nuts, the hinge nut, and the thumbwheel's captive nut (superglue it in).
- **Superglue:** magnet to shaft, thumbwheel nut, servo horns (with their screws).
- **Hot glue:** Plink on its pegs once the air gap is set; cable strain relief.
- **Hockey tape, 1 in (25 mm) wide, cloth.** About 0.25 m. It is trimmed with a knife to the 13.8 land and must caliper 0.5 or
  less with a butt joint (step 6f). Half-inch tape is 1.1 narrower than the land the drop tests assume.
- **Mason jar:** Ball/Kerr regular-mouth pint, with its metal screw band. The flat lid disc isn't used.
- **PLA:** about 1.5 kg of colour A (warm grey) and 0.25 kg of colour B (terracotta), by the geometry estimate in
  `PRINT_PLAN.md`.

## 3. Tools for the build

- 2.5 mm and 2 mm hex keys, plus a straight 2.5 mm bit with 60 mm reach. cadcheck tests every screw with a Ø6 bit or an 18/56 mm
  L-key.
- The long 2 mm bit (item 15).
- Phillips #0 / #1.
- 5.5 mm nut driver or pliers.
- Drill bits Ø2.1, Ø2.5 and Ø3.4 to clean pilots and clearance holes, and to drill the servo controller's holes through its
  bosses.
- Calipers with a depth rod.
- Soldering iron, solder, heat gun. Use card or foil to shield the turntable at step 11a.
- Knife for the tape.
