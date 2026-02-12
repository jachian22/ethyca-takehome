# Tic-Tac-Toe: FastAPI + React

A human-vs-bot tic-tac-toe game with a FastAPI backend and React frontend.

**Stack**: FastAPI + SQLModel (backend), React + TypeScript + Vite + Tailwind (frontend), Postgres (production)

## Public Deployment

- Live app: `https://ethyca-takehome.vercel.app/`
- Frontend host: Vercel
- Backend host: Railway (`/health` and game APIs)

---

## Design Rationale

### Game Mechanics

**Fixed roles**: Human is always X, bot is always O. The interesting variation comes from *who starts*, not which symbol you play.

**Alternating start**: The first game has the bot move first. Subsequent games alternate based on the previous completed/abandoned game. This keeps the experience fair and requires different strategies as opener vs responder.

**Coordinates**: `board[y][x]` with `(0,0)` at top-left. Zero-indexed, row-major to match visual rendering.

### Bot Personalities

**90% Smart Bot**: Follows win > block > random priority. Plays optimally but not unbeatable.

**10% Chaos Bot**: Pure random moves. Determined at game creation and announced to the player. This rare "wild card" event adds surprise and replayability.

**Timing**: API returns moves immediately; the UI adds artificial delay for better game feel. Keeps the API stateless while preserving UX.

### Data Model

**Minimal storage**: Only coordinates and move order are stored. Board state is reconstructed from move history (max 9 moves, trivial computation).

**Derived players**: Don't store which player made each move. `move_number % 2` plus `starting_player` gives us the player deterministically.

**Status values**: `in_progress | x_wins | o_wins | draw | abandoned`

### Game Lifecycle

**Single active game**: Only one `in_progress` game at a time. Creating a new game auto-abandons any existing in-progress game (preserves history, doesn't delete).

**Session persistence**: Stateless REST API. Close browser, reopen, resume via `GET /games/current`. No websockets or server-side sessions.

**No undo/forfeit**: Start a new game to abandon the current one.

### API Design

| Endpoint | Purpose |
|----------|---------|
| `POST /games` | Create new game |
| `GET /games` | List all games |
| `GET /games/current` | Get in-progress game (resume flow) |
| `GET /games/{id}` | Get specific game |
| `POST /games/{id}/moves` | Make a move |
| `GET /games/{id}/moves` | Move history |

**Error responses** include `valid_moves` array to help the UI guide players:

```json
{
  "error": "cell_occupied",
  "message": "That cell is already taken. Try another move.",
  "valid_moves": [{ "x": 0, "y": 0 }]
}
```

Error codes: `game_not_found`, `invalid_payload`, `out_of_bounds`, `cell_occupied`, `game_finished`, `not_your_turn`

### Input UX

**Dual modes**: Click-on-board and text coordinate input (`x`, `y` fields accepting 0-2).

**Real-time feedback**: As coordinates are entered, the board highlights the corresponding row/column/cell. Invalid targets show a red outline.

---

## Quickstart: Local Development

### 1. Frontend dependencies

```bash
pnpm install
```

### 2. Python backend

```bash
cd python-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

### 3. Start backend (port 8000)

```bash
pnpm run api:dev
```

Without `DATABASE_URL`, falls back to SQLite at `python-api/tic_tac_toe.db`.

### 4. Start frontend (port 4000)

```bash
pnpm run dev
```

Calls `http://localhost:8000` by default.

---

## Quickstart: Deploy to Railway + Vercel

### Railway (Backend + Postgres)

1. Create a new Railway project from this repo
2. Set **Root Directory** to `python-api`
3. Add a Railway Postgres service
4. Set environment variables:
   - `DATABASE_URL` = Postgres connection string (Railway provides this)
   - `CORS_ORIGINS` = your Vercel frontend URL (e.g., `https://your-app.vercel.app`)
5. Railway uses `python-api/Procfile`:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```
6. Deploy and verify `https://<railway-url>/health`

### Vercel (Frontend)

1. Create a Vercel project from this repo (root directory = repo root)
2. Set environment variable:
   - `VITE_API_BASE_URL` = `https://<railway-backend-url>`
3. Deploy

### Notes from this deployment

- `VITE_API_BASE_URL` must include protocol and no path suffix:
  - Correct: `https://your-backend.up.railway.app`
  - Incorrect: `your-backend.up.railway.app` or `.../health`
- `CORS_ORIGINS` on Railway must exactly match the Vercel origin:
  - Example: `https://ethyca-takehome.vercel.app`
- Railway Root Directory should be `python-api` (no leading slash)
- Railway Start Command should be:
  - `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Build command can be left blank with Railpack/Nixpacks auto-detection
- Backend exposes both `/` and `/health` as `200` JSON to satisfy platform health checks

---

## Project Structure

```
python-api/
  app/
    main.py           # FastAPI app, CORS, exception handlers
    database.py       # DB engine/session, URL normalization
    models.py         # SQLModel tables and enums
    routers/games.py  # REST handlers
    services/game_logic.py  # Pure game rules and bot logic
  tests/
    test_game_logic.py  # Unit tests
    test_api.py         # Integration tests

src/
  pages/Game.tsx      # UI and interactions
  hooks/useGame.ts    # API-driven game state hook
  lib/api.ts          # API client + typed errors
```

---

## Testing

```bash
# Backend tests
pnpm run api:test

# Frontend lint + build
pnpm run lint
pnpm run build
```

---

## Trade-offs

- **Single-user context**: No auth or per-user partitioning
- **Postgres target**: SQLite is dev convenience only
- **Stateless API**: Bot delay is a frontend concern for better feel

---

## Submission Summary (Copy/Paste)

### Architecture

- Frontend: React + Vite app with API-driven game state (`useGame`), dual input modes (click and coordinates), optimistic UX delay for bot responses, and game history display.
- Backend: FastAPI + SQLModel REST API with persistent game/move tables, board reconstruction from move history, and deterministic lifecycle rules.
- Data: Postgres in production (Railway), local SQLite fallback for development.

### Key behavior decisions

- Human is always `X`, bot is always `O`.
- First game starts with bot; starting player alternates across completed/abandoned games.
- Exactly one `in_progress` game at a time; creating a new game auto-abandons previous in-progress game.
- Bot personalities: 90% smart (`win > block > random`), 10% chaos (random) with reveal messaging.
- API validation errors include helpful machine code + message + `valid_moves`.

### Trade-offs

- Single global game context (no auth/multi-tenant partitioning) to keep scope focused on gameplay correctness.
- No undo/forfeit API; new game creation serves as explicit abandon flow.
- Board state is reconstructed from move history instead of storing snapshots; this avoids redundant data and is trivial at tic-tac-toe scale.

---

## Time Spent

- 2.5 hours from plan to working local end state
- 1 hour to deploy to Railway for the first time (Python + Postgres)

## Feedback on the Challenge

The take-home was fun, and I hope you enjoy the small idiosyncrasies I added to the app.
