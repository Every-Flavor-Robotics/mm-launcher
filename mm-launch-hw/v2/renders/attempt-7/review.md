# Review: M&M Launcher Turret v2, attempt 7

Checks re-run: `CADCHECK PASS: 0 fail, 37 warn (0 untriaged, 37 accepted)` on `/tmp/rv7/model.blend` (tools 6025133 from `alex-3d-skills-pin`, the designer's pin; 183 s). Copy: `review/cadcheck.json`. All 16 check sections match the designer's `renders/attempt-7/cadcheck.json` exactly. Only the timing fields differ.
- Coverage: 36 parts. Interference/clearance: 178 objects in all four collections, 5046 pair-poses, 8 joints swept with 2.5 deg overtravel. Fasteners: 103 screws and 4 nuts at 16 poses over 30 steps. Service: 9 ops, 32 accesses. Drop 4, index 6, slide 16, payload 4, sightlines 3. Assembly: 30 steps, 178 placed, 0 in no step. Stacks 4, flexures 2, stability 3456 poses. Cables: 15 routes with length, 3 chains. `distances` has 90 row-poses, all passing, but it is not listed in `coverage`.
- Not checked (quoted): "fasteners: pilot/clearance hole diameters ...; wrench access to nuts", "stability: dynamic loads (recoil, pan acceleration), friction/sliding", "cables: bend radius, slack across joints, connector positions (review by section render)", "not geometric: teardown step count, alignment-jig datums (declare stacks), aesthetics, BOM correctness".
- `unbounded_allows` (5): nip_wheel x leaf, motor x magnet, flywheel x motor, nip_wheel x stud, stud x tw_nut. All five are glued, threaded or preloaded pairs, unchanged since A6. Agreed.
- Review rows: `review/review_rows.json` -> `review/cadcheck_review.json` (`--only slide --overlay-only`). It adds 6 groove-cap exit slides. The forward-up exit at tilt 45 passes (A7-03); the other five are blocked, which is informative but expected.
- `cad bom BOM_AND_ASSEMBLY.md manifest.json`: 18 rows, 0 disagree, 0 modelled screws in no row.
- Measurement log: `review/notes.md`. Renders: `review/r02_sec_y4.02_splice_top_under_groove_cap.png`. That is 2 of the 12 allowed: r01 had the wrong `--keep` side and was deleted.

| Metric | Score | Anchor matched | One-line reason |
|---|---|---|---|
| Functionality | 9 | "Minor polish only ... cadcheck has 0 fails and every warn is explained"; the functionality-9 list is met | All 31 drops land at both stops, flattest 34.5 deg. The swept entry arc now has every station (8.098 / 8.222 / 8.415). The pan lead hands over on the axis (0.011 / 0.008 / 0.013). Two minors remain: the lead dress at the splice top (A7-02) and the off-axis bundle hand-over (A6-02). |
| Manufacturability | 8 | "Works. At most 2 major issues, each with a known fix under 1 hour of CAD and no reprint of a big part" | A6-01 is fixed in order and rows, and the cap has a measured exit path. One new major (A7-01): step 11a needs the pod at tilt 45, but the tilt servo is installed and can't be powered at that step. The fix is BOM text plus a prop. |
| Aesthetics | 9 | "9 needs every item true" | Nothing visible changed since A6: one EB 1.0 / CR 6 set, colour B traces the candy path, and no PCB, wire or motor can shows in iso or iso_front_left (`cables` exposure: only `CAB_usb`, which is in `cables_ok`). |

## Previous issues

| Issue | Status | New number |
|---|---|---|
| A6-01: splice seated in a hub bore that the cap (2c) and the floor (3) had already closed | **FIXED** | `assembly.step_of`: `BUY_bus_junction`, `CAB_bus_pan_tail`, `PRT_groove_cap`, `FST_gcap_*` are all at 11a, after 11, with 0 findings. Service `v2-A6-01 groove cap off`: 6/6 `tilt=45:straight 14`. Cap +Z 40 at tilt 45: min 0.2 (`post_L`). Splice +Z 40 out of the bore: min 1.000 (`hub_gear`). Captive row: blocked at 3.5 by `PRT_groove_cap`. Full exit (review row): forward-up 45 deg x 160 at tilt 45, not blocked, min 0.2. A new issue comes from the fix: the tilt-45 pose (A7-01). |
| A6-02: static pan lead ended under an orbiting splice | **PARTIAL** | Bus lead fixed. `CAB_bus_pan` > tail reads 0.011 / 0.008 / 0.013 at pan -90 / 0 / 90. Tail > launcher base reads 1.362 / 2.789 / 2.430, and `cad q sweep` over -92.5..92.5 gives min 1.236 at -92.5. Tail > hub gear 5.825. Chain 292.1 / 350. Not fixed (deferred by the designer): the bundle/base hand-over is still at r 4. The v2-A2-02 row reads **0.916** / 0.006 / 0.760 against max 1.0 (A6: 0.133 / 0.002 / 0.097), so its margin to failing is now 0.084. |
| A6-03: swept rows missed psi 0 | **FIXED** | Psi 1..105: all 9 swept row-poses carry no `missed_deg`. Bare gap 8.098 @ 63 / 8.222 @ 91 / 8.415 @ 91; tape 7.598 / 7.722 / 7.915; rest 6.175 / 6.494 / 6.986. |

## Measurements

| Item | Value | Source |
|---|---|---|
| Full check | 0 F / 37 W, 0 untriaged, 0 stale, `poses_past_limits` [], identical to the designer's | `review/cadcheck.json` |
| Entry arc at full lift (min / home / max stop) | 8.098 @ psi 63 / 8.222 @ 91 / 8.415 @ 91 (min 8.0); every station hits | `distances` v2-A5-02 |
| Drops | 31/31 hit at every row; flattest 34.5 at tilt 46 | `checks.drop` |
| Index | +60 and -60 give 1 window each; the column is never open at jar drift 0/5/10/15 | `checks.index` |
| Groove cap screws | engagement 6.5; `FST_gcap_5` at home is **blocked at 13.4 by `PRT_launcher_body`** (L-key short leg blocked); reachable only at tilt 45 | `fasteners.rows` FST_gcap_5 |
| Cap exit, tilt 45, (0,-0.707,0.707) x 160 | not blocked, min 0.2 (`post_L`) | review slide row |
| Cap exit, tilt 45, (0,+0.707,0.707) | blocked at 54 by `PRT_nip_cover` | review slide row |
| Cap exit, shallow -Y 15 deg (tilt 0 / 45) | blocked at 10 by `BUY_bus_junction` (the cap's bore spigot) | review slide rows |
| Tilt and feeder bus leads | **-82.484 mm3 overlap** (one coincident tube from (2.7, -10.8, 97.1) to the splice top) | `cad q dist CAB_bus_tilt CAB_bus_feeder` |
| Bus leads to the cap underside | 0.112 / 0.120; the leads cross the splice top at z 100.5 and drop 1.5 mm onto it (`params.BUS_HUB`) | `cad q dist`, `r02` |
| Splice top to cap underside | 3.0 | `r02`, designer's `cad q dist` |
| Tail vs launcher base, pan sweep | 75 stations, min 1.236 @ -92.5 | `cad q sweep CAB_bus_pan_tail CAB_launcher_base PIV_pan -92.5 92.5 2.5` |
| Bundle/base hand-over | 0.916 @ pan -90 (max 1.0) | `distances` v2-A2-02 |
| Lead spare at the hub end | pan 57.9, tilt 93.5, feeder 180.4 | `cables`, `cables.chains` |
| Stability | worst 31.2 deg | `checks.stability` |
| BOM vs model | 18 rows, 0 disagree | `cad bom` |

## Issues (ranked)

**A7-01 (major, manufacturability): step 11a starts with "Tilt the pod to 45", but at that step the tilt servo is installed and can't be powered.**
- The cap needs tilt 45. `FST_gcap_5` (10, 16.2) is blocked at every fastener pose except tilt 45: at home `PRT_launcher_body` blocks it 13.4 above the head, and the L-key's short leg is blocked too.
- Why the servo can't hold or command that pose:
  - The tilt servo has been engaged in the journal-plate socket since step 8.
  - Its bus lead isn't joined to anything until 11a sub-step 4.
  - The battery goes in last, at step 14.
- So "tilt to 45" here means back-driving an unpowered Hiwonder bus servo through its gear train by the pod. That risks stripping the gears, and the pod also has to be held at 45 while 6 screws go in. The BOM gives no method and no holding fixture.
- The splice service op has the same gap whenever the fault being serviced is the splice itself.
- Evidence: `fasteners.rows` FST_gcap_5 `access.home` blocked_at_mm 13.4 by PRT_launcher_body; BOM 11a.1; steps 8 and 14; `review/notes.md`.
- Fix (BOM plus one small STL, no reprint):
  1. At the start of 11a, take the post cover off (4 x M3 x 14, straight 18) and slide the tilt servo out +X about 10 mm. Its 12 AF key engages 6.5 mm, and the existing `tilt servo out +X` slide row covers that move.
  2. Swing the pod freely to 45 and hold it on a printed 45 deg prop: a wedge about 40 x 30 x 30, under the nacelle on the turntable, clear of the groove cap. Add `stl/tools/tilt45_prop.stl`.
  3. Do 11a.
  4. Lower the pod to 0, re-seat the servo key and refit the cover.
  5. Add a `service` row "groove cap at tilt 45 with BUY_servo_tilt slid out" (`remove` [PRT_post_R_cover, FST_postcover_*]) and a `distances` row for the prop to the cap of at least 1.0.
- Alternative: move `FST_gcap_5` out from under the pod, for example to (-30, 16.2), so that all six go in at tilt 0 (straight or L-key). That means reprinting the cap (12.6 g) and drilling one new Ø2.5 pilot in the turntable.

**A7-02 (minor, functionality / cables): the lead dress at the splice top isn't buildable as modelled, and the solder service length has no place to go.**
- `CAB_bus_tilt` and `CAB_bus_feeder` share one tube from the groove to the splice top (-82.5 mm3 overlap).
- Both leads cross the splice top at z 100.5. They are 0.112 / 0.120 from the cap underside, then turn 90 deg down onto the face 1.5 mm below. Two Ø2.8 leads need 5.6 mm side by side, and a zero-radius bend at the heat-shrink exit is the weakest point of the splice. Bend radius is in `not_checked`.
- Step 11a.3-4 makes the splice "above the turntable", about 60 above it. That needs about 85 extra length on the pan lead and about 60 on each of the tilt and feeder leads. After the splice is lowered, this length plus the stock spare (pan 57.9, tilt 93.5, feeder 180.4) has no stated home:
  - the pan excess goes "back into its U-loop", which then becomes about 50 % longer than the modelled +58.2 loop under the pan gears;
  - nothing at all is said about the tilt and feeder excess (about 270 mm).
- Evidence: `cad q dist` lines in `review/notes.md`; `params.BUS_HUB`; `review/r02_sec_y4.02_splice_top_under_groove_cap.png`; `cables` spare.
- Fix:
  1. Shorten `BUS_JCT` `l` 25 -> 20, so the splice is z 74..94. That leaves 8.0 under the cap for the turn, at about R 4.
  2. Route the tilt and feeder leads side by side: offset `BUS_HUB` x by ±1.5 per lead and end them on the top face at ±2.
  3. Add `distances` rows `CAB_bus_tilt` / `CAB_bus_feeder` > `PRT_groove_cap`, min 0.5.
  4. In BOM 11a.4, trim the tilt and feeder leads to "route + 70" and the pan lead to "route + 90" before soldering. Say where the 60-mm service loop lies once the splice is seated: for example, folded into the groove run x 10..60 for the tilt lead, and into the left-post channel for the feeder lead. Back that with a section render.

**A6-02 (minor, functionality / cables, PARTIAL): the launcher bundle/base hand-over is still at r 4 off the pan axis.**
- The bus half is fixed. The Ø6 bundle (3 phases + encoder) still hands over at (-2.29, -3.28, 70), and its moving end swings a 5.66 chord over ±90.
- The v2-A2-02 "meet" row passes only because the two Ø6 sleeves overlap. It now reads 0.916 at pan -90 against a 1.0 maximum (A6: 0.133). The inner leg moved r 3 -> 6.5 to clear the bus tail.
- Evidence: `distances` v2-A2-02 rows (0.916 / 0.006 / 0.760).
- Fix, either of:
  - Give the bundle the same tail treatment: put the hand-over on the axis at about z 55, below `BUS_PAN_AX` z 63. The static bus lead approaches from az 35 and the launcher leg from az 235. Tighten the row to max 0.5.
  - If there is no room, keep r 4, but state the 5.66 chord swing in the row's `why` and add a section at pan ±90 showing the sleeve's bend there.

**A7-03 (minor, check config): the cap-removal evidence stops 40 mm up, under the pod. Some `why` text is stale.**
- The designer's `v2-A6-01 groove cap lifts +Z` row moves the cap 40 mm, which leaves it between the posts under the nip cover (nip cover at z 159 above x 30, y 20 at tilt 45). The BOM says the cap comes off.
- The review row proves the full exit: (0, -0.707, 0.707) x 160 at tilt 45, not blocked, min 0.2.
- The checks.json `why` text of the v2-A6-02 rows says "z 64" and "r 6", while the model has 63 and 6.5. The designer already listed this.
- Evidence: `review/cadcheck_review.json` "R7 A7-01 groove cap leaves the machine forward-up".
- Fix: adopt that row from `review/review_rows.json` into checks.json, and correct the two `why` strings.

## Check-config audit
- **allow** (11): agreed, unchanged since A6. `unbounded_allows` lists 5 pairs, each glued or threaded (agreed).
- **fits** (33): agreed. `post_R x journal_plate` still has no `contact_normal`; this tool-limit deferral is agreed.
- **distances**:
  - v2-A6-02 rows: agreed (`why` text stale, A7-03).
  - v2-A2-02 base > bundle `max 1.0`: disputed as evidence that the two ends meet. It passes on sleeve overlap (A6-02).
  - The swept entry-arc rows (psi 1..105) are agreed.
- **accepted_warns** (37): agreed. Both new ones are reasoned:
  - `FST_gcap_5 reachable only at tilt=45`, but the pose isn't reachable at that step without a method (A7-01);
  - `no lead length: CAB_bus_pan_tail` is covered by the chain row.
- **drop_tests**: agreed (both stops x tilt -3..46, 7.0 and 7.5 candies).
- **index_tests / service / slide_out vs the BOM (A2-F2):**
  - Every BOM motion or service claim has a matching row: index +60 / -60 one window each, and the column never open at drift 0..15; leaf, pod cover, pinch bolts and encoder at tilt 45; tilt servo +X 60; feeder servo and lobe cover +Z; base floor -Z 40; refill (jar, gate, stops); battery +X 120; pod lift-out at tilt 20; thumbwheel sightlines; the new 11a service and three slides.
  - The one claim without a full row was "the cap comes off". I added it, and it passes (A7-03).
  - No row or pose covers how the pod reaches tilt 45 at assembly step 11a (A7-01).
- **assembly_order**: matches BOM steps 1..14 with 11a. `assembly.step_of` places all 178 objects.

## What is good
- A6-01 is fixed by order, not by geometry. The cap, its screws, the splice and the tail all move to 11a, and each sub-step cites a row. Every number re-ran exactly.
- The pan lead now hands over on the axis. The designer modelled the launcher-leg conflict first (`tail_feasibility.py`) and moved the leg, rather than accepting a warn.
- The swept rows now start at psi 1, all 9 row-poses are complete, and the BOM quotes the whole profile.
- `cad bom` is clean. There are 0 untriaged warns, and the designer listed their own stale `why` text as not met.
