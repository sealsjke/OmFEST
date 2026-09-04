#!/usr/bin/env python3
import base64
import random
import socket
import string

HOST = "0.0.0.0"
PORT = 9000
FLAG = "OmFEST{t00_c00l3st_r4di0ph0n3}"


def random_string(n=24):
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        with conn:
            print(f"Connection from {addr}")
            for i in range(1, 101):
                if i % 10 == 0:
                    payload = base64.b64encode(FLAG.encode()).decode()
                else:
                    payload = random_string()

                conn.sendall((payload + "\n").encode())

                import time
                time.sleep(0.2)
