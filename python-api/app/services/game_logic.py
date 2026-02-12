from __future__ import annotations

import random
from typing import Any, Sequence

from ..models import BotType, GameStatus, Player

Board = list[list[str]]
WIN_LINES = [
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]


def build_empty_board() -> Board:
    return [[".", ".", "."], [".", ".", "."], [".", ".", "."]]


def other_player(player: Player) -> Player:
    return Player.O if player == Player.X else Player.X


def derive_player(starting_player: Player, move_number: int) -> Player:
    return starting_player if move_number % 2 == 1 else other_player(starting_player)


def _read_move_coordinate(move: Any, key: str) -> int:
    if isinstance(move, dict):
        return int(move[key])
    return int(getattr(move, key))


def reconstruct_board(starting_player: Player, moves: Sequence[Any]) -> Board:
    board = build_empty_board()

    for move in moves:
        move_number = _read_move_coordinate(move, "move_number")
        x = _read_move_coordinate(move, "x")
        y = _read_move_coordinate(move, "y")
        player = derive_player(starting_player, move_number)
        board[y][x] = player.value

    return board


def get_empty_cells(board: Board) -> list[dict[str, int]]:
    empty_cells: list[dict[str, int]] = []
    for y in range(3):
        for x in range(3):
            if board[y][x] == ".":
                empty_cells.append({"x": x, "y": y})
    return empty_cells


def valid_moves(board: Board) -> list[dict[str, int]]:
    return get_empty_cells(board)


def check_winner(board: Board) -> Player | None:
    for line in WIN_LINES:
        (ax, ay), (bx, by), (cx, cy) = line
        cell_a = board[ay][ax]
        cell_b = board[by][bx]
        cell_c = board[cy][cx]
        if cell_a != "." and cell_a == cell_b and cell_b == cell_c:
            return Player(cell_a)
    return None


def is_draw(board: Board) -> bool:
    return all(cell != "." for row in board for cell in row)


def evaluate_status(board: Board) -> GameStatus:
    winner = check_winner(board)
    if winner == Player.X:
        return GameStatus.x_wins
    if winner == Player.O:
        return GameStatus.o_wins
    if is_draw(board):
        return GameStatus.draw
    return GameStatus.in_progress


def apply_move(board: Board, x: int, y: int, player: Player) -> Board:
    next_board = [row[:] for row in board]
    next_board[y][x] = player.value
    return next_board


def find_winning_move(board: Board, player: Player) -> dict[str, int] | None:
    for cell in get_empty_cells(board):
        candidate = apply_move(board, cell["x"], cell["y"], player)
        if check_winner(candidate) == player:
            return cell
    return None


def get_bot_move(board: Board, bot_type: BotType) -> dict[str, int]:
    empty_cells = get_empty_cells(board)
    if not empty_cells:
        raise ValueError("No valid bot moves available")

    if bot_type == BotType.smart:
        winning = find_winning_move(board, Player.O)
        if winning:
            return winning

        blocking = find_winning_move(board, Player.X)
        if blocking:
            return blocking

    return random.choice(empty_cells)


def choose_bot_type() -> BotType:
    return BotType.chaos if random.random() < 0.1 else BotType.smart


def choose_starting_player(previous_starting_player: Player | None) -> Player:
    if previous_starting_player is None:
        return Player.O
    return other_player(previous_starting_player)


def compute_current_turn(status: GameStatus, starting_player: Player, move_count: int) -> Player | None:
    if status != GameStatus.in_progress:
        return None
    if move_count % 2 == 0:
        return starting_player
    return other_player(starting_player)
