#!/usr/bin/env python3
import random
import socket
import time

HOST = "0.0.0.0"
PORT = 9001
FLAG = "OmFEST{y0u_l1k3_0p3nh31m3r}"


def make_problem():
    a = random.randint(1, 50)
    b = random.randint(1, 50)
    op = random.choice(["+", "-", "*"])

    if op == "+":
        answer = a + b
    elif op == "-":
        answer = a - b
    else:
        answer = a * b

    return f"{a} {op} {b} = ", answer


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

            conn.sendall(
                f"Привет, твоя задача - набрать 30 баллов\n"
                f"Верный ответ +1 балл | Неверный ответ -5 баллов\n"
            )

            while score < 30:
                problem, answer = make_problem()
                conn.sendall((problem + "\nYour answer: ").encode())

                data = conn.recv(1024)
                if not data:
                    break

                try:
                    user_answer = int(data.strip())
                except ValueError:
                    score -= 5
                    conn.sendall(
                        f"Неверно! Ответ был {answer}. Счет: {score}\n\n".encode()
                    )
                    continue

                if user_answer == answer:
                    score += 1
                    conn.sendall(f"Верно! Счет: {score}\n\n".encode())
                else:
                    score -= 5
                    conn.sendall(
                        f"Неверно! Ответ был {answer}. Счет: {score}\n\n".encode()
                    )

            if score >= 30:
                conn.sendall(
                    f"Поздравляем! Ваш счет {score}.\n"
                    f"флаг: {FLAG}\n".encode()
                )
