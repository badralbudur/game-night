# Sister Cities (deliverable repo)

This is the **deliverable** for the game-night-harness project — the
actual game being built, not the harness that builds it.

The game is **Sister Cities**. Its in-fiction newspaper is **The Daily
Manifest**. See [`NAME.md`](NAME.md) for why, and [`content/`](content)
for the seeded game content (import needs, city gazetteer, mayor
questions). All configurable parameters live in
[`config.json`](config.json).

- Harness (process, spec, decisions): https://github.com/badralbudur/game-night-harness
- This repo tracks the deliverable's own build history independently, per
  spec requirement #35 (no shared git history with the harness repo).

Work lands here one commit per harness run/milestone attempt, per spec
requirement #35's git policy. The Coordinator owns that commit; the
Generator writes the files and the Evaluator grades them.

The requirements this deliverable is built against live in the harness
repo's `spec.md` — deliberately not mirrored here, so there is exactly
one authoritative copy and no chance of grading against a stale
snapshot.

## What exists so far

| Milestone | Status |
| --- | --- |
| **M1** — seeded game content ([`content/`](content), [`NAME.md`](NAME.md)) | built |
| **M2** — core round-flow engine ([`engine/`](engine), [`tests/`](tests)) | built — see [`docs/m2-engine.md`](docs/m2-engine.md) |

The engine covers the round timer and its lockstep, the city order queue and its
two rotations, the import/export/winner cycle with every fallback, the import
repetition rule, and blind-voting data handling. Run its tests with:

```
python3 run_tests.py
```

Still later milestones: the newspaper and its private hosting, generated images,
the phrasing and aggregation of mayor questions, the endgame articles and
per-city portraits, and the duplicate-city reassignment procedure. The engine
marks each of those with an explicit `[[M5 ...]]`-style stub where its data
would otherwise carry the finished thing.
