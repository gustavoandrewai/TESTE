import { describe, expect, it } from "vitest";
import { sanitizeDraft } from "@/lib/ai/sanitize-draft";

describe("sanitizeDraft", () => {
  it("guarantees executiveSummary with at least 3 items", () => {
    const result = sanitizeDraft(
      {
        subject: "Teste",
        executiveSummary: ["item único"],
        sections: [
          { section: "Macro", items: [] },
          { section: "Mercados", items: [] },
          { section: "Política", items: [] }
        ]
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
    expect(result.sections?.length).toBeGreaterThanOrEqual(3);
    expect(result.sections?.every((section) => section.items.length >= 1)).toBeTruthy();
  });
});
