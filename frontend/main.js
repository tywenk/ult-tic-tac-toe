const base_el = document.getElementById("board");
const board = await request("GET");
base_el.dataset.status = board.status;
let nextPlayer = board.next_player;
const next_player_el = document.getElementById("next-player");
next_player_el.innerText = nextPlayer;
next_player_el.style.color =
  nextPlayer === "X" ? "lightcoral" : "cornflowerblue";

const resetButton = document.getElementById("reset");
resetButton.addEventListener("click", async () => {
  await request("DELETE");
  const board = await request("GET");
  updateBoard(board);
});

// to get quadrant i cell j status, we need to do
// board.state[i].state[j].status
function getCellStatus(i, j) {
  return board.state[i].state[j].status;
}

function makeCell(quad_el, cell_item, quad_index, cell_index) {
  const cell_el = document.createElement("button");
  cell_el.className = "cell";
  cell_el.id = `cell-${quad_index}-${cell_index}`;
  cell_el.innerText = `${
    cell_item.status === "pending" ? "-" : cell_item.status
  }`;
  cell_el.dataset.status = cell_item.status;
  cell_el.disabled = quad_el.dataset.is_interactive === "false";
  cell_el.addEventListener("click", async () => {
    const newBoard = await request("PUT", {
      player: nextPlayer,
      quad_index,
      cell_index,
    });
    updateBoard(newBoard);
  });
  quad_el.appendChild(cell_el);
}

function makeQuadrant(quad_item, quad_index) {
  const quad_el = document.createElement("div");
  quad_el.className = "quadrant";
  quad_el.id = `quad-${quad_index}`;
  quad_el.dataset.status = quad_item.status;
  quad_el.dataset.is_interactive = quad_item.is_interactive;
  for (const [cell_index, cell_item] of board.state.entries()) {
    makeCell(quad_el, cell_item, quad_index, cell_index);
  }
  base_el.appendChild(quad_el);
  return quad_el;
}

function makeBoard(board) {
  for (const [index, quad_item] of board.state.entries()) {
    makeQuadrant(quad_item, index);
  }
}

function updateBoard(board) {
  next_player_el.innerText = board.next_player;
  next_player_el.style.color =
    board.next_player === "X" ? "lightcoral" : "cornflowerblue";
  for (const [index, quad_item] of board.state.entries()) {
    const quad_el = document.getElementById(`quad-${index}`);
    quad_el.dataset.status = quad_item.status;
    quad_el.dataset.is_interactive = quad_item.is_interactive;
    for (const [cell_index, cell_item] of quad_item.state.entries()) {
      const cell_el = document.getElementById(`cell-${index}-${cell_index}`);
      cell_el.innerText = `${
        cell_item.status === "pending" ? "-" : cell_item.status
      }`;
      cell_el.dataset.status = cell_item.status;
      if (quad_item.is_interactive) {
        cell_el.disabled = false;
      } else {
        cell_el.disabled = true;
      }
    }
  }
  base_el.dataset.status = board.status;
  nextPlayer = board.next_player;
}

// Make initial board
makeBoard(board);

async function request(method, params) {
  const query = new URLSearchParams(params);
  const url = `http://localhost:8000/board?${query.toString()}`;
  try {
    const res = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (res.ok) {
      return await res.json();
    } else {
      alert("Something went wrong");
    }
  } catch (e) {
    console.error(e);
  }
}
