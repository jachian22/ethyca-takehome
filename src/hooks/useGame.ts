import { useCallback, useEffect, useRef, useState } from "react";
import { ApiRequestError, apiRequest } from "../lib/api";
import type {
  Board,
  BotType,
  CreateGameResponse,
  GameDetail,
  GameStatus,
  GameSummary,
  GamesListResponse,
  MakeMoveResponse,
  Player,
  Position,
} from "../types";

const EMPTY_BOARD: Board = [
  [".", ".", "."],
  [".", ".", "."],
  [".", ".", "."],
];

const BOT_DELAY_MS = 900;

interface UseGameState {
  gameId: string | null;
  board: Board;
  status: GameStatus;
  currentTurn: Player | null;
  botType: BotType | null;
  message: string | null;
  error: string | null;
  validMoves: Position[];
  history: GameSummary[];
  loading: boolean;
  isBotThinking: boolean;
}

function cloneBoard(board: Board): Board {
  return board.map((row) => [...row]) as Board;
}

function getValidMoves(board: Board): Position[] {
  const validMoves: Position[] = [];
  for (let y = 0; y < 3; y += 1) {
    for (let x = 0; x < 3; x += 1) {
      if (board[y][x] === ".") {
        validMoves.push({ x, y });
      }
    }
  }
  return validMoves;
}

function getChaosMessage(botType: BotType | null): string | null {
  return botType === "chaos" ? "You're facing the Chaos Bot!" : null;
}

export function useGame() {
  const [state, setState] = useState<UseGameState>({
    gameId: null,
    board: EMPTY_BOARD,
    status: "in_progress",
    currentTurn: "X",
    botType: null,
    message: null,
    error: null,
    validMoves: getValidMoves(EMPTY_BOARD),
    history: [],
    loading: true,
    isBotThinking: false,
  });
  const botTimeoutRef = useRef<number | null>(null);

  const clearBotTimeout = useCallback(() => {
    if (botTimeoutRef.current !== null) {
      window.clearTimeout(botTimeoutRef.current);
      botTimeoutRef.current = null;
    }
  }, []);

  const refreshHistory = useCallback(async () => {
    try {
      const response = await apiRequest<GamesListResponse>("/games");
      setState((prev) => ({ ...prev, history: response.games }));
    } catch {
      // Keep existing history if request fails; gameplay should still work.
    }
  }, []);

  const setFromGameDetail = useCallback((game: GameDetail) => {
    setState((prev) => ({
      ...prev,
      gameId: game.id,
      board: game.board,
      status: game.status,
      currentTurn: game.current_turn,
      botType: game.bot_type,
      message: getChaosMessage(game.bot_type),
      error: null,
      validMoves: game.status === "in_progress" ? getValidMoves(game.board) : [],
      loading: false,
      isBotThinking: false,
    }));
  }, []);

  const setFromCreateResponse = useCallback(
    (response: CreateGameResponse) => {
      clearBotTimeout();

      if (response.bot_move && response.starting_player === "O") {
        const boardBeforeBot = cloneBoard(response.board);
        boardBeforeBot[response.bot_move.y][response.bot_move.x] = ".";

        setState((prev) => ({
          ...prev,
          gameId: response.id,
          board: boardBeforeBot,
          status: "in_progress",
          currentTurn: "O",
          botType: response.bot_type,
          message: response.message ?? getChaosMessage(response.bot_type),
          error: null,
          validMoves: getValidMoves(boardBeforeBot),
          loading: false,
          isBotThinking: true,
        }));

        botTimeoutRef.current = window.setTimeout(() => {
          setState((prev) => ({
            ...prev,
            board: response.board,
            status: response.status,
            currentTurn: response.current_turn,
            botType: response.bot_type,
            message: response.message ?? getChaosMessage(response.bot_type),
            validMoves: response.status === "in_progress" ? getValidMoves(response.board) : [],
            isBotThinking: false,
          }));
          void refreshHistory();
        }, BOT_DELAY_MS);
      } else {
        setState((prev) => ({
          ...prev,
          gameId: response.id,
          board: response.board,
          status: response.status,
          currentTurn: response.current_turn,
          botType: response.bot_type,
          message: response.message ?? getChaosMessage(response.bot_type),
          error: null,
          validMoves: response.status === "in_progress" ? getValidMoves(response.board) : [],
          loading: false,
          isBotThinking: false,
        }));
        void refreshHistory();
      }
    },
    [clearBotTimeout, refreshHistory]
  );

  const handleApiError = useCallback((error: unknown) => {
    if (error instanceof ApiRequestError) {
      setState((prev) => ({
        ...prev,
        error: error.payload?.message ?? error.message,
        validMoves: error.payload?.valid_moves ?? prev.validMoves,
        loading: false,
        isBotThinking: false,
      }));
      return;
    }

    setState((prev) => ({
      ...prev,
      error: "Unable to connect to the API.",
      loading: false,
      isBotThinking: false,
    }));
  }, []);

  const newGame = useCallback(async () => {
    clearBotTimeout();
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = await apiRequest<CreateGameResponse>("/games", {
        method: "POST",
      });
      setFromCreateResponse(response);
    } catch (error) {
      handleApiError(error);
    }
  }, [clearBotTimeout, handleApiError, setFromCreateResponse]);

  const makeMove = useCallback(
    async (x: number, y: number) => {
      if (!state.gameId || state.status !== "in_progress" || state.currentTurn !== "X" || state.isBotThinking) {
        return;
      }

      setState((prev) => ({ ...prev, error: null }));

      try {
        const response = await apiRequest<MakeMoveResponse>(`/games/${state.gameId}/moves`, {
          method: "POST",
          body: JSON.stringify({ x, y }),
        });

        if (response.bot_move) {
          const boardAfterHuman = cloneBoard(state.board);
          boardAfterHuman[y][x] = "X";

          clearBotTimeout();
          setState((prev) => ({
            ...prev,
            board: boardAfterHuman,
            status: "in_progress",
            currentTurn: "O",
            message: prev.message,
            validMoves: getValidMoves(boardAfterHuman),
            isBotThinking: true,
          }));

          botTimeoutRef.current = window.setTimeout(() => {
            setState((prev) => ({
              ...prev,
              board: response.board,
              status: response.status,
              currentTurn: response.current_turn,
              message: response.message ?? prev.message,
              validMoves: response.status === "in_progress" ? getValidMoves(response.board) : [],
              isBotThinking: false,
            }));
            void refreshHistory();
          }, BOT_DELAY_MS);
        } else {
          setState((prev) => ({
            ...prev,
            board: response.board,
            status: response.status,
            currentTurn: response.current_turn,
            message: response.message ?? prev.message,
            validMoves: response.status === "in_progress" ? getValidMoves(response.board) : [],
            isBotThinking: false,
          }));
          void refreshHistory();
        }
      } catch (error) {
        handleApiError(error);
      }
    },
    [clearBotTimeout, handleApiError, refreshHistory, state.board, state.currentTurn, state.gameId, state.isBotThinking, state.status]
  );

  useEffect(() => {
    let isMounted = true;

    async function initializeGame() {
      try {
        const current = await apiRequest<GameDetail>("/games/current");
        if (!isMounted) {
          return;
        }
        setFromGameDetail(current);
        await refreshHistory();
      } catch (error) {
        if (!isMounted) {
          return;
        }

        if (error instanceof ApiRequestError && error.status === 404 && error.payload?.error === "game_not_found") {
          await newGame();
          return;
        }

        handleApiError(error);
      }
    }

    void initializeGame();

    return () => {
      isMounted = false;
      clearBotTimeout();
    };
  }, [clearBotTimeout, handleApiError, newGame, refreshHistory, setFromGameDetail]);

  return {
    ...state,
    makeMove,
    newGame,
    refreshHistory,
  };
}
