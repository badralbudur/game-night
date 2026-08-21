"""Read-only projections of game state for consumers outside the engine.

Two audiences, two functions, and the difference between them is the whole
point:

* :func:`importer_ballot` -- what the mayor who opened an import need sees while
  voting. Refs and export text. No cities (spec #18).
* :func:`round_briefing` / :func:`archive` -- the *facts* the newspaper milestone
  will write from. Winners are named; everyone else's submission appears with its
  origin withheld, permanently (spec #21).

These are data, not prose. Headlines, copy, images and the aggregate phrasing of
mayor answers belong to M5/M6; every place one is due carries an explicit
``[[M5 ...]]``/``[[M6 ...]]`` stub so a missing piece reads as a milestone
boundary rather than as finished work.
"""

from . import ballot, money
from .errors import PickRejected
from .state import (
    COLLECTING,
    PICKING,
    RESOLVED,
    READ_WINNER_REVEAL,
)

ORIGIN_WITHHELD = "withheld"


def importer_ballot(engine, player_id, need_key=None):
    """The blind ballot for the need this mayor must resolve (spec #18)."""
    need = engine.picking_need_for(player_id) if need_key is None else engine.needs.get(need_key)
    if need is None:
        raise PickRejected("no import need is awaiting a pick from %r" % player_id)
    if need.importing_player_id != player_id:
        raise PickRejected(
            "only the importing mayor of %s sees that ballot" % need.importing_city
        )
    return {
        "need": need.need_key,
        "importing_city": need.importing_city,
        "need_brief": need.rendered["need_brief"],
        "closes_at": engine.rounds[engine.current_round].ends_at.isoformat(),
        "entries": ballot.build(engine.submissions_for(need.need_key)),
    }


def _submission_line(engine, submission, reveal):
    """One submission as the outside world may see it.

    Built from a whitelist. A winner's city is named; a non-winner has no city
    field at all -- not ``None``, not an id, absent -- so there is nothing for a
    downstream template to accidentally render.
    """
    line = {
        "ballot_ref": submission.ballot_ref,
        "export": submission.text,
        "won": bool(submission.is_winner),
    }
    if reveal and submission.is_winner:
        line["origin_city"] = engine.ledger.city_for(
            submission.submission_id, READ_WINNER_REVEAL
        )
    else:
        line["origin"] = ORIGIN_WITHHELD
    return line


def need_briefing(engine, need):
    """One import need's public record, redacted for its current status."""
    submissions = engine.submissions_for(need.need_key)
    out = {
        "need": need.need_key,
        "importing_city": need.importing_city,
        "importing_mayor": engine.players[need.importing_player_id].mayor,
        "category": need.category,
        "title": need.rendered["title"],
        "need_brief": need.rendered["need_brief"],
        "opened_round": need.opened_round,
        "closed_round": need.closed_round,
        "resolved_round": need.resolved_round,
        "rotation": need.rotation,
        "status": need.status,
    }
    if need.status == COLLECTING:
        # Nothing about live submissions is public -- not even how many, which
        # would tell a watching mayor whether their export was the only one.
        out["submissions"] = []
        out["note"] = "export window open; submissions are not public until resolved"
        return out
    if need.status == PICKING:
        out["submissions"] = []
        out["note"] = "awaiting the importing mayor's pick; nothing is published yet"
        return out

    reveal = need.status == RESOLVED
    out["submissions"] = [_submission_line(engine, s, reveal) for s in submissions]
    resolution = dict(need.resolution or {})
    out["resolution"] = resolution
    if resolution.get("mode"):
        # Already rendered exactly at resolution time -- see engine.money.
        out["profit_awarded"] = resolution["awards"]
    return out


def round_briefing(engine, round_index):
    """The facts of one round -- the input to one newspaper edition (spec #26)."""
    record = engine.rounds[round_index]
    briefing = {
        "round": record.index,
        "starts_at": record.starts_at.isoformat(),
        "ends_at": record.ends_at.isoformat(),
        "lockstep": [dict(event) for event in record.events],
        "opened": None,
        "closed": None,
        "resolved": None,
        "mayor_question": None,
        "newspaper": {
            "edition_stub": "[[M5: edition for round %d -- headline, copy and one "
                            "generated image go here]]" % record.index,
        },
    }
    for event in record.events:
        if event.get("need") is None:
            continue
        need = engine.needs[event["need"]]
        if event["op"] == "OPEN":
            briefing["opened"] = need_briefing(engine, need)
        elif event["op"] == "CLOSE":
            briefing["closed"] = {
                "need": need.need_key,
                "importing_city": need.importing_city,
                "submission_count": event.get("submissions", 0),
            }
        elif event["op"] == "RESOLVE":
            briefing["resolved"] = need_briefing(engine, need)

    if record.question_id is not None:
        question = engine.content.question_by_id(record.question_id)
        briefing["mayor_question"] = {
            "question_id": question["id"],
            "text": question["text"],
            "newspaper_hook": question.get("newspaper_hook"),
            # Answers are keyed by city, never by handle (spec #28).
            "answers_by_city": {
                engine.players[pid].city: answer for pid, answer in record.answers.items()
            },
            "answered": len(record.answers),
            "asked_of": sum(1 for p in engine.players.values() if p.joined_round <= record.index),
            "aggregate_phrasing_stub": "[[M5/M6: aggregate these into 'the world' / "
                                       "'most nations' / 'some countries' phrasing]]",
        }
    if engine.config.require_bool("economy.leaderboard_visible_in_newspaper"):
        briefing["leaderboard"] = engine.leaderboard()
    return briefing


def archive(engine):
    """Every edition so far, oldest first (spec #27 -- an archive, not an overwrite)."""
    return {
        "game": "Sister Cities",
        "publication": "The Daily Manifest",
        "editions": [round_briefing(engine, index) for index in sorted(engine.rounds)],
        "phase": engine.phase,
        "hosting_stub": "[[M5: unguessable subdomain + robots noindex, per the "
                        "fulcra-dashboard pattern (spec #26)]]",
    }


def standings(engine):
    decimals = engine.config.require_int("economy.profit_display_decimals")
    total = sum(p.cumulative_profit for p in engine.players.values())
    return {
        "leaderboard": engine.leaderboard(),
        "total_profit_awarded": money.to_json(total, decimals),
    }
