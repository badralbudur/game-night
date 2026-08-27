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
| **M3** — economy: profit rolls, leaderboard, exposure ([`engine/economy.py`](engine/economy.py)) | built — see [`docs/m3-economy.md`](docs/m3-economy.md) |
| **M4** — facilitator questions: two-slot check-in, framing, aggregate data ([`engine/aggregate.py`](engine/aggregate.py)) | built — see [`docs/m4-questions.md`](docs/m4-questions.md) |
| **M5** — newspaper rendering core: prose, redaction, tone, one image per edition ([`newspaper/`](newspaper), [`content/newspaper.json`](content/newspaper.json)) | built — see [`docs/m5-newspaper.md`](docs/m5-newspaper.md) |
| **M6** — publication & archive: the private address, the browsable back issues, the curated public manifest ([`hosting/`](hosting), [`site/`](site)) | built — see [`docs/m6-hosting.md`](docs/m6-hosting.md) |

The engine covers the round timer and its lockstep, the city order queue and its
two rotations, the import/export/winner cycle with every fallback, the import
repetition rule, blind-voting data handling, the economy — profit rolls, the
cumulative per-city leaderboard, and the exposure policy around both — and the
mayor questions: the two-slot check-in, the framing rules, and what a round's
answers add up to.

The newspaper turns that into **The Daily Manifest**: one edition per completed
round, written from the frames in [`content/newspaper.json`](content/newspaper.json),
with mayors named by city and office only, the aggregate item written in wording
the arithmetic actually licenses, and one image per edition. Run the tests with:

```
python3 run_tests.py
```

A rendered twelve-round sample game is committed at
[`editions/sample-game/`](editions/sample-game) —
[`index.md`](editions/sample-game/index.md) is its archive index. This
deployment has no image-generation provider configured, so every edition uses
the permitted deterministic SVG fallback and records that in its own
`image.provenance`.

[`hosting/`](hosting) publishes those editions as the paper itself: one fixed,
unguessable, `noindex` address with every back issue still browsable at it
(spec #26–#27). The built site is committed at [`site/`](site) —
`site/public/` is exactly what is served and
[`site/publication-manifest.json`](site/publication-manifest.json) records why
each file in it is public. The address is **not** in any of it, and is not in
this repo: it lives in a `0600`, git-ignored `.site-id`, and the build refuses
to publish anything containing it. Serve it with `python3 -m hosting.serve`,
which prints the URL.

Still later milestones: the endgame articles and per-city portraits (spec
#31–#32), and the duplicate-city reassignment procedure. Where the engine's data
would otherwise carry a finished piece it does not own yet, it carries an
explicit `[[M… ]]`-style stub instead.
