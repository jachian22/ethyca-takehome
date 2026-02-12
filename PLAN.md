# Tic-Tac-Toe REST API - Implementation Plan

## Overview

**Goal**: Build a REST API for playing tic-tac-toe against a computer opponent.

**Approach**: Prototype in TypeScript (T3 stack + tRPC) for type safety and rapid iteration, then port to Python with FastAPI/SQLModel for final deliverable.

---

## Core Game Mechanics

### Players
- **Human = X** (always)
- **Bot = O** (always)

### Alternating Start
- Game 1: Bot (O) goes first
- Game 2: Human (X) goes first
- ...alternates based on previous completed/abandoned game

### Coordinate System
- `board[y][x]` — row-major indexing
- `(0,0)` = top-left, `(2,2)` = bottom-right
- Input: `{"x": col, "y": row}` where both are 0-2

### Turn Flow
1. Clear indication of whose turn it is
2. Bot has artificial delay (UI-side, not instant)
3. API response includes bot's counter-move, UI delays display
4. Game ends immediately on win (no bot move after winning move)

### Validation
- Cell occupied → reject with helpful message, include valid_moves
- Out of bounds → reject, guide to 0-2 range
- Finished game → block submission
- Malformed input → reject, guide to valid format

### Win/Draw Detection
- **Win**: 8 lines (3 rows, 3 cols, 2 diagonals) — check after each move
- **Draw**: Board full (9 moves), no winner

### Bot Personality (Per-Game)
- **90% Smart Bot**: win > block > random (silent start)
- **10% Chaos Bot**: pure random (revealed: "You're facing the Chaos Bot!")

```python
def get_bot_move(board: Board, bot_type: str) -> tuple[int, int]:
    if bot_type == "smart":
        winning_move = find_winning_move(board, "O")
        if winning_move:
            return winning_move
        blocking_move = find_blocking_move(board, "X")
        if blocking_move:
            return blocking_move
    return random.choice(get_empty_cells(board))
```

### Game Lifecycle
- Only one `in_progress` game at a time
- Creating new game auto-abandons any in-progress game
- No forfeit, no undo
- Session persistence: stateless REST, resume via `GET /games/current`

---

## Data Model

**Game table:**
```
id               : cuid
status           : in_progress | x_wins | o_wins | draw | abandoned
starting_player  : X | O
bot_type         : smart | chaos
created_at       : timestamp
```

**Move table:**
```
id          : cuid
game_id     : FK → Game
move_number : int (1, 2, 3, ...)
x           : int (0-2)
y           : int (0-2)
created_at  : timestamp
```

Player derived from: `starting_player if move_number % 2 == 1 else other_player`

---

## API Design (REST)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/games` | Create new game (auto-abandons in-progress) |
| `GET` | `/games` | List all games (chronological) |
| `GET` | `/games/current` | Get in-progress game (for resume) |
| `GET` | `/games/{id}` | Get specific game with full board |
| `POST` | `/games/{id}/moves` | Make a move |
| `GET` | `/games/{id}/moves` | Get move history |

### Response Shapes

**POST /games**
```json
{
  "id": "clx123",
  "status": "in_progress",
  "starting_player": "O",
  "bot_type": "chaos",
  "board": [[".", ".", "."], [".", "O", "."], [".", ".", "."]],
  "current_turn": "X",
  "bot_move": {"x": 1, "y": 1},
  "message": "You're facing the Chaos Bot!"
}
```

**POST /games/{id}/moves**
```json
{
  "board": [["X", ".", "."], [".", "O", "."], [".", ".", "O"]],
  "status": "in_progress",
  "current_turn": "X",
  "bot_move": {"x": 2, "y": 2},
  "message": null
}
```

**GET /games**
```json
{
  "games": [
    {
      "id": "clx123",
      "status": "x_wins",
      "bot_type": "smart",
      "move_count": 7,
      "created_at": "2024-...",
      "final_board": [["X", "O", "X"], ["O", "X", "O"], [".", ".", "X"]]
    }
  ]
}
```
- `final_board` only for completed/abandoned games
- In-progress: `final_board: null`

**Error response**
```json
{
  "error": "cell_occupied",
  "message": "That cell is already taken. Try another move.",
  "valid_moves": [{"x": 0, "y": 0}, {"x": 2, "y": 1}]
}
```

---

## Web App UX

### Board Display
- ASCII aesthetic, monospace font
- Clear turn indicator

### Click Mode
- Empty cells: hover state
- Occupied cells: locked appearance, no hover

### Text Input Mode (x, y fields)
- Only `0`, `1`, `2` accepted — other keys rejected
- Placeholder: gray `0-2`
- Invalid state: light red outline
- Real-time board highlighting:
  - `y="0"` only → top row highlighted
  - `x="1"` only → middle column highlighted
  - `x="1" y="1"` → single cell pulse/glow
  - Occupied target → red cell, submit disabled

### Chaos Bot Reveal
- Special announcement when 10% chaos bot is rolled
- Opportunity for fun animations/personality

---

## Stack

### Phase 1: TypeScript Prototype

| Component | Choice |
|-----------|--------|
| Framework | Next.js (Pages Router) |
| API | tRPC |
| ORM | Prisma |
| Database | SQLite |
| Styling | Tailwind |

### Phase 2: Python Final

| Component | Choice |
|-----------|--------|
| Framework | FastAPI |
| ORM | SQLModel |
| Database | SQLite |
| Validation | Pydantic (via SQLModel) |

---

## File Structure

### TypeScript
```
/ts-prototype/
├── prisma/
│   └── schema.prisma
├── src/
│   ├── pages/
│   │   ├── index.tsx
│   │   └── api/trpc/[trpc].ts
│   ├── server/
│   │   ├── routers/
│   │   │   ├── game.ts
│   │   │   └── move.ts
│   │   ├── trpc.ts
│   │   └── db.ts
│   ├── lib/
│   │   └── game-logic.ts
│   └── components/
│       ├── Board.tsx
│       ├── MoveHistory.tsx
│       └── GameStatus.tsx
├── package.json
└── tsconfig.json
```

### Python
```
/python-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── games.py
│   └── services/
│       ├── __init__.py
│       └── game_logic.py
├── tests/
│   ├── __init__.py
│   ├── test_game_logic.py
│   └── test_api.py
├── requirements.txt
└── README.md
```

---

## Testing Strategy (Python)

### Unit Tests (`test_game_logic.py`)
- `test_is_valid_move()` — bounds, occupied, game over
- `test_apply_move()` — correct board mutation
- `test_check_winner()` — all 8 win conditions
- `test_is_draw()` — full board detection
- `test_get_bot_move_smart()` — win > block > random priority
- `test_get_bot_move_chaos()` — pure random
- `test_reconstruct_board()` — from move history

### Integration Tests (`test_api.py`)
- `test_create_game()` — returns valid game, bot moves if starting
- `test_make_move()` — valid move, board updates, bot responds
- `test_make_move_invalid()` — cell occupied, out of bounds, game over
- `test_get_games()` — list with correct fields
- `test_get_current_game()` — resume flow
- `test_new_game_abandons_current()` — auto-abandon behavior
- `test_alternating_start()` — bot/human starting alternates

---

## Creative Feature: Chaos Bot Personality

The 10% Chaos Bot is the "gee-whizz" element:
- Surprise reveal at game start
- Pure chaotic randomness vs strategic smart bot
- UI opportunity: different animations, personality, fun copy
- Stored in DB for game history context ("you beat the Chaos Bot!")

This is already designed into the core mechanics — implementation focuses on making the reveal moment delightful.

---

## Implementation Order

### Phase 1: TypeScript Prototype
1. Scaffold T3 app (Pages Router, tRPC, Prisma, Tailwind)
2. Define Prisma schema, run migrations
3. Implement game logic (pure functions)
4. Build tRPC routers
5. Create minimal UI (board, inputs, status)
6. Test full game flow

### Phase 2: Python Port
1. Scaffold FastAPI project
2. Define SQLModel models
3. Port game logic from TypeScript
4. Implement REST endpoints
5. Write unit tests
6. Write integration tests
7. Manual test via Swagger UI

### Phase 3: Polish
1. README (setup, assumptions, trade-offs)
2. Code cleanup
3. Final testing

---

## Verification

### TypeScript
1. `npm run dev` → play full game via UI
2. Test: create game, make moves, win/draw/abandon
3. Test: invalid moves show errors
4. Test: resume after page refresh

### Python
1. `uvicorn app.main:app --reload`
2. Swagger UI (`/docs`) — test all endpoints
3. `pytest` — all tests pass
4. Verify game logic matches TypeScript behavior

---

## Deliverables

- [ ] Python REST API (FastAPI + SQLModel + SQLite)
- [ ] All 5 requirements met:
  - [x] Create game, return ID
  - [x] Make move, return board + computer move
  - [x] View moves for a game (chronological)
  - [x] View all games (chronological)
  - [x] Creative feature (Chaos Bot)
- [ ] Unit + Integration tests
- [ ] README with:
  - How to run
  - Assumptions
  - Trade-offs
  - Time spent
