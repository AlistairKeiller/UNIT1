import time
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import groupby
from typing import Callable, List, ParamSpec, TypeVar, Optional
from uuid import uuid4

from pywebio import start_server, config
from pywebio.input import input_group, actions, checkbox, radio
from pywebio.io_ctrl import Output
from pywebio.output import (
    put_text,
    put_table,
    put_markdown,
    put_button,
    use_scope,
    clear,
    put_scope,
    popup,
    close_popup,
    toast,
    put_error,
)
from pywebio.session import local as session_data, ThreadBasedSession, run_js
from pywebio_battery import get_query

from chessmaker.chess.base.board import Board
from chessmaker.chess.base.game import Game, AfterTurnChangeEvent, AfterGameEndEvent
from chessmaker.chess.base.move_option import MoveOption
from chessmaker.chess.base.piece import Piece, AfterMoveEvent
from chessmaker.chess.base.player import Player
from chessmaker.chess.base.position import Position
from chessmaker.chess.base.square import Square
from chessmaker.chess.game_factory import create_game
from chessmaker.events import EventPriority
from chessmaker.clients.pywebio_ui import (
    public_games,
    join_game,
    client_games,
    shared_positions,
    new_game,
    PIECE_URLS,
    CSS,
)


def start_pywebio_chess_server(
    game_factory: Callable[..., Game],
    supported_options: List[str] = None,
    piece_urls: dict[str, tuple[str, ...]] = PIECE_URLS,
    remote_access: bool = False,
    port: int = 8000,
    debug: bool = False,
    host: str = "",
):
    if supported_options is None:
        supported_options = []

    @config(
        title="ChessMaker",
        description="An easily extendible chess implementation designed to support any custom rule or feature.",
        css_style=CSS,
    )
    def main():
        games_to_remove = []
        for game_id, (time_created, game) in public_games.items():
            if time.time() - time_created > 5 * 60:
                games_to_remove.append(game_id)
        for game_id in games_to_remove:
            public_games.pop(game_id)

        if get_query("game_id"):
            if get_query("game_id") not in client_games:
                popup("Error", put_error("Game not found"))
            else:
                join_game(get_query("game_id"))
            return

        if get_query("position_id"):
            if get_query("position_id") not in shared_positions:
                popup("Error", put_error("Position not found"))
            else:
                form_result = input_group(
                    "New Game",
                    [
                        radio(
                            "Mode",
                            [
                                "Singleplayer",
                                "Multiplayer (Private)",
                                "Multiplayer (Public)",
                            ],
                            name="mode",
                            value="Singleplayer",
                        ),
                        actions(
                            "-",
                            [
                                {"label": "Create", "value": "create"},
                            ],
                            name="action",
                        ),
                    ],
                )
                shared_position = shared_positions[get_query("position_id")]
                new_game(
                    lambda **_: Game(
                        shared_position.board.clone(),
                        deepcopy(shared_position.get_result),
                    ),
                    shared_position.options,
                    form_result["mode"],
                    piece_urls,
                )
            return

        form_result = input_group(
            "New Game",
            [
                radio(
                    "Mode",
                    ["Singleplayer", "Multiplayer (Private)", "Multiplayer (Public)"],
                    name="mode",
                    value="Singleplayer",
                ),
                checkbox(
                    "Options",
                    options=supported_options,
                    name="options",
                    help_text=f"See details at https://wolfdwyc.github.io/ChessMaker/packaged-variants/",
                ),
                actions(
                    "Public Games",
                    [
                        {
                            "label": f"Join game: {', '.join(public_game.options) or 'standard'}",
                            "value": game_id,
                        }
                        for game_id, (_, public_game) in public_games.items()
                    ],
                    name="public_games",
                ),
                actions(
                    "-",
                    [
                        {"label": "Create", "value": "create"},
                    ],
                    name="action",
                ),
            ],
        )

        if form_result["public_games"] is not None:
            public_games.pop(form_result["public_games"])
            join_game(form_result["public_games"])
            return

        new_game(game_factory, form_result["options"], form_result["mode"], piece_urls)

    start_server(main, port=port, remote_access=remote_access, debug=debug, host=host)
