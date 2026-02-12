from __future__ import annotations

from app.models import BotType, Player
from app.services.game_logic import (
    apply_move,
    check_winner,
    choose_starting_player,
    get_bot_move,
    is_draw,
    reconstruct_board,
)


def test_check_winner_all_lines():
    line_sets = [
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)],
    ]

    for line in line_sets:
        board = [[".", ".", "."], [".", ".", "."], [".", ".", "."]]
        for x, y in line:
            board[y][x] = "X"
        assert check_winner(board) == Player.X


def test_is_draw_true_when_board_full_without_winner():
    board = [
        ["X", "O", "X"],
        ["X", "O", "O"],
        ["O", "X", "X"],
    ]
    assert is_draw(board) is True


def test_reconstruct_board_from_move_history():
    moves = [
        {"move_number": 1, "x": 0, "y": 0},
        {"move_number": 2, "x": 1, "y": 1},
        {"move_number": 3, "x": 2, "y": 2},
    ]

    board = reconstruct_board(Player.O, moves)
    assert board == [
        ["O", ".", "."],
        [".", "X", "."],
        [".", ".", "O"],
    ]


def test_smart_bot_prioritizes_winning_move():
    board = [
        ["O", "O", "."],
        ["X", "X", "."],
        [".", ".", "."],
    ]

    move = get_bot_move(board, BotType.smart)
    assert move == {"x": 2, "y": 0}


def test_smart_bot_blocks_human_if_no_win_available():
    board = [
        ["X", "X", "."],
        [".", "O", "."],
        [".", ".", "."],
    ]

    move = get_bot_move(board, BotType.smart)
    assert move == {"x": 2, "y": 0}


def test_chaos_bot_selects_only_empty_cells():
    board = [
        ["X", "O", "X"],
        ["O", ".", "X"],
        [".", "O", "X"],
    ]

    for _ in range(20):
        move = get_bot_move(board, BotType.chaos)
        assert move in [{"x": 1, "y": 1}, {"x": 0, "y": 2}]


def test_choose_starting_player_alternates():
    assert choose_starting_player(None) == Player.O
    assert choose_starting_player(Player.O) == Player.X
    assert choose_starting_player(Player.X) == Player.O


def test_apply_move_sets_expected_cell():
    board = [[".", ".", "."], [".", ".", "."], [".", ".", "."]]
    updated = apply_move(board, 1, 2, Player.X)

    assert board[2][1] == "."
    assert updated[2][1] == "X"
