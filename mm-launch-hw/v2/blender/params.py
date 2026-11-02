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
IF_TILT_ADAPTER = (13.0, 45.7, 52.0)    # horn adapter disc R, x0, x1 (+X face carries the 1.0 horn recess)
IF_TILT_KEY_X = (38.7, 45.7)    # 12 AF hex key on the adapter (x span)
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
IF_FEED_BOLTS = [(-36.0, -21.0), (-36.0, 21.0), (34.0, -20.0), (34.0, 20.0)]   # M3 csk, housing to beam (finish: x40 sat on post_R's inner face, driver blocked).
                                # v2-A1-05: the -X pair moved y 18 -> 21, so the pilot sits 28.66 from the feeder pinion axis
                                # (-55.5, 0) and keeps a 3.1 wall to the R24.35 pinion chamber (A1: 1.08)
IF_FEED_BUS_XY = (-98.0, -16.0) # feeder bus passes down through the beam into the left post channel
IF_POST_L_CHANNEL = (-104.0, -92.0, -22.0, -12.0)   # x0 x1 y0 y1 vertical cable channel (launcher bundle + feeder bus)
IF_POST_R_CHANNEL = (90.0, 100.0, -22.0, -12.0)     # tilt servo bus
# feeder <-> jar
IF_JAR_XY = IF_PAN_XY
IF_SOCKET_ID = 68.6             # bayonet socket in the feeder housing (valve body OD 68)
IF_SOCKET_Z = (274.0, 286.0)    # socket floor .. housing top (12 mm engagement)
IF_BAYO_N = 3
IF_BAYO_LUG_R = 37.0            # lug tips (valve body R34)
IF_BAYO_LUG_Z = (275.0, 279.0)
IF_BAYO_TWIST = 30.0            # PIV_jar 0 = locked, 30 = free to lift
IF_GATE_Z = (288.0, 290.4)      # gate slot plane (above the housing top: the blade never passes a wall)
IF_VALVE_Z1 = 300.0             # valve body top = band lip face
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
ADAPTER_SCREW_L = 20.0          # self-tap M3 from the deck top into the adapter holes; tip >= 3 above the battery face (A3-M2)
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
# MotorGo mounting screws (v2 brief, launch-rig finding 2026-10-24): REF/mg_axis.stl holes measure Ø2.5, not the Ø3.4 in
# components.json. Use M2.5 until the user confirms on the real board; then set MG_SCREW 'M3_cap', MG_HOLE_D 3.4, MG_PILOT_D 2.5.
MG_SCREW = "M2.5_cap"
MG_SCREW_SPEC = (2.5, 4.5, 2.5)  # shank d, head d, head h (DIN 912 M2.5)
MG_HOLE_D = 2.7                 # M2.5 clearance through the PCB
MG_PILOT_D = 2.1                # M2.5 self-tap pilot in the partition standoffs
MG_PART_X = (-80.0, 0.0)     # rear partition (separate part on the floor plate)
NICHE_W = 30.0                  # USB niche slot width; V floor at NICHE_V_SLOPE (print: deck down, V points up)
NICHE_V_SLOPE = 1.2
NICHE_TOP_Z = 48.5              # rear-wall opening top
BUCK_HOLE_Y = 33.4              # components.json flange holes (on the fin-free flange strips)
BUCK_BOSS_H = 5.0
BUCK_FLANGE_T = 3.0
CTRL_BOSS_D = 7.0
FLOOR_SCREWS = [(-112.0, 60.0), (-112.0, -75.0), (-30.0, -112.0), (2.0, -100.0), (60.0, -30.0), (112.0, 0.0),
                (60.0, 112.0), (-60.0, 112.0)]
FLOOR_COL_R = 5.0
UART_CLIPS = [(-20.0, 5.0), (40.0, 5.0)]
PAN_SERVO_TOP_Z = 72.0          # pan servo case top = mount plate underside
PAN_PLATE_T = 4.0
PAN_PLATE = (-42.0, 42.0, 30.0, 96.0)
PAN_POSTS = [(-34.0, 38.0), (34.0, 38.0), (-34.0, 88.0), (34.0, 88.0)]
PAN_PLATE_HOLE_R = 13.5
PINION_HUB_R = 12.0
HORN_LIFT = 1.0                 # horn hub underside above the servo case
HORN_RECESS = 1.0

# =====================================================================================================
# PAN STAGE (turntable, posts = slices of the R108 drum, beam, tilt servo)
# =====================================================================================================
POST_T_MIN = 14.0               # left post minimum wall at y = +/-26 (arc to IF_ARM_L_IN)
GEAR_BACKLASH = 0.15
SERVO_POCKET_CLR = 0.3
RING_R = (20.0, 44.0)           # thrust ring (rides with the turntable, keyed on the hub; slides on the deck)
TT_GROOVE = (-100.5, 100.0, -22.0, -12.0, 93.6)   # turntable cable groove x0 x1 y0 y1 floor z (under the posts it
                                # opens to the post feet; between them a 2 mm cap closes it)
GCAP_T = 3.0                    # groove cap thickness (a proud strip on the flat turntable top: a flush rebate
                                # would need a 36 mm bridge with the turntable printed top-down)
GCAP_Y = (-30.0, -4.0)          # groove cap strip width (8 mm screw lands each side of the groove)
GCAP_DISC_R = 24.0              # groove cap disc over the hub bore
HUB_SCREW_R = 17.0              # FST_hub_*: up through the hub gear into the hub wall (R14..R20)
HUB_GEAR_BORE_R = 13.0          # hub gear bore (1 mm inside the hub bore so the Ø3.4 clearance holes keep a 2.3 wall)
POST_L_BORE_X0 = -96.0          # left U-bore blind end; end wall to POST_L_WALL_X
POST_L_WALL_X = -97.8
POST_L_CAVITY = (-104.0, POST_L_WALL_X, -22.0, 7.0, 211.0, 233.0)   # bundle turns from the journal axis into the channel
POST_R_BORE_X1 = 52.0           # right U-bore end (journal + adapter disc); servo cavity beyond
POST_R_TEAR_R = 13.5            # teardrop passage for the adapter disc (R13 + 0.5, faceted)
POST_R_CHANNEL_Z1 = 184.0       # right channel top (the bus enters from the servo pocket through a notch)
POST_R_COVER_X = 96.2           # cover inner face = servo back face + SERVO_POCKET_CLR
POST_R_COVER_Z = (186.0, 244.0) # cover band (full post width, outer arc face)
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
HINGE_AXLE_L = 35.0             # v2: M3 x 35 into a nut trap on the journal-plate side (A3-F2)
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
SLEEVE_R = (1.7, 3.8)           # v2-A1-01 PRT_nip_stop_sleeve bore / OD radius: OD past the thumbwheel's AF 5.7 nut trap
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
LEAF_BLOCK_H, LEAF_BLOCK_L = 3.6, 6.0   # root block under the strip (thread for FST_leaf_*, pilot runs through), length along v
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
HORN_CAV_R = 11.2               # horn disc R10 + M2 heads (1.2 running clearance)
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
GATE_TAB = (GATE_X1 - 4.0, GATE_X1, 10.0, 297.0)   # pull tab x0 x1, half width y, top z (3.0 to the R27.5 spout when closed;
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
# v2-A2-A1-09 gate detent: PRT_gate_detent, a separate flat-printed PLA clip (1 x M3 self-tap, FST_detent_0) whose bump
# drops into a notch on the blade top. The notches sit at the closed position and at closed - GATE_TRAVEL (that notch comes
# under the bump when the gate is pulled open +52). The clip yields bump_h to pass between them (its own flexures row).
# Layout (attempt 3 feeder step): the band lip (z 300.5, R36.75) covers the cheek top, so no screw can be driven down
# into it. The clip is a tab hugging the +Y cheek's R34 outside face (radial M3 self-tap into the cheek, like
# FST_valve_*) plus a 1.2 plate at blade-top level that runs +X past the cheek end (x 15) to the bump. The beam runs
# along world X (flexures dir [1,0,0]); the part prints on its flat +Y back face, so the beam bends in the layer plane.
GATE_DETENT = {
    "clip": (12.5, 14.5, 1.2),  # beam free length (along x root 17 -> bump 29.5), width (y 24..38.5), thickness (z)
    "bump_r": 1.0,              # spherical-cap bump under the free end: R1 ...
    "bump_h": 0.5,              # ... standing 0.5 proud (the clip lifts 0.4 to ride the blade between notches)
    "x": 29.5,                  # bump x at the closed pose: between the R27.5 spout OD and the tab (GATE_TAB x0 30.5)
    "y": GATE_W / 2.0 - 2.5,    # 25.5: bump y, 2.5 inside the blade's +Y edge (clear of the 0.6 blade EB)
    "notch_clr": 0.1,           # notch = bump + this on radius and depth (seated row: clip to blade <= 0.15)
    "gap": 0.1,                 # plate underside over the blade top (the seated-bump distances row reads this)
    "plate_x": (15.4, 31.5),    # plate: 0.4 off the +Y cheek's +X end (x 15) .. 2 past the bump
    "plate_y": (24.0, 39.9),    # 24: r 28.5 at x 15.4, 1.0 off the R27.5 spout; 39.9 = the flat back (print bed) face.
                                # v2-A3-A3-01: 36.5 -> 38.5 so the x 10 screw under a 1.0 counterbore ends at y 27.5 (the A3
                                # x 9 tip): at 36.5 the x 10 tip reached y 25.5, 1.0 into the R27.5 adapter spout.
                                # v2-A4-01: 38.5 -> 39.9 with the counterbore 1.0 -> 2.4, so the pan head (2.4 tall on its
                                # bearing face at y 37.5) sits flush; the bearing face and the y 27.5 tip do not move
    "tab_x": (3.5, 17.0),       # tab: clear of the FST_valve_0 head (x +/-2.75) .. the beam root at x 17
    "tab_r": VALVE_OD / 2.0 + 0.05,   # tab inner face: 0.05 off the cheek's R34 outside face (the screw pulls it on)
    "tab_z0": 288.4,            # v2-A3-A3-01 tab bottom (A3: the plate underside 290.45), 2.4 over the crown top 286 and
                                # 2.8 under the counterbore; outside the R34 cheeks, so it passes nothing on the way down
    "tab_z1": IF_BAND_Z0 - 1.0, # v2-A5-01 (attempt 6) flat tab top at 299.5, 1.0 under the band lip's lower face (z 300.5;
                                # A5 301.5 with a 45 deg chamfer read 0.322 to the band). Vertical stack row v2-A5-01, WC 0.8.
                                # The Ø6.6 x 2.4 counterbore (top z 297.8) keeps 1.7 to the flat top and about 0.7 to the
                                # back-face edge under the EB 1.0; the Ø3.4 clearance hole (top 296.2) keeps 3.3 to the top
    "screw": (9.5, 294.5, 10.0),    # FST_detent_0 x, z, length: -Y from the back face. v2-A3-A3-01 x 7.1 -> 9.5 so the
                                # counterbore keeps 2.7 to the tab's -X end (x 3.5); z 294.5 keeps the tip 2.65 over the blade.
                                # v2-A5-01: the counterbore keeps 2.7 to the -X end and 2.8 to the bottom, but only 1.7 to
                                # the 299.5 flat top (0.7 at the back-face edge under the EB): cad q section x 9.5.
                                # v2-A3-A3-01: stock M3 x 10 pan self-tap (A3 x 9, not stock). Head on the counterbore floor
                                # at y 37.5 (back face 39.9 - cbore[1] 2.4; A4 38.5 - 1.0), tip at y 27.5 where the x 9 tip was: past the cheek
                                # inner face (y 28.4) 0.9 into the gate slot, 0.9 off the spout, 2.65 above the blade
    "cbore": (6.6, 2.4),        # v2-A3-A3-01 head counterbore in the tab back face: Ø (cadlib RULES m3_pan_head_d + 0.6, the
                                # review asked 6.5), depth = screw_hole sink. Clamp through the tab 4.8 (r 34.05 face at y 32.7).
                                # v2-A4-01: depth 1.0 -> 2.4 = the M3 pan head height, so the head is flush with the back face
    "tab_eb": EB,               # v2-A3-A3-01 edge break on the tab: the form language EB 1.0 (A3 0.3 on the whole clip)
    "plate_eb": 0.4,            # v2-A3-A3-01 edge break on the 1.2 plate. The review asked 0.6 (GATE_BLADE_EB, on the 2.0
                                # blade it leaves 0.8 of flat); on 1.2 the two 0.6 breaks meet in a knife edge, 0.4 leaves 0.4
    "plate_end_r": 3.0,         # v2-A3-A3-01 plan radius on the plate's free (+X) end corners (A3 square, a snag point at r 48)
}
GATE_DETENT_NOTCH_R = GATE_DETENT["bump_r"] + GATE_DETENT["notch_clr"]           # 1.1
GATE_DETENT_NOTCH_D = GATE_DETENT["bump_h"] + GATE_DETENT["notch_clr"]           # 0.6 deep: 1.4 of blade left under it
GATE_DETENT_NOTCH_X = (GATE_DETENT["x"], GATE_DETENT["x"] - GATE_TRAVEL)         # blade x at the closed pose: closed, open
GATE_DETENT_L = GATE_DETENT["x"] - GATE_DETENT["tab_x"][1]                      # 12.5 free beam length to the bump
GATE_DETENT_LIFT = GATE_DETENT["bump_h"] - GATE_DETENT["gap"]                    # 0.4 deflection riding the blade
GATE_DETENT_STRESS = 3 * 3500.0 * GATE_DETENT["clip"][2] * GATE_DETENT_LIFT / (2 * GATE_DETENT_L ** 2)   # 16.1 MPa (E 3.5 GPa)
ADAPTER_SPOUT_Z0 = GATE_Z[1] + 0.35     # 290.7: spout bottom = blade roof (0.35 over the blade)
VALVE_SCREW_Z = 295.5
VALVE_SCREW_A = (90.0, 180.0, 270.0)    # through the three cheeks into pads inside the spout
SPOUT_PAD_R = 20.5
BAFFLE_R = (10.5, 30.4)         # baffle on the VALVE (jar locked at 0 -> over the outlet sector); outer edge buried in the
                                # skirt (A1 ended on the skirt's own R31 face: coincident facets left 0.02 slivers)
BAFFLE_FLAT = 0.8               # v2-A1-08: the underside ramps stop 0.8 above the baffle bottom (vertical flat at the foot)
BAFFLE_RAMP_TOP = DISC_Z[1] + 5.5       # 276.8: underside ramps start above a 13 mm candy standing in a pocket (4.7 proud)
BAFFLE_EDGE_TOP = 278.0
BAFFLE_ROOF = 35.0              # roof slope toward both edges (candy sheds into the parked pockets)
BAFFLE_TOP = 286.0
FIN_R, FIN_T = 8.8, 2.4         # agitator fins on the disc hub (baffle inner edge 10.5)
SERVO_POCKET = (-85.9, -45.1, 10.4)    # x0 x1 half-y (servo body -85.5..-45.5 x +/-10.07)
COVER_BOX = (-89.6, -42.6, 14.0, IF_SOCKET_Z[1], FEED_SERVO_FACE_Z + 40.0 + 3.9 + 0.4 + 1.8)   # x0 x1 hy z0 z1 (over the idler boss;
                                # v2-A1-10: x0 -1 and hy +1 so the R6 plan corners keep 2.2 over the pocket corners)
COVER_SCREWS = [(-66.0, 18.6), (-66.0, -18.6)]
PLATE_SCREWS = [(0.0, 41.0), (0.0, -41.0)]
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
BUS_JCT = {"d": 10.0, "l": 25.0, "r": 7.0, "az": 35.0, "z0": 74.0}
BUS_JCT_XY = (BUS_JCT["r"] * math.cos(math.radians(BUS_JCT["az"])), BUS_JCT["r"] * math.sin(math.radians(BUS_JCT["az"])))  # (5.73, 4.02)
BUS_JCT_TOP = (BUS_JCT_XY[0], BUS_JCT_XY[1], BUS_JCT["z0"] + BUS_JCT["l"])      # tilt / feeder bus ends (z 99)
BUS_JCT_BOT = (BUS_JCT_XY[0], BUS_JCT_XY[1], BUS_JCT["z0"])                     # CAB_bus_pan end (z 74)
# Bundle/base meeting point: the plan's az 235 / r 4, lowered to z 70 (BUS_JCT z0 - 4). Measured alternatives:
# - (-2.29, -3.28, 76) at the splice height: 2.855 to the splice at home, but the static base end overlaps the moving splice at
#   pan -90 (cad q sweep BUY_bus_junction CAB_launcher_base: -5.09 mm3 at -90, -0.34 at -75; splice centre az -55 is 70 deg
#   from az 235).
# - az 215 / r 6.5 at z 76: 1.46 to the splice over pan -92.5..92.5, but the bundle and base ends drift 9.2 apart at pan +/-90,
#   so the v2-A2-02 rows (base to bundle <= 1.0 at pan +/-90) fail at 3.38 / 3.29.
# At r 4 the two Ø6 ends overlap at every pan (chord 2 x 4 x sin 45 = 5.66 < 6), and at z 70 the static base end sits 3+ under
# the splice bottom (z 74) at every pan, while the moving bundle passes the splice at 2.855 (same body).
BUS_LB_JCT_AZ, BUS_LB_JCT_R = 235.0, 4.0
BUS_LB_JCT = (BUS_LB_JCT_R * math.cos(math.radians(BUS_LB_JCT_AZ)), BUS_LB_JCT_R * math.sin(math.radians(BUS_LB_JCT_AZ)),
              BUS_JCT["z0"] - 4.0)                                              # (-2.29, -3.28, 70)
# v2-A6-02 (attempt 7): the pan bus lead is split on the pan axis at BUS_PAN_AX. The static U-loop (CAB_bus_pan, base) ends
# there, and the PIV_pan tail (CAB_bus_pan_tail, pan_stage) runs from it to the splice's bottom face centre (BUS_JCT_BOT).
# Coaxial ends never open over pan, so the static end no longer sits under an orbiting splice (A6: r 7, 9.9 swing at +/-90).
BUS_PAN_AX = (IF_PAN_XY[0], IF_PAN_XY[1], 63.0)
_HUB_GY, _HUB_GZ = 0.5 * (TT_GROOVE[2] + TT_GROOVE[3]), 0.5 * (TT_GROOVE[4] + IF_TT_Z1)   # groove centre y -17, z 97.8
# hub lists (groove exit -> bore -> end), shared by pan_stage (bundle, tilt bus) and feeder (feeder bus). The bus leads
# cross the junction top at z 100.5 (tube 99.1..101.9: over the top face 99, under the groove cap 102) and drop onto it.
BUS_HUB = [(4.0, _HUB_GY + 8, _HUB_GZ + 0.7), (BUS_JCT_XY[0], -1.5, 100.5), (BUS_JCT_XY[0], BUS_JCT_XY[1], 100.5), BUS_JCT_TOP]
LB_HUB = [(0.0, _HUB_GY + 8, _HUB_GZ - 1), (-1.5, -4.5, 90.0), (BUS_LB_JCT[0], BUS_LB_JCT[1], 80.0), BUS_LB_JCT]
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
COLOUR_B = ["PRT_jar_adapter", "PRT_jar_valve", "PRT_jar_gate", "PRT_feeder_housing", "PRT_feeder_disc",
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
