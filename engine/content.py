"""Loading and drawing from the seeded game content (spec #13, #14, #33).

The content itself (import needs, gazetteer, mayor questions) was produced in
M1 and lives in ``content/``. This module only loads it and implements the
*draw* rules: which needs a given city is still eligible to receive, and which
questions have not been asked yet.

File locations come from config.json (``content.*_file``) -- the engine does not
know the paths.
"""

import json
import os
import unicodedata

from .config import repo_root
from .errors import ContentError, NoEligibleImportNeed

SOURCE_SEED = "seed"
SOURCE_PLAYER = "player"


def normalize_city(name):
    """Fold a city name to a comparison key, per gazetteer.resolution_rules.

    Case-folded, trimmed, diacritics stripped, internal whitespace collapsed.
    A parenthetical qualifier is *kept* -- "Athens (Georgia)" and "Athens" are
    deliberately different keys, because treating them as one puts a mayor on
    the wrong continent.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("city name must be a non-empty string, got %r" % (name,))
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(stripped.casefold().split())


def _read_json(path, what):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise ContentError("%s not found at %s" % (what, path))
    except ValueError as exc:
        raise ContentError("%s at %s is not valid JSON: %s" % (what, path, exc))


class Content:
    """The seeded content, plus anything players added during play."""

    def __init__(self, needs, categories, questions, gazetteer, root):
        self.needs = list(needs)
        self.categories = {c["id"]: c for c in categories}
        self.questions = list(questions)
        self.gazetteer = gazetteer
        self.root = root
        self._validate()

    @classmethod
    def load(cls, config, root=None):
        root = root or repo_root()
        needs_doc = _read_json(
            os.path.join(root, config.require_str("content.import_needs_file")),
            "import needs",
        )
        gaz_doc = _read_json(
            os.path.join(root, config.require_str("content.gazetteer_file")), "gazetteer"
        )
        q_doc = _read_json(
            os.path.join(root, config.require_str("content.questions_file")), "questions"
        )
        expected_set = config.require_str("content.question_set_id")
        if q_doc.get("set_id") != expected_set:
            raise ContentError(
                "questions file declares set_id %r but config.content.question_set_id "
                "is %r" % (q_doc.get("set_id"), expected_set)
            )
        return cls(
            needs=needs_doc.get("needs", []),
            categories=needs_doc.get("categories", []),
            questions=q_doc.get("questions", []),
            gazetteer=gaz_doc,
            root=root,
        )

    def _validate(self):
        if not self.needs:
            raise ContentError("import-need list is empty; spec #13 needs a seeded list")
        if not self.questions:
            raise ContentError("question bank is empty; spec #24 needs a seeded set")
        seen = set()
        for need in self.needs:
            for field in ("id", "category", "need_brief", "exporter_prompt"):
                if not need.get(field):
                    raise ContentError("import need %r is missing %r" % (need.get("id"), field))
            if need["id"] in seen:
                raise ContentError("duplicate import-need id %r" % need["id"])
            seen.add(need["id"])
            if need["category"] not in self.categories:
                raise ContentError(
                    "import need %r references unknown category %r"
                    % (need["id"], need["category"])
                )
        q_seen = set()
        for question in self.questions:
            if not question.get("id") or not question.get("text"):
                raise ContentError("question %r is missing id/text" % (question.get("id"),))
            if question["id"] in q_seen:
                raise ContentError("duplicate question id %r" % question["id"])
            q_seen.add(question["id"])

    # -- import needs -----------------------------------------------------

    def add_player_need(self, need):
        """Append a player-suggested need (spec #13)."""
        need = dict(need)
        need.setdefault("source", SOURCE_PLAYER)
        if need.get("category") not in self.categories:
            raise ContentError(
                "player-suggested need %r must use a known category; got %r"
                % (need.get("id"), need.get("category"))
            )
        if any(existing["id"] == need.get("id") for existing in self.needs):
            raise ContentError("import-need id %r already exists" % need.get("id"))
        self.needs.append(need)
        self._validate()
        return need

    def eligible_needs(
        self,
        used_need_ids,
        categories_used_by_city,
        categories_used_anywhere,
        allow_repeat_for_same_city,
        allow_repeat_across_cities,
        allow_need_reuse,
    ):
        """Needs a city may still be given, per spec #14 and its config knobs.

        ``categories_used_by_city`` is the set of categories that *this* city has
        already imported. ``categories_used_anywhere`` is every category drawn so
        far in the game -- only consulted when config forbids cross-city repeats.
        """
        out = []
        for need in self.needs:
            if not allow_need_reuse and need["id"] in used_need_ids:
                continue
            category = need["category"]
            if not allow_repeat_for_same_city and category in categories_used_by_city:
                continue
            if not allow_repeat_across_cities and category in categories_used_anywhere:
                continue
            out.append(need)
        return out

    def draw_need(self, rng, city, **rules):
        candidates = self.eligible_needs(**rules)
        if not candidates:
            raise NoEligibleImportNeed(
                "no import need left for %s under the current repetition rules "
                "(spec #14 / config.imports)" % city
            )
        # Sorted first so the draw depends only on the seed, never on dict or
        # file ordering that a content edit could quietly change.
        candidates.sort(key=lambda n: n["id"])
        return rng.choice(candidates)

    def need_by_id(self, need_id):
        for need in self.needs:
            if need["id"] == need_id:
                return need
        raise ContentError("unknown import need %r" % need_id)

    def render_need(self, need, city):
        """Substitute the declared placeholders (content/import_needs.json)."""
        def sub(text):
            return (text or "").replace("{city}", city).replace("{mayor}", "the Mayor of %s" % city)

        return {
            "title": need.get("title", ""),
            "need_brief": sub(need.get("need_brief")),
            "exporter_prompt": sub(need.get("exporter_prompt")),
        }

    # -- questions --------------------------------------------------------

    def draw_question(self, rng, asked_ids):
        """One unasked question (content/questions.json asking_rules)."""
        remaining = sorted(
            (q for q in self.questions if q["id"] not in asked_ids), key=lambda q: q["id"]
        )
        if not remaining:
            return None
        return rng.choice(remaining)

    def question_by_id(self, question_id):
        for question in self.questions:
            if question["id"] == question_id:
                return question
        raise ContentError("unknown question %r" % question_id)

    # -- gazetteer --------------------------------------------------------

    def gazetteer_entry(self, city):
        key = normalize_city(city)
        for entry in self.gazetteer.get("cities", []):
            if normalize_city(entry["name"]) == key:
                return entry
            if any(normalize_city(alias) == key for alias in entry.get("aliases", [])):
                return entry
        return None

    def nearby_names(self, city):
        entry = self.gazetteer_entry(city)
        return list(entry.get("nearby", [])) if entry else []
