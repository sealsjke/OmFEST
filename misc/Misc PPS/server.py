"""Netcat maze challenge. Python standard library only."""

import json
import os
import random
import socketserver

SIZE = 100
ROUNDS = 10
DIRECTIONS = (("N", 0, -1), ("E", 1, 0), ("S", 0, 1), ("W", -1, 0))
MOVES = {letter: (index, dx, dy) for index, (letter, dx, dy) in enumerate(DIRECTIONS)}
MENU = """
Меню:
1. Показать весь лабиринт (P — игрок, E — выход)
2. Вывести матрицу стен [y][x][N, E, S, W]
3. Загрузить путь или сделать ход (N/E/S/W)
4. Показать количество пройденных лабиринтов
5. Показать позицию игрока и выход [X, Y]
6. Вывести сетку: 1 — стена, 0 — проход
0. Выход
>> """


class Maze:
    def __init__(self, size=SIZE, rng=None):
        self.size = size
        rng = rng or random.SystemRandom()
        self.walls = [[[1, 1, 1, 1] for _ in range(size)] for _ in range(size)]
        self.position = (0, 0)
        self.goal = (size - 1, size - 1)
        visited = {(0, 0)}
        stack = [(0, 0)]
        # Iterative randomized DFS builds a spanning tree of all cells.
        while stack:
            x, y = stack[-1]
            neighbors = [(i, x + dx, y + dy) for i, (_, dx, dy) in enumerate(DIRECTIONS)
                         if 0 <= x + dx < size and 0 <= y + dy < size
                         and (x + dx, y + dy) not in visited]
            if not neighbors:
                stack.pop()
                continue
            direction, nx, ny = rng.choice(neighbors)
            self.walls[y][x][direction] = 0
            self.walls[ny][nx][(direction + 2) % 4] = 0
            visited.add((nx, ny))
            stack.append((nx, ny))

    def move(self, path):
        path = "".join(path.upper().split())
        if not path or any(letter not in MOVES for letter in path):
            return False, "Используйте только N, E, S, W. Позиция не изменена."
        x, y = self.position
        for step, letter in enumerate(path, 1):
            direction, dx, dy = MOVES[letter]
            nx, ny = x + dx, y + dy
            if self.walls[y][x][direction] or not (0 <= nx < self.size and 0 <= ny < self.size):
                return False, f"Стена на шаге {step}. Весь путь отменён."
            x, y = nx, ny
        self.position = (x, y)
        return self.position == self.goal, "Путь принят."

    def grid(self):
        grid = [[1] * (2 * self.size + 1) for _ in range(2 * self.size + 1)]
        for y, row in enumerate(self.walls):
            for x, walls in enumerate(row):
                gx, gy = 2 * x + 1, 2 * y + 1
                grid[gy][gx] = 0
                for direction, (_, dx, dy) in enumerate(DIRECTIONS):
                    if not walls[direction]:
                        grid[gy + dy][gx + dx] = 0
        return grid

    def draw(self):
        canvas = [["#" if value else " " for value in row] for row in self.grid()]
        for (x, y), marker in ((self.goal, "E"), (self.position, "P")):
            canvas[2 * y + 1][2 * x + 1] = marker
        return "\n".join("".join(row) for row in canvas)


class Handler(socketserver.StreamRequestHandler):
    def send(self, text):
        self.wfile.write(text.encode("utf-8"))
        self.wfile.flush()

    def line(self):
        data = self.rfile.readline()
        if not data:
            return None
        return data.decode("utf-8", errors="replace").strip()

    def handle(self):
        try:
            self.play()
        except (ConnectionError, OSError):
            pass  # A disconnected player simply loses their session.

    def play(self):
        maze = Maze()
        solved = 0
        self.send("OmFEST / Misc PPS\nПройдите 10 лабиринтов размером 100 на 100 клеток.\n"
                  "Координаты [X, Y], начало [0, 0], выход [99, 99].\n"
                  "В матрице стен: 1 — стена, 0 — проход. Север уменьшает Y.\n"
                  "Путь вводится одной строкой, например EESSWN.\nЛабиринт 1/10\n")
        while True:
            self.send(MENU)
            choice = self.line()
            if choice is None or choice == "0":
                return
            if choice == "1":
                self.send(maze.draw() + "\n")
            elif choice == "2":
                self.send(json.dumps(maze.walls, separators=(",", ":")) + "\n")
            elif choice == "3":
                self.send("Путь (N/E/S/W), одна строка:\npath> ")
                path = self.line()
                if path is None:
                    return
                won, message = maze.move(path)
                self.send(message + "\n")
                if won:
                    solved += 1
                    self.send(f"Лабиринт пройден! {solved}/{ROUNDS}\n")
                    if solved == ROUNDS:
                        self.send("FLAG: " + self.server.flag + "\n")
                        return
                    maze = Maze()
                    self.send(f"Лабиринт {solved + 1}/{ROUNDS}\n")
            elif choice == "4":
                self.send(f"{solved}/{ROUNDS}\n")
            elif choice == "5":
                self.send(json.dumps({"position": maze.position, "goal": maze.goal}) + "\n")
            elif choice == "6":
                self.send(json.dumps(maze.grid(), separators=(",", ":")) + "\n")
            else:
                self.send("Нет такого пункта меню.\n")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, flag=None):
        self.flag = flag if flag is not None else os.environ.get("FLAG", "OmFEST{H0w_4r3_y0u_do1ng_1n_th3_m4z3?}")
        super().__init__(address, Handler)


if __name__ == "__main__":
    address = (os.environ.get("HOST", "0.0.0.0"), int(os.environ.get("PORT", "30003")))
    with Server(address) as server:
        print(f"Misc PPS listening on {address[0]}:{address[1]}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
