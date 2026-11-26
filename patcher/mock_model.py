"""Mock model: a fake model server for tests and CI.

It answers Ollama's /api/chat and the OpenAI /v1/chat/completions (vLLM, Modal), so
`patcher.generate` calls it through `base_url` with either `api` of configs/model.yaml.
It never runs a model. Each call returns one of four replies:

- good       the corrected function from a replies file, in the production layout
- malformed  prose and a unified diff, no code block (breaks the layout)
- empty      an empty string
- unchanged  the vulnerable function from the prompt, returned as is

Run:  python3 -m patcher.mock_model --mode good
"""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .prompts import ROOT

MODES = ("good", "malformed", "empty", "unchanged")
DEFAULT_PORT = 11435  # Ollama uses 11434; the mock can run next to it.

MALFORMED = ("Sure! Here is the fix as a diff:\n"
             "--- a/source.py\n+++ b/source.py\n@@ -1,2 +1,2 @@\n-    old line\n+    new line\n"
             "Let me know if you need anything else.")

_FUNCTION = re.compile(r"Vulnerable function:\n```(\w+)\n(.*?)\n```", re.S)
_PY_NAME = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", re.M)
_C_NAME = re.compile(r"(\w+)\s*\([^;{]*\)\s*\{")


def target(user):
    """Return (language, source, name) of the vulnerable function in a p5 user prompt."""
    match = _FUNCTION.search(user)
    if not match:
        raise ValueError("no 'Vulnerable function:' block in the prompt")
    language, source = match[1], match[2]
    name = (_PY_NAME if language == "python" else _C_NAME).search(source)
    if not name:
        raise ValueError("no function name in the vulnerable function")
    return language, source, name[1]


def layout(language, function, explanation, includes=()):
    """Build a reply in the production layout of docs/prompting.md."""
    reply = f"```{language}\n{function.strip()}\n```\nEXPLANATION: {explanation}"
    if includes:
        reply += "\nINCLUDES: " + ", ".join(includes)
    return reply


def gold_replies(path=ROOT / "training/gold.jsonl"):
    """Good replies for the train functions, built from the reviewed gold repairs."""
    replies = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        language = row["finding"]["language"]
        code = row["repair"]
        includes = re.findall(r"^#include\s+(<[\w./]+>)\s*$", code, re.M)
        code = re.sub(r"^#include[^\n]*\n", "", code, flags=re.M)
        _, _, name = target(f"Vulnerable function:\n```{language}\n{code.strip()}\n```")
        replies[name] = layout(language, code, row["explanation"], includes)
    return replies


class MockModel:
    """Reply state: the list of modes (one per call, the last repeats) and the good replies."""

    def __init__(self, modes=("good",), replies=None):
        modes = [modes] if isinstance(modes, str) else list(modes)
        unknown = [m for m in modes if m not in MODES]
        if not modes or unknown:
            raise ValueError(f"modes must be among {MODES}, got {modes}")
        self.modes = modes
        self.replies = gold_replies() if replies is None else dict(replies)
        self.calls = []  # every /api/chat payload, for test assertions
        self.lock = threading.Lock()

    def reply(self, payload):
        with self.lock:
            mode = self.modes[min(len(self.calls), len(self.modes) - 1)]
            self.calls.append(payload)
        if mode == "empty":
            return ""
        if mode == "malformed":
            return MALFORMED
        user = next(m["content"] for m in payload["messages"] if m["role"] == "user")
        language, source, name = target(user)
        if mode == "unchanged":
            return layout(language, source, "The function is already safe.")
        if name not in self.replies:
            raise LookupError(f"no good reply for function {name!r}; add it to the replies file")
        return self.replies[name]


def handler(model):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, body):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/api/version":
                self.send(200, {"version": "mock"})
            elif self.path == "/api/tags":
                self.send(200, {"models": [{"name": "any tag", "model": "any tag"}]})
            else:
                self.send(404, {"error": "not found"})

        def do_POST(self):
            if self.path not in ("/api/chat", "/v1/chat/completions"):
                return self.send(404, {"error": "not found"})
            try:
                payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                # Ollama streams unless told not to; the OpenAI API does not stream unless told to.
                if payload.get("stream", self.path == "/api/chat"):
                    return self.send(400, {"error": "the mock supports stream: false only"})
                content = model.reply(payload)
            except (ValueError, KeyError, StopIteration, LookupError) as exc:
                return self.send(400, {"error": str(exc)})
            if self.path == "/v1/chat/completions":
                return self.send(200, {"id": "mock", "object": "chat.completion", "created": 0,
                                       "model": payload.get("model"),
                                       "choices": [{"index": 0, "finish_reason": "stop",
                                                    "message": {"role": "assistant", "content": content}}],
                                       "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}})
            self.send(200, {"model": payload.get("model"), "created_at": "1970-01-01T00:00:00Z",
                            "message": {"role": "assistant", "content": content},
                            "done": True, "done_reason": "stop",
                            "prompt_eval_count": 0, "eval_count": 0,
                            "total_duration": 0, "load_duration": 0, "eval_duration": 0})

        def log_message(self, *args):  # keep test output quiet
            pass
    return Handler


@contextmanager
def serve(modes=("good",), replies=None, host="127.0.0.1", port=0):
    """Run the mock in a thread; yield (base_url, model). Port 0 picks a free port."""
    model = MockModel(modes, replies)
    server = ThreadingHTTPServer((host, port), handler(model))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{server.server_address[1]}", model
    finally:
        server.shutdown()
        server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", default="good",
                        help="one mode, or a comma list used one per call, the last repeating "
                             "(e.g. malformed,good). Modes: " + ", ".join(MODES))
    parser.add_argument("--replies", type=Path,
                        help="JSON file {function name: reply} for good mode (default: training/gold.jsonl)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    replies = json.loads(args.replies.read_text(encoding="utf-8")) if args.replies else None
    model = MockModel(args.mode.split(","), replies)
    server = ThreadingHTTPServer((args.host, args.port), handler(model))
    print(f"mock model on http://{args.host}:{args.port} mode {args.mode}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
