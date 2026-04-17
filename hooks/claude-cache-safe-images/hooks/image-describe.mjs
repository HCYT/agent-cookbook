#!/usr/bin/env node

import { spawnSync } from "node:child_process";

const imagePath = process.argv[2];
if (!imagePath) {
  process.exit(1);
}

const geminiBin = process.env.GEMINI_BIN || "gemini";
const geminiModel = process.env.GEMINI_MODEL || "";

const prompt = [
  `Read this image first: @${imagePath}`,
  "",
  "Reply in Traditional Chinese.",
  "Keep it under 300 Chinese characters.",
  "State what kind of image this is.",
  "Preserve code, error text, labels, and key UI copy when relevant.",
  "Ignore decorative detail unless it changes the meaning.",
  "Write one compact paragraph. No bullet points."
].join("\n");

const args = [];
if (geminiModel) {
  args.push("-m", geminiModel);
}
args.push("-p", prompt);

const result = spawnSync(geminiBin, args, {
  encoding: "utf8",
  stdio: ["ignore", "pipe", "ignore"],
});

if (result.status !== 0) {
  process.exit(1);
}

const output = (result.stdout || "").trim();
if (!output) {
  process.exit(1);
}

process.stdout.write(output);
