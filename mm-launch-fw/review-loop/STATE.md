# Review loop state

Rounds: 3 max. Rounds 1 and 2 always run; round 3 runs only if review 2 says CONTINUE.

Snapshots: /tmp/mml-snap-<N> (round N output; snap-0 is the first pass).

| Round | Phase | Result |
|---|---|---|
| 1 | done | CONTINUE: R1-01 BLOCKER (cal abort race), R1-02/03 MAJOR, 13 MINOR (review-1.md) |
| 2 | done | CONTINUE: R2-01 MAJOR (stop ramps at fw ramp, up to ~140 s); R2-02..07 MINOR (review-2.md) |
| 3 | done | DONE: 0 BLOCKER/MAJOR, 3 MINOR (R3-01..03), bring-up watch list in review-3.md |
