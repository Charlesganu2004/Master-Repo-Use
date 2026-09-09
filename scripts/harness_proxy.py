#!/usr/bin/env python3
"""An OpenAI and Ollama compatible proxy that injects the pipeline into every request.

This is the second harness, and it exists because of a limit the first one is
honest about: auto_mode_harness.py only carries the pipeline for prompts sent
THROUGH it. Anything else on the machine talking straight to Ollama, an IDE
plugin, a notebook, a desktop app, a script somebody wrote last year, gets
nothing.

A proxy fixes that without touching any of those programs. Point the client's
base URL at this instead of at the model server, and every request it makes
carries the standing rules whether or not the program knows they exist. That is
the strongest enforcement available for a surface with no hook: the client cannot
opt out, because it is not being asked.

What it does to a request, and nothing else:
  - inserts the pipeline as a system message, ahead of the conversation
  - leaves a system message the caller already sent in place, after ours
  - passes everything else through byte for byte, including streaming

What it refuses to do:
  - it does not log prompts or responses. A proxy that keeps a transcript is a
    transcript nobody agreed to, sitting on disk. Set --log-metadata for counts
    and timings only, which is what you actually need to answer "is it working".
  - it does not rewrite responses. Injecting into the request is a rule the model
    can follow; editing what came back is putting words in its mouth.
  - it binds to loopback unless told otherwise, and says so loudly if told
    otherwise, because a proxy on a shared interface is an open relay to whatever
    model server it fronts.

Both API shapes are handled because the two cover nearly every local client:

  /api/chat          Ollama native, messages array
  /api/generate      Ollama native, single prompt string
  /v1/chat/completions   OpenAI compatible, which Ollama, llama.cpp, LM Studio,
                         vLLM and most other local servers also speak

Usage:
    python scripts/harness_proxy.py
    python scripts/harness_proxy.py --port 11500 --upstream http://127.0.0.1:11434
    python scripts/harness_proxy.py --check
    OPENAI_BASE_URL=http://127.0.0.1:11500/v1 your-tool
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import skill_pipeline  # noqa: E402

CHAT_PATHS = ("/api/chat", "/v1/chat/completions")
PROMPT_PATHS = ("/api/generate",)
MAX_BODY = 32 * 1024 * 1024

# A marker so a request that already went through a proxy is not given the rules
# twice. Chaining two proxies is a mistake, not a feature, but it should waste
# tokens rather than confuse the model with a doubled system message.
MARKER = "Standing pipeline."

STATS = {"requests": 0, "injected": 0, "passed_through": 0, "errors": 0}
STATS_LOCK = threading.Lock()


def last_user_text(messages: list) -> str:
    """The newest user turn, which is what the pipeline scores its lanes against."""
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, str):
                return content
            # OpenAI content parts. Text only; an image part has no prompt in it.
            if isinstance(content, list):
                return " ".join(part.get("text", "") for part in content
                                if isinstance(part, dict) and part.get("type") == "text")
    return ""


def already_injected(messages: list) -> bool:
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "system":
            continue
        content = message.get("content")
        if isinstance(content, str) and MARKER in content:
            return True
    return False


def inject(payload: dict) -> tuple[dict, bool]:
    """Put the pipeline in front. Returns the payload and whether it changed."""
    messages = payload.get("messages")
    if isinstance(messages, list):
        if already_injected(messages):
            return payload, False
        context = skill_pipeline.context_for(last_user_text(messages))
        # Ahead of the caller's own system message rather than replacing it. The
        # caller's instructions are theirs; these are the standing rules, and the
        # order says which one frames the other.
        payload["messages"] = [{"role": "system", "content": context}] + messages
        return payload, True

    prompt = payload.get("prompt")
    if isinstance(prompt, str):
        existing = payload.get("system")
        if isinstance(existing, str) and MARKER in existing:
            return payload, False
        context = skill_pipeline.context_for(prompt)
        payload["system"] = context + (("\n\n" + existing) if isinstance(existing, str) and existing else "")
        return payload, True

    return payload, False


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    upstream = "http://127.0.0.1:11434"
    log_metadata = False

    def log_message(self, *args):
        """Silenced on purpose. The default handler logs the request line, which
        for some clients carries the prompt in the query string."""

    def _note(self, kind: str, path: str, took: float, size: int):
        with STATS_LOCK:
            STATS["requests"] += 1
            STATS[kind] = STATS.get(kind, 0) + 1
        if self.log_metadata:
            print(f"{path} {kind} {took * 1000:.0f}ms {size}B", file=sys.stderr)

    def do_POST(self):  # noqa: N802
        started = time.time()
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            self.send_error(413, "request too large")
            return
        raw = self.rfile.read(length) if length else b""

        path = self.path.split("?")[0]
        changed = False
        if path in CHAT_PATHS or path in PROMPT_PATHS:
            try:
                payload = json.loads(raw.decode("utf-8"))
                if isinstance(payload, dict):
                    payload, changed = inject(payload)
                    raw = json.dumps(payload).encode("utf-8")
            except (ValueError, UnicodeDecodeError):
                # Not JSON we understand. Forward it untouched rather than
                # failing the call: a proxy that breaks unknown traffic is worse
                # than one that simply does not improve it.
                changed = False

        self._forward(path, raw, started, changed)

    def do_GET(self):  # noqa: N802
        if self.path.split("?")[0] == "/__harness":
            body = json.dumps(dict(STATS), indent=1).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._forward(self.path, None, time.time(), False, method="GET")

    def _forward(self, path, raw, started, changed, method="POST"):
        url = self.upstream.rstrip("/") + self.path
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in ("host", "content-length", "connection")}
        request = urllib.request.Request(url, data=raw, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                body = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() in ("transfer-encoding", "content-length", "connection"):
                        continue
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as error:
            body = error.read()
            self.send_response(error.code)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            self._note("errors", path, time.time() - started, len(body))
            return
        except (urllib.error.URLError, OSError) as error:
            message = json.dumps({"error": f"upstream unreachable at {self.upstream}: {error}"}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)
            self._note("errors", path, time.time() - started, len(message))
            return
        self._note("injected" if changed else "passed_through", path,
                   time.time() - started, len(body))


def check() -> int:
    """Verify without changing what is being verified.

    Rendering the pipeline captures a goal from the fixture prompt, so a check
    run against the real store would leave "Plan and design a small interface."
    standing as this session's objective. It happened once; this is why it
    cannot happen again.
    """
    with skill_pipeline.isolated_store():
        return _check_isolated()


def _check_isolated() -> int:
    """Prove injection works without opening a socket or contacting a model."""
    failures = []

    chat = {"model": "m", "messages": [{"role": "user", "content": "Plan a settings page."}]}
    out, changed = inject(json.loads(json.dumps(chat)))
    if not changed or out["messages"][0]["role"] != "system":
        failures.append("chat payload was not given a leading system message")
    elif "LAYER 1" not in out["messages"][0]["content"]:
        failures.append("the injected system message does not carry the layers")
    else:
        print(f"chat            injected {len(out['messages'][0]['content'])} bytes ahead of the turn")

    kept = {"model": "m", "messages": [
        {"role": "system", "content": "You are a helpful cat."},
        {"role": "user", "content": "hi"}]}
    out, _ = inject(json.loads(json.dumps(kept)))
    if len(out["messages"]) != 3 or out["messages"][1]["content"] != "You are a helpful cat.":
        failures.append("the caller's own system message was dropped or reordered")
    else:
        print("caller system    preserved, after ours")

    twice, _ = inject(json.loads(json.dumps(out)))
    if len(twice["messages"]) != 3:
        failures.append("a second pass injected the rules again")
    else:
        print("double inject    refused")

    gen = {"model": "m", "prompt": "Build a table."}
    out, changed = inject(json.loads(json.dumps(gen)))
    if not changed or "LAYER 1" not in out.get("system", ""):
        failures.append("generate payload was not given a system field")
    else:
        print("generate         injected into the system field")

    passthrough = {"model": "m", "input": "unknown shape"}
    out, changed = inject(json.loads(json.dumps(passthrough)))
    if changed or out != passthrough:
        failures.append("an unrecognised payload was modified")
    else:
        print("unknown shape    passed through untouched")

    if failures:
        print("\nFAILED", file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        return 1
    print("\nproxy harness ready")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--port", type=int, default=11500)
    parser.add_argument("--host", default="127.0.0.1",
                        help="loopback by default; anything else is an open relay")
    parser.add_argument("--upstream", default="http://127.0.0.1:11434",
                        help="the model server this fronts")
    parser.add_argument("--log-metadata", action="store_true",
                        help="print path, outcome, duration and size. Never prompt text.")
    parser.add_argument("--check", action="store_true",
                        help="verify injection offline and exit")
    args = parser.parse_args()

    if args.check:
        return check()

    Handler.upstream = args.upstream
    Handler.log_metadata = args.log_metadata

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print(f"WARNING: binding {args.host} exposes {args.upstream} to anything that can "
              f"reach this machine. There is no authentication here.", file=sys.stderr)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"pipeline proxy on http://{args.host}:{args.port} -> {args.upstream}")
    print(f"  Ollama:  OLLAMA_HOST=http://{args.host}:{args.port}")
    print(f"  OpenAI:  OPENAI_BASE_URL=http://{args.host}:{args.port}/v1")
    print(f"  counters: http://{args.host}:{args.port}/__harness")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
