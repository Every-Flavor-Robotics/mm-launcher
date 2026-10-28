"""M&M launcher turret v2: named parameters (mm, deg) and the joint tree.

World: X right, Y forward (muzzle), Z up, origin on the table under the pan axis.
Blocks:  STYLE | JAR_* (purchased jar, confirm with calipers) | IF_* (interfaces between subsystems: change
only through the planner) | BASE | PAN STAGE | LAUNCHER (= the launch test rig, v1 attempt-3 geometry; single
source of truth, feed physical results back here) | FEEDER.
Launcher frame (p, q): p = world Y, q = world Z - IF_TILT_Z, at tilt 0. psi = deg from BDC toward the rear.
"""
import math
from cadlib import asm

# =====================================================================================================
# STYLE (one form language, base to pod)
# =====================================================================================================
EB = 1.0                    # edge break on every printed part
CR = 6.0                    # standard corner radius
CH = 4.0                    # the one chamfer (45 deg x 4) on top outer edges: posts, beam, crown, pod
BASE_CORNER_R = 30.0        # base plan corners (the only large radius)
CLR = 0.5                   # minimum running clearance between bodies that move relative to each other

# =====================================================================================================
# JAR: Ball/Kerr regular-mouth pint, hung upside down. NOMINAL: confirm with calipers. Never print glass threads.
# Design rule: nothing may depend on glass tolerance tighter than +/-JAR_TOL.
# =====================================================================================================
JAR_D = 77.0                # body OD
JAR_H = 130.0               # rim to base, including the neck
JAR_THREAD_OD = 70.0
JAR_THREAD_H = 12.0
JAR_MOUTH_ID = 60.0
JAR_GLASS_T = 3.5           # placeholder wall (sets the hollow for the fill mass object)
JAR_BAND_OD = 73.5          # metal screw band (the user's own)
JAR_BAND_H = 13.0
JAR_BAND_LIP_ID = 58.0      # band top-lip opening (faces DOWN when inverted)
JAR_BAND_LIP_T = 0.5
JAR_LID_D = 69.0            # flat lid disc: replaced by the printed adapter
JAR_LID_T = 0.6
JAR_TOL = 1.0
JAR_MASS_GLASS = 350.0      # g
JAR_MASS_FILL = 400.0       # g of M&Ms (about 650 candies)
JAR_MASS_BAND = 15.0

# =====================================================================================================
# CANDY: plain M&M (oblate lentil). ASSUMED range: CONFIRM WITH 20 CALIPERED CANDIES and feed the min/max back here.
# The nip (NIP_PASS, HOOD_GAP_MIN) and the pocket (POCKET_D, the lentil probe) are sized from these.
# =====================================================================================================
MM_D = (12.5, 13.5)         # v2-A2-A1-03 diameter min, max (confirm with 20 calipered candies)
MM_T = (6.3, 7.5)           # v2-A2-01 thickness min, max (confirm with 20 calipered candies)
MM_D_NOM, MM_T_NOM = 13.0, 7.0

# =====================================================================================================
# INTERFACES (IF_*). Each subsystem reads these; only the planner changes them.
# =====================================================================================================
# base <-> pan_stage
IF_PAN_XY = (0.0, 0.0)          # pan axis (= jar axis = feeder disc axis)
IF_DECK_Z = 90.0                # base deck top
IF_DECK_HOLE_R = 20.3           # hub journal hole in the deck (hub R20)
IF_RING_H = 2.0                 # printed thrust ring under the turntable
IF_TT_Z0 = IF_DECK_Z + IF_RING_H        # 92 turntable underside
IF_TT_Z1 = IF_TT_Z0 + 10.0              # 102 turntable top
IF_TT_R = 108.0                 # turntable radius = the yoke drum radius (post outer faces are arcs of it)
IF_HUB_R = 20.0
IF_HUB_BORE_R = 14.0            # hollow pan hub: every cable crossing the pan axis goes through here
IF_GEAR_M, IF_GEAR_N = 1.5, 36  # 1:1 hub gear / pan pinion
IF_PINION_XY = (0.0, IF_GEAR_M * IF_GEAR_N)   # (0, 54): pan servo spline axis
IF_GEAR_Z = (77.5, 85.0)        # base work item: hub gear + pan pinion face (under the deck, 1 mm below its underside).
                                # Pinion phase 5 deg (gap toward the hub), so the hub gear uses phase 0.
PAN_LO, PAN_HI = -90.0, 90.0
# pan_stage <-> launcher (tilt)
IF_TILT_Z = 222.0               # tilt axis height, axis along world X through y = 0
IF_TILT_Y = 0.0
TILT_LO, TILT_HI = 0.0, 45.0    # firmware range
TILT_STOP_LO, TILT_STOP_HI = -3.0, 46.0  # printed hard stops (contact faces declared as fits)
IF_ARM_L_IN = -88.0             # left post inner face (pod must stay inboard with >= 2 mm at every tilt)
IF_ARM_R_IN = 40.0              # right post inner face
IF_JOURNAL_R = 15.0             # pod journals (left: nacelle, hollow for the bundle; right: journal plate)
IF_BORE_R = 15.2                # post bores (open U at the top; beam tongues close them)
IF_JOURNAL_BORE_R = 6.0         # hollow left journal: launcher bundle passes the tilt axis on-axis
IF_TILT_KEY_AF = 12.0           # hex key on the tilt horn adapter, into the journal plate socket
IF_TILT_KEY_HOLE_D = 6.5        # through the key: drive the horn centre screw before fitting
IF_TILT_SPLINE_X = 52.0         # tilt servo spline tip plane (servo body outboard, inside the right post)
# pan_stage <-> launcher, added by the pan_stage work item (attempt 1; planner to confirm). The launcher reads these.
IF_JOURNAL_L_X1 = -95.7         # left journal outer end (post U-bore blind at -96, 1.8 end wall, bundle hole R7 on the axis)
IF_JOURNAL_R_X1 = 51.7          # right journal outer end (post U-bore to 52). The journal plate journal carries a counterbore
                                # R13.3 from IF_TILT_KEY_X[1] - 0.3 to here for the adapter disc, and a 12 AF + 0.3 hex socket
                                # from there back 7.5 mm
IF_TILT_ADAPTER = (13.0, 45.7, 53.7)    # v3-A1 horn adapter: disc R, x0 (45 deg cone from the key, R IF_TILT_KEY_R at x0, to R13),
                                # x1 (+X face = HORN pocket mouth: 2.7 deep, 8 printed O2.0 pins in the horn holes)
IF_TILT_KEY_X = (38.7, 45.7)    # key on the adapter (x span; the prism runs on 1.0 into the cone)
IF_TILT_KEY_R = 6.5             # v3-A1 double-D key: circle R6.5 cut by two flats at y +/- IF_TILT_KEY_AF / 2 (vertical at tilt 0)
# v3-A1 top-open fork in the journal plate (launcher item builds it; pan_stage drops the tilt drive in -Z at tilt 0):
# slot width IF_TILT_FORK_W (y, centred on the tilt axis) from a U bottom of radius IF_TILT_FORK_R about the axis up through
# the journal top, over x IF_TILT_KEY_X[1] - 0.3 - 7.5 .. IF_TILT_KEY_X[1] - 0.3; the R13.3 counterbore beyond it opens to
# the top the same way (slot 2 x 13.3) so the adapter disc drops in with the key.
IF_TILT_FORK_W = 12.3
IF_TILT_FORK_R = 6.8
IF_STOP_R = (19.0, 23.5)        # hard-stop lug radial band about the tilt axis
IF_STOP_JP_A, IF_STOP_JP_HW = -120.0, 8.0   # journal-plate lug centre (deg from +Y toward +Z, tilt 0) and half width:
                                # down-rear, so the post lugs sit clear of the post's R6 front corner
IF_STOP_JP_X = (35.5, 38.6)     # journal-plate lug x span (X_COVER_OUT .. +3.1)
IF_STOP_POST_X = (36.9, 40.0)   # right-post lugs x span (inner face 40, 3.1 proud)
# pan_stage <-> feeder
IF_BEAM_Z0 = IF_TILT_Z + 30.0   # 252 beam underside (pod sweep + 3 mm below it)
IF_BEAM_T = 8.0
IF_BEAM_Z1 = IF_BEAM_Z0 + IF_BEAM_T     # 260 feeder mount face
IF_BEAM_Y = (-30.0, 30.0)
IF_POST_Y = (-26.0, 22.0)         # front face 22: flywheel slides off +X at tilt 45 with 5 mm to spare (scaffold run: 0.94 at 26)
IF_DROP_XY = (21.0, 0.0)        # drop axis: feeder outlet, beam hole, over the tilt axis in the wheel plane
IF_OUTLET_D = 16.0
IF_BEAM_HOLE_D = 30.0           # beam clearance hole around the feeder spout
IF_SPOUT_OD = 22.0              # feeder floor spout reaches down through the beam
IF_SPOUT_Z0 = IF_TILT_Z + 23.0  # 245: spout tip, 3 mm above the pod's drum at every tilt
IF_FEED_BOLTS = []   # v3-A1: FST_feedmount deleted (crown hooks in IF_CROWN_HOOKS slots). v2: [(-36, -21), (-36, 21), (34, -20), (34, 20)]   # M3 csk, housing to beam (finish: x40 sat on post_R's inner face, driver blocked).
                                # v2-A1-05: the -X pair moved y 18 -> 21, so the pilot sits 28.66 from the feeder pinion axis
                                # (-55.5, 0) and keeps a 3.1 wall to the R24.35 pinion chamber (A1: 1.08)
IF_FEED_BUS_XY = (-98.0, -16.0) # feeder bus passes down through the beam into the left post channel
IF_POST_L_CHANNEL = (-104.0, -92.0, -22.0, -12.0)   # x0 x1 y0 y1 vertical cable channel (launcher bundle + feeder bus)
IF_POST_R_CHANNEL = (90.0, 100.0, -22.0, -12.0)     # tilt servo bus
# feeder <-> jar
IF_JAR_XY = IF_PAN_XY
IF_SOCKET_ID = 68.6             # bayonet socket in the feeder housing (valve body OD 68)
# v3-A1 (feeder item): JAR_LIFT raises the whole jar stack (socket, lugs, gate, valve top, band, glass) 36 mm so the crown's
# socket rim and its closed servo-lobe roof are ONE top plane (z 322): the crown prints top-down with all of it on the bed.
# v2's lobe cover rose 36 mm above the 286 crown top, so a merged crown with the 286 rim could not print (the rim would
# hang 36 mm over the bed). Nothing under the socket floor moves (beam, disc, pinion, servo, baffle, drop/index/payload).
JAR_LIFT = 36.0
IF_SOCKET_Z = (274.0 + JAR_LIFT, 286.0 + JAR_LIFT)    # socket floor .. crown top 322 (12 mm engagement)
IF_BAYO_N = 3
IF_BAYO_LUG_R = 37.0            # lug tips (valve body R34)
IF_BAYO_LUG_Z = (275.0 + JAR_LIFT, 282.5 + JAR_LIFT)  # v3-A1: 50 deg lug underside (BAYO_LUG_SLOPE) from the body at 311 to
                                # the R37 tip at 317.55, flat top 318.5 (v2: flat 5.5 mm cantilevers at 275, printcheck fail)
BAYO_LUG_SLOPE = 50.0           # lug underside / L-slot leg floor cone, deg from horizontal (prints both ways up)
IF_BAYO_TWIST = 30.0            # PIV_jar 0 = locked, 30 = free to lift
IF_GATE_Z = (288.0 + JAR_LIFT, 290.4 + JAR_LIFT)      # gate slot plane (above the crown top: the blade never passes a wall)
IF_VALVE_Z1 = 300.0 + JAR_LIFT  # valve cheek tops = the adapter shoulder's bearing face (0.5 under the band lip)
IF_BAND_Z0 = IF_VALVE_Z1 + 0.5  # band lip outer face
IF_GLASS_RIM_Z = IF_BAND_Z0 + JAR_BAND_LIP_T + 1.6   # 302.6 (adapter flange 1.6)

# =====================================================================================================
# BASE (v1 layout carried forward: low battery, vertical USB-C to a rear niche, buck by the louvres)
# =====================================================================================================
BASE_HALF = 120.0
WALL = 3.0
FLOOR_T = 3.0
DECK_T = 4.0
BATT = (10.0, 125.0, -115.0, -39.0, 4.6, 74.6)   # x0 x1 y0 y1 z0 z1 (115 x 76 x 70), slides out +X
ADAPTER = (24.0, 110.6, -106.5, -47.5, 62.6, 86.0)
BAY_CLR = 2.0
BAY_WINDOW_Z1 = BATT[5] + 2.0   # +X window = pack outline + 2 (A3-A3)
BAY_SCALLOP_D = 30.0            # finger scallops top and bottom of the bay opening (A3-M2)
BUCK_C = (-76.0, -19.0)
CTRL = (73.0, 115.0, 20.0, 78.0)
CTRL_BOSS_H = 5.0
# v2-A1-11: the controller's bottom (long) edge faces the +X wall (REF photo: slide switch centre-left, blue 2-pole
# terminal bottom-right -> world y 40.6..58.7 and 59.6..72.5). Two port-only windows in one printed bezel replace the A1
# 52 x 24 notch; both sit above z 15 so the wall stays closed over the PCB at the v2-A1-11 ray rows (y 32/50/68, z 14).
CTRL_SW = (40.6, 58.7, 8.0, 5.0, 4.5, 4.0)  # switch y0 y1, body depth from the PCB edge, body h, lever w (travel +/-2.75), lever h
CTRL_TB = (59.6, 72.5, 8.5, 10.0)         # terminal y0 y1, depth from the PCB edge, h
CTRL_WIN_SW = (42.0, 57.0)                # switch window y (lever 45.4..49.9 at OFF, travel +5.5, + margin); 3 web
CTRL_WIN_TB = (60.0, 73.5)                # terminal window y
CTRL_WIN_Z = (15.5, 22.0)                 # both windows; 1.5 above the z 14 ray rows
CTRL_BEZEL = (2.5, 1.2)                   # bezel frame width round the windows, proud of the wall (45 deg sides)
MG_WALL_Y = -87.0
MG_STANDOFF = 12.5
USB_STEP = (57.6, -14.0, 7.97)
NICHE_DEPTH = 30.0
# base work item (attempt 1)
ADAPTER_HOLE_INSET = 6.0        # adapter corner holes from its edges. ESTIMATED: confirm with calipers
BATT_STEM_INSET = (10.5, 10.0)  # battery rail stem (top 12 mm, inside the adapter) inset from the adapter outline, x / y.
                                # ESTIMATED. The corner holes must sit outside the rail channel; if they don't, use M3 x 12.
MG_X0, MG_Z0 = -10.0, 16.5      # MotorGo STEP-origin hole, world x / z (v1 -30: moved +20 so the USB niche sits on the
                                # straight rear wall, clear of the R30 corner)
MG_PCB_T = 1.77
# v3-A1: the MotorGo has no screws (card guides, MG_GUIDE); its STL holes measure Ø2.5 (v2 launch-rig finding), opened
# to MG_HOLE_D in the placeholder only
MG_HOLE_D = 2.7
MG_PART_X = (-80.0, 0.0)        # rear partition wall, now integral to PRT_base_floor (v3-A1)
NICHE_W = 30.0                  # USB niche slot width; V floor at NICHE_V_SLOPE (print: deck down, V points up)
NICHE_V_SLOPE = 1.2
NICHE_TOP_Z = 48.5              # rear-wall opening top
BUCK_HOLE_Y = 33.4              # components.json flange holes (on the fin-free flange strips)
BUCK_BOSS_H = 5.0               # buck flange underside above the floor (v3-A1: the hook-rail tops)
BUCK_FLANGE_T = 3.0
CTRL_BOSS_D = 7.0
UART_CLIPS = [(-20.0, 5.0), (40.0, 5.0)]
PAN_SERVO_TOP_Z = 72.0          # pan servo case top = mount plate underside
PAN_PLATE_T = 4.0
PAN_PLATE = (-42.0, 42.0, 30.0, 96.0)
PAN_POSTS = [(-34.0, 38.0), (34.0, 38.0), (-34.0, 88.0), (34.0, 88.0)]
PAN_PLATE_HOLE_R = 13.5
PINION_HUB_R = 12.0
HORN_LIFT = 1.0                 # horn hub underside above the servo case
HORN_RECESS = 1.0
# ---- v3 attempt 1 (min-hardware): printed joints in the base (DESIGN_LOG "Attempt 1: plan" joint table)
PAN_HORN_POCKET = 2.7           # HORN: pan pinion pocket depth (disc 2.5 + 0.2), pocket d = disc + 0.2
PAN_HORN_PIN = (1.0, 2.4)       # 8 printed pins in the horn's O2.2 holes: radius, length (from the pocket floor)
PAN_POST_PIN = (2.0, 3.5)       # deck-post end pins into the mount plate: radius, length (post shoulder = the seat)
PAN_POST_RIB = (0.4, 0.15)      # 3 crush ribs per plate hole: rib radius, interference on the pin
PAN_COLUMN_GAP = 0.3            # floor servo column top under the pan servo's idler boss
ADAPTER_SCREWS = (0, 3)         # diagonal corners kept (Geo.adapter_holes index): FST_adapter_0, _1
ADAPTER_SCREW_L3 = 10.0         # M3 pan x 10 (spec shared with FST_motor), counterbored flush in the deck
ADAPTER_CBORE = 2.4             # counterbore depth = pan head 2.4 (flush); 1.6 of deck under the head
ADAPTER_FENCE = (2.0, 0.4, 74.6, 76.0)   # fence thickness, clearance, bottom z (3 sides), bottom z of the +X fence (battery stem exit)
# floor latches (SNAP-IP, beam in the floor plane). +Y: square barb, finger release. -Y: 45/45 detent, pops on a pull.
FLOOR_LATCH = [(-65.0, -30.0), (60.0, 25.0)]   # +Y arms: root x, tip x (L 35)
FLOOR_LATCH_WD = (2.5, 1.5, 2.0)              # arm width (in plane), barb engagement, release deflection
FLOOR_DETENT = [(-10.0, -40.0), (-50.0, -80.0)]  # -Y arms: root x, tip x (L 30)
FLOOR_DETENT_WD = (3.0, 0.8, 1.2)
FLOOR_ARM_Y = 113.25            # arm centreline |y| (wall inner face 117)
FLOOR_BARB_Z = 7.0              # barb underside z (keeper top 0.1 below)
MG_GUIDE = (0.3, 2.0, 13.0, 0.5)  # MotorGo card guides: slot clearance (on 1.77), edge engagement (+Y header face), floor stop z
                                # (board bottom), engagement on the -Y component face (parts sit 0.7 / 1.2 from the edges)
MG_RIB_X = [(-62.0, -56.0), (-15.0, -9.0)]   # deck ribs over the MotorGo top edge (0.5 over it), clear of CAB_launcher_base (x -47..-19)
BUCK_RAIL = (0.3, 3.4, 0.2)     # buck hook rails: side clearance, lip overlap on the flange strip, lip gap over the flange
BUCK_STOP_Y = [-47.0, 9.0]      # shell -X wall ribs 0.3 off the buck's -X end, between the louvres
CTRL_TONGUE_X = (62.0, 94.0)    # servo controller hold-downs (SNAP-IP in the floor): arm root x, tip x (L 32); head + lip x 94..100
CTRL_TONGUE_Y = [14.25, 83.75]  # arm centrelines, beside the PCB's two short edges (y 20 / 78), clear of the corner fences
CTRL_TONGUE_WD = (2.5, 1.0, 1.2)  # arm width, lip overlap on the PCB edge strip, release deflection

# =====================================================================================================
# PAN STAGE (turntable, posts = slices of the R108 drum, beam, tilt servo)
# =====================================================================================================
POST_T_MIN = 14.0               # left post minimum wall at y = +/-26 (arc to IF_ARM_L_IN)
GEAR_BACKLASH = 0.15
SERVO_POCKET_CLR = 0.3
RING_R = (20.05, 44.0)          # thrust ring (rides with the turntable; slides on the deck). v3-A1: ID R20.05 = the turntable
                                # socket, so the hub fingers' barbs (r 20.5) deflect 0.45 through both
TT_GROOVE = (-100.5, 100.0, -22.0, -12.0, 93.6)   # v3-A1: closed tunnels inside the turntable: x0 x1 y0 y1 floor z
TT_TUNNEL_Z1 = 100.3            # tunnel ceiling (roof 100.3..102 printed as a 10 mm bridge, turntable bottom-down)
TT_TUNNEL_BEND_R = 15.0         # cable centreline bend radius, post channel (vertical) -> tunnel (horizontal)
TT_TUNNEL_ZC = 96.9             # tunnel cable centreline z (bundle R3: 0.3 to the floor and to the roof)
TT_HUB_POCKET = (-10.0, 10.0, -22.0, -6.0)        # tunnels -> hub bore, x0 x1 y0 y1
TT_HUB_X, TT_HUB_Z1 = 13.0, 100.3                   # |x| < 13: tunnel + pocket ceiling (0.3 over the bore roof at 100.0,
                                                    # so the roof bridge (24.6) and the pocket bridge are separate layers)
# v3-A1 hub tube on PRT_hub_gear (FST_hub x3 deleted): R20 tube journals in the R20.3 deck hole, R14 bore, gear top 85 to
# HUB_TUBE_Z1; the turntable socket (R HUB_SOCKET_R, z 92..HUB_SOCKET_Z1) takes it. 3 torque dogs on the tube top in
# turntable pockets; 3 SNAP-V fingers in the tube wall (outer skin t 1.2, L 15 from the gear top) click their barbs over a
# ledge in the socket (beam across layers: 3 E t d / 2 L^2 = 3 x 3500 x 1.2 x 0.45 / (2 x 225) = 12.6 MPa < 15).
HUB_TUBE_R = (14.0, 20.0)
HUB_TUBE_Z1 = 97.0              # tube: R20 to z 92, then a 45 deg chamfer to R15 at z 97 (flat top r 14..15)
HUB_CONE = (20.3, 92.0)         # turntable hub cavity: 45 deg cone, radius 20.3 at z 92 (the bed) closing to R12 at the
                                # roof (z 100.3): no flat socket ceiling to cantilever (the tube chamfer sits 0.3 under it)
HUB_SOCKET_R = 20.05            # finger slots in the cone wall: the barbs ride r 20.05 up to the ledge
HUB_DOG = {"w": 5.0, "top": 99.5, "clr": 0.15, "az": [335.0, 70.0, 160.0]}   # tangential width, top z (pocket 0.2 over)
HUB_FINGER = {"t": 1.2, "w": 5.0, "L": 15.0, "barb": 0.45, "gap": 1.2, "slot": 0.7, "az": [25.0, 115.0, 200.0],
              "catch_z": 98.55, "ledge_z": 98.5, "tip_z": 100.0}
HUB_ROOF_Z = 100.0              # flat bore roof z 100.0..102 over r < 12.3 (24.6 bridge; the hub pocket ceiling is 0.3 higher)
HUB_GEAR_BORE_R = 13.0          # hub gear bore
POST_L_BORE_X0 = -96.0          # left U-bore blind end; end wall to POST_L_WALL_X
POST_L_WALL_X = -97.8
POST_L_CAVITY = (-104.0, POST_L_WALL_X, -22.0, 7.0, 211.0, 233.0)   # bundle turns from the journal axis into the channel
POST_R_BORE_X1 = 52.0           # right U-bore end (journal + adapter disc); servo cavity beyond
POST_R_TEAR_R = 13.5            # teardrop passage for the adapter disc (R13 + 0.5, faceted)
POST_R_CHANNEL_Z1 = 184.0       # right channel top (the bus enters from the servo pocket through a notch)
POST_R_COVER_X = 96.2           # v3-A1: servo pocket +X wall (servo back face + SERVO_POCKET_CLR); the cover is merged away
POST_R_IDLER_R = 3.5            # idler boss slot (R3 boss + 0.5), open to the post top
TILT_TONGUE_Z0 = 232.5          # beam tongue underside over the tilt servo (servo top 232.07: 0.43, <= 1.0)
# v3-A1 beam hooks (SNAP-V, 2 per post, L 20, t 1.4 in x, barb 0.5 toward the post inner face; 3 E t d / 2 L^2 = 9.2 MPa at
# the 0.5 engage, 12.9 at the 0.7 release) into slots in the post tops; a flat screwdriver through a slot in the post's
# inner face pushes the barb outboard. (x of the hook's barb-side face, y centre)
BEAM_HOOK = {"t": 1.4, "w": 2.2,   # A2 hotfix (v3-A1-01): 3.0 -> 2.2, 0.3 a side in the 2.8 release slot
              "L": 20.0, "barb": 0.5, "release": 0.7, "slot_hw": 1.4, "post_slot_w": 3.0,   # slot_hw: screwdriver slot half width; post_slot_w: post-top hook slot = this + 0.3 a side (A1 value, kept so the turntable needs no reprint)
             "pos": [(-91.0, 18.0, 1), (-91.0, -21.0, 1), (43.0, 18.0, -1), (43.0, -21.0, -1)]}     # (x barb face, y, s): s = +1 barb toward +X (left post), -1 toward -X
IF_CROWN_HOOKS = [(36.5, 0.0), (-36.0, -22.0), (-36.0, 22.0)]   # v3-A1 crown hook slot centres through the beam (feeder item:
                                # hooks L 16, t 1.0, barb 0.5 radial outward, catching the pocket roof at z 254)
IF_CROWN_HOOK_SLOT = (6.4, 2.6, 2.0, 4.0)   # tangential width, radial depth, under-pocket height (z 252..254), pocket radial depth
BUS_R, BUNDLE_R = 1.4, 3.0      # cable radii: servo bus, launcher bundle (3 phase + encoder JST)

# =====================================================================================================
# LAUNCHER = LAUNCH TEST RIG (v1 attempt-3 values unless marked v2). x is world X.
# =====================================================================================================
W_P, W_Q = 37.0, -52.0          # wheel centre from the tilt axis (launcher frame)
X_MF = 0.0                      # motor front face plane
NAC_PLATE_T = 4.0
BODY_WALL = 4.0
X_BODY_OUT = X_MF + NAC_PLATE_T # 4
X_BODY_IN = X_BODY_OUT + BODY_WALL   # 8
X_COVER_IN = 31.5
COVER_T = 4.0
X_COVER_OUT = X_COVER_IN + COVER_T   # 35.5
WHEEL_R = 35.0                  # tape land radius before tape
WHEEL_FLANGE_R = 36.0
WHEEL_X0, WHEEL_X1 = 12.5, 29.5 # 14 land + 2 x 1.5 flanges
WHEEL_XW = 0.5 * (WHEEL_X0 + WHEEL_X1)   # 21 = IF_DROP_XY[0]
TAPE_T = 0.5
HUB_X0 = 9.6                    # launcher work item: v1 9.0 sat 1.0 off the wall (x 8); 1.5 wanted (A1-#11)
WEB_X1 = WHEEL_X0 + 1.6         # web on the motor side; cup opens to +X for the L-key
FW_HUB_R = 13.5
FW_HUB_X1 = 25.0
FW_RIM_T = 3.5
FW_BOLT_X = 19.5                # pinch-bolt plane
FW_BOLT_OFF = 6.5
FW_BOLT_L = 20.0                # M3 x 20 through the nut (A2-3)
SHAFT_LEN = 21.0
DRUM_R = 20.0                   # feed drum about the tilt axis
FAN_A0, FAN_A1 = -27.0, 75.0
COL_MARGIN = 1.0
WC_R = 38.5
FIN_R0, FIN_R1 = 37.6, 39.2    # launcher work item: +0.1 so the faceted fin keeps 1.5 to the R36 flange (v1 37.5, 39.1)
LIP_PSI = 100.0
GUARD_WALL = 3.0
HOOD_GAP = 6.5                  # bare gap at BDC as modelled: 6.0 over tape = 1 mm squeeze on a 7 mm M&M
HOOD_GAP_MIN = 6.2              # v2-A2-01: printed min-gap stop (PRT_nip_stop), A2 5.3. Sized so the full leaf lift at the
                                # min-gap setting still passes the thickest candy (NIP_PASS, asserted below). HOOD_GAP_MAX
                                # is derived below from HOOD_LO
HOOD_T = 6.0
PSI_C, PSI_TOP, BP_PSI0 = 45.0, 112.0, -3.0
                                # v2-A4-A2-01 (review A4, A2-01): PSI_C 78 -> 45, so the entry taper starts at the stud line
                                # (JACK_PSI 45). With PSI_C 78 the hood swung about HINGE on the full leaf lift and the
                                # constant-gap band beyond the jack line closed toward the wheel: the entry arc at the min
                                # stop read 7.50 at psi 80 (< NIP_PASS 8.0) while BDC read 8.18. HOOD_GAP_LIFT now takes the
                                # minimum over the whole arc (gap_arc). Rest gap over psi 0..45 is unchanged (6.18..7.00).
                                # Rig feedback: the test rig's backplate takes the same params, so it must use PSI_C 45 too
                                # (BOM rig-feedback note). Fallback if an entry-arc ray reads < 8.05: PSI_C 40 (analytic 8.202)
                                # v2-A4 launcher step: PSI_C 45 (quadratic) passed the arc but stalled 14 drop rows: the 7.0
                                # candy reached the tape only at psi 63-66, a 15-27 deg slide at tilt 45. gap_at is now the
                                # lift-matched profile (GAP_PROFILE "lift", below); PSI_C only feeds gap_quad. The rig's
                                # backplate takes the same gap_at table (BOM rig-feedback note)
G_IN = 13.0                     # v2: was 21 (A3-F1: funnel flattened the slide to 20 deg at tilt 46)
HINGE_OFF, HINGE_BOSS_R = 2.0, 4.3
HINGE_AXLE_L = 35.0             # v2: M3 x 35 into a nut trap on the journal-plate side (A3-F2); unused since v3-A1
HINGE_PIN_R, PIN_CLR = 2.5, 0.15   # v3-A1 hood hinge: O5 stubs (body -X stub into the hood, hood +X stub into the journal
                                # plate), bores 0.15 radial (running fit). Replaces FST_hinge M3 x 35 + FST_hinge_nut
HINGE_STUB_L = (5.0, 2.0)       # engagement: body stub in the hood bore, hood stub in the journal plate bore (plate 4 thick)
JP_PEG = (2.5, 2.1, 0.1)        # v3-A1 journal plate pegs (replace FST_jp x3): radius, length past the body's +X face,
                                # crush-rib interference (3 ribs per hole, bore 0.15 radial)
JACK_PSI = 45.0                 # nip stud line
NIP_SET = (HOOD_GAP_MIN, 7.0)   # v2-A2-01: thumbwheel range, bare gap at BDC: 6.2 = printed stop, 7.0 = stud sleeve (static max).
                                # The 12.0 of attempt 1 let the hood swing into the body (A1-01)
STUD_L = 16.0                   # v2-A1-01 (launcher step): M3 x 16 (A1 x 20). Static range 6.2..7.0 (A2-01; A2 5.3..7.0). At
                                # 7.0 the tip sits u 7.1 and 8.6 at full leaf lift (gap 8.35), under the leaf slot and 2.4 below
                                # the cover roof; launcher_geom.report() prints the tip u at every setting. v2-A3-A2-01: full
                                # lift 2.2 (gap 8.99 at the 7.0 setting) with the roof 0.5 higher, tip predicted about 2.2 under it
TW_R, TW_T = 8.5, 5.0           # thumbwheel
LEAF_T, LEAF_PRE, LEAF_TRAVEL = 2.3, 1.2, 2.2   # v2: separate flat-printed leaf (A3-M1). v2-A3-A2-01: travel 1.5 -> 2.2 and
                                # T 2.5 -> 2.3 (pre 1.2 kept), so the full lift at the min-gap stop passes MM_T max over the
                                # tape (NIP_PASS 8.0). SHELL_U0 (cover roof) rises a net 0.5; leaf 35.5 MPa solid (leaf_numbers)
LEAF_L, LEAF_W = 34.0, 21.9
LEAF_ROOT_R = 2.0
MUZZLE_FRONT = W_P + 62.0
MUZZLE_ROOF = W_Q - WHEEL_R + 5.0
MUZZLE_FLARE = 4.0
MOTOR_D, MOTOR_L = 35.9, 74.0
REAR_ACCESS_D = 8.0
REAR_SHAFT_RECESS = 0.5
JIG_SPIGOT_D, JIG_SPIGOT_L = 7.9, 1.0   # v2-A1-07: 7.9 in the motor's 8.0 rear access hole (stack term tol 0.05; A1 7.8)
MAGNET_D, MAGNET_T = 6.0, 2.5
ENC_GAP = 1.0
ECAP_T = 4.0                    # v3-A1 encoder cap flange thickness; it sits in a nacelle rear counterbore this deep (the
                                # nacelle grew ECAP_T rearward, so the flange seat on the counterbore floor keeps ENC_GAP)
ECAP_R, ECAP_CLR = 22.8, 0.2    # flange radius about the wheel axis, radial clearance in the counterbore (lobe keys it)
ECAP_ARM = (18.0, 1.5, 0.6)     # v3-A1 SNAP-IP arms (replace FST_enc x2): arc length, radial width, barb engagement =
                                # release deflection -> 1.5 E w d / L^2 = 14.6 MPa (E 3500)
ECAP_GROOVE = (0.8, 2.6)        # groove in the counterbore wall: radial depth past the counterbore, axial width
PLINK_IC_TOP = 3.25
PLINK_PEG_D, PLINK_HOLE_D = 2.4, 2.5   # v2-A1-07: encoder cap pegs locate the Plink PCB by its 2.5 holes (stack term tol 0.05)
NAC_RW, NAC_RT = 26.5, 17.0
BORE_CLR = 0.2
STALL_DEG = 28.0                # drop-test stall angle (A3-F1: reviewer asks 28 with a pass at tilt 46)
# launcher work item (attempt 1): v1 attempt-3 layout values that were local to ../blender/build_assembly.py
POD_X = (-86.0, 37.5)           # pod envelope in x at every tilt (journals, journal-plate stop lug excepted)
NAC_COLLAR_R = 17.0             # left journal collar, nacelle back face .. POD_X[0]
CH_X0 = WHEEL_XW - 8.0          # chute / fan left wall (x 13 .. X_COVER_IN)
ROOF_P0 = W_P + 30.0            # muzzle roof step
TONGUE_T = 1.6                  # chute rear-wall tongue, shingled inside the backplate top end
TONGUE_DPSI = (-6.0, 4.0)       # tongue span about PSI_TOP
REAR_WALL_ANG = 81.0            # chute rear wall, launcher frame (35 deg in world at tilt 46)
JP_R = 23.8                     # journal plate / cover parting arc about the tilt axis (v1 24.5: the flywheel slid off
                                # +X at tilt 45 with 1.32 to the plate's lap step)
NIP_X = 19.5                    # nip stud plane (1.5 off the wheel plane)
SEAT_H = 3.2                    # thumbwheel seat land proud of the guard at the stud (v1 2.2; +1 for the 5.5..12 range)
STUD_HOLE_R = 4.4               # stud slot in the guard (the stud head passes in from outside). v2-A1-01: 3.6 -> 4.4 so the
                                # R3.8 stop sleeve keeps >= 0.5 to the guard over the hood range
SLEEVE_R = (1.7, 3.6)           # v3-A1: the max-gap spigot (integral on PRT_nip_wheel, was PRT_nip_stop_sleeve R3.8) bore / OD
                                # radius; R3.6 keeps 0.6 radial to the hood's R4.2 spot face (fits hood x nip_wheel min 0.5) and
                                # still covers the AF 5.5 head (corner R3.18). v2 note: OD past the thumbwheel's AF 5.7 nut trap
                                # (corner R3.29), so the thumbwheel underside bottoms on the sleeve, not on the nut
NIP_STOP_T = 7.0                # v2-A1-01 PRT_nip_stop: thickness along the hood end-face normal (holds the M3 pilot)
NIP_STOP_W = 20.0               # width along x (the 20 of the "3 x 20 land")
NIP_STOP_H = 6.5                # height along the hood end face, from the muzzle floor down
NIP_STOP_SCREW_L = 6.0          # FST_nipstop: M3 x 6 from the pod's outer skin up into the pad (4.3 in the pad, tip 2.2 below
                                # the muzzle floor)
HOOD_LUG = (6.0, 2.5)           # v2-A1-01 stop lug on the hood's free (front) end: psi span, radial height past the back
                                # face. The end face then reaches 3.4 below the muzzle floor = the 3 mm tall contact land
HOOD_FLANGE_RELIEF = (4.1, 3.23, 1.5)  # v2-A1-01 hood relief over the flywheel's R36 flange tracks: clearance radius about the
                                # flange corner, face height over the flange top at hood +2.315 (cad q, psi 20), depth over the
                                # flange: hood to wheel >= 4.0 one degree past the min-gap stop (launcher.relief_cuts)
BAY_OVER = 1.1                  # v2-A1-01 the bay (and the chute tongue's swing envelope) runs 1.1 deg past the min-gap stop,
                                # so the stop is PRT_nip_stop, never the guard (rows at hood +2.315 keep 0.5 to the body)
FINGER_SLOT = (22.0, 8.3)       # v2-A1-02 finger slot through the nip cover's -v end wall (x length, u height): the review's
                                # 22 x 7 plus 0.5, because at full leaf lift the rim's -v edge rises 1.72 (66 mm from the hinge).
                                # v2-A3-A2-01: 7.5 -> 8.3; the 2.19 deg lift raises that edge about 2.5, rim keeps >= 1.0 to the cover
NIP_COVER_V0 = -(8.5 - 2.0)     # v2-A1-02 nip cover -v end wall outer face: the R8.5 thumbwheel rim stands 2.0 proud through
                                # the slot (the land stays at LAND_V[0] = -12 as a finger shelf)
FINGER_SLOT_LIFT = 0.3          # v2-A2 launcher step: the slot top opens 0.3 over the thumbwheel rim (x NIP_X +- TW_R) so the
                                # rim keeps >= 1.0 to the cover at full leaf lift (A2: 0.83)
FINGER_SCALLOP = (3.0, -15.6, 8.5, 20.0, 1.0)   # v2-A2-03 finger scallop in the guard shelf: (nip u, v) of the R8 fingertip
                                # centre (O0 = nip (4.0, -22.0) + u(-1) + d(6.4)), cutter radius 8.5, full-depth length along x,
                                # 45 deg edge break (adds 1.0 at each end: 22 at the surface)
NIPCOVER_PILOT_OVER = 0.5       # FST_nipcover_* pilot in the body ends 0.5 past the screw tip (default 1.0 left a 1.12 wall
                                # over the hood bay at u -5.2)
STUD_POCKET_D = 2.2             # head pocket in the backplate back face. v2-A4 (A3-02): FST_nip_stud is M3_hex (ISO 4017,
                                # AF 5.5 x 2.0), so 3.2 (cap head 3.0) -> head 2.0 + 0.2; the AF 5.7 hex keeps 0.1 a side
STUD_SPOT_D = 0.6               # spot face (R4.2, square to the stud) this far below the head's bearing face: the +v flats
                                # key the hex over 2.2 - 0.6 = 1.6 (A4 cap pocket: 1.6 at spot 1.6, pocket 3.2)
TW_NUT_U = (0.8, 3.2)           # captive nut inside the thumbwheel (u from the seat)
LAND_U0 = -10.0                 # flat land on the guard: u -10..0 (local nip frame)
LAND_V = (-12.0, 49.5)          # v2: +3.5 so the cover screws sit past the leaf root block
NIP_SHELL_T, NIP_END_T, NIP_SLIT = 2.0, 2.0, 0.8
NIP_V_TIP = -2.6                # leaf tip (past the pads). v2-A1-02: -8 -> -3.5, inside the cover's new -v end wall; launcher
                                # step: -2.6 (0.6 past the pads) so the cover's slot-end corner keeps a 1.7 wall outside the tip's path
LEAF_PAD_H = 2.0                # contact pads under the leaf (free state: LEAF_PRE into the thumbwheel)
LEAF_TIP_CH = 0.5               # 45 deg chamfer on the leaf tip's outer (+u, bed) edge: at full lift the tip lies on the cover
                                # roof, and the cover's 45 deg slot-end corner keeps 0.3 to it and 1.7 of wall (v2-A2 launcher step)
LEAF_BLOCK_H, LEAF_BLOCK_L = 5.55, 6.0   # root block under the strip, length along v. v3-A1 (FST_leaf x2 deleted): the block
                                # reaches down to 0.25 over the land, so with the nip cover on it is captive: roof above, land
                                # below, cover end walls 0.8 at the x ends, cavity end +v, the stud in its fork -v (A3: 3.6)
CV_TABS = (("top", 4.0, 2.5, 2.5), ("diag", 22.5, 2.5, 2.5))   # v3-A1 wheel-side cover hook tabs (FST_cover x4 deleted):
                                # (line, position along it from the arc end, half width, depth); clear of the pegs and hinge bore.
                                # Top / diagonal parting line (launcher_geom JP lines); 1.2 thick,
                                # under the journal plate's edge (pocket 0.3 clear); they pull out as the cover slides +Y at tilt 45
CV_LATCH = (7.0, 22.0, 1.5, 0.8)   # SNAP-IP latch: position on the diagonal, L along the slide, w across, hook engagement
                                # -> 1.5 E w d / L^2 = 13.0 MPa
NIP_DOVE = (1.5, 0.15)          # v3-A1 nip cover dovetail (FST_nipcover x2 deleted): 45 deg tongue depth under each end wall
                                # into a land rebate, clearance per face. The cover slides off +V (toward the hinge)
NIP_DETENT = (16.0, 1.5, 0.45, 8.0, 44.0)   # SNAP-IP detent arm: L along x, w along u, bump height, root x, v0 (to the
                                # cover's +v face): 1.5 E w d / L^2 = 13.8 MPa
LEAF_SCREW_V = LEAF_L + 3.0     # FST_leaf_*: through the cover into the root block
NIPCOVER_SCREW_V = 44.0         # FST_nipcover_*: through the cover into the land
NIP_SCREW_X = (10.0, 26.0)
STUD_WINDOW_R = 4.0             # stud tip shows through the cover shell (gap indicator)
JIG_PLUG_R = 17.8               # magnet jig plug relieved in the bore: the Ø7.8 spigot is the only datum


def pw(r, psi):
    """launcher (p, q) at radius r about the wheel centre, psi deg from BDC toward the rear"""
    a = math.radians(psi)
    return (W_P - r * math.sin(a), W_Q - r * math.cos(a))


def rot2(p, ang, c=(0.0, 0.0)):
    x, y = p[0] - c[0], p[1] - c[1]
    ca, sa = math.cos(ang), math.sin(ang)
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def gap_quad(psi):
    """A1-A4 profile: concentric to PSI_C, then a quadratic taper to G_IN at PSI_TOP"""
    if psi <= PSI_C:
        return HOOD_GAP
    s = min(1.0, (psi - PSI_C) / (PSI_TOP - PSI_C))
    return HOOD_GAP + (G_IN - HOOD_GAP) * s * s


# v2-A4 launcher step (A2-01 + drops). The hood rotates about HINGE (psi 112) for both the thumbwheel setting and the leaf
# lift, so at every psi the static-max rest gap is the min-stop full-lift gap minus the opening of a fixed 1.305 deg turn
# (0.64 at psi 82). With the full-lift arc held at >= 8.1, the static-max rest gap therefore cannot drop below 7.46 at psi
# 82, and a 7.0 candy meets the tape (bare 7.5) only from psi ~83 down. The profile is the tightest one that the arc
# allows: from psi ~50 to ~94 it is the gap whose point, turned to the min stop with the leaf solid, sits LIFT_FLOOR off the
# land; above that a funnel with taper angle psi - FUNNEL_PSI0 reaches G_IN at PSI_TOP, so the slide never gets flatter
# than about 34 deg at tilt 46 (drop rows: flattest 34.5). Rest gap at psi 0..47 is the A4 6.18..7.05.
GAP_PROFILE = "lift"            # "quad" = gap_quad (PSI_C); "lift" = lift-matched (below)
LIFT_FLOOR = 8.105              # full-lift gap at the min stop along the entry arc (assert >= NIP_PASS + 0.1 = 8.1)
FUNNEL_PSI0 = 82.0              # funnel taper angle <= psi - 82: hood slide >= 34 deg at tilt 46 (80 gave 32.5, 1 deg facets)
_GAP_TAB = []


def _gap_table():
    """home-pose gap profile, 0.25 deg table from BP_PSI0 - 10 to PSI_TOP: max(HOOD_GAP, floor, funnel).
    floor(psi) = the gap whose point, rotated about HINGE to the min stop with the leaf solid, sits LIFT_FLOOR off the land;
    funnel = G_IN at PSI_TOP integrated down with taper angle psi - FUNNEL_PSI0"""
    if _GAP_TAB:
        return _GAP_TAB
    e = solve_eps(HOOD_GAP_MIN) - LEAF_TRAVEL / jack_r()
    def lifted(ps, gg):
        p = rot2(pw(WHEEL_R + gg, ps), e, HINGE)
        return math.hypot(p[0] - W_P, p[1] - W_Q) - WHEEL_R
    n = int(round((PSI_TOP - BP_PSI0 + 10.0) / 0.25))
    psis = [BP_PSI0 - 10.0 + 0.25 * i for i in range(n + 1)]
    fun = [0.0] * len(psis)
    fun[-1] = G_IN
    for i in range(len(psis) - 1, 0, -1):
        a = max(0.0, psis[i] - 0.125 - FUNNEL_PSI0)
        fun[i - 1] = fun[i] - (WHEEL_R + fun[i]) * math.tan(math.radians(a)) * math.radians(0.25)
    flo = []
    for ps in psis:
        lo, hi = 4.0, 16.0
        for _ in range(50):
            m = 0.5 * (lo + hi)
            if lifted(ps, m) < LIFT_FLOOR:
                lo = m
            else:
                hi = m
        flo.append(hi)
    met = False                     # the funnel runs down only to where it meets the floor (below that it would plateau
    for i in range(len(psis) - 1, -1, -1):          # above HOOD_GAP and lift BDC off the NIP_SET settings)
        met = met or flo[i] >= fun[i]
        _GAP_TAB.insert(0, (psis[i], max(HOOD_GAP, flo[i], 0.0 if met else fun[i])))
    return _GAP_TAB


def gap_at(psi):
    if GAP_PROFILE == "quad":
        return gap_quad(psi)
    if psi >= PSI_TOP:
        return G_IN
    t = _gap_table()
    if psi <= t[0][0]:
        return HOOD_GAP
    k = min(len(t) - 2, int((psi - t[0][0]) / 0.25))
    (a, ga), (b, gb) = t[k], t[k + 1]
    return ga + (gb - ga) * (psi - a) / (b - a)


HINGE = pw(WHEEL_R + G_IN + HOOD_T + HINGE_OFF, PSI_TOP)


def gap_bdc(eps):
    pts = [rot2(pw(WHEEL_R + HOOD_GAP, ps), eps, HINGE) for ps in (-2 + 0.5 * i for i in range(9))]
    return min(math.hypot(p[0] - W_P, p[1] - W_Q) for p in pts) - WHEEL_R


def gap_arc(eps):
    """minimum radial bare gap over the hood arc psi BP_PSI0..PSI_TOP (0.5 deg steps) of the gap_at profile rotated by eps
    (rad, + closes) about HINGE. v2-A4-A2-01: the full-lift pass rule uses this, not the BDC-only gap_bdc"""
    n = int(round((PSI_TOP - BP_PSI0) / 0.5))
    pts = [rot2(pw(WHEEL_R + gap_at(ps), ps), eps, HINGE) for ps in (BP_PSI0 + 0.5 * i for i in range(n + 1))]
    return min(math.hypot(p[0] - W_P, p[1] - W_Q) for p in pts) - WHEEL_R


def solve_eps(target):
    """backplate rotation (rad, + closes) about HINGE that gives `target` bare gap at BDC"""
    lo, hi = -0.3, 0.3
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if gap_bdc(m) > target:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def jack_r():
    """hinge -> nip stud line point (= launcher_geom.Geo.JACK_PT), the lever arm of the leaf lift"""
    j = pw(WHEEL_R + HOOD_GAP + HOOD_T, JACK_PSI)
    return math.hypot(j[0] - HINGE[0], j[1] - HINGE[1])


# PIV_hood range. HI = the printed min-gap stop (v2-A2-01: gap 6.2, +0.327 deg; A2 gap 5.3, +1.315). LO = the static max-gap
# setting (thumbwheel on the stud sleeve, gap 7.0, -0.558 deg) minus the leaf lift.
# v2-A2-01 lift limit: a jammed candy pushes hood + stud + thumbwheel open against the leaf until the leaf stack goes solid.
# Thumbwheel top to cover roof along the stud axis is LEAF_PAD_H + LEAF_T + LEAF_TRAVEL at rest; the stack between them is
# LEAF_PAD_H + LEAF_T (pads + strip), so the thumbwheel lifts LEAF_TRAVEL before the strip lands flat on the roof.
# v2-A3-A2-01: 6.5 at rest, stack 4.3, travel 2.2 (A3: 6.0 / 4.5 / 1.5, cad q 4.495 at PIV_nip_lift -1.493). The stud tip
# is not the limit: it stays about 2.2 below the roof under the leaf slot (A3 2.4). On the 57.56 lever arm (jack_r) 2.2 is
# 2.190 deg, so LO is -2.748 deg, gap about 9.06. launcher_geom.report() prints these.
HOOD_HI = math.degrees(solve_eps(HOOD_GAP_MIN))
HOOD_STATIC_LO = math.degrees(solve_eps(NIP_SET[1]))
HOOD_LEAF_LIFT = math.degrees(LEAF_TRAVEL / jack_r())
HOOD_LO = HOOD_STATIC_LO - HOOD_LEAF_LIFT
HOOD_GAP_MAX = gap_bdc(math.radians(HOOD_LO))     # bare gap at BDC with the hood fully open (jam relief)
# v2-A2-01 nip pass rule: at the tightest setting (the min-gap stop) the leaf's full lift must still open the bare gap to the
# thickest candy over the tape, so a candy that wedges at the min gap pushes through instead of stalling the wheel.
# v2-A3-A2-01: MM_T max (A3 used MM_T_NOM: 7.5, and the lift opened only 7.55), with 0.1 over it for the ray-vs-gap_bdc spread.
NIP_PASS = MM_T[1] + TAPE_T                         # 8.0
NIP_PASS_MARGIN = 0.1
# v2-A4-A2-01: the pass rule now holds over the whole entry arc (gap_arc), not only at BDC (gap_bdc 8.181 hid 7.50 at psi 80).
# gap_bdc stays the definition of the NIP_SET settings (solve_eps). HOME = PIV_hood 0 (gap 6.5), MAX = the static max (7.0).
HOOD_GAP_LIFT = gap_arc(solve_eps(HOOD_GAP_MIN) - LEAF_TRAVEL / jack_r())    # 8.105: min-gap stop, leaf solid (= LIFT_FLOOR)
HOOD_GAP_LIFT_HOME = gap_arc(-LEAF_TRAVEL / jack_r())                        # 8.206: home, leaf solid (report)
HOOD_GAP_LIFT_MAX = gap_arc(solve_eps(NIP_SET[1]) - LEAF_TRAVEL / jack_r())  # 8.380: static max, leaf solid (report)
assert HOOD_GAP_LIFT >= NIP_PASS + NIP_PASS_MARGIN, (
    "nip entry arc at the min-gap stop opens to %.3f at full leaf lift < NIP_PASS %.2f + %.1f" % (HOOD_GAP_LIFT, NIP_PASS,
                                                                                         NIP_PASS_MARGIN))

# =====================================================================================================
# FEEDER (jar adapter + valve + gate, housing, 3-pocket disc on the jar axis, gear-driven by servo #3)
# =====================================================================================================
FEED_RP = 21.0                  # pocket circle radius = distance jar axis -> drop axis
N_POCKETS = 3                   # 120 deg pitch: park pockets at +/-60 and 180 from the outlet
POCKET_D = 13.75                # v2-A2-A1-03: 14.4 -> 13.9. Two edge-on lentils cannot sit side by side down to MM_D/MM_T
                                # min (12.5 x 6.3: the pair overlaps the bore, tools/lentil_probe.py); one flat 13.5 x 7.5
                                # still drops. v2-A3-A1-03: 13.9 -> 13.75 balances the two payload_fit margins (min pair
                                # blocked by about 0.08-0.1, flat 13.5 fits by 0.125; A3 0.00 / 0.20). Set it from the
                                # pocket coupon (tools/pocket_coupon.py). Pocket over the Ø16 outlet: (16 - 13.75) / 2 = 1.125
POCKET_CH = 1.0                 # v2-A1-03: 45 deg x 1 chamfer on the pocket top rim (lead-in for a candy on edge)
DISC_T = 8.0                    # one flat candy (7) fits, two cannot stack
FEED_FLOOR_T = 3.0
FEED_FLOOR_Z = IF_BEAM_Z1 + FEED_FLOOR_T          # 263 disc runs on this face
DISC_CLR = 0.3
DISC_Z = (FEED_FLOOR_Z + DISC_CLR, FEED_FLOOR_Z + DISC_CLR + DISC_T)   # 263.3 .. 271.3
DISC_GEAR_N, PINION_N, FEED_GEAR_M = 44, 30, 1.5   # ratio 1.467: disc +/-60 = servo -/+88
FEED_PINION_XY = (-(DISC_GEAR_N + PINION_N) * FEED_GEAR_M / 2.0, 0.0)  # (-55.5, 0) feeder servo spline axis
CHAMBER_R = 31.0                # candy chamber above the disc (lip covers the gear ring: no candy in the mesh)
FEED_FIRE = 60.0                # disc stroke: park 0 -> +60 -> 0 drops one; next shot uses -60
BAFFLE_HALF = 28.0              # baffle over the outlet sector, deg either side
BAFFLE_RAMP = 45.0              # anti-shear lead-in on both baffle edges (feeder work item: 30 -> 45 deg from horizontal;
                                # the baffle prints bottom-down on the valve and a 30 deg underside needs support)
AGITATOR_H = 6.0                # fins on the disc hub reaching up toward the valve bore
FEED_SERVO_FACE_Z = DISC_Z[1] + 4.9   # spline face down onto the pinion horn
ADAPTER_D = 69.0
ADAPTER_FLANGE_T = 1.6          # brief: <= 1.6 so the band still engages its threads
ADAPTER_SPOUT_OD = 55.0         # brief: <= 56, passes the Ø58 band lip
ADAPTER_SPOUT_ID = 50.0
VALVE_OD = 68.0
VALVE_BORE = ADAPTER_SPOUT_ID
GATE_T = 2.0
GATE_W = 56.0
GATE_TRAVEL = 52.0              # pull +X to open; the model's home pose is CLOSED (refill state)
# feeder work item (attempt 1). Split: PRT_feeder_housing = floor plate + outlet spout (on the beam, printed top face
# down, spout up); PRT_feeder_crown = everything above the floor (disc cavity, lip, pinion chamber, bayonet socket,
# servo pocket), printed upside down so every ceiling becomes a floor. The disc and pinion go in from below on the
# bench before the floor plate closes them in (the Ø69 disc cannot pass the Ø68.6 socket).
FEED_CAV_R = 35.0               # gear-band cavity (tips R34.5 + 0.5)
DISC_BAND_H = 4.0               # 44T band at the disc bottom (263.3..267.3); the plain land above journals in the lip
DISC_LAND_R = CHAMBER_R         # 31.0: land journal = the chamber wall, so no candy reaches the band
LAND_BORE_R = CHAMBER_R + DISC_CLR + 0.05   # 31.35 crown bore (journal + chamber; +0.05 over the 0.3 fit for facets)
FEED_LIP_Z = DISC_Z[0] + DISC_BAND_H + DISC_CLR + 0.05   # 267.65 lip underside over the gear band
CROWN_R = (48.0, 44.5)          # crown collar: lower (bolt bosses at R43.9) .. upper (servo face at x -45.5)
CROWN_STEP_Z = (270.8, 274.5)   # 45 deg step between the two (no ceiling when printed upside down)
PINION_CH_R = 24.35             # pinion chamber (tips R24.0; 0.35 so facets keep the 0.3 fit)
SOCKET_CONE = 1.09              # socket floor is a 47.5 deg cone R31.3 @ 274 -> R34.3 @ 277.27 (not a ledge)
BAYO_LUG_HW = 10.0              # lug half width, deg
BAYO_LEG = (-13.0, 43.5)        # horizontal leg of each L-slot, deg from the lug's locked centre
BAYO_ENTRY = (18.5, 43.5)       # vertical entry (lug at +30 = a+20..a+40)
BAYO_LEG_Z1 = IF_BAYO_LUG_Z[1] + 0.4
VALVE_Z0 = DISC_Z[1] + 1.6      # 272.9: valve skirt + baffle bottom, 1.6 over the disc (>= 1.5 rule)
VALVE_SKIRT_R = CHAMBER_R       # skirt rides inside the 31.3 bore
VALVE_LEADIN = (29.8, 25.0, 278.7)      # bore lead-in cone r0 @ VALVE_Z0 -> r1 @ z (v2-A1-08: r0 30.4 -> 29.8, skirt foot 1.2 wide)
VALVE_BODY_Z1 = IF_GATE_Z[0]    # lower body top = gate floor 288; above it only the three cheeks (no slot roof to bridge)
CHEEK_Y = 28.4                  # +/-Y cheeks inner faces (blade guides; v2-A1-09: 0.4 to the 56 blade, A1 0.2)
GATE_SLOT_X0 = -27.4            # -X cheek face (closed stop; v2-A1-09: 0.4 to the blade end)
GATE_X0, GATE_X1 = -27.0, 34.5  # closed blade span; open = +52 -> leading edge at x 25 = bore edge.
                                # v2-A1-12: the +X end sits flush with the valve OD (R34, +0.5; brief tolerance +/-1), A1 ran 8 proud
GATE_Z = (IF_GATE_Z[0] + 0.35, IF_GATE_Z[0] + 0.35 + GATE_T)   # 288.35..290.35 (v2-A1-09: 0.35 to the valve floor, A1 0.2)
GATE_CHAMFER = 30.0             # leading edge, top face
GATE_TAB = (GATE_X1 - 4.0, GATE_X1, 10.0, 297.0 + JAR_LIFT)   # pull tab x0 x1, half width y, top z (3.0 to the R27.5 spout when closed;
                                # v2-A1-09: top 296 -> 297 so the R6 top corners fit, 3.5 under the band)
GATE_TAB_R = CR                 # v2-A1-12: tab top corners and blade +X plan corners R6 (the form language)
GATE_EB = EB                    # 1.0 edge break on the blade and tab
GATE_FLUSH_TOL = 1.0            # blade +X end within VALVE_OD/2 +/- this (closed)
GATE_KNIFE_FLAT = 1.0           # v2-A1-08: vertical flat on the 30 deg leading edge (A1 knife, wall 0.77; 0.8 left a
                                # 1.15 probe where the chamfer meets the 0.6 side EB, so 1.0 keeps every wall >= 1.2)
GATE_BLADE_EB = 0.6             # edge break on the 2.0 blade (EB 1.0 would meet in the middle); the tab gets GATE_EB
GATE_STOP_LUG = (1.5, 3.0, 1.2) # v2-A1-09 open stop: lug on top of the blade's -X end (x length, half y, height). It rides
                                # in notches in the adapter spout tip: a through notch at -X (closed) and a blind one at +X
                                # whose shoulder it meets at +52 + GATE_STOP_CLR. Up, so the gate still prints flat.
GATE_STOP_CLR = 0.35            # lug to the notch ends, sides and roof
SPOUT_STOP_BOSS = (28.6, 5.0, 2.4)      # boss on the spout OD behind the +X shoulder: r, half y, height (band lip r29)
GATE_STOP_X = GATE_X0 + GATE_TRAVEL     # 25.0: the blade's -X end meets a positive open stop here (= bore edge); the
                                # stop is a design feature checked by a section (cadcheck slide_out can't assert "blocked past X")
# v3-A1 gate detent (PRT_gate_detent + FST_detent deleted): SNAP-IP finger cut in the flat-printed blade along its +Y
# edge (blade x -3 .. 12 at the closed pose, root at -X, free end +X), its R1 bump standing 0.8 proud of the blade edge
# (0.4 into the +Y cheek face at y CHEEK_Y) clicks into a R1.1 notch in that face at x 12 when the gate is closed. Beam
# along x, bending in y: in the layer plane. 3 E w d / 2 L^2 = 3 x 3500 x 1.5 x 0.4 / (2 x 15^2) = 14.0 MPa.
# Only the CLOSED (refill) position has a notch: the +Y cheek face spans x -15..15 (R34 body) and the travel is 52, so no
# point of the blade meets that face at both ends of the travel (it would need a 52 mm face). Open is the positive stop
# (stop lug on the spout shoulder at 52.35); the leading edge then sits on the bore edge.
GATE_FINGER = {
    "L": 15.0, "w": 1.5,        # free length root -> bump, width (y)
    "x_bump": 12.0,             # bump (and notch) x at the closed pose; finger root at x_bump - L
    "bump_r": 1.0, "bump_d": 0.4,   # bump radius, interference with the cheek face (= the finger deflection)
    "slot": 0.5,                # relief slot width (along the inner side and across the free end)
    "notch_clr": 0.1,           # notch = bump + this (seated row: ray through the bump, gap <= 0.15)
    "free": 1.5,                # finger runs this far past the bump centre to its free end
}
GATE_FINGER_STRESS = 3 * 3500.0 * GATE_FINGER["w"] * GATE_FINGER["bump_d"] / (2 * GATE_FINGER["L"] ** 2)   # 14.0 MPa
# A2 hotfix (v3-A1-03) OPEN detent: the +Y 1.5 of the stop lug sits on a SNAP-IP finger cut in the blade's -X end
# (beam along x, root at x GATE_X0 + L, free end at the blade's -X edge, bends in y: in the layer plane). A R0.6 bump on
# its +Y face stands 0.65 proud (0.3 into the spout notch's +Y side wall at y GATE_STOP_LUG hw + GATE_STOP_CLR) and drops
# into a R(0.6 + clr) dimple in that wall at PIV_gate 52, slotted to 52 + GATE_STOP_CLR so the positive stop still works.
GATE_OPEN_DETENT = {
    "y": (1.5, 3.0),            # finger y span (the lug's +Y part); inner relief slot 1.0..1.5, outer slot 3.0..4.2
    "slot_in": 0.5, "slot_out": 1.2,
    "L": 16.0,                  # root at GATE_X0 + L (closed frame); bump centre at GATE_X0 + lug x / 2
    "bump_r": 0.6, "bump_d": 0.3,   # bump radius, interference with the notch side wall (= finger deflection)
    "dimple_clr": 0.05,         # dimple = bump + this; 0.05 seated (distances row)
    "closed_clr": 0.35,         # the closed through-notch is widened on +Y so the bump clears it by this
}
GATE_OPEN_DETENT_L = GATE_OPEN_DETENT["L"] - GATE_STOP_LUG[0] / 2          # 15.25 root -> bump
GATE_OPEN_DETENT_STRESS = 3 * 3500.0 * (GATE_OPEN_DETENT["y"][1] - GATE_OPEN_DETENT["y"][0]) * GATE_OPEN_DETENT["bump_d"] / (
    2 * GATE_OPEN_DETENT_L ** 2)  # 10.2 MPa
ADAPTER_SPOUT_Z0 = GATE_Z[1] + 0.35     # 290.7: spout bottom = blade roof (0.35 over the blade)
# v3-A1 valve to adapter spout (FST_valve x3 deleted), option (b) push fit: the spout goes straight down into the
# cheeks (its tip notch over the gate's stop lug), a 3 mm key rib on the +Y cheek pad runs in a groove in the spout OD
# (the refill twist and the relock turn the jar group as one), the spout shoulder (R SPOUT_SHOULDER_R) bears on the cheek
# tops / pads (jar weight), and 2 SNAP-V fingers cut in the +/-Y cheeks (barbs into a groove round the spout) take the
# lift. Fingers are vertical (across layers in the valve's bottom-down print): 3 E t d / 2 L^2 <= 12 MPa.
VALVE_SNAP = {
    "x": (2.0, 8.0),            # finger x span on both +/-Y cheeks (clear of the gate notch at x 12)
    "t": 1.0, "relief": 1.0,    # finger thickness (y), relief gap behind it and at its sides (0.6)
    "side": 0.6,
    "z_root": 321.0,            # relief slots cut 3 below the cheek root into the valve body (finger L 15 to the top)
    "barb_r": 27.1,             # barb tip radius: 0.4 inside the R27.5 spout OD (the install deflection)
    "barb_z": 334.6,            # barb catch face (underside); the spout groove's lower wall is 0.1 under it
    "groove_r": 27.0,           # spout groove floor (0.1 radial clear of the barb tip)
}
VALVE_SNAP_L = VALVE_SNAP["barb_z"] + 0.2 - VALVE_SNAP["z_root"]          # 13.8 root -> barb
VALVE_SNAP_STRESS = 3 * 3500.0 * VALVE_SNAP["t"] * 0.4 / (2 * VALVE_SNAP_L ** 2)   # 11.0 MPa
SPOUT_SHOULDER_R = 28.3         # spout root R28.3 from the cheek tops to the lid disc (band lip ID R29: 0.7 radial)
VALVE_PAD_X = (-13.0, -1.0)     # centring pads on the +/-Y cheek faces (above the blade; 45 deg undersides), 0.15 to the spout
VALVE_KEY = (-7.0, 3.0, 0.75)   # key rib on the +Y pad: x centre, width, radial height; spout groove +0.2 a side, +0.1 deep
VALVE_KEY_GROOVE_OVER = 1.0     # A2 hotfix (v3-A1-01): the spout key groove runs this far past the rib top (cheek top); A1 stopped 0.5 short
BAFFLE_R = (10.5, 30.4)         # baffle on the VALVE (jar locked at 0 -> over the outlet sector); outer edge buried in the
                                # skirt (A1 ended on the skirt's own R31 face: coincident facets left 0.02 slivers)
BAFFLE_FLAT = 0.8               # v2-A1-08: the underside ramps stop 0.8 above the baffle bottom (vertical flat at the foot)
BAFFLE_RAMP_TOP = DISC_Z[1] + 5.5       # 276.8: underside ramps start above a 13 mm candy standing in a pocket (4.7 proud)
BAFFLE_EDGE_TOP = 278.0
BAFFLE_ROOF = 35.0              # roof slope toward both edges (candy sheds into the parked pockets)
BAFFLE_TOP = 286.0
FIN_R, FIN_T = 8.8, 2.4         # agitator fins on the disc hub (baffle inner edge 10.5)
SERVO_POCKET = (-85.9, -45.1, 10.4)    # x0 x1 half-y (servo body -85.5..-45.5 x +/-10.07)
COVER_SCREWS = [(-66.0, 18.6), (-66.0, -18.6)]   # v2 lobe-cover ear centres: still define the lobe plan hull (R6 corners)
# v3-A1 crown lobe (PRT_feeder_cover merged): servo #3 goes up into the lobe pocket from below, seats against the closed
# roof (0.05 modelled), crush ribs on the +/-Y walls hold it; the idler boss sits in a blind recess in the roof.
LOBE_ROOF_Z = FEED_SERVO_FACE_Z + 40.0 + 0.05     # 316.25 roof underside (servo top + 0.05)
assert LOBE_ROOF_Z + 3.9 + 0.35 + 1.5 <= IF_SOCKET_Z[1] + 1e-6, "lobe roof must fit under the crown top plane"
CRUSH_RIB = (1.0, 0.1, 290.0, 314.0)   # rib width, interference into the servo, z0 (45 deg lead-in below), z1
# v3-A1 crown hooks (FST_feedmount x4 deleted): SNAP-V, L 16 (root z 268 -> tip 252), t 1.0 radial, 5 wide, barb 0.55
# radially outward (0.5 over the slot's outer wall) catching the beam's under-pocket roof (z 254) with 0.1 to spare.
CROWN_HOOK = {"L": 16.0, "t": 1.0, "w": 5.0, "barb": 0.55, "root_z": 268.0, "gap_out": 0.05}
CROWN_HOOK_STRESS = 3 * 3500.0 * CROWN_HOOK["t"] * 0.5 / (2 * CROWN_HOOK["L"] ** 2)        # 10.3 MPa engage
CROWN_HOOK_RELEASE = 3 * 3500.0 * CROWN_HOOK["t"] * 0.6 / (2 * CROWN_HOOK["L"] ** 2)       # 12.3 MPa at the release
FEED_HORN_POCKET = PAN_HORN_POCKET      # HORN: feeder pinion pocket (disc 2.5 + 0.2) + 8 PAN_HORN_PIN pins, no centre screw
FEED_HUB_R = 12.0                       # pinion hub round the pocket (R10.1 pocket, 1.9 wall)
HORN_CAV_R = FEED_HUB_R + 0.45          # crown cavity round the pinion hub / horn below the servo face (0.35 + facet sag)
BUS_TAB = [(-98.0, -16.0), (-86.0, -16.0)]

# =====================================================================================================
# CABLES: purchased lead length per cable (mm), same values as checks.json "cable_leads" (cadcheck reads that copy; keep both
# in step). v2-A2-02: every A.cable passes lead_len=CABLE_LEADS[...]; CAB_launcher_base is the new hub-to-MotorGo lead.
# =====================================================================================================
CABLE_LEADS = {
    "CAB_phase_*": 80,          # motor phase tails
    "CAB_usb": 1000,
    "CAB_12v_in": 200,
    "CAB_12v_mg": 100,
    "CAB_12v_ctrl": 250,
    "CAB_uart": 300,
    "CAB_bus_pan": 350,         # v2-A3-A2-02: next Hiwonder bus lead up (300 kept 9.5 spare)
    "CAB_bus_tilt": 300,
    "CAB_bus_feeder": 500,
    "CAB_launcher_bundle": 350,
    "CAB_launcher_base": 250,   # v2-A2-02 hub-bottom junction -> 45 mm U-loop under the hub gear -> MotorGo J6/J8 + encoder JST
    "CAB_encoder": None,        # v2-A3-A2-02: derived below from ENC_LEAD (A3 150 ended at the journal bore)
}
# v2-A3-A2-02 encoder lead: ONE purchased 5-wire JST-SH lead, Plink -> MotorGo encoder JST, unspliced across both joints.
# It rides the launcher bundle and the base lead, so the CAB_encoder route (Plink -> left journal end) gets what is left:
# ENC_LEAD - bundle path - base path - ENC_SPARE. finish.py recomputes it from the built path_len values (enc_budget) and
# asserts it covers the CAB_encoder path; the A3 paths (265.4 + 164.8) give the 115 that checks.json cable_leads holds.
ENC_LEAD = 550
ENC_SPARE = 5.0
ENC_A3_PATHS = (265.4, 164.8)   # CAB_launcher_bundle, CAB_launcher_base path_len (attempt 3 manifest)


def enc_budget(bundle_len, base_len):
    """lead budget for the CAB_encoder route given the bundle and base path lengths (mm)"""
    return ENC_LEAD - bundle_len - base_len - ENC_SPARE


CABLE_LEADS["CAB_encoder"] = int(round(enc_budget(*ENC_A3_PATHS)))     # 115 until finish.py writes the built value


# v2-A2-02 pan-axis slack: the static side of each hub junction carries a loop under the hub gear that adds >= PAN_LOOP_ADD
# over the straight line between its ends (pi/2 x R14 x 2 = 44 for +/-90 pan). base.build_cables asserts it and writes
# parts.<CAB>.loop {path_len, straight, added} into the manifest.
HUB_JCT_Z = IF_GEAR_Z[0] - 1.5   # 76: the moving bundle and tilt bus end on the pan axis here (pan_stage hub list), under the gear bore
# v2-A5-03 (attempt 6): the 3-way bus splice (BOM 14a, 3 x 3-to-1 solder splices under heat shrink, sleeved) modelled as
# BUY_bus_junction, a Ø10 x 25 envelope on PIV_pan, axis Z, in the hub bore's az-35 half (the bus loop side) at r 7 from the
# pan axis: r 2..12, so 1.0 to the R13 hub-gear bore and 2.0 to the R14 turntable bore. z0..z0+l = 74..99. The tilt and
# feeder bus hub lists end on its top face, the static CAB_bus_pan riser on its bottom face; the launcher bundle/base
# meeting point moves off the axis to BUS_LB_JCT (az 235, r 4, z 70), so the bus ends and the launcher pair share no point.
# v3-A1 (V2R7 A7-02): splice shortened to 20 and seated 72..92, so the two bus leads have 2.9 straight + an R2.5 bend under
# the bore roof (z 100.3); the bundle/base meeting point stays at z 70 (no longer tied to z0).
BUS_JCT = {"d": 10.0, "l": 20.0, "r": 7.0, "az": 35.0, "z0": 72.0}
BUS_JCT_XY = (BUS_JCT["r"] * math.cos(math.radians(BUS_JCT["az"])), BUS_JCT["r"] * math.sin(math.radians(BUS_JCT["az"])))  # (5.73, 4.02)
BUS_JCT_TOP = (BUS_JCT_XY[0], BUS_JCT_XY[1], BUS_JCT["z0"] + BUS_JCT["l"])      # tilt / feeder bus ends (z 92)
BUS_JCT_BOT = (BUS_JCT_XY[0], BUS_JCT_XY[1], BUS_JCT["z0"])                     # CAB_bus_pan_tail end (z 72)
# Bundle/base meeting point: the plan's az 235 / r 4 at z 70. Measured alternatives (v2 A6):
# - (-2.29, -3.28, 76) at the splice height: 2.855 to the splice at home, but the static base end overlaps the moving splice at
#   pan -90 (cad q sweep BUY_bus_junction CAB_launcher_base: -5.09 mm3 at -90, -0.34 at -75; splice centre az -55 is 70 deg
#   from az 235).
# - az 215 / r 6.5 at z 76: 1.46 to the splice over pan -92.5..92.5, but the bundle and base ends drift 9.2 apart at pan +/-90,
#   so the v2-A2-02 rows (base to bundle <= 1.0 at pan +/-90) fail at 3.38 / 3.29.
# At r 4 the two O6 ends overlap at every pan (chord 2 x 4 x sin 45 = 5.66 < 6).
BUS_LB_JCT_AZ, BUS_LB_JCT_R = 235.0, 4.0
BUS_LB_JCT = (BUS_LB_JCT_R * math.cos(math.radians(BUS_LB_JCT_AZ)), BUS_LB_JCT_R * math.sin(math.radians(BUS_LB_JCT_AZ)),
              70.0)                                                             # (-2.29, -3.28, 70)
# v2-A6-02 (attempt 7): the pan bus lead is split on the pan axis at BUS_PAN_AX. The static U-loop (CAB_bus_pan, base) ends
# there, and the PIV_pan tail (CAB_bus_pan_tail, pan_stage) runs from it to the splice's bottom face centre (BUS_JCT_BOT).
BUS_PAN_AX = (IF_PAN_XY[0], IF_PAN_XY[1], 63.0)
# v3-A1 cable dress in the turntable tunnels (V2R7 A7-02: every lead its own route). Left post channel / tunnel: the bundle
# on the inner side (y LB_Y), the feeder bus outboard (y FB_Y); right: the tilt bus (y TB_Y). Both channels turn into the
# tunnel on an R15 centreline (TT_TUNNEL_BEND_R). In the hub the two bus leads run side by side (+/-1.5 about the splice
# axis) up to the splice top and drop onto it straight; the bundle drops into the bore at BUS_LB_JCT's xy.
LB_Y, FB_Y, TB_Y = -15.4, -20.3, -17.0
_BUS_DX = 1.5
_BUS_ZH = BUS_JCT_TOP[2] + 2.9 + 2.5    # 97.4: bus corner over the splice (2.9 straight + R2.5)


def hub_bus(x_off, y):
    """tunnel -> splice top for a bus lead at y in the tunnel: (point, fillet radius) list, ends on the splice top"""
    x = BUS_JCT_XY[0] + x_off
    return [((x, y, TT_TUNNEL_ZC), 4.0), ((x, BUS_JCT_XY[1], _BUS_ZH), 2.5), ((x, BUS_JCT_XY[1], BUS_JCT_TOP[2]), 0.0)]


def channel_down(x, y, z_from):
    """vertical post channel at (x, y) from z_from down into the tunnel: the R15 corner"""
    return [((x, y, z_from), None), ((x, y, TT_TUNNEL_ZC), TT_TUNNEL_BEND_R)]


BUS_HUB_FEED = hub_bus(-_BUS_DX, FB_Y)
BUS_HUB_TILT = hub_bus(+_BUS_DX, TB_Y)
LB_HUB = [((BUS_LB_JCT[0], LB_Y, TT_TUNNEL_ZC - 0.2), 6.0), ((BUS_LB_JCT[0], BUS_LB_JCT[1], TT_TUNNEL_ZC - 0.2), 6.0),
          ((BUS_LB_JCT[0], BUS_LB_JCT[1], 80.0), None), (BUS_LB_JCT, 0.0)]


def fillet_path(pts, r_default):
    """pts: [(xyz, r)] (r None = r_default, 0 = keep sharp / end). Each interior corner becomes an arc of its radius
    (shrunk so two tangents share a segment), sampled every 10 deg; returns the xyz list for asm.cable."""
    P = [tuple(map(float, p)) for p, _ in pts]
    R = [r_default if r is None else float(r) for _, r in pts]
    R[0] = R[-1] = 0.0
    sub = lambda a, b: (a[0] - b[0], a[1] - b[1], a[2] - b[2])
    ln = lambda a: math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)
    nrm = lambda a: (a[0] / ln(a), a[1] / ln(a), a[2] / ln(a))
    n = len(P)
    th, t = [0.0] * n, [0.0] * n
    for i in range(1, n - 1):
        a, b = nrm(sub(P[i], P[i - 1])), nrm(sub(P[i + 1], P[i]))
        c = max(-1.0, min(1.0, sum(a[k] * b[k] for k in range(3))))
        th[i] = math.acos(c)
        t[i] = R[i] * math.tan(th[i] / 2) if th[i] > 1e-4 else 0.0
    for i in range(n - 1):                     # two tangents share a segment
        L = ln(sub(P[i + 1], P[i]))
        if t[i] + t[i + 1] > L:
            f = L / (t[i] + t[i + 1])
            t[i] *= f
            t[i + 1] *= f
    out = [P[0]]
    for i in range(1, n - 1):
        if t[i] < 1e-6:
            out.append(P[i])
            continue
        a, b = nrm(sub(P[i], P[i - 1])), nrm(sub(P[i + 1], P[i]))
        r = t[i] / math.tan(th[i] / 2)
        T1 = tuple(P[i][k] - a[k] * t[i] for k in range(3))
        bis = nrm(tuple(b[k] - a[k] for k in range(3)))
        C = tuple(P[i][k] + bis[k] * r / math.cos(th[i] / 2) for k in range(3))
        T2 = tuple(P[i][k] + b[k] * t[i] for k in range(3))
        u, w = sub(T1, C), sub(T2, C)
        m = max(2, int(math.ceil(math.degrees(th[i]) / 10.0)))
        s = math.sin(th[i])
        for j in range(m + 1):
            f0, f1 = math.sin((1 - j / m) * th[i]) / s, math.sin(j / m * th[i]) / s
            out.append(tuple(C[k] + u[k] * f0 + w[k] * f1 for k in range(3)))
    out.append(P[-1])
    clean = [out[0]]
    for q in out[1:]:
        if ln(sub(q, clean[-1])) > 1e-3:
            clean.append(q)
    return clean


PAN_LOOP_ADD = 45.0
PAN_LOOP_ZC = 48.0               # centre height of the hanging U-loops (bottoms at 41.5-45, above the buck top 39 and the battery x >= 10)
# v2-A6-02: the launcher U (az 235) inner leg moves out from r 3 to r 6.5, so the PIV_pan bus tail near the pan axis
# (z 63..74) clears the launcher sleeve over pan (capsule model in renders/attempt-7/tail_feasibility.py: r 3 gave -1.4).
# The outer leg stays at r 16 (LB_U_RC + LB_U_R) into the existing riser.
LB_LEG_R = 6.5
LB_LOOP_ZC = 46.5
LB_U_RC, LB_U_R = 11.25, 4.75    # U bottom centreline z 41.75
# MotorGo connection points in STEP x/y (world x = MG_X0 - sx, z = MG_Z0 - sy). The two 4.5 mm blocks on the J6/J8 edge are
# the encoder JSTs: STEP x 18.5-25 and 43-50, y -49.5..-52 (cad q ray on REF/mg_axis.stl, attempt 3). components.json has no
# pad map, so the phase pads go on the flat band between the JSTs (the rig used STEP x 14-30, y -51: that overlaps JST 1).
MG_ENC_JST_STEP = (21.8, -50.8)  # encoder JST 1 centre (top face 4.5 off the PCB)
MG_PHASE_PAD_STEP = (34.0, -51.0)  # J6/J8 phase pad group centre (flat, on the component face)


def cable_lead(name):
    """lead length for a cable object name; '*' keys match by prefix (CAB_phase_a -> CAB_phase_*)"""
    if name in CABLE_LEADS:
        return CABLE_LEADS[name]
    for k, v in CABLE_LEADS.items():
        if k.endswith("*") and name.startswith(k[:-1]):
            return v
    return None

# v2-A1-12 colour map. pla_b (terracotta) = the candy path and the touch points; every other printed part is pla_a
# (warm grey): static structure and drivetrain (base, turntable, posts, beam, crown, covers, nacelle, journal plate,
# encoder cap, gears, pinions, stops). apply_colours() runs after every subsystem is built, so modules need not agree.
# v3-A1 finish: PRT_feeder_housing merged into PRT_beam (structure, A; DESIGN_LOG plan "Form language")
COLOUR_B = ["PRT_jar_adapter", "PRT_jar_valve", "PRT_jar_gate", "PRT_feeder_disc",
            "PRT_launcher_body", "PRT_hood", "PRT_flywheel", "PRT_nip_wheel"]


JAR_GLASS_RGBA = (0.80, 0.90, 0.95, 0.25)   # v2-A1-11: BUY_jar glass, transmissive in the view set (parts/finish.py)


def colour_of(name):
    return "pla_b" if name in COLOUR_B else "pla_a"


def apply_colours(objects):
    """re-assign every PRT_ material from COLOUR_B (objects: an iterable of Blender objects)"""
    for ob in objects:
        if ob.name.startswith("PRT_") and ob.type == 'MESH':
            ob.data.materials.clear()
            ob.data.materials.append(asm.mat(colour_of(ob.name)))


RENDER_POSES = {
    "pan-90_tilt0": {"PIV_pan": -90}, "pan+90_tilt45": {"PIV_pan": 90, "PIV_tilt": 45},
    "tilt45": {"PIV_tilt": 45}, "jar_unlocked": {"PIV_jar": IF_BAYO_TWIST},
}


def joints():
    asm.joint("PIV_pan", (IF_PAN_XY[0], IF_PAN_XY[1], IF_DECK_Z), 'Z', PAN_LO, PAN_HI, step=15)
    asm.joint("PIV_pan_pinion", (IF_PINION_XY[0], IF_PINION_XY[1], IF_DECK_Z), 'Z', PAN_LO, PAN_HI,
              couple_to="PIV_pan", couple_ratio=-1.0)
    asm.joint("PIV_tilt", (0.0, IF_TILT_Y, IF_TILT_Z), 'X', TILT_LO, TILT_HI, parent="PIV_pan", step=2.5)
    asm.joint("PIV_flywheel", (WHEEL_XW, W_P, IF_TILT_Z + W_Q), 'X', parent="PIV_tilt", continuous=True, step=60)
    # v2-A1-01 (launcher step): the hood range is split so the thumbwheel's kinematics are exact. PIV_nip_lift = the leaf
    # lift (a jam pushes hood + stud + thumbwheel open, -2.19..0 since v2-A3; A3 -1.49); PIV_hood (child) = the thumbwheel setting 7.0..6.2
    # (-0.558..+1.315). Their sum spans HOOD_LO..HOOD_HI. The thumbwheel and its nut ride PIV_nip_lift, the hood, stud and
    # stop sleeve ride PIV_hood, so the sleeve meets the thumbwheel only at the gap-7.0 stop.
    asm.joint("PIV_nip_lift", (WHEEL_XW, HINGE[0], IF_TILT_Z + HINGE[1]), 'X', -HOOD_LEAF_LIFT, 0.0, parent="PIV_tilt",
              step=1.5)
    asm.joint("PIV_hood", (WHEEL_XW, HINGE[0], IF_TILT_Z + HINGE[1]), 'X', HOOD_STATIC_LO, HOOD_HI, parent="PIV_nip_lift",
              step=1.0)
    asm.joint("PIV_feeder", (IF_JAR_XY[0], IF_JAR_XY[1], FEED_FLOOR_Z), 'Z', -FEED_FIRE, FEED_FIRE,
              parent="PIV_pan", step=5)
    asm.joint("PIV_feeder_pinion", (FEED_PINION_XY[0], FEED_PINION_XY[1], FEED_FLOOR_Z), 'Z',
              -FEED_FIRE * DISC_GEAR_N / PINION_N, FEED_FIRE * DISC_GEAR_N / PINION_N, parent="PIV_pan",
              couple_to="PIV_feeder", couple_ratio=-DISC_GEAR_N / PINION_N)
    asm.joint("PIV_jar", (IF_JAR_XY[0], IF_JAR_XY[1], IF_SOCKET_Z[0]), 'Z', 0.0, IF_BAYO_TWIST, parent="PIV_pan",
              step=5)
    # v2-A4 (attempt 5 feeder): the gate is a slide, so its open state joins every sweep (V2A3-T6). Home 0 = closed
    # (refill state), hi = GATE_TRAVEL 52 = the open notch under the detent bump. The positive stop (lug on the adapter
    # shoulder) is at 52 + GATE_STOP_CLR; the default 1.0 overtravel reaches 53 past it (accepted warn).
    asm.joint("PIV_gate", (IF_JAR_XY[0], IF_JAR_XY[1], GATE_Z[0]), 'X', 0.0, GATE_TRAVEL, parent="PIV_jar",
              step=GATE_TRAVEL / 4.0, prismatic=True)
