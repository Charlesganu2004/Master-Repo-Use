"""Exercise real local HTTP forwarding; no model/provider is contacted."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tests.test_token_limit_and_super_mode import IsolatedStore, harness_proxy


class ProxyBudgetHTTP(IsolatedStore):
    def setUp(self):
        super().setUp()
        self.requests = []
        records = self.requests

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *args):
                return

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                records.append((body, dict(self.headers)))
                result = json.dumps(body).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(result)))
                self.end_headers()
                self.wfile.write(result)

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        handler = type("IsolatedProxy", (harness_proxy.Handler,), {
            "upstream": f"http://127.0.0.1:{upstream.server_port}",
            "log_metadata": False,
        })
        proxy = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.url = f"http://127.0.0.1:{proxy.server_port}/v1/chat/completions"
        for server in (upstream, proxy):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(thread.join, 5)
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)

    def send(self, text, session=None, **extra):
        headers = {"Content-Type": "application/json"}
        if session is not None:
            headers["X-Master-Harness-Session"] = session
        body = {"messages": [{"role": "system", "content": harness_proxy.MARKER},
                             {"role": "user", "content": text}], **extra}
        request = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers=headers)
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response)

    def test_wire_cap_persistence_reset_and_header_removal(self):
        first = self.send("/token limit 40 write", "alpha", max_tokens=900)
        self.assertEqual(first["max_tokens"], 40)
        self.assertEqual(len(first["messages"]), 2)
        self.assertFalse(any(key.lower() == "x-master-harness-session"
                             for key in self.requests[-1][1]))
        self.assertEqual(self.send("continue", "alpha")["max_tokens"], 40)
        self.assertNotIn("max_tokens", self.send("continue", "beta"))
        self.assertNotIn("max_tokens", self.send("continue"))
        self.assertNotIn("max_tokens", self.send("/token limit off", "alpha"))
        self.assertNotIn("max_tokens", self.send("continue", "alpha"))

    def test_invalid_header_is_not_forwarded(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.send("hello", "x" * 257)
        self.assertEqual(error.exception.code, 400)
        error.exception.close()
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
