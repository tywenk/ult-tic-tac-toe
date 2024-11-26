from __future__ import annotations

from enum import Enum

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, PositiveInt

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Status(Enum):
    PENDING = "pending"
    TIED = "tied"
    O = "O"  # noqa
    X = "X"


class Player(Enum):
    O = "O"  # noqa
    X = "X"

    def other(self) -> Player:
        return Player.O if self == Player.X else Player.X


class Cell(BaseModel):
    status: Status


class Quadrant(BaseModel):
    state: list[Cell]
    status: Status
    is_interactive: bool


class Board(BaseModel):
    state: list[Quadrant]
    status: Status
    next_player: Player

    @classmethod
    def new(cls) -> Board:
        return Board(
            state=[
                Quadrant(
                    state=[Cell(status=Status.PENDING) for _ in range(9)],
                    status=Status.PENDING,
                    is_interactive=True,
                )
                for _ in range(9)
            ],
            status=Status.PENDING,
            next_player=Player.X,
        )


# Create an empty board on server startup
board = Board.new()


@app.get("/board", response_model=Board)
async def get_board():
    return board


def is_valid_move(quadrant: Quadrant, cell: Cell) -> bool:
    return quadrant.is_interactive and cell.status is Status.PENDING


def is_valid_player(player: Player) -> bool:
    return player == board.next_player


def determine_item_status(player: Player, *, item: Quadrant | Board) -> Status:
    players_selections_set = set(
        idx for idx, cell in enumerate(item.state) if cell.status == player
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
        return player
    if all(_.status != Status.PENDING for _ in item.state):
        return Status.TIED
    else:
        return Status.PENDING


@app.put("/board", response_model=Board)
async def update_board(
    player: Player,
    quad_index: PositiveInt = Query(ge=0, lt=9),
    cell_index: PositiveInt = Query(ge=0, lt=9),
):
    quadrant = board.state[quad_index]
    cell = quadrant.state[cell_index]

    # Validate that the player is allowed to make a move
    if not is_valid_move(quadrant, cell):
        raise HTTPException(status_code=400, detail="Move is not valid")

    if not is_valid_player(player):
        raise HTTPException(status_code=400, detail="Player is not valid")

    # Validate that a player has not won
    if board.status != Status.PENDING:
        raise HTTPException(status_code=400, detail="Someone has already won")

    # Check and update cell status
    cell.status = player

    # Check and update qudarant status
    quadrant.status = determine_item_status(player, item=quadrant)

    # Normalize interactivity
    for q in board.state:
        q.is_interactive = False

    targeted_quad = board.state[cell_index]

    if targeted_quad.status != Status.PENDING:
        pending_quads = [q for q in board.state if q.status == Status.PENDING]
        for q in pending_quads:
            q.is_interactive = True
    else:
        targeted_quad.is_interactive = True

    # Check and update board status
    board.status = determine_item_status(player, item=board)

    # Update the next player
    board.next_player = player.other()

    return board


@app.delete("/board", status_code=204, response_model=None)
async def restart_board():
    global board
    board = Board.new()
