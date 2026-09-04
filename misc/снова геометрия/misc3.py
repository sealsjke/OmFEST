#!/usr/bin/env python3
import math
import random
import socket

HOST = "0.0.0.0"
PORT = 9002
FLAG = "OmFEST{y0u_4r3_4_m4th_g3n1us}"


def fmt(x):
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def task_base_height():
    base = random.randint(6, 30)
    height = random.randint(4, 20)
    return f"треугольник с основанием {base} и высотой {height}. Найдите площадь.", base * height / 2


def task_right_triangle():
    a = random.randint(3, 20)
    b = random.randint(3, 20)
    return f"Прямоугольный треугольник: катеты = {a} и {b}. Найдите площадь.", a * b / 2


def task_heron():
    while True:
        a = random.randint(5, 15)
        b = random.randint(5, 15)
        c = random.randint(abs(a - b) + 1, a + b - 1)
        p = (a + b + c) / 2
        value = p * (p - a) * (p - b) * (p - c)
        if value > 0:
            return (
                f"треугольник со сторонами {a}, {b}, {c}. Найдите площадь (используйте формулу Герона).",
                math.sqrt(value),
            )


def task_coordinates():
    while True:
        x1, y1 = random.randint(-8, 8), random.randint(-8, 8)
        x2, y2 = random.randint(-8, 8), random.randint(-8, 8)
        x3, y3 = random.randint(-8, 8), random.randint(-8, 8)
        determinant = abs(
            x1 * (y2 - y3)
            + x2 * (y3 - y1)
            + x3 * (y1 - y2)
        )
        if determinant:
            return (
                f"треугольник с вершинами A({x1},{y1}), B({x2},{y2}), C({x3},{y3}). Найдите площадь.",
                determinant / 2,
            )


def task_two_sides_angle():
    angle = random.choice([30, 45, 60, 90])
    a = random.randint(4, 16)
    b = random.randint(4, 16)
    area = 0.5 * a * b * math.sin(math.radians(angle))
    return (
        f"треугольник с двумя сторонами {a} и {b} и углом между ними {angle}°. Найдите площадь.",
        area,
    )


def task_equilateral():
    # a chosen so the area is easy-ish but can still be irrational.
    side = random.choice([4, 6, 8, 10, 12])
    area = side * side * math.sqrt(3) / 4
    return (
        f"Равносторонний треугольник: сторона = {side}. Найдите площадь. Вы можете ответить десятичным числом.",
        area,
    )


def make_task():
    return random.choice([
        task_base_height,
        task_right_triangle,
        task_heron,
        task_coordinates,
        task_two_sides_angle,
        task_equilateral,
    ])()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        with conn:
            print(f"Connection from {addr}")
            score = 0
            solved = 0

            conn.sendall(
                f"реши 10 задач по геометрии\n"
                f"Правильный ответ: +1 балл | Неправильный ответ: -5 баллов\n"
                f"Вы должны правильно решить все 10 задач, чтобы получить флаг.\n\n"
            )

            for i in range(1, 11):
                question, answer = make_task()
                conn.sendall(f"Task {i}/10\n{question}\nYour answer: ".encode())

                data = conn.recv(1024)
                if not data:
                    break

                try:
                    user_answer = float(data.decode().strip().replace(",", "."))
                    correct = abs(user_answer - answer) <= 0.01
                except (ValueError, UnicodeDecodeError):
                    correct = False

                if correct:
                    score += 1
                    solved += 1
                    conn.sendall(f"Correct! Score: {score}\n\n".encode())
                else:
                    score -= 5
                    conn.sendall(
                        f"Wrong! Correct answer: {fmt(answer)}. Score: {score}\n\n".encode()
                    )

            if solved == 10:
                conn.sendall(
                    f"Поздравляем! Вы решили все 10 задач.\n"
                    f"Финальный счет: {score}\n"
                    f"ФЛАГ: {FLAG}\n".encode()
                )
            else:
                conn.sendall(
                    f"Испытание завершено. Вы не решили все 10 задач правильно.\n"
                )
