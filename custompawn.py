import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Type

from chessmaker.chess.base.game import AfterTurnChangeEvent
from chessmaker.chess.base.move_option import MoveOption
from chessmaker.chess.base.piece import (
    Piece,
    BeforeMoveEvent,
    AfterMoveEvent,
    BeforeCapturedEvent,
    AfterCapturedEvent,
)
from chessmaker.chess.base.player import Player
from chessmaker.chess.base.position import Position
from chessmaker.chess.piece_utils import iterate_until_blocked, is_in_board
from chessmaker.events import EventPriority, Event, event_publisher
from chessmaker.chess.pieces import Pawn


class CustomPawn(Pawn):
    def _get_move_options(self):
        move_options = []
        non_capture_positions = [
            *list(iterate_until_blocked(self, (0, self._direction.value)))[:1],
            *list(iterate_until_blocked(self, (-self._direction.value, 0)))[:1],
        ]
        if (
            len(non_capture_positions) != 0
            and self.board[non_capture_positions[-1]].piece is not None
        ):
            non_capture_positions.pop()
        move_options += [MoveOption(position) for position in non_capture_positions]

        capture_positions = [
            self.position.offset(1, self._direction.value),
            self.position.offset(-1, self._direction.value),
            self.position.offset(-self._direction.value, -self._direction.value),
        ]
        capture_positions = filter(
            lambda position: is_in_board(self.board, position), capture_positions
        )

        for position in capture_positions:
            position_piece = self.board[position].piece
            if position_piece is None:
                above_position, below_position = (
                    Position(position.x, position.y + 1),
                    Position(position.x, position.y - 1),
                )
                if not is_in_board(self.board, above_position) or not is_in_board(
                    self.board, below_position
                ):
                    continue
                squares = self.board[above_position], self.board[below_position]

                for i, square in enumerate(squares):
                    if (
                        square is not None
                        and isinstance(square.piece, Pawn)
                        and square.piece.player != self.player
                        and square.piece._last_position == squares[1 - i].position
                        and 0 <= square.piece._moved_turns_ago <= 1
                    ):
                        move_options.append(
                            MoveOption(
                                position,
                                extra=dict(en_passant=True),
                                captures={square.position},
                            )
                        )
                continue
            elif position_piece.player == self.player:
                continue
            move_options.append(MoveOption(position, captures={position}))

        for move_option in list(move_options):
            position = move_option.position
            last_position_in_column = max(
                filter(lambda square: square.position.x == position.x, self.board),
                key=lambda square: square.position.y * self._direction.value,
            ).position
            last_position_in_row = max(
                filter(lambda square: square.position.y == position.y, self.board),
                key=lambda square: -square.position.x * self._direction.value,
            ).position
            if position == last_position_in_column or position == last_position_in_row:
                move_options.remove(move_option)
                for promotion_name in self.promotions:
                    move_options.append(
                        dataclasses.replace(
                            move_option, extra=dict(promote=promotion_name)
                        )
                    )

        return move_options
