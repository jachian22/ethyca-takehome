from datetime import UTC, datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel


class Player(str, Enum):
    X = "X"
    O = "O"


class GameStatus(str, Enum):
    in_progress = "in_progress"
    x_wins = "x_wins"
    o_wins = "o_wins"
    draw = "draw"
    abandoned = "abandoned"


class BotType(str, Enum):
    smart = "smart"
    chaos = "chaos"


def generate_cuid() -> str:
    return f"c{uuid4().hex}"


class Game(SQLModel, table=True):
    id: str = Field(default_factory=generate_cuid, primary_key=True, index=True)
    status: GameStatus = Field(default=GameStatus.in_progress, index=True)
    starting_player: Player
    bot_type: BotType
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)

    moves: List["Move"] = Relationship(back_populates="game")


class Move(SQLModel, table=True):
    id: str = Field(default_factory=generate_cuid, primary_key=True, index=True)
    game_id: str = Field(foreign_key="game.id", index=True)
    move_number: int = Field(index=True)
    x: int
    y: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    game: Optional[Game] = Relationship(back_populates="moves")
