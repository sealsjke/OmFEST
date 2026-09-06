import json
import random
import socket
import subprocess
import sys
import threading
import unittest
from collections import deque
from pathlib import Path

from server import Maze, Server
from solve import Client, find_path


class MazeTests(unittest.TestCase):
    def test_generated_mazes_are_connected_and_walls_agree(self):
        for seed in range(5):
            maze = Maze(rng=random.Random(seed))
            self.assertEqual(len(maze.walls), 100)
            visited = {(0, 0)}
            queue = deque(visited)
            while queue:
                x, y = queue.popleft()
                self.assertEqual(len(maze.walls[y]), 100)
                for direction, (dx, dy) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
                    nx, ny = x + dx, y + dy
                    wall = maze.walls[y][x][direction]
                    if not (0 <= nx < 100 and 0 <= ny < 100):
                        self.assertEqual(wall, 1)
                        continue
                    self.assertEqual(wall, maze.walls[ny][nx][(direction + 2) % 4])
                    if not wall and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
            self.assertEqual(len(visited), 10000)
            route = find_path(maze.walls, maze.position, maze.goal)
            self.assertTrue(maze.move(route)[0])
            self.assertEqual(maze.position, maze.goal)

    def test_grid_rendering_and_invalid_paths(self):
        maze = Maze(rng=random.Random(7))
        grid = maze.grid()
        self.assertEqual(len(grid), 201)
        self.assertTrue(all(len(row) == 201 for row in grid))
        self.assertEqual(maze.draw().count("P"), 1)
        self.assertEqual(maze.draw().count("E"), 1)
        self.assertFalse(maze.move("N")[0])
        self.assertFalse(maze.move("invalid")[0])
        self.assertEqual(maze.position, (0, 0))
        route = find_path(maze.walls, maze.position, maze.goal)
        self.assertFalse(maze.move(route + "SS")[0])
        self.assertEqual(maze.position, (0, 0))
        self.assertTrue(maze.move(" ".join(route.lower()))[0])

    def test_netcat_menu_and_solver_ten_rounds(self):
        flag = "OmFEST{integration_test_flag}"
        with Server(("127.0.0.1", 0), flag=flag) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                with socket.create_connection(server.server_address, timeout=10) as connection:
                    client = Client(connection)
                    self.assertNotIn(flag, client.read_until())
                    client.send("1")
                    drawing = client.read_until().split("\n\nМеню:")[0].splitlines()
                    self.assertEqual(len(drawing), 201)
                    self.assertTrue(all(len(row) == 201 for row in drawing))
                    client.send("6")
                    grid = json.loads(client.read_until().splitlines()[0])
                    self.assertEqual(len(grid), 201)
                    client.send("3")
                    client.read_until(b"path> ")
                    client.send("N")
                    self.assertIn("Стена", client.read_until())
                    # A second connection completes ten rounds independently.
                    result = subprocess.run(
                        [sys.executable, str(Path(__file__).with_name("solve.py")),
                         "127.0.0.1", str(server.server_address[1])],
                        capture_output=True, text=True, timeout=60,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.count("Solved "), 10)
                    self.assertIn("FLAG: " + flag, result.stdout)
                    client.send("4")
                    self.assertTrue(client.read_until().startswith("0/10\n"))
                    client.send("0")
                    self.assertEqual(client.read_until(), "")
            finally:
                server.shutdown()
                thread.join()


if __name__ == "__main__":
    unittest.main()
