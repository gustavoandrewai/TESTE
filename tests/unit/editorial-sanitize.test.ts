import { describe, expect, it } from "vitest";
import { sanitizeDraft } from "@/lib/ai/sanitize-draft";

describe("sanitizeDraft", () => {
  it("guarantees executiveSummary with at least 3 items", () => {
    const result = sanitizeDraft(
      {
        subject: "Teste",
        executiveSummary: ["item único"]
      },
      {
        news: [
          {
            title: "Fed mantém juros",
            sourceName: "Mock",
            sourceUrl: "https://example.com/1",
            publishedAt: new Date(),
            category: "macro",
            content: "Texto"
          }
        ]
      }
    );

    expect((result.executiveSummary || []).length).toBeGreaterThanOrEqual(3);
    expect(result.sections?.length).toBeGreaterThan(0);
  });
});
