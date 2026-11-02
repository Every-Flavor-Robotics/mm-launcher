"""Build steps.json and the self-contained assembly_guide.html for the v3 (min-hardware) launcher. Plain Python 3, no Blender.

    python3 build_guide.py            # needs assembly.glb from export_glb.py next to it

Ported from the v2 guide (../../../v2/BUILD/guide/build_guide.py). Reads (never writes) ../ASSEMBLY.md,
../MEASURE_FIRST.md, ../plates.json, ../print_estimate.json, ../renders/, ../../blender/{checks.json,manifest.json,
params.py}, ../../renders/attempt-1/ (design renders), ../../renders/attempt-2/cadcheck.json (the hotfix check: header
facts and the insertion directions) and the alex-style web files. Writes steps.json and assembly_guide.html here.

Step mapping: every ASSEMBLY.md step is tied to the checks.json assembly_order entry with the same label. Its new
objects are the entry's globs resolved against the GLB node names. When two entries' globs match one object, the more
specific glob wins (step 9's CAB_launcher* also matches CAB_launcher_base, which step 13 names as CAB_launcher_base*).
Fastener counts in the step text are compared with the manifest's per-fastener step labels (the model calls 6c/6d "6c").

A step is "clean" when its entry exists, every glob that names a part the text asks for resolves, the fastener counts
agree, every warning's quoted source text is found in ASSEMBLY.md / MEASURE_FIRST.md, and every fly-in direction either
agrees with cadcheck's insertion row for that part (attempt-2 cadcheck.json, checks.insertion.rows free_dir) or says
why not (CURATED dir_why). Otherwise it is "flagged" with the reason.

Fly-in directions are the way each part goes in, reversed (where it comes from), in the design frame. Sources, in order
of preference: the checks.json slide_out row that takes the part out for service, the step's insert_dirs (cadcheck:
"the direction the part moves to come out"), the ASSEMBLY.md text, cadcheck's insertion free_dir. Each is noted in
CURATED. Warnings are (level, text, [(file, quoted text), ...]); the build finds each quote and cites its section and
line, so a warning whose source text moves or disappears flags its step.
"""
import base64
import fnmatch
import html
import json
import math
import os
import re
import struct
import subprocess
import tempfile
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.dirname(HERE)
V3 = os.path.dirname(BUILD)
BL = os.path.join(V3, "blender")
A1 = os.path.join(V3, "renders", "attempt-1")
A2 = os.path.join(V3, "renders", "attempt-2")
CADCHECK = os.path.join(A2, "cadcheck.json")
STYLE = "/Users/alxchunlin/code-stuff/alex-style-guide/web"
GLB = os.path.join(HERE, "assembly.glb")
OUT_HTML = os.path.join(HERE, "assembly_guide.html")
OUT_STEPS = os.path.join(HERE, "steps.json")
DOCS = {"ASSEMBLY": os.path.join(BUILD, "ASSEMBLY.md"), "MEASURE_FIRST": os.path.join(BUILD, "MEASURE_FIRST.md")}
THREE = "0.170.0"   # the version the style guide's ax-three.js is written against

# ---------------------------------------------------------------- curated per-step data
# Directions are in the design frame (+X right, +Y front/muzzle, +Z up). "explode" maps object globs to the direction a
# part comes from (length scales the travel); fasteners not listed back out along -into from the manifest (nuts move
# along +into). Unlisted parts of a step with rules stay still: they are the part the others go onto. "view" is where
# the camera sits relative to the focus parts (Follow parts mode). "pose_in" holds a joint at its insertion angle while
# the step's parts fly in, then eases it home (step 7: pod nose-up 20; step 15: jar dropped in at +30 and twisted to 0).
# "joint" is the kind of joint the step makes; snap / slide / press steps must carry ASSEMBLY.md Seats and Release lines.
# "dir_why": why a fly-in differs from cadcheck's insertion free_dir for that object.
UP, DOWN, RIGHT, LEFT, FRONT, BACK = [0, 0, 1], [0, 0, -1], [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]
STUD = [0, -0.9479, -0.3185]      # FST_nip_stud.into: head -> tip; the thumbwheel threads on from the tip side
V_OUT = [0, -0.3185, 0.9479]      # 6e insert_dirs = slide_out 'nip cover + leaf ... along +V' at tilt 0
COVER_OUT = [0, 0.7071, -0.7071]  # 6g insert_dirs = slide_out 'wheel-side cover slides off +Y at tilt 45' at tilt 0
DEFAULT_VIEW = [1.0, 1.25, 0.9]
A = "ASSEMBLY"
M = "MEASURE_FIRST"


def sc(v, k):
    return [c * k for c in v]


LIFT_TEXT = ("Lift and carry the machine by the base only, never by the jar, the crown or the beam. Lifted by the jar, "
             "the whole 4075 g hangs on three rows of snap fingers that all bend across layers, each with less than one "
             "layer of Z clearance. To move it: battery out, then both hands flat under the base shell.")
LIFT_SRC = [(A, "WARNING: lift and carry the machine by the base only"),
            (A, "To move the machine: battery out, then both")]

CURATED = {
    "0": dict(view=[1.0, 1.3, 0.8],
              renders=[("../renders/attempt-1/iso.png", "the finished machine (attempt 1; the hotfix changed the beam, "
                                                       "jar adapter and gate)")],
              warnings=[
                  ("critical", LIFT_TEXT, LIFT_SRC),
                  ("critical", "All three servos ship as bus ID 1. Give pan, tilt and feeder different IDs and label each "
                               "servo before anything else: after step 11a they share one bus.",
                   [(A, "give the pan, tilt and feeder servos different bus IDs")]),
                  ("warning", "Command each servo to mid (500 on the 0..1000 scale) before its horn goes on, and don't "
                              "turn the output by hand after that. Mid is pan 0, tilt 0 and the feeder's park position.",
                   [(A, "command each servo to its mid position")]),
                  ("warning", "Fit-test first: the beam, hub, crown and valve snaps have less than one layer of Z "
                              "clearance (0.05 to 0.1). Print plate 0a and pass its coupons, and build the jar group "
                              "from plate 0b, before the big plates.",
                   [(A, "**Measured and fit-tested:**"), (M, "The joints most likely to fail are the vertical snaps")]),
                  ("warning", "There are no horn screws in v3: each horn presses over 8 printed pins. Keep the horns' own "
                              "screws in the bag.", [(A, "Keep the horns' own screws in the bag.")])]),
    "1": dict(joint="screws", explode={"BUY_dewalt_adapter": DOWN}, view=[1.0, -0.8, -0.35],
              explode_src="adapter up into its deck fences from below (cadcheck insertion -Z); screws from the deck top",
              warnings=[("warning", "Measure first (item 9): the adapter's corner hole size is unknown. If the holes are Ø3 "
                                    "or bigger, M3 won't self-tap: use machine screws with nuts, or epoxy. The tips must "
                                    "stay 3 or more above the battery face (5.46 now). These 2 screws carry the 620 g "
                                    "pack's hanging load.", [(M, "| Corner hole diameter and depth |")])]),
    "1a": dict(joint="press (8 printed pins)", view=[1.0, 1.0, -0.3],
               explode={"PRT_pan_pinion": UP, "BUY_horn_pan": UP, "BUY_servo_pan": sc(DOWN, 1.2)},
               explode_src="servo up into the mount pocket (cadcheck -Z); pinion and horn, pressed together, down onto "
                           "the spline; centre screw down through the pinion",
               dir_why={"BUY_horn_pan": "the horn is pressed into the pinion first, so it goes onto the spline with the "
                                        "pinion, from above; cadcheck's -Z is the horn alone out of the pinion's pocket"},
               warnings=[("warning", "Press the pinion and horn onto the spline with the servo still at mid.",
                          [(A, "press the pinion and horn onto the spline")]),
                         ("warning", "Measure first (item 5): the 8 Ø2.0 pins have 0.1 radial clearance in the horn's "
                                     "Ø2.2 holes. A bolt circle off by more than about 0.2 stops the horn seating. The "
                                     "tilt_horn_adapter on plate 0a is the test.",
                          [(M, "The Ø2.0 pins have 0.1 radial clearance in Ø2.2 holes.")])]),
    "1b": dict(joint="press (crush-rib pins)", explode={"*": DOWN}, view=[1.0, 1.2, -0.3],
               explode_src="pan drive pressed up onto the deck posts (slide row 'v3-A1 pan drive off the deck posts -Z')",
               dir_why={"group": "slide row 'v3-A1 pan drive off the deck posts -Z' and ASSEMBLY 1b ('press the mount "
                                 "plate up onto the 4 deck posts'); cadcheck's insertion reports +Z first for the group"}),
    "2a": dict(joint="loose (laid on)", explode={"PRT_thrust_ring": sc(UP, 0.6), "PRT_turntable": UP},
               view=[1.0, 1.2, 0.5], explode_src="both laid on from above (cadcheck +Z)"),
    "2b": dict(joint="snap (permanent)", explode={"PRT_hub_gear": sc(DOWN, 1.2)}, view=[1.0, 1.1, -0.4],
               explode_src="pushed straight up (+Z) through the deck hole (ASSEMBLY 2b; insert_ok, not ray-tested)",
               renders=[("../renders/attempt-1/sec_hub_roof_y4.0.png", "section through the hub and the bore roof")],
               warnings=[("critical", "This snap can't be released: the barbs sit inside the socket where no tool reaches "
                                      "them, and taking the turntable off breaks the fingers (the hub gear is a 15.6 g "
                                      "reprint). Pass the c2 coupon first.",
                          [(A, "**Release: none.** The barbs sit inside the socket"),
                           (M, "This joint can't be released, so on the real machine a bad fit means a broken hub gear")]),
                         ("warning", "Mesh the hub gear with the pan servo at mid and the posts square across the base, "
                                     "so the pod faces +Y at pan 0.",
                          [(A, "with the pan servo at mid and the posts square across the base")])]),
    "6a": dict(joint="press (crush ribs) + screws", view=[0.35, 1.0, 0.4],
               explode={"BUY_motor": sc(LEFT, 1.3), "PRT_launcher_body": sc(RIGHT, 1.2), "CAB_*": [0, 0, 0]},
               explode_src="motor into the nacelle bore from the rear (cadcheck -X); body onto the motor's front boss "
                           "from +X; motor screws from inside the guard (-X)",
               dir_why={"PRT_launcher_body": "ASSEMBLY 6a fits the body after the motor, over the motor's front boss, so "
                                             "it goes on along the motor axis from +X; cadcheck's order put the body "
                                             "before the motor and found +Z"},
               warnings=[("warning", "Measure first (item 11): the Ø6 bundle carries three 16 AWG phases and the encoder "
                                     "lead through the Ø12 journal bore. If your wire is fatter than about 3.0 OD, try "
                                     "the bundle through a Ø12 hole in scrap before the pod goes in.",
                          [(M, "If yours is fatter, try the bundle through a Ø12 hole in scrap")])]),
    "6b": dict(joint="snap (2 arms, in plane)", view=[-0.6, 1.0, 0.4],
               explode={"BUY_magnet": sc(LEFT, 0.8), "BUY_plink_encoder": sc(LEFT, 1.6), "PRT_encoder_cap": sc(LEFT, 1.6),
                        "CAB_*": [0, 0, 0]},
               explode_src="the cap, with the Plink on its pegs, into the rear counterbore from -X (slide row 'v3-A1 "
                           "encoder cap pulls off -X'); magnet glued on from the rear with the jig",
               dir_why={"BUY_magnet": "glued on through the rear access hole before the cap goes on (ASSEMBLY 6b); "
                                      "cadcheck's order put the magnet after the cap and found +X"},
               warnings=[("warning", "Glue the magnet with the printed jig and wait 10 min. The magnet stack's worst case "
                                     "is 0.30 against 0.30.",
                          [(A, "Wait 10 min;"), (A, "the stack's worst case is 0.30 against 0.30")]),
                         ("warning", "If a gap shows under the cap's flange, the barb is riding the groove edge: ease the "
                                     "groove's outer edge with a knife rather than forcing the cap.",
                          [(A, "ease the groove's outer edge with a knife rather than forcing the cap")])]),
    "6c/6d": dict(joint="slide + press (crush-rib pegs)", view=[1.0, -0.4, 0.6],
                  explode={"PRT_hood": RIGHT, "PRT_journal_plate": sc(RIGHT, 1.8), "FST_nip_stud": sc(STUD, 1.2)},
                  explode_src="hood -X onto its hinge stub and journal plate -X onto its pegs, both from +X (cadcheck "
                              "+X); stud head-first into the hood's hex pocket, so it comes from its tip side",
                  warnings=[("warning", "The journal plate has no planned release (checks.json: not serviced). On the "
                                        "bench, pry it off evenly.", [(A, "On the bench, pry it off evenly.")])]),
    "6e": dict(joint="slide (dovetail) + snap (detent)", view=[1.0, -0.35, 0.15],
               explode={"PRT_nip_wheel": sc(STUD, 1.2), "FST_tw_nut": sc(STUD, 1.2), "PRT_nip_leaf": sc(V_OUT, 1.6),
                        "PRT_nip_cover": sc(V_OUT, 1.6)},
               explode_src="thumbwheel and its nut along the stud (cadcheck 'along FST_nip_stud'); leaf in the cover's "
                           "T-slot, both along the 45 deg dovetail (6e insert_dirs; slide row 'nip cover + leaf slide "
                           "off the land's dovetail along +V')",
               dir_why={"PRT_nip_leaf": "the leaf rides in the cover's T-slot, so it goes on with the cover along the "
                                        "dovetail (slide row 'nip cover + leaf ... along +V'); cadcheck's -Z is the leaf "
                                        "alone, before the cover"},
               warnings=[("warning", "The spare leaf goes in the bag, unloaded: it's the creep reference.",
                          [(A, "The spare leaf goes in the bag, unloaded, as the creep reference.")]),
                         ("warning", "Measure first (item 4): if MM_T max is over 7.3, run the thumbwheel at home or "
                                     "above, not at the min stop.", [(M, "If `MM_T` max is over 7.3")])]),
    "6f": dict(joint="screws (pinch bolts)", view=[1.0, 0.9, 0.6],
               explode={"PRT_flywheel": sc(RIGHT, 1.4), "BUY_tape": sc(RIGHT, 1.4)},
               explode_src="wheel and tape onto the D-shaft from +X (cadcheck +X; slide row 'flywheel off +X at tilt 45')",
               warnings=[("critical", "Butt-join the tape, no overlap. It must caliper 0.5 or less (TAPE_T) at three "
                                      "places and at the seam: an overlap doubles it and eats the 0.098 entry-arc margin.",
                          [(A, "**butt-join them, no overlap**"), (M, "the min-stop margin is only 0.098")])]),
    "6g": dict(joint="slide (hook tabs) + snap (latch)", view=[1.0, 0.6, 0.15],
               explode={"PRT_launcher_cover": sc(COVER_OUT, 1.3)},
               explode_src="6g insert_dirs (0, 0.71, -0.71), the way out at tilt 0; slide row 'wheel-side cover slides "
                           "off +Y at tilt 45' is the same direction with the pod tilted"),
    "7": dict(joint="slide (journals into U-slots)", explode={"*": UP}, pose_in={"tilt": 20}, view=[1.0, 1.2, 0.3],
              explode_src="lowered straight down, nose-up 20 deg (slide row 'v2-A1-06 step 7 reversed: pod lifts +Z'); "
                          "the pod flies in at tilt 20 and is then levelled",
              warnings=[("warning", "Hold the pod nose-up about 20 deg and lower it straight down until both journals "
                                    "seat in the U-slots, then level it.",
                         [(A, "hold the pod nose-up about 20 deg and lower it straight down")])]),
    "8a": dict(joint="press (8 printed pins) + screw", view=[0.5, 1.0, 0.5],
               explode={"BUY_horn_tilt": RIGHT, "BUY_servo_tilt": sc(RIGHT, 2.2)},
               explode_src="horn into the adapter's pocket from +X (cadcheck +X); adapter and horn onto the servo's "
                           "spline, along its axis; centre screw from -X through the key hole",
               dir_why={"BUY_servo_tilt": "a spline only engages along its axis (X); cadcheck allows the servo x horn "
                                          "spline pair, so its ray test reports +Z first"},
               warnings=[("warning", "Fit the adapter to the tilt servo's spline with the servo at mid.",
                          [(A, "Fit the adapter to the tilt servo's spline")]),
                         ("warning", "Measure first (item 2): press a horn into the real tilt_horn_adapter from plate 0a "
                                     "first. If the 8 pins don't all go in, fix servo_horn_disc before plates 3 and 5.",
                          [(M, "Fix `servo_horn_disc` before plates 3 and 5")])]),
    "8": dict(joint="slide (drop-in)", explode={"*": UP, "CAB_*": [0, 0, 0]}, view=[0.6, 1.0, 0.5],
              explode_src="servo, horn and adapter lowered -Z into the open-top pocket (slide row 'v3-A1 tilt servo + "
                          "adapter lift +Z')",
              warnings=[("warning", "Hold the pod level (tilt 0) while the servo goes in.",
                         [(A, "hold the pod level by hand (tilt 0)")]),
                        ("warning", "The tunnels are closed: push a stiff wire or nylon line through first and draw the "
                                    "lead after it.", [(A, "closed, so push a stiff wire or nylon line through first")])]),
    "9": dict(joint="snap (4 hooks, across layers)", explode={"PRT_beam": UP, "CAB_*": [0, 0, 0]}, view=[1.0, 1.2, 0.5],
              explode_src="beam pushed down onto the posts (slide row 'v3-A1 beam + feeder lift +Z'; insert_ok, not "
                          "ray-tested)",
              renders=[("../renders/attempt-1/sec_beam_hook_y18_xR.png",
                        "attempt-1 hook: the hotfix narrowed it to 2.2 (v3-A1-01)")],
              warnings=[("critical", "Don't swing the pod by hand from here on: that back-drives the tilt servo's gears. "
                                     "The tilt range is checked under power at step 16.",
                         [(A, "**Don't swing the pod by hand from here on:**")]),
                        ("warning", "Release the hooks only at tilt 0, with a flat screwdriver no wider than 2.5 in the "
                                    "2.8 release slots. At tilt 45 the nacelle blocks the line to the right-front barb.",
                         [(A, "push each barb outboard 0.7 with a flat screwdriver no wider than 2.5"),
                          (A, "do it at tilt 0: from the front and rear openings")]),
                        ("warning", "Fit-test first (item 2, c1): if the beam-hook coupon won't click, or is slack after "
                                    "the click, don't print plates 3 and 4.",
                         [(M, "In either case don't print plates 3 and 4.")]),
                        ("warning", "From here on, never lift the machine by the beam. Lift by the base only.",
                         [(A, "then the crown, then the **3 crown hooks**, then the beam, then the **4 beam hooks**")])]),
    "10a": dict(joint="loose (laid on)", explode={"PRT_feeder_disc": UP}, view=[0.7, 1.0, 0.8],
                explode_src="laid on the feed floor from above (cadcheck +Z)",
                warnings=[("warning", "Lay the disc in the park position: solid disc over the outlet.",
                           [(A, "in the **park** position")]),
                          ("warning", "Measure first (item 4): POCKET_D comes from the pocket coupon, before plate 2.",
                           [(M, "Set `POCKET_D` (now 13.75)")])]),
    "10b": dict(joint="press (crush ribs, 8 pins)", view=[0.7, 1.0, -0.25],
                explode={"BUY_servo_feeder": sc(DOWN, 1.2), "BUY_horn_feeder": sc(DOWN, 1.2),
                         "PRT_feeder_pinion": sc(DOWN, 1.8), "CAB_*": [0, 0, 0]},
                explode_src="servo and horn up into the closed lobe pocket from below, then the pinion onto the horn "
                            "(slide row 'v3-A1 feeder servo + horn + pinion out of the lobe -Z')",
                dir_why={"BUY_servo_feeder": "the lobe pocket is closed on top: the servo goes up into it from below "
                                             "(ASSEMBLY 10b; slide row 'feeder servo + horn + pinion out of the lobe "
                                             "-Z'). cadcheck's +Z comes from the crown x servo crush-rib allow, which "
                                             "drops that pair from its ray test"},
                warnings=[("warning", "Press the pinion onto the horn with the servo at mid. It has no centre screw: "
                                      "spline friction holds it.", [(A, "press the feeder pinion onto the horn")]),
                          ("warning", "Measure first (item 6): the servo seats against the lobe roof with 0.05 to spare, "
                                      "and a servo 0.2 over 20.14 wide will be very tight in the crown's crush ribs.",
                           [(M, "so a servo 0.2 over 20.14 wide will be very tight in the crown")])]),
    "11": dict(joint="snap (3 hooks, across layers)", explode={"*": UP, "CAB_*": [0, 0, 0]}, view=[1.0, 1.2, 0.4],
               explode_src="crown group lowered straight onto the beam (slide row 'v3-A1 crown group lifts +Z')",
               renders=[("../renders/attempt-1/sec_crown_hook_y0_xR.png", "section through a crown hook")],
               warnings=[("warning", "Disc at park and servo at mid when the pinion meshes the disc band.",
                          [(A, "the pinion meshes the disc band (disc at park, servo at mid)")]),
                         ("warning", "Never lift the machine by the crown: its 3 hooks bend across layers. Lift by the "
                                     "base only.",
                          [(A, "then the crown, then the **3 crown hooks**, then the beam, then the **4 beam hooks**")])]),
    "11a": dict(joint="slide (splice up the bore)", view=[1.0, 1.0, -0.5],
                explode={"BUY_bus_junction": sc(DOWN, 1.2), "CAB_bus_pan_tail": sc(DOWN, 1.2)},
                explode_src="splice pushed up the hub-gear bore (cadcheck -Z; slide row 'v3-A1 bus splice pulls -Z')",
                warnings=[("critical", "The finished splice must be Ø10 x 20 or smaller.",
                           [(A, "**The finished splice must be Ø10 x 20 or smaller**")]),
                          ("warning", "Shield the PLA with card or foil while soldering.",
                           [(A, "Shield the PLA with card or foil.")]),
                          ("warning", "Trim the tilt and feeder leads to route + 70; leave the pan lead long.",
                           [(A, "**Trim the tilt and feeder leads to route + 70**"),
                            (A, "Leave it long.")]),
                          ("warning", "The 2 x 70 of trimmed spare has no home in the model (review v3-A1-07, open). Push "
                                      "the tilt spare toward the right post channel and the feeder spare toward the left, "
                                      "so the bore under the splice stays clear.",
                           [(A, "the model gives no home to the 2 x 70 of trimmed spare")]),
                          ("warning", "Overlap the sleeves loosely at the hand-over, with no tie: it swings a 5.7 chord "
                                      "over ±90 pan.", [(A, "sleeves loosely, with no tie")]),
                          ("warning", "The shell goes on its side here: hold it by the base shell, never by the beam or "
                                      "the crown. (On a later service, take the jar off first.)",
                           [(A, "If it has to go on its side (step 11a, service), take the jar off first.")])]),
    "12": dict(joint="slide (card guides, hook rails) + snap (2 tongues)", view=[0.6, -1.0, 0.7],
               explode={"BUY_motorgo_axis": UP, "BUY_buck_12v": sc(LEFT, 1.2), "BUY_servo_controller": UP},
               explode_src="MotorGo down its card guides (cadcheck +Z); buck +X under its hook rails, so from -X "
                           "(cadcheck -X); controller pressed down into its fences",
               warnings=[("warning", "Don't drill the controller's bosses: in v3 the board has no screws.",
                          [(A, "Don't drill the bosses"), (M, "The board sits on 4 Ø7 bosses. Don't drill them")]),
                         ("warning", "Measure first (item 7): nothing on the MotorGo's component face may sit closer "
                                     "than 0.5 to either side edge, where the card guides run.",
                          [(M, "Check nothing on your board is closer than 0.5 to either side edge")]),
                         ("warning", "Measure first (item 10): fins inside the buck's 3.4 flange strips stop the slide.",
                          [(M, "Fins inside that strip stop the slide.")])]),
    "13": dict(joint="snap (2 latches, 2 detents, in plane)", view=[1.0, -1.0, -0.35],
               explode={"*": DOWN, "CAB_*": [0, 0, 0], "BUY_usbc_plug": sc(BACK, 1.0)},
               explode_src="floor pushed straight up into the shell (slide row 'v3-A1 base floor + electronics drop "
                           "-Z'); USB-C plug in from the rear (cadcheck -Y)",
               warnings=[("warning", "Both U-loops must hang free under the hub gear: they are the ±90 pan slack.",
                          [(A, "Check that both U-loops hang free under the hub gear")]),
                         ("warning", "The phases are soldered to the MotorGo: when the floor comes off, lower it gently "
                                     "on its leads.", [(A, "The phases are soldered, so lower it gently on its leads")])]),
    "14": dict(joint="slide (gate) + snap (2 valve fingers, across layers)", view=[1.0, 1.2, 0.2],
               explode={"BUY_jar_band": sc(DOWN, 0.6), "PRT_jar_adapter": sc(DOWN, 0.6), "PRT_jar_valve": sc(DOWN, 1.4),
                        "PRT_jar_gate": [1.0, 0, -1.4]},
               explode_src="machine frame (the jar hangs mouth-down): band and adapter disc onto the jar mouth (cadcheck "
                           "-Z for the band); gate slid -X into the valve, so from +X, riding with the valve; valve and "
                           "gate pushed onto the adapter spout",
               renders=[("../renders/attempt-1/sec_gate_finger_z325.png",
                         "attempt-1 gate: the hotfix added the open detent (v3-A1-03)")],
               warnings=[("critical", "Carry the jar group by itself, and never the machine by the jar. The 2 valve "
                                      "fingers bend across layers: about 32 N and 12.3 MPa when it hangs, and a 1.5 g "
                                      "jolt takes them to about 19 MPa, past the 15 MPa interlayer limit.",
                          [(A, "Carry the jar group by itself, never the machine by the jar."),
                           (A, "band, then adapter, then the **2 valve fingers**: about 32 N, 12.3 MPa")] + LIFT_SRC[:1]),
                         ("critical", "Shoulder contact: no daylight between the spout shoulder and the ±Y cheek-pad tops, "
                                      "and a 0.1 feeler mustn't go in. If either pad shows a gap, the jar's weight goes "
                                      "onto the 2 valve fingers: don't fill or mount the jar.",
                          [(A, "**shoulder contact (hotfix review N1):**"), (M, "don't fill or mount the jar")]),
                         ("warning", "Gate first: it can't go in once the adapter is on.",
                          [(A, "the gate can't go in once the adapter is on")]),
                         ("warning", "Measure first (item 3a): every 0.5 finger slot in the gate must show daylight along "
                                     "its whole length before it goes into the valve. First-layer squish can bridge them "
                                     "and lock a finger.", [(M, "First-layer squish can bridge them and lock a finger.")]),
                         ("warning", "Measure first (item 1): a band over about 74 OD eats the 3.0 gap to the feed floor.",
                          [(M, "A band over about 74 eats that gap.")])]),
    "15": dict(joint="bayonet (drop in at +30, twist to 0)", explode={"*": UP}, pose_in={"jar": 30},
               view=[1.0, 1.2, 0.4],
               explode_src="dropped in at +30 and twisted to 0 (pose PIV_jar 30; slide row 'jar group lifts off when "
                           "unlocked' +Z)",
               renders=[("../renders/attempt-1/jar_unlocked.png", "the jar at +30, unlocked")],
               warnings=[("critical", LIFT_TEXT + " The jar is now on: it is the part most likely to be grabbed.",
                          LIFT_SRC + [(A, "Lift it by the jar and the whole 4075 g machine")]),
                         ("warning", "Close the gate before you drop the jar group in.", [(A, "**Do:** close the gate.")])]),
    "16": dict(joint="slide (battery rail)", explode={"BUY_battery": sc(RIGHT, 1.2)}, view=[0.5, -1.0, 0.45],
               explode_src="slid onto the rail from +X (cadcheck +X; slide row 'battery out +X')",
               renders=[("../renders/attempt-1/side.png", "the finished machine from the side (attempt 1)")],
               warnings=[("critical", "Power up with the flywheel motor disabled. Spin it up only after the servos are "
                                      "pinged and trimmed and the tilt is clamped to 0..45 in firmware.",
                          [(A, "Power up with the flywheel motor disabled."), (A, "Clamp firmware tilt to 0..45")]),
                         ("warning", "If the pod isn't level at tilt 0, set a firmware offset rather than moving the horn.",
                          [(A, "set a tilt offset in firmware rather than moving the horn")]),
                         ("critical", "To move the finished machine: battery out, then both hands flat under the base "
                                      "shell. Never by the jar, the crown or the beam.", LIFT_SRC)]),
}

# step id -> checks.json assembly_order labels (default: the id itself)
LABELS = {"0": []}
# manifest fastener step labels that differ from ASSEMBLY.md
MANIFEST_ALIAS = {"6c/6d": ["6c", "6d"]}
# joint kinds that must carry ASSEMBLY.md Seats and Release lines
NEEDS_SEATS = ("snap", "slide", "press", "bayonet")
# assembly_order globs that match nothing in the model, and why it does or doesn't matter
DEAD_GLOBS = {
    "PRT_cable_clip*": ("note", "Glob matches nothing; the 2 UART clips are printed into the floor (UART_CLIPS), so "
                                "there is no separate part."),
    "FST_clip_*": ("note", "Glob matches nothing; v3 has no clip screws (manifest fastener_summary: 11 screws)."),
}


# thumbnails: path relative to BUILD/ as written in ASSEMBLY.md -> file on disk
def render_path(ref):
    ref = ref.strip("`")
    if not ref.endswith(".png"):
        ref += ".png"
    if ref.startswith("renders/"):
        return os.path.join(BUILD, ref)
    if ref.startswith("../renders/"):
        return os.path.join(V3, ref[3:])
    return None


# ---------------------------------------------------------------- markdown helpers
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


ITEM = re.compile(r"^(\s*)(-|\d+\.)\s+(.*)$")


def md_list_to_html(lines):
    """nested - / 1. lists with wrapped continuation lines -> HTML. Lines that aren't list items are paragraphs."""
    merged = []                  # join wrapped continuation lines first, so **bold** can span a line break
    for ln in lines:
        if not ln.strip():
            continue
        if ITEM.match(ln) or not merged:
            merged.append(ln.rstrip())
        else:
            merged[-1] += " " + ln.strip()
    lines = merged
    out, stack = [], []          # stack of (indent, tag)
    def close_to(indent):
        while stack and stack[-1][0] > indent:
            out.append("</li></%s>" % stack.pop()[1])
    para = []
    def flush_para():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()
    for ln in lines:
        if not ln.strip():
            continue
        m = ITEM.match(ln)
        if m:
            flush_para()
            ind = len(m.group(1))
            tag = "ol" if m.group(2)[0].isdigit() else "ul"
            close_to(ind)
            if stack and stack[-1][0] == ind:
                out.append("</li><li>%s" % inline(m.group(3)))
            else:
                out.append("<%s><li>%s" % (tag, inline(m.group(3))))
                stack.append((ind, tag))
        elif stack:
            out[-1] += " " + inline(ln.strip())
        else:
            para.append(ln.strip())
    flush_para()
    close_to(-1)
    return "".join(out)


def split_fields(body):
    """top-level '- **Label:** text' bullets (with their nested lines) -> OrderedDict label -> (text, nested lines);
    other top-level lines -> paragraphs (wrapped lines joined; a blank line ends one)"""
    fields, paras, cur, in_para = OrderedDict(), [], None, False
    for ln in body:
        m = re.match(r"^- \*\*(.+?):\*\*\s*(.*)$", ln)
        # '- **Release: none.** The barbs ...' (the value is inside the bold)
        m2 = None if m else re.match(r"^- \*\*([A-Z][^*:]*?):\s+([^*]+?)\*\*\s*(.*)$", ln)
        # '- **Do, in this order** (the gate can't go in ...):'
        m3 = None if m or m2 else re.match(r"^- \*\*([A-Z][^*]*?)\*\*\s*(\(.*\)):\s*(.*)$", ln)
        if m:
            cur, in_para = m.group(1), False
            fields[cur] = [m.group(2), []]
        elif m2:
            cur, in_para = m2.group(1), False
            fields[cur] = ["**%s** %s" % (m2.group(2), m2.group(3)), []]
        elif m3:
            cur, in_para = m3.group(1), False
            fields[cur] = [(m3.group(2) + " " + m3.group(3)).strip(), []]
        elif ln.startswith("  ") and cur is not None:
            fields[cur][1].append(ln[2:])
        elif ln.strip():
            cur = None
            if in_para:
                paras[-1] += " " + ln.strip()
            else:
                paras.append(ln.strip())
            in_para = True
        else:
            in_para = False
    return fields, paras


RENDER_LEAD = re.compile(r"^(?:Render|Exploded view):\s*`[^`]+`[^.]*\.\s*")


def strip_render_refs(p):
    """'Render: `renders/x.png` (note). If you did ...' -> 'If you did ...' (the renders are shown as figures)"""
    while RENDER_LEAD.match(p):
        p = RENDER_LEAD.sub("", p, count=1)
    return p


def field_html(text, nested):
    head = inline(text) if text else ""
    rest = md_list_to_html(nested) if nested else ""
    if head and rest and not nested[0].lstrip().startswith(("-", "1.")):
        # wrapped continuation of the first line
        cont, lst = [], []
        for i, ln in enumerate(nested):
            if ITEM.match(ln):
                lst = nested[i:]
                break
            cont.append(ln.strip())
        head = inline(" ".join([text] + cont))
        rest = md_list_to_html(lst) if lst else ""
    return ("<p>%s</p>" % head if head else "") + rest


def field_text(text, nested):
    return " ".join([text] + [ln.strip() for ln in nested]).strip()


# ---------------------------------------------------------------- fasteners
# "2 x M3 pan x 10", "1 x M3 x 6 socket cap", "the M3 x 16 hex-head stud" (v3 names the head between size and length)
SCREW = re.compile(r"(?:(\d+)\s*x\s*|the\s+)(?:\*\*)?(M[\d.]+)(?:\s+(?:pan|cap|hex|csk))?\s*x\s*(\d+)(?:\*\*)?")
NUT = re.compile(r"(?:(\d+)\s*(?:x\s*)?)?(?:captive\s+)?M3 nuts?\b")


def parse_fasteners(text):
    """'2 x M3 pan x 10 (...); ...' -> rows {qty, spec, note} and a Counter keyed (size, length) / 'nut'"""
    rows, count = [], Counter()
    plain = text.replace("**", "")
    for seg in [s.strip() for s in re.split(r";\s*", plain) if s.strip()]:
        seg_rows = []
        for m in SCREW.finditer(seg):
            # skip alternatives ("or M3 x 10 if you changed MG_*")
            pre = seg[max(0, m.start() - 4):m.start()]
            if "or " in pre and not m.group(1):
                continue
            qty = int(m.group(1)) if m.group(1) else 1
            count[(m.group(2), int(m.group(3)))] += qty
            seg_rows.append(qty)
        for m in NUT.finditer(seg):
            qty = int(m.group(1)) if m.group(1) else 1
            count["nut"] += qty
            seg_rows.append(qty)
        if seg_rows:
            qty = seg_rows[0]
            spec = re.sub(r"^\d+\s*x\s*", "", seg)
            rows.append({"qty": qty, "text": seg, "spec": spec})
        else:
            rows.append({"qty": None, "text": seg, "spec": seg})
    return rows, count


def manifest_count(parts, labels):
    c = Counter()
    for n, v in parts.items():
        if not n.startswith("FST_") or v.get("step") not in labels:
            continue
        spec = v.get("part", "")
        if "nut" in spec:
            c["nut"] += 1
            continue
        m = re.match(r"(M[\d.]+)_\w+ x (\d+)", spec)
        if m:
            c[(m.group(1), int(m.group(2)))] += 1
    return c


def fmt_count(c):
    return ", ".join("%d x %s" % (n, k if k == "nut" else "%s x %d" % k) for k, n in sorted(c.items(), key=str))


# ---------------------------------------------------------------- ASSEMBLY.md and MEASURE_FIRST.md
STEP_ID = r"\d+[a-z]?(?:/\d+[a-z]?)?"


def parse_assembly(path):
    """### N. title -> a step in the current ## group. A numbered ## heading with no ### under it (v3's '## 11a. Bus
    splice from below') is a step of its own, in a group of the same name."""
    lines = open(path).read().splitlines()
    steps, group, group_paras = [], None, {}
    cur, pending = None, None      # pending: a numbered ## heading that is a step unless a ### follows
    step_head = re.compile(r"^### (%s)\.?\s+(.*)$" % STEP_ID)
    for ln in lines:
        if ln.startswith("## "):
            cur, pending = None, None
            h = ln[3:].strip()
            m = re.match(r"Step (\d+): (.*)", h)
            if m:
                group = "Before you start"
                cur = {"id": m.group(1), "title": m.group(2)[0].upper() + m.group(2)[1:], "group": group, "body": []}
                steps.append(cur)
                continue
            m = re.match(r"(%s)\.\s+(.*)" % STEP_ID, h)
            group = m.group(2) if m else h
            group_paras[group] = []
            if m:
                pending = {"id": m.group(1), "title": m.group(2), "group": group, "body": []}
                steps.append(pending)
                cur = pending
            continue
        m = step_head.match(ln)
        if m:
            if pending is not None:          # the ## was a group heading after all
                steps.remove(pending)
                group_paras[group] = pending["body"]
                pending = None
            cur = {"id": m.group(1), "title": m.group(2).strip(), "group": group, "body": []}
            steps.append(cur)
            continue
        if cur is not None:
            cur["body"].append(ln)
        elif group in group_paras:
            group_paras[group].append(ln)
    return steps, group_paras


def doc_index(path, kind):
    """line number -> the section it is in ('14', '11a', 'intro' / '3b', '2'), for warning citations"""
    sect, out = "intro", []
    for ln in open(path).read().splitlines():
        if kind == "ASSEMBLY":
            m = re.match(r"^## Step (\d+):", ln) or re.match(r"^#{2,3} (%s)\.?\s" % STEP_ID, ln)
            if m:
                sect = m.group(1)
            elif ln.startswith("## "):
                sect = ln[3:].strip()
        else:
            m = re.match(r"^#{2,3} (\d+[a-z]?)\.\s", ln)
            if m:
                sect = m.group(1)
        out.append((sect, ln))
    return out


def cite(src, idx):
    """[(doc, quoted text)] -> ('ASSEMBLY 14, line 410 · ...', missing quotes). The quote may wrap across lines: the
    doc is searched as one string with each line's indent and '> ' stripped, and the hit is cited at its first line."""
    parts, missing = [], []
    for doc, needle in src:
        flat, starts = "", []
        for sect, ln in idx[doc]:
            starts.append(len(flat))
            flat += re.sub(r"^\s*>?\s*", "", ln).rstrip() + " "
        at = flat.find(" ".join(needle.split()))
        if at < 0:
            missing.append("%s: %r" % (doc, needle))
            continue
        line = max(i for i, st in enumerate(starts) if st <= at)
        sect = idx[doc][line][0]
        parts.append("%s %s, line %d" % (doc, sect if len(sect) < 12 else "'%s'" % sect, line + 1))
    return " · ".join(parts), missing


def parse_measure(path):
    """MEASURE_FIRST.md '## N. title (before ...)' -> rows for the overview table"""
    rows = []
    for ln in open(path).read().splitlines():
        m = re.match(r"^## (\d+)\. (.*)$", ln)
        if not m:
            continue
        title, before = m.group(2), ""
        p = re.search(r"\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*$", title)
        if p:
            before = p.group(1)
            title = title[:p.start()]
            if before.startswith("before "):
                before = before[7:]
        rows.append({"item": m.group(1), "what": title, "before": before})
    return rows


# ---------------------------------------------------------------- GLB
def glb_json(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + n]), b


def thumb(path, cache):
    if path in cache:
        return cache[path]
    tmp = tempfile.mkdtemp(prefix="mmguide_")
    out = os.path.join(tmp, "t.jpg")
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "78", "-Z", "720", path, "--out", out],
                   check=True, capture_output=True)
    data = "data:image/jpeg;base64," + base64.b64encode(open(out, "rb").read()).decode()
    cache[path] = data
    return data


# ---------------------------------------------------------------- directions
AXES = {"+X": RIGHT, "-X": LEFT, "+Y": FRONT, "-Y": BACK, "+Z": UP, "-Z": DOWN}


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return [c / n for c in v] if n > 1e-9 else [0, 0, 0]


def words(v):
    u = unit(v)
    for k, a in AXES.items():
        if sum(x * y for x, y in zip(u, a)) > 0.999:
            return "from " + k
    return "from (%s)" % ", ".join("%.2f" % c for c in u)


def rot_x(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c]


def glob_rank(g):
    """more specific globs rank higher: exact names first, then the longer literal prefix"""
    lit = re.split(r"[*?\[]", g)[0]
    return (1 if lit == g else 0, len(lit))


# ---------------------------------------------------------------- main
def main():
    checks = json.load(open(os.path.join(BL, "checks.json")))
    man = json.load(open(os.path.join(BL, "manifest.json")))
    parts = man["parts"]
    plates = json.load(open(os.path.join(BUILD, "plates.json")))
    est = json.load(open(os.path.join(BUILD, "print_estimate.json")))
    cc = json.load(open(CADCHECK))
    gj, glb_bytes = glb_json(GLB)
    nodes = [n["name"] for n in gj["nodes"]]
    mesh_nodes = [n["name"] for n in gj["nodes"] if "mesh" in n]
    order = [e for e in checks["assembly_order"] if e.get("step")]
    empty_entries = len(checks["assembly_order"]) - len(order)
    by_label = {e["step"].split(" ")[0]: (i, e) for i, e in enumerate(order)}
    idx = {k: doc_index(p, k) for k, p in DOCS.items()}
    free = {}   # cadcheck insertion: object or group -> (free_dir vector, obstacles)
    for r in cc["checks"]["insertion"]["rows"]:
        fd = r.get("free_dir")
        if fd in AXES:
            vec = AXES[fd]
        elif fd and fd.startswith("along "):
            vec = parts[fd[6:]]["into"]
        elif fd and fd.startswith("against "):
            vec = [-c for c in parts[fd[8:]]["into"]]
        else:
            vec = None
        m = re.match(r"group '(\w+)'", r["object"])
        free[("group", m.group(1)) if m else r["object"]] = (vec, r["obstacles"], fd)

    # who places what: each mesh node goes to the entry whose matching glob is most specific (ties: the earlier entry)
    owner, claim_notes = {}, {}
    for i, e in enumerate(order):
        for g in e["objects"]:
            for n in mesh_nodes:
                if fnmatch.fnmatchcase(n, g):
                    rank = glob_rank(g)
                    if n not in owner or rank > owner[n][2]:
                        if n in owner:
                            claim_notes.setdefault(owner[n][0], []).append((owner[n][1], n, i, g))
                        owner[n] = (i, g, rank)

    asm_steps, group_paras = parse_assembly(DOCS["ASSEMBLY"])
    placed, out_steps, bench_of = set(), [], {}
    thumbs_cache, thumbs = {}, {}
    used_labels = set()
    tilt_children = {n for n, v in parts.items() if v.get("joint") in ("PIV_tilt", "PIV_flywheel", "PIV_hood",
                                                                       "PIV_nip_lift")}

    for k, s in enumerate(asm_steps):
        sid = s["id"]
        cur = CURATED.get(sid, {})
        labels = LABELS.get(sid, [sid])
        flags, notes = [], list(cur.get("notes", []))
        if sid not in CURATED:
            flags.append("No CURATED entry for this step (no fly-in directions, view or warnings).")
        entries = []
        for lab in labels:
            if lab not in by_label:
                flags.append("No checks.json assembly_order entry labelled %s." % lab)
                continue
            entries.append(by_label[lab])
            used_labels.add(lab)
        bench = next((e.get("bench") for _, e in entries if e.get("bench")), None)
        merge = next((e.get("merge") for _, e in entries if e.get("merge")), None)
        new, globs = [], []
        for i, e in entries:
            for g in e["objects"]:
                globs.append(g)
                hit = [n for n in mesh_nodes if fnmatch.fnmatchcase(n, g)]
                if not hit:
                    kind, why = DEAD_GLOBS.get(g, ("flag", "Glob matches nothing in the model."))
                    (flags if kind == "flag" else notes).append("%s: %s" % (g, why))
                for n in hit:
                    if owner[n][0] != i:
                        oi, og, _ = owner[n]
                        notes.append("%s also matches %s, which step %s names more exactly (%s); it is placed there."
                                     % (g, n, order[oi]["step"].split(" ")[0], og))
                        continue
                    if n not in placed:
                        placed.add(n)
                        new.append(n)
                        if bench:
                            bench_of[n] = bench
        if not labels and sid != "0":
            flags.append("No assembly_order label for this step.")

        fields, paras = split_fields(s["body"])
        F = OrderedDict()
        for lab, (text, nested) in fields.items():
            F[lab] = {"html": field_html(text, nested), "text": field_text(text, nested)}
        tools = []
        if "Tools" in F:
            tools = [t.strip() for t in re.split(r",\s*(?![^(]*\))", F["Tools"]["text"].rstrip(".")) if t.strip()]
            tools = [inline(t) for t in tools]
        fast_rows, fast_count = [], Counter()
        if "Fasteners" in F:
            fast_rows, fast_count = parse_fasteners(F["Fasteners"]["text"])
            for r in fast_rows:
                r["text"] = inline(r["text"])
                r["spec"] = inline(r["spec"])
        mlabels = [x for l in labels for x in MANIFEST_ALIAS.get(l, [l])]
        model_count = manifest_count(parts, mlabels)
        if not fast_count and not model_count:
            fcheck = {"state": "na", "text": "No metal fasteners in this step."}
        elif fast_count == model_count:
            fcheck = {"state": "good", "text": "Model agrees: " + fmt_count(model_count)}
        else:
            fcheck = {"state": "warning", "text": "ASSEMBLY.md lists %s; the model has %s." % (
                fmt_count(fast_count) or "none", fmt_count(model_count) or "none")}
            flags.append("Fastener counts disagree: " + fcheck["text"])

        # joint: Seats and Release lines
        joint = cur.get("joint")
        seats = next((lab for lab in F if lab.startswith("Seats")), None)
        release = next((lab for lab in F if lab.startswith("Release")), None)
        if joint and any(joint.startswith(j) or (", " + j) in joint or ("+ " + j) in joint for j in NEEDS_SEATS):
            miss = [w for w, have in (("Seats", seats), ("Release", release)) if not have]
            if miss:
                notes.append("ASSEMBLY.md gives no %s line for this %s step." % (" or ".join(miss), joint))

        # renders: every .png named in the step body, plus its section's, plus the curated design renders
        refs = re.findall(r"`((?:\.\./)?renders/[^`]+?\.png)`", "\n".join(s["body"]))
        sect = re.findall(r"`((?:\.\./)?renders/[^`]+?\.png)`", "\n".join(group_paras.get(s["group"], [])))
        renders = []
        for ref, scope, note in ([(r, "step", "") for r in refs] + [(r, "section", "") for r in sect] +
                                 [(r, "design", n) for r, n in cur.get("renders", [])]):
            p = render_path(ref)
            if p and os.path.exists(p) and ref not in [x["ref"] for x in renders]:
                key = os.path.splitext(os.path.basename(p))[0]
                thumbs[key] = thumb(p, thumbs_cache)
                renders.append({"ref": ref, "key": key, "scope": scope, "note": note})
            elif p and not os.path.exists(p):
                flags.append("Render %s is missing on disk." % ref)

        def resolve(gl):
            out = []
            for g in gl:
                out += [n for n in nodes if fnmatch.fnmatchcase(n, g) and n not in out]
            return out

        focus = resolve(cur["focus"]) if "focus" in cur else list(new)
        if merge:
            focus = list(new) + [n for n, b in bench_of.items() if b == merge and n not in new]

        # explode vectors (design frame, unit-ish; JS scales by the step size)
        exp_rules = cur.get("explode", {})
        for g in exp_rules:
            if g != "*" and not resolve([g]):
                flags.append("CURATED explode glob %s matches nothing in the GLB." % g)
        explode = {}
        for n in focus:
            rule = None
            for g, d in exp_rules.items():
                if g != "*" and fnmatch.fnmatchcase(n, g):
                    rule = d
                    break
            p = parts.get(n, {})
            if rule is None and n.startswith("FST_") and p.get("into"):
                into = p["into"]
                sign = 1.0 if "nut" in p.get("part", "") else -1.0
                base = exp_rules.get("*")
                vec = [sign * c * 1.4 for c in into]
                if base and merge and bench_of.get(n) == merge:
                    vec = list(base)          # a fastener riding a merged sub-assembly moves with it
                rule = vec
            if rule is None:
                rule = exp_rules.get("*")
            if rule is None:
                rule = [0, 0, 0] if exp_rules else "radial"
            explode[n] = rule

        # the pose a joint holds while the parts fly in: parts under PIV_tilt get their offset counter-rotated, so
        # they still come straight down in the world while the pod is nose-up
        pose_in = cur.get("pose_in")
        if pose_in and pose_in.get("tilt"):
            for n in explode:
                if n in tilt_children and isinstance(explode[n], list):
                    explode[n] = [round(c, 4) for c in rot_x(explode[n], -pose_in["tilt"])]

        # fly-in directions against cadcheck's insertion rows
        dir_why = cur.get("dir_why", {})
        checked = []
        for n, rule in explode.items():
            if not isinstance(rule, list) or not any(rule) or n.startswith(("FST_", "CAB_")):
                continue
            key = ("group", merge) if merge and bench_of.get(n) == merge else n
            if key in checked:
                continue
            checked.append(key)
            vec, obst, fd = free.get(key, (None, 0, None))
            if vec is None or obst == 0:
                continue          # blocked both ways (a snap or a press: its slide row is the source) or nothing to pass
            ours = rule if not (pose_in and pose_in.get("tilt") and n in tilt_children) else rot_x(rule, pose_in["tilt"])
            if sum(a * b for a, b in zip(unit(ours), unit(vec))) < 0.5:
                why = dir_why.get("group" if isinstance(key, tuple) else n)
                label = "group '%s'" % merge if isinstance(key, tuple) else n
                if why:
                    notes.append("Fly-in for %s is %s; cadcheck's insertion found it free along %s: %s." % (
                        label, words(ours), fd, why))
                else:
                    flags.append("Fly-in for %s is %s, but cadcheck's insertion found it free along %s (no dir_why)."
                                 % (label, words(ours), fd))
        moving = OrderedDict()
        for n, rule in explode.items():
            if isinstance(rule, list) and any(rule) and not n.startswith("FST_"):
                moving.setdefault(words(rule), []).append(n)
        fly = "; ".join("%s %s" % (", ".join(v), w) for w, v in moving.items())
        if fly:
            notes.insert(0, "Fly-in: %s. Source: %s." % (fly, cur.get("explode_src", "not stated")))

        # warnings, each citing the line its text comes from
        warnings = []
        for lv, t, src in cur.get("warnings", []):
            where, missing = cite(src, idx)
            for q in missing:
                flags.append("Warning source text not found in %s." % q)
            warnings.append({"level": lv, "text": t, "source": where})

        status = "flagged" if flags else "clean"
        out_steps.append(OrderedDict([
            ("index", k), ("id", sid), ("title", s["title"]), ("group", s["group"]),
            ("status", status), ("flags", flags), ("notes", notes),
            ("assembly_order", [{"label": e["step"].split(" ")[0], "index": i, "step": e["step"],
                                 "bench": e.get("bench"), "merge": e.get("merge"),
                                 "insert_dirs": e.get("insert_dirs"), "pose": e.get("pose")} for i, e in entries]),
            ("bench", bench), ("merge", merge), ("joint", joint),
            ("new_objects", new), ("focus_objects", focus), ("extra_objects", resolve(cur.get("extra", []))),
            ("hide_objects", resolve(cur.get("hide", []))),
            ("shift", {"objects": resolve(cur["shift"]["objects"]), "mm": cur["shift"]["mm"]} if "shift" in cur else None),
            ("pose", dict({"pan": 0, "tilt": 0, "jar": 0}, **cur.get("pose", {}))),
            ("pose_in", pose_in),
            ("view", cur.get("view", DEFAULT_VIEW)),
            ("explode", explode),
            ("tools", tools),
            ("fasteners", fast_rows),
            ("fastener_check", fcheck),
            ("seats", F[seats]["text"] if seats else None),
            ("release", {"label": release, "text": F[release]["text"]} if release else None),
            ("fields", [{"label": lab, "html": v["html"],
                         "kind": "seats" if lab == seats else "release" if lab == release else None}
                        for lab, v in F.items() if lab not in ("Tools", "Fasteners")]),
            ("check", F.get("Check", {}).get("text", "")),
            ("paragraphs", [inline(q) for q in (strip_render_refs(p) for p in paras) if q]),
            ("warnings", warnings),
            ("renders", renders),
        ]))

    unused = [e["step"].split(" ")[0] for e in order if e["step"].split(" ")[0] not in used_labels]
    unplaced = [n for n in mesh_nodes if n not in placed and not n.startswith("TOOL_")]

    # parts table for tooltips and the overview
    stl_plate = {}
    for p in plates["plates"]:
        for it in p["items"]:
            if "test copy" not in it.get("note", ""):
                stl_plate[it["stl"]] = p["name"]
    first_step = {}
    for st in out_steps:
        for n in st["new_objects"]:
            first_step[n] = st["id"]
    colour_b = COLOUR_B()
    PT = {}
    for n in mesh_nodes:
        p = parts.get(n, {})
        d = {"kind": n.split("_")[0], "step": first_step.get(n)}
        if n.startswith("PRT_"):
            d.update(stl=p.get("stl"), plate=stl_plate.get(p.get("stl")), orient=p.get("orient"), infill=p.get("infill"),
                     colour="B" if n in colour_b else "A")
        elif n.startswith("BUY_"):
            d.update(mass_g=p.get("mass_g"), src=p.get("src"))
        elif n.startswith("FST_"):
            d.update(spec=p.get("part"), host=p.get("host"))
        elif n.startswith("CAB_"):
            d.update(lead=p.get("lead_len"), path=round(p["path_len"]) if p.get("path_len") else None)
        PT[n] = d

    plate_rows = []
    for p in plates["plates"]:
        e = est["plates"].get(p["name"], {})
        plate_rows.append({"name": p["name"], "printer": p["printer"], "colour": p["colour"], "subsystem": p["subsystem"],
                           "h": e.get("h"), "g": e.get("g"),
                           "items": [{"stl": it["stl"].split("/")[-1] if it["stl"].startswith("../") else it["stl"],
                                      "qty": it.get("qty", 1), "infill": it["infill"],
                                      "hotfix": bool(it.get("hotfix")),
                                      "kind": "machine" if any(v.get("stl") == it["stl"] for v in PT.values())
                                              and "test copy" not in it.get("note", "") else
                                              "test" if it["stl"].startswith("../") or "test copy" in it.get("note", "")
                                              else "tool",
                                      "objects": [n for n, v in PT.items() if v.get("stl") == it["stl"]]
                                      if "test copy" not in it.get("note", "") else []}
                                     for it in p["items"]]})
    measure = parse_measure(DOCS["MEASURE_FIRST"])

    clean = sum(1 for s in out_steps if s["status"] == "clean")
    summary = {
        "steps": len(out_steps), "clean": clean, "flagged": len(out_steps) - clean,
        "assembly_order_entries_unused": unused, "assembly_order_empty_entries": empty_entries,
        "objects_never_placed": unplaced,
    }
    steps_doc = OrderedDict([
        ("_about", "ASSEMBLY.md steps mapped to the GLB's objects (BUILD/guide/build_guide.py). new_objects: objects that "
                   "first appear in the step, from checks.json assembly_order. focus_objects: what the viewer highlights "
                   "(new objects, plus a merged bench sub-assembly). explode: the direction each part flies in from. "
                   "Directions are in the design frame: +X right, +Y front, +Z up. status 'flagged' lists the reason in "
                   "flags."),
        ("summary", summary),
        ("steps", out_steps),
    ])
    json.dump(steps_doc, open(OUT_STEPS, "w"), indent=1)

    # header facts, from the files
    ccs = cc["summary"]
    fs = man["fastener_summary"]
    nuts = sum(1 for n, v in parts.items() if n.startswith("FST_") and "nut" in v.get("part", ""))
    kinds = Counter(n.split("_")[0] for n in parts)
    machine_prints = sum(it.get("qty", 1) for p in plate_rows for it in p["items"] if it["kind"] == "machine")
    twice = [it["stl"] for p in plate_rows for it in p["items"] if it["kind"] == "machine" and it["qty"] > 1]
    by_printer = Counter()
    for p in plate_rows:
        by_printer[p["printer"]] += p["h"] or 0
    meta = {
        "title": "M&M launcher v3 assembly",
        "model": "v3 attempt 1 + attempt-2 hotfix",
        "cadcheck": "%d fails, %d warns" % (ccs["fails"], ccs["warns"]),
        "cadcheck_detail": "%d accepted, %d untriaged, %d config (renders/attempt-2/cadcheck.json, %s)" % (
            len(ccs["accepted_warns"]), ccs["untriaged_warns"], len(ccs["config_warns"]), cc["generated"][:10]),
        "hardware": "%d printed parts · %d screws + %d nuts" % (kinds["PRT"], fs["screws"], nuts),
        "objects": len(mesh_nodes), "glb_mb": round(len(glb_bytes) / 1e6, 2),
        "totals": est["total"], "estimate_label": est["_label"],
        "counts": dict(Counter(v["kind"] for v in PT.values())),
        "tiles": {
            "parts_sub": "%d prints: the %s twice" % (machine_prints, ", ".join(t.replace("_", " ") for t in twice))
                         if twice else "%d prints" % machine_prints,
            "plates_sub": " · ".join("%s %d" % (pr, sum(1 for p in plate_rows if p["printer"] == pr))
                                     for pr in sorted(by_printer)),
            "time_sub": "about %d h on both printers" % round(max(by_printer.values())),
            "fasteners": fs["screws"] + nuts,
            "fasteners_sub": "%d screws + %d nuts, %d screw specs; the rest snaps, slides and pins" % (
                fs["screws"], nuts, fs["distinct"]),
        },
    }
    data = {"meta": meta, "steps": out_steps, "parts": PT, "plates": plate_rows, "measure": measure, "thumbs": thumbs,
            "bench_of": bench_of}

    src = os.path.join(HERE, "src")
    tpl = open(os.path.join(src, "template.html")).read()
    three_mod = open(os.path.join(STYLE, "ax-three.js")).read()
    three_mod = "\n".join(l for l in three_mod.splitlines() if not l.startswith("import "))
    three_mod = three_mod.replace("export function axScene", "function axScene")
    app = open(os.path.join(src, "app.js")).read()
    rep = {
        "/*@TOKENS_CSS@*/": open(os.path.join(STYLE, "tokens.css")).read(),
        "/*@GUIDE_CSS@*/": open(os.path.join(src, "guide.css")).read(),
        "/*@AX_FX@*/": open(os.path.join(STYLE, "ax-fx.js")).read(),
        "/*@AX_THREE@*/": three_mod,
        "/*@APP@*/": app,
        "@THREE@": THREE,
        "@DATA@": json.dumps(data, separators=(",", ":")).replace("</", "<\\/"),
        "@GLB@": base64.b64encode(glb_bytes).decode(),
    }
    for k in ("/*@AX_FX@*/", "/*@AX_THREE@*/", "/*@APP@*/"):
        # the style guide's files show usage like <script src="ax-fx.js"></script> in comments; inlined, that
        # would close the page's script element
        rep[k] = re.sub(r"</(script)", r"<\\/\1", rep[k], flags=re.I)
    for k, v in rep.items():
        assert k in tpl, k
        tpl = tpl.replace(k, v)
    open(OUT_HTML, "w").write(tpl)
    print("header: model %s · cadcheck %s (%s) · %s" % (meta["model"], meta["cadcheck"], meta["cadcheck_detail"],
                                                      meta["hardware"]))
    print("steps: %d (%d clean, %d flagged)" % (len(out_steps), clean, len(out_steps) - clean))
    for s in out_steps:
        print("  %-6s %-8s new %3d focus %3d warn %d  %s" % (s["id"], s["status"], len(s["new_objects"]),
                                                            len(s["focus_objects"]), len(s["warnings"]),
                                                            "; ".join(s["flags"])[:200]))
    print("unused assembly_order entries:", unused, " empty entries:", empty_entries, " never placed:", unplaced)
    print("wrote %s (%.2f MB), %s" % (OUT_HTML, os.path.getsize(OUT_HTML) / 1e6, OUT_STEPS))


def COLOUR_B():
    """params.COLOUR_B, read from the source so the guide never imports the design's params (it imports bpy)"""
    txt = open(os.path.join(BL, "params.py")).read()
    m = re.search(r"COLOUR_B\s*=\s*\[(.*?)\]", txt, re.S)
    return set(re.findall(r'"(PRT_[^"]+)"', m.group(1)))


if __name__ == "__main__":
    main()
