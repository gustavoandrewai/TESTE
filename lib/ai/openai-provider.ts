import OpenAI from "openai";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { newsletterDraftSchema } from "@/lib/validation/schemas";
import { sanitizeDraft } from "./sanitize-draft";
import type { AIProvider, EditorialDraft, EditorialInput } from "./types";

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export class OpenAIProvider implements AIProvider {
  async generateEditorial(input: EditorialInput): Promise<EditorialDraft> {
    const systemPrompt = readFileSync(join(process.cwd(), "prompts/editor-system.txt"), "utf-8");
    const userPrompt = readFileSync(join(process.cwd(), "prompts/editor-user.txt"), "utf-8");

    const response = await client.responses.create({
      model: process.env.OPENAI_MODEL || "gpt-4.1-mini",
      input: [
        { role: "system", content: systemPrompt },
        { role: "user", content: `${userPrompt}\n\n${JSON.stringify(input.news.slice(0, 20))}` }
      ],
      text: { format: { type: "json_object" } }
    });

    const raw = response.output_text || "{}";
    const parsed = JSON.parse(raw) as Partial<EditorialDraft>;
    const sanitized = sanitizeDraft(parsed, input);

    return newsletterDraftSchema.parse(sanitized);
  }
}
