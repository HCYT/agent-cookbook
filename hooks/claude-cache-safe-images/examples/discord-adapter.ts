import { writeFileSync, unlinkSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";

export interface AttachmentLike {
  url: string;
  name?: string;
  contentType?: string | null;
  size?: number | null;
}

const IMAGE_TYPES = new Set(["image/png", "image/jpeg", "image/gif", "image/webp"]);
const MAX_IMAGE_SIZE = 20 * 1024 * 1024;

function describeImageFile(imagePath: string, scriptPath: string): string | null {
  const result = spawnSync("node", [scriptPath, imagePath], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"],
  });

  if (result.status !== 0) return null;
  const text = (result.stdout || "").trim();
  return text || null;
}

export async function describeAttachmentsAsText(
  attachments: AttachmentLike[],
  scriptPath: string,
): Promise<string | null> {
  const results = await Promise.all(
    attachments
      .filter((item) => item.contentType && IMAGE_TYPES.has(item.contentType) && (item.size ?? 0) <= MAX_IMAGE_SIZE)
      .map(async (item) => {
        const response = await fetch(item.url);
        if (!response.ok) return null;

        const buffer = Buffer.from(await response.arrayBuffer());
        const tempPath = join(tmpdir(), `discord-image-${Date.now()}-${Math.random().toString(36).slice(2)}.bin`);
        writeFileSync(tempPath, buffer);

        try {
          const description = describeImageFile(tempPath, scriptPath);
          if (!description) return null;
          return `[Image: ${item.name || "attachment"}]\n\n${description}`;
        } finally {
          try {
            unlinkSync(tempPath);
          } catch {}
        }
      }),
  );

  const merged = results.filter((item): item is string => Boolean(item));
  return merged.length > 0 ? merged.join("\n\n") : null;
}

export async function buildPromptWithImages(
  basePrompt: string,
  attachments: AttachmentLike[],
  scriptPath: string,
): Promise<string> {
  const imageText = await describeAttachmentsAsText(attachments, scriptPath);
  return imageText ? `${basePrompt}\n\n${imageText}` : basePrompt;
}

/*
Usage shape:

const prompt = await buildPromptWithImages(
  "[Discord @alice] Please debug this screenshot",
  message.attachments,
  "/ABSOLUTE/PATH/TO/agent-cookbook/hooks/claude-cache-safe-images/hooks/image-describe.mjs",
);

session.send(prompt);
*/
