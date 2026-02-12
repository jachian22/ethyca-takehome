export type Player = "X" | "O";
export type Cell = "." | Player;
export type Board = [[Cell, Cell, Cell], [Cell, Cell, Cell], [Cell, Cell, Cell]];
export type GameStatus = "in_progress" | "x_wins" | "o_wins" | "draw" | "abandoned";
export type BotType = "smart" | "chaos";

export interface Position {
  x: number;
  y: number;
}

export interface ErrorResponse {
  error: string;
  message: string;
  valid_moves?: Position[];
}

export interface CreateGameResponse {
  id: string;
  status: GameStatus;
  starting_player: Player;
  bot_type: BotType;
  board: Board;
  current_turn: Player | null;
  bot_move: Position | null;
  message: string | null;
}

export interface MakeMoveResponse {
  board: Board;
  status: GameStatus;
  current_turn: Player | null;
  bot_move: Position | null;
  message: string | null;
}

export interface GameSummary {
  id: string;
  status: GameStatus;
  bot_type: BotType;
  move_count: number;
  created_at: string;
  final_board: Board | null;
}

export interface GamesListResponse {
  games: GameSummary[];
}

export interface GameDetail {
  id: string;
  status: GameStatus;
  starting_player: Player;
  bot_type: BotType;
  created_at: string;
  board: Board;
  current_turn: Player | null;
}

export interface MoveHistoryItem {
  id: string;
  move_number: number;
  x: number;
  y: number;
  player: Player;
  created_at: string;
}

export interface MovesListResponse {
  game_id: string;
  moves: MoveHistoryItem[];
}
