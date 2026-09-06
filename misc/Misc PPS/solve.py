"""Retrieve wall matrices, find routes with BFS, and solve all ten rounds."""

import argparse
import json
import socket
from collections import deque


def find_path(walls, start, goal):
    start, goal = tuple(start), tuple(goal)
    queue = deque([start])
    parents = {start: None}
    directions = (("N", 0, -1), ("E", 1, 0), ("S", 0, 1), ("W", -1, 0))
    while queue:
        x, y = queue.popleft()
        if (x, y) == goal:
            path = []
            current = goal
            while parents[current] is not None:
                current, letter = parents[current]
                path.append(letter)
            return "".join(reversed(path))
        for direction, (letter, dx, dy) in enumerate(directions):
            neighbor = (x + dx, y + dy)
            if (not walls[y][x][direction] and 0 <= neighbor[1] < len(walls)
                    and 0 <= neighbor[0] < len(walls[0]) and neighbor not in parents):
                parents[neighbor] = ((x, y), letter)
                queue.append(neighbor)
    raise ValueError("Maze has no solution")


class Client:
    def __init__(self, connection):
        self.connection = connection
        self.buffer = b""

    def read_until(self, marker=b">> "):
        while marker not in self.buffer:
            chunk = self.connection.recv(65536)
            if not chunk:
                result, self.buffer = self.buffer, b""
                return result.decode("utf-8")
            self.buffer += chunk
        end = self.buffer.index(marker) + len(marker)
        result, self.buffer = self.buffer[:end], self.buffer[end:]
        return result.decode("utf-8")

    def send(self, value):
        self.connection.sendall((value + "\n").encode("utf-8"))


def solve(host, port):
    with socket.create_connection((host, port), timeout=30) as connection:
        client = Client(connection)
        client.read_until()
        for round_number in range(1, 11):
            client.send("2")
            walls = json.loads(client.read_until().splitlines()[0])
            client.send("5")
            state = json.loads(client.read_until().splitlines()[0])
            path = find_path(walls, state["position"], state["goal"])
            client.send("3")
            client.read_until(b"path> ")
            client.send(path)
            response = client.read_until()
            if "Лабиринт пройден!" not in response:
                raise RuntimeError(f"Route rejected: {response}")
            print(f"Solved {round_number}/10 ({len(path)} moves)", flush=True)
            for line in response.splitlines():
                if line.startswith("FLAG: "):
                    print(line, flush=True)
                    return line[6:]
        raise RuntimeError("Ten rounds completed but no flag received")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", nargs="?", default="127.0.0.1")
    parser.add_argument("port", nargs="?", type=int, default=30003)
    args = parser.parse_args()
    solve(args.host, args.port)
