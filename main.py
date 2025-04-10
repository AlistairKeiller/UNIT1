from itertools import cycle

from chessmaker.chess.base import Board, Game, Player, Square
from chessmaker.chess.pieces import Bishop, King, Knight, Pawn, Queen, Rook
from chessmaker.chess.results import (
    NoCapturesOrPawnMoves,
    Repetition,
    checkmate,
    no_kings,
    stalemate,
)

from chessmaker.clients import start_pywebio_chess_server

from custompawn import CustomPawn


def _empty_line(length: int) -> list[Square]:
    return [Square() for _ in range(length)]


def get_result(board: Board) -> str:
    for result_function in [
        no_kings,
        checkmate,
        stalemate,
        Repetition(3),
        NoCapturesOrPawnMoves(50),
    ]:
        result = result_function(board)
        if result:
            return result


piece_row = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]


def create_game(**_) -> Game:
    white = Player("white")
    black = Player("black")
    turn_iterator = cycle([white, black])

    def _pawn(player: Player):
        if player == white:
            return CustomPawn(
                white, Pawn.Direction.UP, promotions=[Bishop, Rook, Queen, Knight]
            )
        elif player == black:
            return CustomPawn(
                black, Pawn.Direction.DOWN, promotions=[Bishop, Rook, Queen, Knight]
            )

    game = Game(
        board=Board(
            squares=[
                [
                    *_empty_line(3),
                    Square(_pawn(black)),
                    Square(Rook(black)),
                    Square(Bishop(black)),
                    Square(Queen(black)),
                    Square(),
                ],
                [
                    *_empty_line(4),
                    Square(_pawn(black)),
                    Square(Knight(black)),
                    Square(_pawn(black)),
                    Square(King(black)),
                ],
                [
                    *_empty_line(4),
                    Square(_pawn(black)),
                    Square(_pawn(black)),
                    Square(Bishop(black)),
                    Square(Knight(black)),
                ],
                [
                    Square(_pawn(white)),
                    *_empty_line(4),
                    Square(_pawn(black)),
                    Square(_pawn(black)),
                    Square(Rook(black)),
                ],
                [
                    Square(Rook(white)),
                    Square(_pawn(white)),
                    Square(_pawn(white)),
                    *_empty_line(4),
                    Square(_pawn(black)),
                ],
                [
                    Square(Knight(white)),
                    Square(Bishop(white)),
                    Square(_pawn(white)),
                    Square(_pawn(white)),
                    *_empty_line(4),
                ],
                [
                    Square(King(white)),
                    Square(_pawn(white)),
                    Square(Knight(white)),
                    Square(_pawn(white)),
                    *_empty_line(4),
                ],
                [
                    Square(),
                    Square(Queen(white)),
                    Square(Bishop(white)),
                    Square(Rook(white)),
                    Square(_pawn(white)),
                    *_empty_line(3),
                ],
            ],
            players=[white, black],
            turn_iterator=turn_iterator,
        ),
        get_result=get_result,
    )

    return game


if __name__ == "__main__":
    start_pywebio_chess_server(create_game)
