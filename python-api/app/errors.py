from __future__ import annotations

from dataclasses import dataclass


@dataclass
class APIError(Exception):
    status_code: int
    error: str
    message: str
    valid_moves: list[dict[str, int]] | None = None
