import http.client
import sqlite3
from contextlib import closing
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

import app


class ChallengeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        app.DATABASE = Path(cls.temp.name) / "test.db"
        app.initialize_database()
        cls.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, method, path, data=None, cookie=None):
        connection = http.client.HTTPConnection(*self.server.server_address)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if cookie:
            headers["Cookie"] = cookie
        connection.request(method, path, urlencode(data) if data else None, headers)
        response = connection.getresponse()
        result = response.status, response.getheaders(), response.read().decode()
        connection.close()
        return result

    def test_complete_challenge(self):
        credentials = {"username": "contestant", "password": "test-password", "role": "admin"}
        status, headers, _ = self.request("POST", "/register", credentials)
        self.assertEqual(status, 303)
        cookie = "; ".join(value.split(";", 1)[0] for key, value in headers if key.lower() == "set-cookie")
        self.assertIn("role=user", cookie)
        with closing(sqlite3.connect(app.DATABASE)) as db:
            self.assertEqual(db.execute("SELECT role FROM users WHERE username='contestant'").fetchone()[0], "user")
        self.assertIn('href="/flag"', self.request("GET", "/", cookie=cookie)[2])
        for denied_cookie in (None, cookie):
            status, _, body = self.request("GET", "/flag", cookie=denied_cookie)
            self.assertEqual(status, 403)
            self.assertNotIn(app.FLAG, body)
        status, _, body = self.request("GET", "/flag", cookie=cookie.replace("role=user", "role=admin"))
        self.assertEqual(status, 200)
        self.assertIn(app.FLAG, body)
        self.assertEqual(self.request("POST", "/register", credentials)[0], 409)
        self.assertEqual(self.request("POST", "/login", {"username": "contestant", "password": "wrong"})[0], 401)
        status, headers, _ = self.request("POST", "/login", credentials)
        self.assertEqual(status, 303)
        self.assertIn(("Set-Cookie", "role=user; Path=/"), headers)
        status, headers, _ = self.request("GET", "/logout", cookie=cookie)
        self.assertEqual(status, 303)
        self.assertEqual(sum("Max-Age=0" in value for key, value in headers if key.lower() == "set-cookie"), 2)


if __name__ == "__main__":
    unittest.main()
