"""config.json is the single source for every configurable parameter.

Read-tracking shows the engine *consults* config; the override tests show it
*obeys* it; the deletion tests show there is no inline default hiding behind it.
All three are needed -- an engine that reads a key and then ignores the value
would pass the first alone.
"""

import copy
import json
import os
import unittest

from harness import advance, everyone_exports, make_config, new_game, play_out
from engine import Config, Content
from engine.config import repo_root
from engine.errors import MissingConfigKey

#: Parameters this milestone's engine must take from config.json rather than
#: from a literal in the code. Every one is asserted read during a full game.
EXPECTED_READS = {
    "players.min_players",
    "players.max_players",
    "cities.enforce_unique_city_names",
    "content.import_needs_file",
    "content.gazetteer_file",
    "content.questions_file",
    "content.question_set_id",
    "rounds.round_window_hours",
    "rounds.rotations_target",
    "imports.allow_repeat_category_across_cities",
    "imports.allow_repeat_category_for_same_city",
    "imports.reuse_same_need_within_game",
    "exports.max_submissions_per_player_per_import_per_round",
    "exports.importer_may_export_to_own_need",
    "economy.profit_roll",
    "economy.profit_display_decimals",
    "economy.even_split_mode",
    "economy.leaderboard_visible_in_newspaper",
    "facilitator_questions.enabled",
    "facilitator_questions.ask_every_n_rounds",
    "facilitator_questions.max_per_player_per_round",
    "facilitator_questions.fill_second_slot_only_if_no_second_game_action_pending",
}


def raw_config():
    with open(os.path.join(repo_root(), "config.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def config_without(dotted):
    data = copy.deepcopy(raw_config())
    path = dotted.split(".")
    node = data
    for part in path[:-1]:
        node = node[part]
    del node[path[-1]]
    return Config(data, source="config.json minus %s" % dotted)


class ReadTrackingTest(unittest.TestCase):
    def test_the_engine_reads_every_parameter_it_should_from_config(self):
        from engine import views

        config = make_config()
        # One cooperative game, for the winner-pick path and the check-in slots.
        game = new_game(config=config)
        for player_id in sorted(game.players):
            game.checkin(player_id)
        play_out(game)
        views.archive(game)
        # One abandoned game, so the even-split fallback's config is read too.
        lapsed = new_game(config=config)
        while lapsed.phase == "running":
            everyone_exports(lapsed)
            advance(lapsed)

        missing = EXPECTED_READS - set(config.keys_read())
        self.assertEqual(missing, set(), "not read from config.json: %s" % sorted(missing))

    def test_every_key_the_engine_reads_actually_exists_in_config_json(self):
        config = make_config()
        play_out(new_game(config=config))
        data = raw_config()
        for dotted in config.keys_read():
            node = data
            for part in dotted.split("."):
                self.assertIn(part, node, "engine read %r, absent from config.json" % dotted)
                node = node[part]

    def test_config_offers_no_way_to_supply_an_inline_default(self):
        # A `get(key, default)` API is how config values start drifting back
        # into code, so the class deliberately does not have one.
        self.assertFalse(hasattr(Config, "get"))
        self.assertFalse(hasattr(Config, "get_or_default"))


class NoInlineDefaultsTest(unittest.TestCase):
    """Deleting a key must break the engine, not fall back to a literal."""

    def _assert_needs(self, dotted, action):
        config = config_without(dotted)
        with self.assertRaises(MissingConfigKey, msg="%s has an inline default" % dotted):
            action(config)

    def test_round_window_has_no_inline_default(self):
        self._assert_needs("rounds.round_window_hours", lambda c: new_game(config=c))

    def test_rotations_target_has_no_inline_default(self):
        self._assert_needs("rounds.rotations_target", lambda c: new_game(config=c))

    def test_profit_roll_has_no_inline_default(self):
        self._assert_needs(
            "economy.profit_roll", lambda c: play_out(new_game(config=c))
        )

    def test_submission_cap_has_no_inline_default(self):
        def act(config):
            game = new_game(config=config)
            game.submit_export("p2", "something")

        self._assert_needs("exports.max_submissions_per_player_per_import_per_round", act)

    def test_repetition_rule_has_no_inline_default(self):
        self._assert_needs(
            "imports.allow_repeat_category_for_same_city", lambda c: new_game(config=c)
        )

    def test_player_limits_have_no_inline_default(self):
        self._assert_needs("players.max_players", lambda c: new_game(config=c))
        self._assert_needs("players.min_players", lambda c: new_game(config=c))

    def test_question_cadence_has_no_inline_default(self):
        self._assert_needs(
            "facilitator_questions.ask_every_n_rounds", lambda c: new_game(config=c)
        )

    def test_content_paths_have_no_inline_default(self):
        self._assert_needs("content.import_needs_file", lambda c: Content.load(c))


class BehaviourFollowsConfigTest(unittest.TestCase):
    def test_the_round_window_sets_the_length_of_a_round(self):
        for hours in (1, 6, 24, 72):
            game = new_game(rounds__round_window_hours=hours)
            self.assertEqual(game.timer.window.total_seconds(), hours * 3600)
            game.clock.advance(game.timer.window)
            game.tick()
            self.assertEqual(game.current_round, 2)

    def test_a_fractional_round_window_is_honoured(self):
        game = new_game(rounds__round_window_hours=0.5)
        self.assertEqual(game.timer.window.total_seconds(), 1800)

    def test_questions_can_be_switched_off_entirely(self):
        game = new_game(facilitator_questions__enabled=False)
        self.assertIsNone(game.rounds[1].question_id)
        self.assertEqual(
            [s for s in game.checkin("p1")["slots"] if s], []
        )

    def test_question_cadence_is_configurable(self):
        game = new_game(facilitator_questions__ask_every_n_rounds=2)
        asked = {}
        while game.phase == "running":
            asked[game.current_round] = game.rounds[game.current_round].question_id
            everyone_exports(game)
            advance(game)
        self.assertIsNotNone(asked[1])
        self.assertIsNone(asked[2])
        self.assertIsNotNone(asked[3])
        self.assertIsNone(asked[4])

    def test_a_question_is_never_repeated_within_a_game(self):
        game = play_out(new_game())
        asked = [r.question_id for r in game.rounds.values() if r.question_id]
        self.assertEqual(len(asked), len(set(asked)))

    def test_suppressing_questions_for_a_mayor_leaves_the_round_question_asked(self):
        game = new_game(facilitator_questions__max_per_player_per_round=0)
        self.assertIsNotNone(game.rounds[1].question_id)
        self.assertEqual([s for s in game.checkin("p1")["slots"] if s], [])

    def test_more_than_one_question_per_mayor_per_round_is_refused_not_capped(self):
        from engine.errors import ConfigError

        game = new_game(facilitator_questions__max_per_player_per_round=2)
        with self.assertRaises(ConfigError):
            game.checkin("p1")

    def test_the_leaderboard_exposure_policy_comes_from_config(self):
        from engine import views

        shown = new_game(economy__leaderboard_visible_in_newspaper=True)
        hidden = new_game(economy__leaderboard_visible_in_newspaper=False)
        self.assertIn("leaderboard", views.round_briefing(shown, 1))
        self.assertNotIn("leaderboard", views.round_briefing(hidden, 1))

    def test_the_rng_seed_comes_from_config_when_not_overridden(self):
        from engine import GameEngine

        config = make_config(engine__rng_seed=99)
        game = GameEngine(config=config, content=Content.load(config))
        self.assertIn("engine.rng_seed", config.keys_read())
        self.assertEqual(game._seed, 99)

    def test_a_null_seed_means_a_genuinely_random_game(self):
        from engine import GameEngine

        config = make_config(engine__rng_seed=None)
        game = GameEngine(config=config, content=Content.load(config))
        self.assertIsNone(game._seed)


if __name__ == "__main__":
    unittest.main()
