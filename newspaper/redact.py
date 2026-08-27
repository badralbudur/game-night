"""Who the paper may name, and how (spec #21, #28).

Spec #28 says players are identified in the newspaper by city and office only,
never by real name or handle, and that the policy is configurable. Spec #21 says
a non-winning export's origin city is never exposed -- not during the round and
not after it. Those are different rules with different enforcement:

* the handle rule is *absolute over the whole edition*. There is no place in a
  newspaper where a handle is correct, so the check is "does this string appear
  anywhere at all", including in the rendered markdown and in the image.
* the origin rule is *structural*. The engine already makes a losing export's
  city unavailable without a deliberate, reasoned ledger read
  (:mod:`engine.state`), so the paper cannot print one by accident. What it
  *can* do by accident is reprint an export whose own text names its sender --
  a mayor who signed their work -- and publishing that would leak the origin
  just as thoroughly as printing a field would. So a declined export is
  reprinted only if its text names no city in the game
  (:func:`may_reprint_declined`), and the paper says, in character, that it has
  withheld one.

Both are then re-checked over the finished edition by
:func:`assert_edition_is_redacted`, which leans on :mod:`engine.audit` rather
than reimplementing it -- the audit already walks arbitrary payloads, and
running the same tripwire the engine's own tests use is the point.
"""

import re

from engine import audit
from engine.content import normalize_city
from engine.errors import ConfigError, RuleViolation

#: The identity styles this paper knows how to print (spec #28). An unknown
#: style is refused rather than treated as "print whatever": the config key
#: exists to make the paper *more* anonymous later, and a typo in it must not be
#: the thing that makes it less.
IDENTITY_STYLES = {
    "city_mayor_only": {
        "prints": "the city's name and the office of its mayor",
        "never_prints": "a real name, a handle, or a player id",
        "spec": "#28",
    },
}

#: Block role used by :mod:`newspaper.departments` for the reprinted losing
#: exports. Named here because :func:`assert_edition_is_redacted` is what makes
#: the role mean anything.
DECLINED_ROLE = "declined_exports"


def resolve_identity_style(config):
    style = config.require_str("newspaper.player_identity_style")
    try:
        return style, IDENTITY_STYLES[style]
    except KeyError:
        raise ConfigError(
            "config.newspaper.player_identity_style is %r; this paper implements %s "
            "(spec #28)" % (style, sorted(IDENTITY_STYLES))
        )


def cities_named_in(text, cities):
    """Which of ``cities`` this text names, diacritics and case ignored.

    Matching is done on the normalised forms the rest of the engine compares
    cities by (:func:`engine.content.normalize_city`), so "Reykjavik" in an
    export is caught as readily as "Reykjavík".
    """
    if not isinstance(text, str) or not text.strip():
        return []
    haystack = normalize_city(text) if text.strip() else ""
    found = []
    for city in cities:
        needle = normalize_city(city)
        if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(needle), haystack):
            found.append(city)
    return found


def may_reprint_declined(text, cities):
    """Whether a losing export may be printed verbatim (spec #21).

    The paper reprints losing exports because they are the best writing in the
    game and because "The Excess" (see ``NAME.md``) needs them. It does not
    reprint one that names a city: the export text is the one string the paper
    must reproduce exactly, so the only way to keep the origin blind is to
    decline to reproduce it at all.
    """
    return not cities_named_in(text, cities)


def find_printed_identities(engine, strings):
    """Handles and player ids written into any of ``strings`` (spec #28).

    :func:`engine.audit.find_handle_leaks` matches a whole string, which catches
    a ``{"tip_from": "@ada"}`` field but not a handle written into the middle of
    a sentence -- and a sentence is exactly where a handle would end up. So this
    matches as a substring on a word boundary, and it is a function rather than
    a block inside :func:`assert_edition_is_redacted` because the edition is not
    the only rendering of the paper: :mod:`hosting.guard` runs the same check
    over every byte it is about to publish, and running a *second* handle check
    written a second way is how the two would drift.
    """
    problems = {}
    for label, needles in (
        ("handles_printed", sorted(p.handle for p in engine.players.values() if p.handle)),
        ("player_ids_printed", sorted(engine.players)),
    ):
        hits = sorted(
            {
                needle
                for needle in needles
                for text in strings
                if re.search(
                    r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(needle), text
                )
            }
        )
        if hits:
            problems[label] = hits
    return problems


def assert_edition_is_redacted(engine, edition, rendered=None):
    """Raise unless the edition obeys #21, #22, #25 and #28.

    ``rendered`` is the markdown (and any other flat text, such as the SVG) the
    edition was rendered to. It is checked as well as the structured payload,
    because a leak that only exists in the prose is still in the paper.
    """
    payload = {"edition": edition}
    if rendered:
        payload["rendered"] = list(rendered) if isinstance(rendered, (list, tuple)) else [rendered]

    # Handles, ledger misuse, extra timers, and any node tying a non-winning
    # submission to its exporter.
    audit.assert_blind(engine, payload)
    # Anything published that config.json says to withhold (#22, #25).
    audit.assert_exposure_policy(engine, payload)

    strings = list(_all_strings(payload))
    problems = find_printed_identities(engine, strings)

    cities = [p.city for p in engine.players.values()]
    for item in _declined_items(edition):
        named = cities_named_in(item, cities)
        if named:
            problems.setdefault("declined_export_names_a_city", []).append(
                {"export": item, "cities": named, "spec": "#21"}
            )

    if problems:
        raise RuleViolation(
            "identity redaction failed for edition %r: %r"
            % (edition.get("round"), problems)
        )
    return True


def _all_strings(node):
    for value in _walk(node):
        if isinstance(value, str):
            yield value


def _walk(node):
    yield node
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _walk(value)
    elif isinstance(node, (list, tuple)):
        for value in node:
            yield from _walk(value)


def _declined_items(edition):
    """Every reprinted losing export in the edition, by its block role."""
    out = []
    for value in _walk(edition):
        if isinstance(value, dict) and value.get("role") == DECLINED_ROLE:
            out.extend(item for item in value.get("items", []) if isinstance(item, str))
    return out
