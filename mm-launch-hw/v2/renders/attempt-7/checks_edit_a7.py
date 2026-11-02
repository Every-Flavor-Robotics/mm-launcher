import json, sys
path = sys.argv[1]
s = open(path).read()
c = json.loads(s)
about_line = [l for l in s.splitlines() if l.startswith(' "_about"')][0]

c["_about"] += (" Attempt 7: rows tagged v2-A6-NN close issues from ../renders/attempt-6/review.md. The bus splice and the groove cap "
                "move to assembly step 11a (after the feeder is on the beam, pod at tilt 45): every bus lead reaches the turntable "
                "groove only after steps 8 / 9 / 11, so the cap that closes the groove and the hub bore goes on last (A6-01). "
                "CAB_bus_pan is split at the pan axis into the static U-loop (CAB_bus_pan, step 3) and a PIV_pan tail "
                "(CAB_bus_pan_tail, step 11a) ending on the splice's bottom face; cable_chains 'pan bus lead' sums both (A6-02). "
                "The swept entry-arc rows start at psi 1 (psi 0 at full lift is past the hood's entry edge at home / max; A6-03).")

# ---- A6-01 assembly order: groove cap + splice to a new step 11a
ao = c["assembly_order"]
for st in ao:
    if st["step"].startswith("2c "):
        st["step"] = "2c turntable on the bench: posts from the turntable underside (v2-A6-01: the groove cap goes on at 11a, after every bus lead is in the groove)"
        st["objects"] = [o for o in st["objects"] if o not in ("PRT_groove_cap", "FST_gcap_*")]
    if st["step"].startswith("3 "):
        st["objects"] = ["CAB_bus_pan" if o == "CAB_bus_pan*" else o for o in st["objects"]]
    if st["step"].startswith("10d "):
        st["step"] = "10d feeder upright: bus into the channel, servo cover (2 csk); the feeder bus hangs free until 11a (v2-A6-01)"
        st["objects"] = [o for o in st["objects"] if o != "BUY_bus_junction"]
i11 = [i for i, st in enumerate(ao) if st["step"].startswith("11 ")][0]
ao.insert(i11 + 1, {
    "step": "11a pod at tilt 45, groove cap still off (v2-A6-01): tilt / feeder bus leads into the turntable groove; pan lead pulled up the "
            "hub bore; 3-way splice soldered and heat-shrunk above the turntable, then lowered into the hub bore to z 74 at az 35 "
            "(BUY_bus_junction, BOM 14a, with the PIV_pan tail of the pan lead, CAB_bus_pan_tail); groove cap on (6 x M3 x 10 csk)",
    "objects": ["BUY_bus_junction", "CAB_bus_pan_tail", "PRT_groove_cap", "FST_gcap_*"]})

# ---- A6-01 service: groove cap off at tilt 45
c["service"].append({
    "op": "v2-A6-01 groove cap off for the bus splice (BOM 11a / 14a): pod at tilt 45, 6 x M3 x 10 csk with a straight bit (review 6: reach 14)",
    "pose": {"PIV_tilt": 45},
    "fasteners": ["FST_gcap_*"]})

# ---- A6-01 slide rows
GC_IGN = ["CAB_*"]
c["slide_out"] += [
    {"name": "v2-A6-01 groove cap lifts +Z off the turntable at tilt 45 after its 6 screws (BOM 11a reversed; review 6 row: 0.2 to post_L) [0.00 is the seat]",
     "objects": ["PRT_groove_cap", "FST_gcap_*"], "ignore": GC_IGN, "pose": {"PIV_tilt": 45},
     "dir": [0, 0, 1], "dist": 40, "step": 1, "min_clearance": 0.0},
    {"name": "v2-A6-01 bus splice lowered into the hub bore to its seat (z 74, az 35) with the groove cap off, pod at tilt 45 (BOM 11a, reversed: +Z 40 out of the bore) [0.00 is the seat]",
     "object": "BUY_bus_junction", "ignore": ["CAB_*", "PRT_groove_cap", "FST_gcap_*"], "pose": {"PIV_tilt": 45},
     "dir": [0, 0, 1], "dist": 40, "step": 1, "min_clearance": 0.0},
    {"name": "v2-A6-01 the refitted groove cap keeps the splice captive: BUY_bus_junction +Z is stopped by PRT_groove_cap within 3-4 mm (splice top z 99, cap underside z 102)",
     "object": "BUY_bus_junction", "ignore": ["CAB_*"], "dir": [0, 0, 1], "dist": 10, "step": 0.5, "min_clearance": 0.0,
     "expect": "blocked", "blocked_by": ["PRT_groove_cap"], "at_mm": [2.0, 4.5]},
]

c["accepted_warns"].append({"match": "FST_gcap_5 reachable only at tilt=45",
    "why": "v2-A6-01 (attempt 7): the groove cap goes on at step 11a with the pod at tilt 45 (BOM 11a); the service row 'v2-A6-01 groove cap off' reaches all 6 FST_gcap_* with a straight bit (14) at tilt 45. At tilt 0 the pod hangs over FST_gcap_5"})

# ---- A6-02 tail rows + chain
P3 = [{"PIV_pan": -90}, {"PIV_pan": 0}, {"PIV_pan": 90}]
c["distances"] += [
    {"a": "CAB_bus_pan", "b": "CAB_bus_pan_tail", "max": 1.0, "poses": P3,
     "why": "v2-A6-02 (attempt 7) the static pan bus lead (U-loop) and its PIV_pan tail meet near the pan axis at every pan: the joint sits ON the pan axis at z 64 (params BUS_PAN_AX), so the two ends stay coaxial at every pan (chord 0) (A6: the static end sat 1.2 under a splice at r 7 whose bottom centre swings 9.9 over +/-90)"},
    {"a": "CAB_bus_pan_tail", "b": "CAB_launcher_base", "min": 1.0, "poses": P3,
     "why": "v2-A6-02 (attempt 7) the moving pan-bus tail keeps off the static launcher base lead (its meeting point at az 235 r 4 z 70 and its inner U leg, moved r 3 -> r 6 to clear the axis) over the pan range"},
    {"a": "CAB_bus_pan_tail", "b": "PRT_hub_gear", "min": 1.0,
     "why": "v2-A6-02 (attempt 7) the tail rises to the splice inside the R13 hub-gear bore"},
]
c["cable_chains"].append({
    "name": "pan bus lead (BOM item 14, CAB_bus_pan 350)",
    "cables": ["CAB_bus_pan", "CAB_bus_pan_tail"], "lead": 350,
    "why": "v2-A6-02 (attempt 7): one Hiwonder 350 lead, controller to the splice; the static U-loop and the PIV_pan tail are the same wire, split at the pan axis so the last stretch turns with the splice"})

# ---- A6-03 swept rows from psi 1
n = 0
for d in c["distances"]:
    sw = d.get("ray", {}).get("sweep")
    if sw and "v2-A5-02" in d.get("why", "") and sw.get("from") == 0 and sw.get("to") == 104:
        sw["from"], sw["to"] = 1, 105
        d["why"] += ". v2-A6-03 (attempt 7): the sweep runs psi 1..105 so all 53 stations land on the hood at all 3 settings (psi 0 at full lift is past the hood's entry edge at home and the max stop: missed_deg [0] in A6); BDC stays covered by the v2-A3-A2-01 rows"
        n += 1
assert n == 3, n

t = json.dumps(c, indent=1)
new_about = json.dumps({"_about": c["_about"]}, indent=1, ensure_ascii=False).splitlines()[1] + ","
t = "\n".join(new_about if l.startswith(' "_about"') else l for l in t.splitlines())
json.loads(t)
open(path, "w").write(t + ("\n" if s.endswith("\n") else ""))
print("ok", n)
