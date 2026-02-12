from __future__ import annotations

from datetime import datetime

from sqlmodel import SQLModel

from .models import BotType, GameStatus, Player

Board = list[list[str]]


class Position(SQLModel):
    x: int
    y: int


class MoveRequest(SQLModel):
    x: int
    y: int


class ErrorResponse(SQLModel):
    error: str
    message: str
    valid_moves: list[Position] | None = None


class GameCreateResponse(SQLModel):
    id: str
    status: GameStatus
    starting_player: Player
    bot_type: BotType
    board: Board
    current_turn: Player | None
    bot_move: Position | None = None
    message: str | None = None


class GameMoveResponse(SQLModel):
    board: Board
    status: GameStatus
    current_turn: Player | None
    bot_move: Position | None = None
    message: str | None = None


class GameSummary(SQLModel):
    id: str
    status: GameStatus
    bot_type: BotType
    move_count: int
    created_at: datetime
    final_board: Board | None


class GamesListResponse(SQLModel):
    games: list[GameSummary]


class GameDetailResponse(SQLModel):
    id: str
    status: GameStatus
    starting_player: Player
    bot_type: BotType
    created_at: datetime
    board: Board
    current_turn: Player | None


class MoveHistoryItem(SQLModel):
    id: str
    move_number: int
    x: int
    y: int
    player: Player
    created_at: datetime


class MovesListResponse(SQLModel):
    game_id: str
    moves: list[MoveHistoryItem]
