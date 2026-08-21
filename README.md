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

Game-flow logic — round timing, the city queue, export collection, blind
voting, scoring, the newspaper and the endgame — is later milestones.
Nothing in this repo implements them yet.
