"""Sister Cities -- the round-flow engine.

Milestones M2-M3. Implements the round timer and lockstep (spec #9-#12), the
city order queue and its two rotations (#4, #5, #12), the import/export/winner
cycle with all three fallback paths (#15-#19), the import repetition rule (#14),
blind-voting data handling (#18, #21), and the economy -- profit rolls, the
cumulative per-city leaderboard, and the exposure policy around both (#20-#22,
see :mod:`engine.economy`).

Not here yet, by design: newspaper prose and hosting (M5), generated images,
facilitator-question phrasing and aggregation (M6/M7), endgame articles (M7),
and the duplicate-city reassignment procedure (the join milestone -- this engine
refuses a collision and hands the candidate list to whoever catches
:class:`~engine.errors.DuplicateCity`). Every point where later prose is due
carries a ``[[M5 ...]]``-style stub in the data.

Typical use::

    from engine import GameEngine
    game = GameEngine()                       # reads config.json + content/
    game.register_player("p1", "@ada", "Reykjavík", is_facilitator=True)
    game.register_player("p2", "@bo", "Valparaíso")
    game.register_player("p3", "@cy", "Hobart")
    game.start()
    game.checkin("p2")                        # -> two slots
    game.submit_export("p2", "A far side, pre-assembled.")
    game.tick(later)                          # the one timer moves the game
"""

from .config import Config
from .content import Content
from .economy import Economy
from .errors import GameError
from .game import LOCKSTEP_OPS, GameEngine

__all__ = ["GameEngine", "Config", "Content", "Economy", "GameError", "LOCKSTEP_OPS"]
