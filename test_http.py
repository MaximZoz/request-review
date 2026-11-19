import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from app import Handler


class HttpReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=3)

    def post(self, text):
        port = self.server.server_address[1]
        connection = HTTPConnection("127.0.0.1", port, timeout=3)
        body = json.dumps({"text": text}).encode("utf-8")
        connection.request("POST", "/api/review", body, {"Content-Type": "application/json"})
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, payload

    def test_page_opens(self):
        port = self.server.server_address[1]
        connection = HTTPConnection("127.0.0.1", port, timeout=3)
        connection.request("GET", "/")
        response = connection.getresponse()
        html = response.read().decode("utf-8")
        connection.close()
        self.assertEqual(response.status, 200)
        self.assertIn("Ручной разбор", html)

    def test_failures_clear_draft_for_the_manager(self):
        cases = [
            ("   ", 422, "empty_input"),
            ("таймаут связи", 504, "timeout"),
            ("битый ответ", 422, "invalid_ai"),
        ]
        for text, status, reason in cases:
            with self.subTest(text=text):
                code, body = self.post(text)
                self.assertEqual(code, status)
                self.assertEqual(body["draft"], "")
                self.assertTrue(body["manual"])
                self.assertEqual(body["reason"], reason)

    def test_valid_request_returns_draft(self):
        code, body = self.post("нет квитанции")
        self.assertEqual(code, 200)
        self.assertFalse(body["manual"])
        self.assertIn("квитанции", body["draft"])


if __name__ == "__main__":
    unittest.main()
