from enum import Enum
from typing import Tuple

from fastapi import FastAPI, Query
from pydantic import BaseModel, PositiveInt

app = FastAPI()


class Status(Enum):
    PENDING = "pending"
    DONE = "done"


class CellState(Enum):
    O = "O"  # noqa
    X = "X"
    EMPTY = "empty"


class Player(Enum):
    O = "O"  # noqa
    X = "X"


class Cell(BaseModel):
    cell_state: CellState


class Quadrant(BaseModel):
    quad_state: list[Cell]
    quad_status: Status
    is_interactive: bool
    winner: Player | None


class Board(BaseModel):
    board_state: list[Quadrant]
    board_status: Status
    next_player: Player
    winner: Player | None


# Create an empty board on server startup
board = Board(
    board_state=[
        Quadrant(
            quad_state=[Cell(cell_state=CellState.EMPTY) for _ in range(9)],
            quad_status=Status.PENDING,
            is_interactive=True,
        )
        for _ in range(9)
    ],
    board_status=Status.PENDING,
    next_player=Player.X,
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/board", response_model=Board)
async def get_board():
    return board


def is_valid_move(quadrant: Quadrant, cell: Cell) -> bool:
    return quadrant.is_interactive and cell.cell_state == CellState.EMPTY


def is_valid_player(player: Player) -> bool:
    return player == board.next_player


def determine_quad_status(player: Player, quadrant: Quadrant) -> Tuple[Status, bool]:
    players_selections_set = set(
        cell for cell in quadrant.quad_state if cell.cell_state == player
    )

    winning_sets = [
        {0, 1, 2},
        {3, 4, 5},
        {6, 7, 8},
        {0, 3, 6},
        {1, 4, 7},
        {2, 5, 8},
        {0, 4, 8},
        {2, 4, 6},
    ]

    is_player_won = any(
        win_set.issubset(players_selections_set) for win_set in winning_sets
    )

    if is_player_won:
        return (Status.DONE, True)
    if sum(quadrant.quad_state, lambda cell: cell.cell_state != CellState.EMPTY) == 9:
        return (Status.DONE, False)
    else:
        return (Status.PENDING, False)


@app.put("/board", response_model=Board)
async def update_board(
    player: Player,
    quad_index: PositiveInt = Query(ge=0, lt=9),
    cell_index: PositiveInt = Query(ge=0, lt=9),
):
    quadrant = board.board_state[quad_index]
    cell = quadrant.quad_state[cell_index]

    # Validate that the player is allowed to make a move
    if not is_valid_move(quadrant, cell) or not is_valid_player(player):
        raise Exception("Player or move is not valid")

    # Check and update cell status
    cell.cell_state = player

    # Check and update qudarant status
    # check if quad was won/tied
    quad_status, is_player_winner = determine_quad_status(player, quadrant)
    quadrant.quad_status = quad_status
    if is_player_winner:
        quadrant.winner = player

    # get active quad

    # update which quads are active

    # Check and update board status

    #
    return board


@app.delete("/board")
async def restart_board():
    return ""
