#!/usr/bin/env python3
"""
Codex OAuth + ChatGPT Responses API — 批次生圖
支援：prompt 快取、斷點續跑、JSON log

用法：python batch-gen.py

在下方 PROMPTS dict 裡定義你的 prompt，跑完的圖會存到 ./output/batch/，
log 存到 ./output/logs/。已經存在的圖會自動跳過。
"""

import json, os, sys, time, uuid, base64, pathlib, datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

AUTH_PATH = os.path.expanduser("~/.codex/auth.json")
API_URL = "https://chatgpt.com/backend-api/codex/responses"
OUTPUT_DIR = pathlib.Path("./output/batch")
LOG_DIR = pathlib.Path("./output/logs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ─── 讀取 OAuth token ─────────────────────────────────
auth = json.loads(pathlib.Path(AUTH_PATH).read_text())
TOKEN = auth.get("tokens", auth).get("access_token", auth.get("access_token"))
ACCOUNT_ID = auth.get("tokens", auth).get("account_id", auth.get("account_id"))

if not TOKEN or not ACCOUNT_ID:
    print("找不到認證資料 — 請先跑 `codex login`")
    sys.exit(1)

# ═══════════════════════════════════════════════════════
# 在這裡定義你的 prompt 列表
# key = 輸出檔名（不含 .png），value = prompt
# ═══════════════════════════════════════════════════════
PROMPTS = {
    "sunset_dragon": "a dragon flying over ocean at sunset, anime style, warm golden light",
    "forest_spirit": "a forest spirit sitting under a huge ancient tree, anime style, dappled sunlight filtering through leaves",
    "city_night": "anime girl walking through neon-lit city at night, rain reflections on wet street",
    "cafe_morning": "anime girl reading a book at a cozy cafe, morning sunlight through window, steam from coffee",
    "beach_summer": "anime girl at the beach, summer afternoon, clear blue sky, gentle waves",
}

# 參考圖（可選）— 設成你的角色設定圖路徑，或留 None
REF_IMAGE = None  # e.g. "./my-character.png"

# 快取 key — 同一批次用同一個 key，讓 API 端快取共用 prefix
CACHE_KEY = "my-batch-v1"

# 每張之間的間隔秒數
DELAY_SECONDS = 3

# ═══════════════════════════════════════════════════════

ref_b64 = None
if REF_IMAGE and os.path.exists(REF_IMAGE):
    ref_b64 = base64.b64encode(pathlib.Path(REF_IMAGE).read_bytes()).decode()
    print(f"ref: {REF_IMAGE}")


def generate(slug, prompt):
    """呼叫 API 生成一張圖，回傳 (image_base64, text_response)"""
    session_id = str(uuid.uuid4())

    content = []
    if ref_b64:
        content.append({
            "type": "input_image",
            "image_url": f"data:image/png;base64,{ref_b64}",
        })
    content.append({"type": "input_text", "text": prompt})

    body = json.dumps({
        "model": "gpt-5.5",
        "store": False,
        "stream": True,
        "instructions": "Generate images immediately without text response.",
        "input": [{"role": "user", "content": content}],
        "prompt_cache_key": CACHE_KEY,
        "reasoning": {"effort": "low", "summary": "auto"},
        "tools": [{"type": "image_generation", "output_format": "png"}],
    }).encode()

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

    req = Request(API_URL, data=body, headers=headers)
    resp = urlopen(req, timeout=180)

    image_b64 = None
    text_parts = []
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
                if evt.get("type") == "response.output_item.done":
                    item = evt.get("item", {})
                    if item.get("type") == "image_generation_call":
                        image_b64 = item.get("result", image_b64)
                    elif item.get("type") == "message":
                        text_parts.append(
                            (item.get("content") or [{}])[0].get("text", "")
                        )
            except json.JSONDecodeError:
                pass

    return image_b64, "".join(text_parts)


def run_one(idx, total, slug, prompt):
    """生成一張圖，回傳狀態字串"""
    out_path = OUTPUT_DIR / f"{slug}.png"
    if out_path.exists():
        print(f"  [skip] {slug}")
        return "skip"

    print(f"  [{idx + 1}/{total}] {slug} ...", end="", flush=True)
    t0 = time.time()

    try:
        image_b64, text = generate(slug, prompt)
    except HTTPError as e:
        if e.code == 401:
            print(f" Token 過期 — 請重新 `codex login`")
            sys.exit(1)
        print(f" HTTP {e.code}")
        return "error"
    except Exception as e:
        print(f" {str(e)[:60]}")
        return "error"

    elapsed = time.time() - t0

    # 寫 log
    log_entry = {
        "slug": slug,
        "timestamp": datetime.datetime.now().isoformat(),
        "prompt": prompt,
        "success": bool(image_b64),
        "elapsed_s": round(elapsed, 1),
        "text_response": text[:500] if text else None,
    }
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    (LOG_DIR / f"{ts}_{slug}.json").write_text(
        json.dumps(log_entry, indent=2, ensure_ascii=False)
    )

    if image_b64:
        out_path.write_bytes(base64.b64decode(image_b64))
        print(f" ok {elapsed:.0f}s")
        return "success"
    else:
        print(f" blocked {elapsed:.0f}s | {text[:80] if text else 'no response'}")
        return "blocked"


def main():
    total = len(PROMPTS)
    print(f"=== Batch Generate: {total} prompts ===")
    print()

    stats = {"success": 0, "blocked": 0, "skip": 0, "error": 0}

    for i, (slug, prompt) in enumerate(PROMPTS.items()):
        result = run_one(i, total, slug, prompt)
        stats[result] += 1
        if result not in ("skip",):
            time.sleep(DELAY_SECONDS)

    print()
    s = stats
    print(f"=== Done: {s['success']} ok / {s['blocked']} blocked / {s['error']} error / {s['skip']} skip ===")


if __name__ == "__main__":
    main()
