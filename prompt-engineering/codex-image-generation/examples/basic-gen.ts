/**
 * Codex OAuth + ChatGPT Responses API — 最小可用的單張生圖
 * 用法：npx tsx basic-gen.ts "prompt" [參考圖路徑] [輸出檔名]
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { join, basename } from "node:path";

// ─── 設定 ─────────────────────────────────────────────
const AUTH_PATH = join(process.env.HOME!, ".codex", "auth.json");
const API_URL = "https://chatgpt.com/backend-api/codex/responses";
const OUTPUT_DIR = "./output";

if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true });

// ─── 讀取 OAuth token ─────────────────────────────────
const auth = JSON.parse(readFileSync(AUTH_PATH, "utf-8"));
const token = auth.tokens?.access_token ?? auth.access_token;
const accountId = auth.tokens?.account_id ?? auth.account_id;

if (!token || !accountId) {
  console.error("找不到認證資料 — 請先跑 `codex login`");
  process.exit(1);
}

// ─── CLI 參數 ─────────────────────────────────────────
const prompt = process.argv[2] ?? "a cute dragon under a starry sky, anime style";
const refImagePath = process.argv[3] ?? null;
const outputName = process.argv[4] ?? `gen-${Date.now()}`;

// ─── 主函數 ───────────────────────────────────────────
async function generate() {
  const sessionId = randomUUID();

  // 組裝 input content
  const content: any[] = [];

  if (refImagePath && existsSync(refImagePath)) {
    const b64 = readFileSync(refImagePath).toString("base64");
    content.push({
      type: "input_image",
      image_url: `data:image/png;base64,${b64}`,
    });
    console.log(`ref: ${basename(refImagePath)}`);
  }

  content.push({ type: "input_text", text: prompt });

  const body = {
    model: "gpt-5.5",
    store: false,
    stream: true,
    instructions: "Generate images immediately without text response.",
    input: [{ role: "user", content }],
    reasoning: { effort: "low", summary: "auto" },
    tools: [{ type: "image_generation", output_format: "png" }],
  };

  console.log(`prompt: ${prompt.slice(0, 100)}${prompt.length > 100 ? "..." : ""}`);

  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "chatgpt-account-id": accountId,
      "OpenAI-Beta": "responses=experimental",
      originator: "codex_sdk_ts",
      "User-Agent": "codex_sdk_ts/0.130.0",
      session_id: sessionId,
      "x-client-request-id": sessionId,
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(180_000),
  });

  if (!res.ok) {
    const errText = (await res.text()).slice(0, 500);
    console.error(`HTTP ${res.status}: ${errText}`);
    process.exit(1);
  }

  // ─── 解析串流 ───────────────────────────────────────
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  let imageData: string | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });

    let idx: number;
    while ((idx = buf.indexOf("\n")) !== -1) {
      const line = buf.slice(0, idx).trim();
      buf = buf.slice(idx + 1);
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6);
      if (payload === "[DONE]") break;

      try {
        const evt = JSON.parse(payload);

        if (evt.type === "response.image_generation_call.partial_image") {
          imageData = evt.partial_image;
          process.stdout.write(".");
        }

        if (
          evt.type === "response.output_item.done" &&
          evt.item?.type === "image_generation_call"
        ) {
          imageData = evt.item.result ?? imageData;
          console.log("\nimage done");
        }

        if (
          evt.type === "response.output_item.done" &&
          evt.item?.type === "message"
        ) {
          const msgText = evt.item?.content?.[0]?.text ?? "";
          if (
            msgText.includes("cannot") ||
            msgText.includes("policy") ||
            msgText.includes("sorry")
          ) {
            console.log(`\nblocked: ${msgText.slice(0, 200)}`);
          }
        }

        if (evt.type === "response.completed") {
          const u = evt.response?.usage;
          if (u) console.log(`usage: in=${u.input_tokens} out=${u.output_tokens}`);
        }
      } catch {
        // 略過解析失敗的行
      }
    }
  }

  // ─── 存檔 ──────────────────────────────────────────
  if (imageData) {
    const outPath = join(OUTPUT_DIR, `${outputName}.png`);
    writeFileSync(outPath, Buffer.from(imageData, "base64"));
    console.log(`saved: ${outPath}`);
  } else {
    console.log("no image returned");
  }
}

generate().catch(console.error);
