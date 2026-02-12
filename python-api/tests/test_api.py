from __future__ import annotations

from app.models import BotType


def _first_empty(board: list[list[str]]) -> dict[str, int]:
    for y in range(3):
        for x in range(3):
            if board[y][x] == ".":
                return {"x": x, "y": y}
    raise AssertionError("No empty cells available")


def _deterministic_bot_move(board: list[list[str]], _bot_type: BotType) -> dict[str, int]:
    preferred_order = [
        {"x": 0, "y": 2},
        {"x": 1, "y": 2},
        {"x": 2, "y": 2},
        {"x": 0, "y": 1},
        {"x": 1, "y": 1},
        {"x": 2, "y": 1},
        {"x": 0, "y": 0},
        {"x": 1, "y": 0},
        {"x": 2, "y": 0},
    ]

    for candidate in preferred_order:
        if board[candidate["y"]][candidate["x"]] == ".":
            return candidate

    raise AssertionError("Bot had no move")


def test_create_game(client):
    response = client.post("/games")
    assert response.status_code == 201

    payload = response.json()
    assert payload["id"]
    assert payload["status"] == "in_progress"
    assert payload["starting_player"] in ["X", "O"]
    assert payload["bot_type"] in ["smart", "chaos"]
    assert payload["current_turn"] == "X"
    assert len(payload["board"]) == 3

    if payload["starting_player"] == "O":
        assert payload["bot_move"] is not None
    else:
        assert payload["bot_move"] is None


def test_make_move_and_bot_response(client, monkeypatch):
    monkeypatch.setattr("app.routers.games.get_bot_move", _deterministic_bot_move)
    monkeypatch.setattr("app.routers.games.choose_bot_type", lambda: BotType.smart)

    game = client.post("/games").json()
    move = _first_empty(game["board"])

    response = client.post(f"/games/{game['id']}/moves", json=move)
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] in ["in_progress", "o_wins", "draw"]
    assert payload["bot_move"] is not None
    flat = [cell for row in payload["board"] for cell in row]
    assert flat.count("X") == 1
    assert flat.count("O") >= 2


def test_make_move_invalid_cell_occupied(client, monkeypatch):
    monkeypatch.setattr("app.routers.games.get_bot_move", _deterministic_bot_move)

    game = client.post("/games").json()
    occupied = game["bot_move"]

    response = client.post(f"/games/{game['id']}/moves", json=occupied)
    assert response.status_code == 400

    payload = response.json()
    assert payload["error"] == "cell_occupied"
    assert payload["valid_moves"]


def test_make_move_invalid_out_of_bounds(client):
    game = client.post("/games").json()

    response = client.post(f"/games/{game['id']}/moves", json={"x": 9, "y": -1})
    assert response.status_code == 400
    assert response.json()["error"] == "out_of_bounds"


def test_invalid_payload_returns_expected_error(client):
    game = client.post("/games").json()

    response = client.post(f"/games/{game['id']}/moves", json={"x": "nope"})
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_payload"


def test_get_current_game_resume_flow(client):
    created = client.post("/games").json()

    response = client.get("/games/current")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created["id"]
    assert payload["status"] == "in_progress"


def test_new_game_abandons_current(client):
    first = client.post("/games").json()
    second = client.post("/games").json()

    first_game = client.get(f"/games/{first['id']}").json()
    current = client.get("/games/current").json()

    assert first_game["status"] == "abandoned"
    assert current["id"] == second["id"]


def test_alternating_start_between_games(client):
    first = client.post("/games").json()
    second = client.post("/games").json()
    third = client.post("/games").json()

    assert first["starting_player"] != second["starting_player"]
    assert second["starting_player"] != third["starting_player"]


def test_get_games_chronological_and_final_board_rules(client):
    first = client.post("/games").json()
    second = client.post("/games").json()

    response = client.get("/games")
    assert response.status_code == 200
    games = response.json()["games"]

    assert [game["id"] for game in games][-2:] == [first["id"], second["id"]]

    first_listed = next(game for game in games if game["id"] == first["id"])
    second_listed = next(game for game in games if game["id"] == second["id"])

    assert first_listed["status"] == "abandoned"
    assert first_listed["final_board"] is not None
    assert second_listed["status"] == "in_progress"
    assert second_listed["final_board"] is None


def test_get_game_moves_chronological(client, monkeypatch):
    monkeypatch.setattr("app.routers.games.get_bot_move", _deterministic_bot_move)

    game = client.post("/games").json()
    move = _first_empty(game["board"])
    client.post(f"/games/{game['id']}/moves", json=move)

    response = client.get(f"/games/{game['id']}/moves")
    assert response.status_code == 200

    moves = response.json()["moves"]
    numbers = [move["move_number"] for move in moves]
    assert numbers == sorted(numbers)
    assert len(moves) == 3


def test_human_win_has_no_bot_counter_move(client, monkeypatch):
    monkeypatch.setattr("app.routers.games.get_bot_move", _deterministic_bot_move)
    monkeypatch.setattr("app.routers.games.choose_bot_type", lambda: BotType.smart)

    client.post("/games")
    game = client.post("/games").json()
    assert game["starting_player"] == "X"

    first = client.post(f"/games/{game['id']}/moves", json={"x": 0, "y": 0})
    assert first.status_code == 200
    second = client.post(f"/games/{game['id']}/moves", json={"x": 1, "y": 0})
    assert second.status_code == 200
    winning = client.post(f"/games/{game['id']}/moves", json={"x": 2, "y": 0})

    assert winning.status_code == 200
    payload = winning.json()
    assert payload["status"] == "x_wins"
    assert payload["bot_move"] is None
