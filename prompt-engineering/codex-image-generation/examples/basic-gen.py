#!/usr/bin/env python3
"""
Codex OAuth + ChatGPT Responses API — 最小可用的單張生圖
用法：python basic-gen.py "prompt" [參考圖路徑] [輸出檔名]
"""

import json, os, sys, uuid, base64, pathlib
from urllib.request import Request, urlopen
from urllib.error import HTTPError

AUTH_PATH = os.path.expanduser("~/.codex/auth.json")
API_URL = "https://chatgpt.com/backend-api/codex/responses"
OUTPUT_DIR = pathlib.Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── 讀取 OAuth token ─────────────────────────────────
auth = json.loads(pathlib.Path(AUTH_PATH).read_text())
TOKEN = auth.get("tokens", auth).get("access_token", auth.get("access_token"))
ACCOUNT_ID = auth.get("tokens", auth).get("account_id", auth.get("account_id"))

if not TOKEN or not ACCOUNT_ID:
    print("找不到認證資料 — 請先跑 `codex login`")
    sys.exit(1)

# ─── CLI 參數 ──────────────────────────────────────────
prompt = sys.argv[1] if len(sys.argv) > 1 else "a cute dragon under a starry sky, anime style"
ref_path = sys.argv[2] if len(sys.argv) > 2 else None
output_name = sys.argv[3] if len(sys.argv) > 3 else f"gen-{os.getpid()}"

# ─── 組裝 request ─────────────────────────────────────
content = []

if ref_path and os.path.exists(ref_path):
    ref_b64 = base64.b64encode(pathlib.Path(ref_path).read_bytes()).decode()
    content.append({
        "type": "input_image",
        "image_url": f"data:image/png;base64,{ref_b64}",
    })
    print(f"ref: {os.path.basename(ref_path)}")

content.append({"type": "input_text", "text": prompt})

body = json.dumps({
    "model": "gpt-5.5",
    "store": False,
    "stream": True,
    "instructions": "Generate images immediately without text response.",
    "input": [{"role": "user", "content": content}],
    "reasoning": {"effort": "low", "summary": "auto"},
    "tools": [{"type": "image_generation", "output_format": "png"}],
}).encode()

session_id = str(uuid.uuid4())
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "chatgpt-account-id": ACCOUNT_ID,
    "OpenAI-Beta": "responses=experimental",
    "originator": "codex_sdk_ts",
    "User-Agent": "codex_sdk_ts/0.130.0",
    "session_id": session_id,
    "x-client-request-id": session_id,
}

# ─── 呼叫 API ─────────────────────────────────────────
print(f"prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
req = Request(API_URL, data=body, headers=headers)

try:
    resp = urlopen(req, timeout=180)
except HTTPError as e:
    if e.code == 401:
        print("Token 過期 — 請重新 `codex login`")
    else:
        print(f"HTTP {e.code}: {e.read().decode()[:500]}")
    sys.exit(1)
except Exception as e:
    print(f"error: {e}")
    sys.exit(1)

# ─── 解析串流 ─────────────────────────────────────────
image_b64 = None
buf = b""

for chunk in iter(lambda: resp.read(4096), b""):
    buf += chunk
    while b"\n" in buf:
        line, buf = buf.split(b"\n", 1)
        line = line.decode("utf-8", errors="replace").strip()
        if not line.startswith("data: "):
            continue
        payload = line[6:]
        if payload == "[DONE]":
            break
        try:
            evt = json.loads(payload)

            if evt.get("type") == "response.image_generation_call.partial_image":
                image_b64 = evt.get("partial_image", image_b64)
                print(".", end="", flush=True)

            if evt.get("type") == "response.output_item.done":
                item = evt.get("item", {})
                if item.get("type") == "image_generation_call":
                    image_b64 = item.get("result", image_b64)
                    print("\nimage done")
                elif item.get("type") == "message":
                    text = (item.get("content") or [{}])[0].get("text", "")
                    if any(w in text for w in ("cannot", "policy", "sorry", "unable")):
                        print(f"\nblocked: {text[:200]}")

            if evt.get("type") == "response.completed":
                usage = evt.get("response", {}).get("usage")
                if usage:
                    print(f"usage: in={usage.get('input_tokens')} out={usage.get('output_tokens')}")

        except json.JSONDecodeError:
            pass

# ─── 存檔 ─────────────────────────────────────────────
if image_b64:
    out_path = OUTPUT_DIR / f"{output_name}.png"
    out_path.write_bytes(base64.b64decode(image_b64))
    print(f"saved: {out_path}")
else:
    print("no image returned")
