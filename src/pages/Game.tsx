import { useMemo, useState } from "react";
import type { Board, GameSummary } from "../types";
import { useGame } from "../hooks/useGame";

function StatusLabel({ status }: { status: GameSummary["status"] }) {
  if (status === "x_wins") return <span>YOU WON</span>;
  if (status === "o_wins") return <span>BOT WON</span>;
  if (status === "draw") return <span>DRAW</span>;
  if (status === "abandoned") return <span>ABANDONED</span>;
  return <span>IN PROGRESS</span>;
}

function MiniBoard({ board }: { board: Board }) {
  return (
    <div className="grid grid-cols-3 border border-stone-300 bg-stone-50">
      {board.map((row, y) =>
        row.map((cell, x) => (
          <div
            key={`mini-${x}-${y}`}
            className={`h-6 w-6 border-stone-300 text-center text-[10px] leading-6 text-stone-600 ${
              x < 2 ? "border-r" : ""
            } ${y < 2 ? "border-b" : ""}`}
          >
            {cell === "." ? "·" : cell}
          </div>
        ))
      )}
    </div>
  );
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

// Minimalist Zen - Clean white space, Japanese-inspired serenity
export default function Game() {
  const {
    board,
    status,
    currentTurn,
    botType,
    message,
    error,
    loading,
    isBotThinking,
    makeMove,
    newGame,
    validMoves,
    history,
  } = useGame();

  const [inputX, setInputX] = useState("");
  const [inputY, setInputY] = useState("");

  const parsedX = useMemo(() => (inputX === "" ? null : Number.parseInt(inputX, 10)), [inputX]);
  const parsedY = useMemo(() => (inputY === "" ? null : Number.parseInt(inputY, 10)), [inputY]);

  const isValidTarget = (x: number, y: number) => validMoves.some((move) => move.x === x && move.y === y);

  const highlightRow = parsedY !== null && parsedX === null ? parsedY : null;
  const highlightCol = parsedX !== null && parsedY === null ? parsedX : null;
  const highlightCell = parsedX !== null && parsedY !== null ? { x: parsedX, y: parsedY } : null;
  const hasExplicitTarget = parsedX !== null && parsedY !== null;
  const targetIsValid = hasExplicitTarget ? isValidTarget(parsedX, parsedY) : false;

  const canSubmit =
    status === "in_progress" &&
    !isBotThinking &&
    currentTurn === "X" &&
    parsedX !== null &&
    parsedY !== null &&
    targetIsValid;

  const turnText =
    loading
      ? "Loading game..."
      : status === "x_wins"
      ? "You win."
      : status === "o_wins"
      ? "Bot wins."
      : status === "draw"
      ? "Draw."
      : status === "abandoned"
      ? "Game abandoned."
      : isBotThinking || currentTurn === "O"
      ? "Bot is thinking..."
      : "Your turn (X)";

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit || parsedX === null || parsedY === null) {
      return;
    }

    makeMove(parsedX, parsedY);
    setInputX("");
    setInputY("");
  };

  const sanitizeInput = (value: string) => value.replace(/[^0-2]/g, "").slice(0, 1);

  return (
    <div className="relative min-h-screen bg-stone-50 p-4">
      <div
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23a8a29e' fill-opacity='0.2'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
        }}
      />

      <div className="relative z-10 mx-auto grid w-full max-w-6xl gap-10 py-8 lg:grid-cols-[1fr_340px]">
        <main className="flex flex-col items-center justify-start">
          <div className="text-center">
            <h1 className="mb-2 text-4xl font-light tracking-[0.3em] text-stone-700">禅</h1>
            <p className="text-sm tracking-widest text-stone-400">NOUGHTS & CROSSES</p>
          </div>

          <p className="mt-6 text-xs tracking-[0.25em] text-stone-500">{turnText}</p>

          {message && (
            <div className={`mt-4 text-sm tracking-widest ${botType === "chaos" ? "text-red-400" : "text-stone-500"}`}>
              {message}
            </div>
          )}

          {error && (
            <div className="mt-4 border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600">{error}</div>
          )}

          <div className="mt-10">
            <div className="grid grid-cols-3 gap-0">
              {board.map((row, y) =>
                row.map((cell, x) => {
                  const isHighlighted =
                    highlightRow === y ||
                    highlightCol === x ||
                    (highlightCell !== null && highlightCell.x === x && highlightCell.y === y);
                  const canClick =
                    !loading &&
                    !isBotThinking &&
                    status === "in_progress" &&
                    currentTurn === "X" &&
                    cell === ".";
                  const isInvalidTarget =
                    highlightCell !== null &&
                    highlightCell.x === x &&
                    highlightCell.y === y &&
                    !isValidTarget(x, y);

                  return (
                    <button
                      key={`${x}-${y}`}
                      onClick={() => canClick && makeMove(x, y)}
                      disabled={!canClick}
                      className={`relative flex h-24 w-24 items-center justify-center transition-all duration-500 md:h-28 md:w-28
                        ${x < 2 ? "border-r border-stone-300" : ""}
                        ${y < 2 ? "border-b border-stone-300" : ""}
                        ${canClick ? "cursor-pointer hover:bg-stone-100" : "cursor-default"}
                        ${isHighlighted && !isInvalidTarget ? "bg-stone-100" : ""}
                        ${isInvalidTarget ? "bg-red-50" : ""}
                      `}
                    >
                      {cell === "X" && (
                        <svg
                          className="h-14 w-14 text-stone-700 md:h-16 md:w-16"
                          viewBox="0 0 100 100"
                          stroke="currentColor"
                          strokeWidth="2"
                          fill="none"
                        >
                          <line
                            x1="20"
                            y1="20"
                            x2="80"
                            y2="80"
                            className="animate-draw-line"
                            style={{ strokeDasharray: 100, strokeDashoffset: 0 }}
                          />
                          <line
                            x1="80"
                            y1="20"
                            x2="20"
                            y2="80"
                            className="animate-draw-line"
                            style={{ strokeDasharray: 100, strokeDashoffset: 0 }}
                          />
                        </svg>
                      )}
                      {cell === "O" && (
                        <svg
                          className="h-14 w-14 text-stone-400 md:h-16 md:w-16"
                          viewBox="0 0 100 100"
                          stroke="currentColor"
                          strokeWidth="2"
                          fill="none"
                        >
                          <circle
                            cx="50"
                            cy="50"
                            r="35"
                            className="animate-draw-circle"
                            style={{ strokeDasharray: 220, strokeDashoffset: 0 }}
                          />
                        </svg>
                      )}
                      {isHighlighted && isValidTarget(x, y) && cell === "." && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="h-4 w-4 animate-pulse rounded-full bg-stone-300" />
                        </div>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="mt-10 flex items-end gap-6 md:gap-8">
            <div className="flex flex-col items-center">
              <label className="mb-2 text-xs tracking-widest text-stone-400">X</label>
              <input
                type="text"
                value={inputX}
                onChange={(event) => setInputX(sanitizeInput(event.target.value))}
                maxLength={1}
                placeholder="0-2"
                className={`h-14 w-14 border-b-2 bg-transparent text-center text-xl text-stone-700 placeholder:text-stone-300 focus:outline-none transition-colors ${
                  hasExplicitTarget && !targetIsValid ? "border-red-300" : "border-stone-300 focus:border-stone-500"
                }`}
              />
            </div>
            <div className="flex flex-col items-center">
              <label className="mb-2 text-xs tracking-widest text-stone-400">Y</label>
              <input
                type="text"
                value={inputY}
                onChange={(event) => setInputY(sanitizeInput(event.target.value))}
                maxLength={1}
                placeholder="0-2"
                className={`h-14 w-14 border-b-2 bg-transparent text-center text-xl text-stone-700 placeholder:text-stone-300 focus:outline-none transition-colors ${
                  hasExplicitTarget && !targetIsValid ? "border-red-300" : "border-stone-300 focus:border-stone-500"
                }`}
              />
            </div>
            <button
              type="submit"
              disabled={!canSubmit}
              className="border border-stone-300 px-6 py-3 text-sm tracking-widest text-stone-500 transition-all hover:border-stone-500 hover:text-stone-700 disabled:cursor-not-allowed disabled:opacity-30"
            >
              place
            </button>
          </form>

          <button
            onClick={() => {
              setInputX("");
              setInputY("");
              void newGame();
            }}
            disabled={loading}
            className="mt-8 border border-stone-300 px-8 py-3 text-sm tracking-widest text-stone-500 transition-all hover:border-stone-500 hover:text-stone-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            new game
          </button>
        </main>

        <aside className="border border-stone-200 bg-stone-100/50 p-5 backdrop-blur-sm">
          <h2 className="text-sm tracking-[0.2em] text-stone-600">GAME HISTORY</h2>
          <p className="mt-1 text-xs tracking-wider text-stone-400">Chronological</p>

          <div className="mt-4 max-h-[65vh] space-y-3 overflow-y-auto pr-1">
            {history.length === 0 && <p className="text-sm text-stone-400">No games yet.</p>}
            {history.map((game) => (
              <div key={game.id} className="border border-stone-200 bg-stone-50/60 p-3">
                <div className="flex items-start justify-between gap-4 text-xs">
                  <span className="font-mono text-stone-400">{game.id.slice(0, 8)}</span>
                  <span className={`tracking-wider ${game.bot_type === "chaos" ? "text-red-400" : "text-stone-500"}`}>
                    {game.bot_type.toUpperCase()}
                  </span>
                </div>
                <div className="mt-2 text-xs tracking-wider text-stone-600">
                  <StatusLabel status={game.status} />
                </div>
                <div className="mt-1 text-xs text-stone-400">Moves: {game.move_count}</div>
                <div className="mt-1 text-[11px] text-stone-400">{formatTimestamp(game.created_at)}</div>
                <div className="mt-3">
                  {game.final_board ? (
                    <MiniBoard board={game.final_board} />
                  ) : (
                    <div className="border border-dashed border-stone-300 px-3 py-2 text-xs tracking-wider text-stone-400">
                      Active game
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </aside>
      </div>

      <style>{`
        @keyframes draw-line {
          from { stroke-dashoffset: 100; }
          to { stroke-dashoffset: 0; }
        }
        @keyframes draw-circle {
          from { stroke-dashoffset: 220; }
          to { stroke-dashoffset: 0; }
        }
        .animate-draw-line {
          animation: draw-line 0.5s ease-out forwards;
        }
        .animate-draw-circle {
          animation: draw-circle 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
