"""Read-only projections of game state for consumers outside the engine.

Two audiences, two functions, and the difference between them is the whole
point:

* :func:`importer_ballot` -- what the mayor who opened an import need sees while
  voting. Refs and export text. No cities (spec #18).
* :func:`round_briefing` / :func:`archive` -- the *facts* the newspaper milestone
  will write from. Winners are named; everyone else's submission appears with its
  origin withheld, permanently (spec #21).

* :func:`newspaper_mayor_question` -- the round's question item, gated by the
  configured exposure policy, carrying the aggregate as *numbers* (see
  :mod:`engine.aggregate`) rather than as a sentence.

These are data, not prose. Headlines, copy, images and the wording of the
aggregate item belong to M5; every place one is due carries an explicit
``[[M5 ...]]``-style stub so a missing piece reads as a milestone boundary
rather than as finished work.
"""

from . import ballot, money
from .economy import NON_WINNER_ORIGIN_EXPOSURE
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


def newspaper_leaderboard(engine):
    """The leaderboard as the newspaper may print it, or ``None`` (spec #22).

    The single place the exposure decision is taken. Every newspaper-facing
    payload asks this rather than reading the config key itself, so switching
    ``economy.leaderboard_visible_in_newspaper`` off cannot be defeated by one
    view that forgot to check.
    """
    return engine.leaderboard() if engine.economy.leaderboard_visible else None


def newspaper_mayor_question(engine, round_index):
    """The round's question item as the newspaper may print it, or ``None``.

    The one place ``facilitator_questions.answers_shared_in_newspaper`` (spec
    #25's "shared in the newspaper by default (not private)") is consulted, for
    the same reason :func:`newspaper_leaderboard` is the only place the
    leaderboard exposure decision is taken: an exposure policy enforced in two
    views is an exposure policy one of them will forget.

    The payload is the full aggregate report -- the distribution, the selected
    outcome and the wordings that outcome licenses (spec #25's data side). The
    sentence written from it is M5's. Answers are keyed by city throughout
    (spec #28), and nothing here touches the export side of the game: the
    questions channel and the blind-voting channel never cross-reference each
    other (#18, #21).
    """
    shared = engine.config.require_bool("facilitator_questions.answers_shared_in_newspaper")
    if not shared:
        return None
    return engine.mayor_question_report(round_index)


def facilitator_question_report(engine, round_index):
    """The facilitator's view of a round's question -- **not** a newspaper payload.

    Complete regardless of the exposure policy, for the same reason
    :func:`standings` is: the facilitator runs the game and needs to see what
    came back whether or not the paper prints it. ``newspaper_visible`` says at a
    glance that this is not the gated view -- that one is
    :func:`newspaper_mayor_question`.
    """
    report = engine.mayor_question_report(round_index)
    if report is None:
        return None
    return dict(
        report,
        audience="facilitator",
        newspaper_visible=engine.config.require_bool(
            "facilitator_questions.answers_shared_in_newspaper"
        ),
    )


def _submission_line(engine, submission, reveal):
    """One submission as the outside world may see it.

    Built from a whitelist. A winner's city is named; a non-winner has no city
    field at all -- not ``None``, not an id, absent -- so there is nothing for a
    downstream template to accidentally render.

    ``reveal`` only ever widens as far as *winners*. There is no argument, and
    no config key, that names a losing export's city: spec #21 is absolute, and
    :data:`engine.economy.NON_WINNER_ORIGIN_EXPOSURE` records that on purpose.
    """
    line = {
        "ballot_ref": submission.ballot_ref,
        "export": submission.text,
        "won": bool(submission.is_winner),
    }
    if NON_WINNER_ORIGIN_EXPOSURE:  # pragma: no cover - False, permanently (#21)
        raise AssertionError(
            "engine.economy.NON_WINNER_ORIGIN_EXPOSURE was flipped on; spec #21 "
            "does not permit a losing export's origin to be published"
        )
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

    briefing["mayor_question"] = newspaper_mayor_question(engine, round_index)
    leaderboard = newspaper_leaderboard(engine)
    if leaderboard is not None:
        briefing["leaderboard"] = leaderboard
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
    """The facilitator's own view of the economy -- **not** a newspaper payload.

    Always complete, regardless of ``economy.leaderboard_visible_in_newspaper``:
    the facilitator runs the game and needs the totals whether or not the paper
    prints them. It carries ``newspaper_visible`` so a caller building an
    edition can see at a glance that this is not the gated view it wants --
    that one is :func:`newspaper_leaderboard`.
    """
    economy = engine.economy
    total = sum(p.cumulative_profit for p in engine.players.values())
    return {
        "audience": "facilitator",
        "newspaper_visible": economy.leaderboard_visible,
        "leaderboard": engine.leaderboard(),
        "total_profit_awarded": money.to_json(total, economy.decimals),
        "economy": economy.describe(),
    }
