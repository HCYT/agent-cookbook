#!/usr/bin/env python3
"""
矩陣批次生圖 — 角色 × 場景 × 動作

示範怎麼用矩陣思維批量生圖，附帶斷點續跑、JSON log、通過率統計。
改下面的 CHARACTERS / SCENES / ACTIONS 就能直接用。

前置：先跑過 codex login，確認 ~/.codex/auth.json 存在。
"""

import json, os, sys, time, uuid, base64, pathlib, datetime
from collections import defaultdict
from urllib.request import Request, urlopen
from urllib.error import HTTPError

AUTH_PATH = os.path.expanduser("~/.codex/auth.json")
API_URL = "https://chatgpt.com/backend-api/codex/responses"
OUTPUT_DIR = pathlib.Path("./output/matrix")
LOG_DIR = pathlib.Path("./output/logs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

auth = json.loads(pathlib.Path(AUTH_PATH).read_text())
TOKEN = auth.get("tokens", auth).get("access_token", auth.get("access_token"))
ACCOUNT_ID = auth.get("tokens", auth).get("account_id", auth.get("account_id"))

if not TOKEN or not ACCOUNT_ID:
    print("找不到認證資料 — 請先跑 `codex login`")
    sys.exit(1)

# ═══════════════════════════════════════════════════════
# 改這邊：定義你的角色、場景、動作
# ═══════════════════════════════════════════════════════

CHARACTERS = {
    "alice": {
        "ref": "./refs/alice.png",       # 角色設定圖路徑
        "desc": "short brown hair, blue eyes, casual style",
    },
    "bob": {
        "ref": "./refs/bob.png",
        "desc": "tall, black hair, glasses, formal style",
    },
}

SCENES = {
    "kitchen_morning": "bright kitchen, morning sunlight through window, warm tones",
    "cafe_afternoon": "cozy cafe interior, afternoon light, warm wood tones",
    "park_sunset": "city park, golden hour sunset, trees and benches",
}

ACTIONS = {
    "standing": "standing naturally, relaxed posture",
    "sitting": "sitting comfortably",
    "walking": "walking casually",
}

# 共用的風格錨和 negative（每張圖都帶）
STYLE = "anime style, clean sharp linework, high quality rendering"
NEGATIVE = (
    "bad anatomy, extra fingers, deformed hands, broken limbs, "
    "flat shading, dull lighting, muddy colors, blurry, low quality"
)

# 快取 key（同批次共用）
CACHE_KEY = "matrix-batch-v1"

# 每張間隔
DELAY_SECONDS = 3

# ═══════════════════════════════════════════════════════


def build_prompt(char_desc, scene_desc, action_desc):
    """組裝完整 prompt"""
    prompt = f"{STYLE}, {char_desc}, {scene_desc}, {action_desc}"
    if NEGATIVE:
        prompt += f"\n\n## Negative prompt:\n{NEGATIVE}"
    return prompt


def load_ref_b64(path):
    """讀取參考圖的 base64"""
    if not path or not os.path.exists(path):
        return None
    return base64.b64encode(pathlib.Path(path).read_bytes()).decode()


def generate(prompt, ref_b64):
    """呼叫 API 生一張圖"""
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


def run_one(idx, total, slug, prompt, ref_b64):
    """生一張圖，回傳狀態"""
    out_path = OUTPUT_DIR / f"{slug}.png"
    if out_path.exists():
        print(f"  [skip] {slug}")
        return "skip"

    print(f"  [{idx + 1}/{total}] {slug} ...", end="", flush=True)
    t0 = time.time()

    try:
        image_b64, text = generate(prompt, ref_b64)
    except HTTPError as e:
        if e.code == 401:
            print(" Token 過期 — 請重新 `codex login`")
            sys.exit(1)
        print(f" HTTP {e.code}")
        return "error"
    except Exception as e:
        print(f" {str(e)[:60]}")
        return "error"

    elapsed = time.time() - t0

    log_entry = {
        "slug": slug,
        "timestamp": datetime.datetime.now().isoformat(),
        "prompt": prompt[:200],
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
    # 建矩陣
    matrix = {}
    ref_cache = {}

    for char_name, char_info in CHARACTERS.items():
        if char_name not in ref_cache:
            ref_cache[char_name] = load_ref_b64(char_info.get("ref"))

        for scene_name, scene_desc in SCENES.items():
            for action_name, action_desc in ACTIONS.items():
                slug = f"{char_name}_{scene_name}_{action_name}"
                prompt = build_prompt(char_info["desc"], scene_desc, action_desc)
                matrix[slug] = (prompt, char_name)

    total = len(matrix)
    print(f"=== Matrix: {len(CHARACTERS)} chars x {len(SCENES)} scenes x {len(ACTIONS)} actions = {total} ===\n")

    stats = {"success": 0, "blocked": 0, "skip": 0, "error": 0}

    for i, (slug, (prompt, char_name)) in enumerate(matrix.items()):
        result = run_one(i, total, slug, prompt, ref_cache.get(char_name))
        stats[result] += 1
        if result not in ("skip",):
            time.sleep(DELAY_SECONDS)

    # 總統計
    s = stats
    print(f"\n=== Done: {s['success']} ok / {s['blocked']} blocked / {s['error']} error / {s['skip']} skip ===")

    # 按場景統計通過率
    scene_stats = defaultdict(lambda: [0, 0])
    for slug in matrix:
        parts = slug.split("_", 1)
        scene_key = "_".join(slug.split("_")[1:-1])
        scene_stats[scene_key][0] += 1
        if (OUTPUT_DIR / f"{slug}.png").exists():
            scene_stats[scene_key][1] += 1

    print("\n-- pass rate by scene --")
    for scene, (total_count, ok_count) in sorted(
        scene_stats.items(), key=lambda x: -x[1][1] / max(x[1][0], 1)
    ):
        pct = ok_count / total_count * 100 if total_count else 0
        print(f"  {scene}: {ok_count}/{total_count} ({pct:.0f}%)")


if __name__ == "__main__":
    main()
