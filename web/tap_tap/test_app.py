import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

import app


class GameTest(unittest.TestCase):
    def test_game_and_accounts(self):
        with tempfile.TemporaryDirectory() as directory:
            app.DATABASE = Path(directory) / "users.db"
            app.initialize_database()
            server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
            thread = threading.Thread(target=server.serve_forever)
            thread.start()

            def request(method, path, body=None, headers=None):
                conn = http.client.HTTPConnection(*server.server_address)
                conn.request(method, path, body, headers or {})
                response = conn.getresponse()
                result = response.status, dict(response.getheaders()), response.read().decode()
                conn.close()
                return result

            try:
                status, _, body = request("GET", "/")
                self.assertEqual(status, 200)
                self.assertIn("Нажми 100 000 раз", body)
                self.assertNotIn(app.FLAG, body)
                for path in ("/game.js", "/style.css", "/register", "/login"):
                    status, _, body = request("GET", path)
                    self.assertEqual(status, 200)
                    self.assertNotIn(app.FLAG, body)
                credentials = urlencode({"username": "Игрок", "password": "test"})
                self.assertEqual(request("POST", "/register", credentials)[0], 303)
                self.assertEqual(request("POST", "/register", credentials)[0], 409)
                self.assertEqual(request("POST", "/login", urlencode({"username": "Игрок", "password": "wrong"}))[0], 401)
                status, headers, _ = request("POST", "/login", credentials)
                self.assertEqual(status, 303)
                self.assertIn("Игрок", request("GET", "/", headers={"Cookie": headers["Set-Cookie"]})[2])
                for score in (0, 99999):
                    status, _, body = request("POST", "/api/claim", json.dumps({"score": score}))
                    self.assertEqual(status, 403)
                    self.assertNotIn(app.FLAG, body)
                for score in (100000, 1000000):
                    status, _, body = request("POST", "/api/claim", json.dumps({"score": score}))
                    self.assertEqual(status, 200)
                    self.assertEqual(json.loads(body)["flag"], app.FLAG)
                self.assertEqual(request("GET", "/logout")[0], 303)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == "__main__":
    unittest.main()
