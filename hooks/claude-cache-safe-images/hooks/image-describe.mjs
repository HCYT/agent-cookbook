#!/usr/bin/env node

import { spawnSync } from "node:child_process";

const imagePath = process.argv[2];
if (!imagePath) {
  process.exit(1);
}

const visionBin = process.env.VISION_CLI_BIN || "agy";
const visionModel = process.env.VISION_CLI_MODEL || "";

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
if (visionModel) {
  args.push("--model", visionModel);
}
args.push("-p", prompt);

const result = spawnSync(visionBin, args, {
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
