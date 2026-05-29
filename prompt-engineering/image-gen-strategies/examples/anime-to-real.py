#!/usr/bin/env python3
"""
Anime → 真人轉換管道

兩步走：
  1. 用現有動漫圖當 ref
  2. 用標準轉換 template 轉成真人照片

用法：
  python anime-to-real.py <動漫圖路徑> [輸出名]
  python anime-to-real.py ./anime-cafe.png cafe-real
  python anime-to-real.py batch ./anime-images/    # 批次轉整個資料夾
"""

import json, os, sys, uuid, base64, pathlib, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

AUTH_PATH = os.path.expanduser("~/.codex/auth.json")
API_URL = "https://chatgpt.com/backend-api/codex/responses"
OUTPUT_DIR = pathlib.Path("./output/real")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

auth = json.loads(pathlib.Path(AUTH_PATH).read_text())
TOKEN = auth.get("tokens", auth).get("access_token", auth.get("access_token"))
ACCOUNT_ID = auth.get("tokens", auth).get("account_id", auth.get("account_id"))

if not TOKEN or not ACCOUNT_ID:
    print("找不到認證資料 — 請先跑 `codex login`")
    sys.exit(1)

# ═══════════════════════════════════════════════════════
# 轉換 template — 改成你的角色描述
# ═══════════════════════════════════════════════════════

CONVERT_TEMPLATE = """
Convert this anime illustration into a real photograph.
It should look like it was shot with a real DSLR camera,
with natural skin texture, pores, and realistic lighting.
The character is an Asian woman with brown hair.
Keep exactly the same composition, pose, expression, clothing, scene, and lighting.
Photographic style, Sony A7IV, 85mm lens, natural light, shallow depth of field.

## Negative prompt:
anime style, illustration, CG, 3D render, plastic skin, airbrushed skin,
western face, european face, deep set eyes, high nose bridge,
doll-like, cartoon, flat shading
""".strip()

# 你可以替換成自己的角色描述，例如：
# "The character is a European woman with blonde hair and blue eyes."
# 然後對應修改 negative prompt 裡的臉部相關項目。

# ═══════════════════════════════════════════════════════


def convert_one(anime_path, output_name):
    """轉換一張動漫圖為真人"""
    if not os.path.exists(anime_path):
        print(f"  file not found: {anime_path}")
        return False

    out_path = OUTPUT_DIR / f"{output_name}.png"
    if out_path.exists():
        print(f"  [skip] {output_name}")
        return True

    ref_b64 = base64.b64encode(pathlib.Path(anime_path).read_bytes()).decode()
    session_id = str(uuid.uuid4())

    body = json.dumps({
        "model": "gpt-5.5",
        "store": False,
        "stream": True,
        "instructions": "Generate images immediately without text response.",
        "input": [{"role": "user", "content": [
            {"type": "input_image", "image_url": f"data:image/png;base64,{ref_b64}"},
            {"type": "input_text", "text": CONVERT_TEMPLATE},
        ]}],
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

    print(f"  converting {os.path.basename(anime_path)} ...", end="", flush=True)
    t0 = time.time()

    try:
        req = Request(API_URL, data=body, headers=headers)
        resp = urlopen(req, timeout=180)
    except HTTPError as e:
        if e.code == 401:
            print(" Token 過期 — 請重新 `codex login`")
            sys.exit(1)
        print(f" HTTP {e.code}")
        return False
    except Exception as e:
        print(f" {str(e)[:60]}")
        return False

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
                if evt.get("type") == "response.output_item.done":
                    item = evt.get("item", {})
                    if item.get("type") == "image_generation_call":
                        image_b64 = item.get("result", image_b64)
            except json.JSONDecodeError:
                pass

    elapsed = time.time() - t0

    if image_b64:
        out_path.write_bytes(base64.b64decode(image_b64))
        print(f" ok {elapsed:.0f}s -> {out_path}")
        return True
    else:
        print(f" blocked {elapsed:.0f}s")
        return False


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python anime-to-real.py <動漫圖路徑> [輸出名]")
        print("  python anime-to-real.py batch <資料夾路徑>")
        sys.exit(1)

    if sys.argv[1] == "batch":
        # 批次模式：轉換整個資料夾
        folder = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ".")
        files = sorted(
            f for f in folder.iterdir()
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
            and "_real" not in f.stem
        )
        print(f"=== Batch convert: {len(files)} files from {folder} ===\n")

        ok = 0
        for i, f in enumerate(files):
            output_name = f"{f.stem}_real"
            success = convert_one(str(f), output_name)
            if success:
                ok += 1
            if i < len(files) - 1:
                time.sleep(3)

        print(f"\n=== Done: {ok}/{len(files)} converted ===")

    else:
        # 單張模式
        anime_path = sys.argv[1]
        output_name = sys.argv[2] if len(sys.argv) > 2 else (
            pathlib.Path(anime_path).stem + "_real"
        )
        convert_one(anime_path, output_name)


if __name__ == "__main__":
    main()
