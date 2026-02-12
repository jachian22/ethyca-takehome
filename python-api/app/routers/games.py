from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select

from ..database import get_session
from ..errors import APIError
from ..models import Game, GameStatus, Move, Player
from ..schemas import (
    GameCreateResponse,
    GameDetailResponse,
    GameMoveResponse,
    GameSummary,
    GamesListResponse,
    MoveHistoryItem,
    MoveRequest,
    MovesListResponse,
    Position,
)
from ..services.game_logic import (
    apply_move,
    build_empty_board,
    choose_bot_type,
    choose_starting_player,
    compute_current_turn,
    derive_player,
    evaluate_status,
    get_bot_move,
    reconstruct_board,
    valid_moves,
)

router = APIRouter(prefix="/games", tags=["games"])


def _load_game_or_404(session: Session, game_id: str) -> Game:
    game = session.get(Game, game_id)
    if game is None:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            error="game_not_found",
            message="Game not found.",
        )
    return game


def _load_moves(session: Session, game_id: str) -> list[Move]:
    statement = select(Move).where(Move.game_id == game_id).order_by(Move.move_number.asc())
    return list(session.exec(statement).all())


@router.post("", response_model=GameCreateResponse, status_code=status.HTTP_201_CREATED)
def create_game(session: Session = Depends(get_session)) -> GameCreateResponse:
    active_games_statement = (
        select(Game)
        .where(Game.status == GameStatus.in_progress)
        .order_by(Game.created_at.desc())
    )
    active_games = list(session.exec(active_games_statement).all())

    for active_game in active_games:
        active_game.status = GameStatus.abandoned
        session.add(active_game)

    previous_completed_statement = (
        select(Game)
        .where(Game.status != GameStatus.in_progress)
        .order_by(Game.created_at.desc())
    )
    previous_game = session.exec(previous_completed_statement).first()
    previous_starting_player = previous_game.starting_player if previous_game else None

    starting_player = choose_starting_player(previous_starting_player)
    bot_type = choose_bot_type()

    game = Game(
        status=GameStatus.in_progress,
        starting_player=starting_player,
        bot_type=bot_type,
    )
    session.add(game)
    session.flush()

    board = build_empty_board()
    move_count = 0
    bot_move: Position | None = None

    if starting_player == Player.O:
        chosen_move = get_bot_move(board, bot_type)
        move_count = 1
        session.add(
            Move(
                game_id=game.id,
                move_number=move_count,
                x=chosen_move["x"],
                y=chosen_move["y"],
            )
        )
        board = apply_move(board, chosen_move["x"], chosen_move["y"], Player.O)
        bot_move = Position(**chosen_move)

    session.commit()

    message = "You're facing the Chaos Bot!" if bot_type.value == "chaos" else None

    return GameCreateResponse(
        id=game.id,
        status=game.status,
        starting_player=game.starting_player,
        bot_type=game.bot_type,
        board=board,
        current_turn=compute_current_turn(game.status, game.starting_player, move_count),
        bot_move=bot_move,
        message=message,
    )


@router.get("", response_model=GamesListResponse)
def list_games(session: Session = Depends(get_session)) -> GamesListResponse:
    statement = select(Game).order_by(Game.created_at.asc())
    games = list(session.exec(statement).all())

    response_games: list[GameSummary] = []
    for game in games:
        moves = _load_moves(session, game.id)
        game_move_count = len(moves)
        final_board = None
        if game.status != GameStatus.in_progress:
            final_board = reconstruct_board(game.starting_player, moves)

        response_games.append(
            GameSummary(
                id=game.id,
                status=game.status,
                bot_type=game.bot_type,
                move_count=game_move_count,
                created_at=game.created_at,
                final_board=final_board,
            )
        )

    return GamesListResponse(games=response_games)


@router.get("/current", response_model=GameDetailResponse)
def get_current_game(session: Session = Depends(get_session)) -> GameDetailResponse:
    statement = (
        select(Game)
        .where(Game.status == GameStatus.in_progress)
        .order_by(Game.created_at.desc())
    )
    game = session.exec(statement).first()

    if game is None:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            error="game_not_found",
            message="No in-progress game found.",
        )

    moves = _load_moves(session, game.id)
    board = reconstruct_board(game.starting_player, moves)

    return GameDetailResponse(
        id=game.id,
        status=game.status,
        starting_player=game.starting_player,
        bot_type=game.bot_type,
        created_at=game.created_at,
        board=board,
        current_turn=compute_current_turn(game.status, game.starting_player, len(moves)),
    )


@router.get("/{game_id}", response_model=GameDetailResponse)
def get_game(game_id: str, session: Session = Depends(get_session)) -> GameDetailResponse:
    game = _load_game_or_404(session, game_id)
    moves = _load_moves(session, game.id)
    board = reconstruct_board(game.starting_player, moves)

    return GameDetailResponse(
        id=game.id,
        status=game.status,
        starting_player=game.starting_player,
        bot_type=game.bot_type,
        created_at=game.created_at,
        board=board,
        current_turn=compute_current_turn(game.status, game.starting_player, len(moves)),
    )


@router.post("/{game_id}/moves", response_model=GameMoveResponse)
def make_move(
    game_id: str,
    move_input: MoveRequest,
    session: Session = Depends(get_session),
) -> GameMoveResponse:
    game = _load_game_or_404(session, game_id)
    moves = _load_moves(session, game.id)
    board = reconstruct_board(game.starting_player, moves)

    if game.status != GameStatus.in_progress:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="game_finished",
            message="This game has already finished.",
            valid_moves=valid_moves(board),
        )

    if move_input.x < 0 or move_input.x > 2 or move_input.y < 0 or move_input.y > 2:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="out_of_bounds",
            message="Coordinates must be in range 0-2 for both x and y.",
            valid_moves=valid_moves(board),
        )

    current_turn = compute_current_turn(game.status, game.starting_player, len(moves))
    if current_turn != Player.X:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="not_your_turn",
            message="Please wait for the bot to move.",
            valid_moves=valid_moves(board),
        )

    if board[move_input.y][move_input.x] != ".":
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="cell_occupied",
            message="That cell is already taken. Try another move.",
            valid_moves=valid_moves(board),
        )

    next_move_number = len(moves) + 1
    session.add(
        Move(
            game_id=game.id,
            move_number=next_move_number,
            x=move_input.x,
            y=move_input.y,
        )
    )

    board_after_human = apply_move(board, move_input.x, move_input.y, Player.X)
    status_after_human = evaluate_status(board_after_human)

    if status_after_human != GameStatus.in_progress:
        game.status = status_after_human
        session.add(game)
        session.commit()

        return GameMoveResponse(
            board=board_after_human,
            status=status_after_human,
            current_turn=None,
            bot_move=None,
            message=None,
        )

    chosen_bot_move = get_bot_move(board_after_human, game.bot_type)
    bot_move_number = next_move_number + 1
    session.add(
        Move(
            game_id=game.id,
            move_number=bot_move_number,
            x=chosen_bot_move["x"],
            y=chosen_bot_move["y"],
        )
    )

    board_after_bot = apply_move(board_after_human, chosen_bot_move["x"], chosen_bot_move["y"], Player.O)
    status_after_bot = evaluate_status(board_after_bot)
    game.status = status_after_bot
    session.add(game)
    session.commit()

    return GameMoveResponse(
        board=board_after_bot,
        status=status_after_bot,
        current_turn=compute_current_turn(status_after_bot, game.starting_player, bot_move_number),
        bot_move=Position(**chosen_bot_move),
        message=None,
    )


@router.get("/{game_id}/moves", response_model=MovesListResponse)
def get_game_moves(game_id: str, session: Session = Depends(get_session)) -> MovesListResponse:
    game = _load_game_or_404(session, game_id)
    moves = _load_moves(session, game.id)

    move_items: list[MoveHistoryItem] = []
    for move in moves:
        move_items.append(
            MoveHistoryItem(
                id=move.id,
                move_number=move.move_number,
                x=move.x,
                y=move.y,
                player=derive_player(game.starting_player, move.move_number),
                created_at=move.created_at,
            )
        )

    return MovesListResponse(game_id=game.id, moves=move_items)
