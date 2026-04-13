import { describe, expect, it } from "vitest";
import { deduplicateNews } from "@/lib/news/deduplication";
import { rankNews } from "@/lib/news/ranking";

describe("news pipeline", () => {
  it("deduplicates repeated items", () => {
    const items = [
      {
        title: "Fed mantém juros",
        sourceName: "A",
        sourceUrl: "https://x.com/1",
        publishedAt: new Date(),
        category: "macro",
        content: "texto"
      },
      {
        title: "Fed mantém juros",
        sourceName: "A",
        sourceUrl: "https://x.com/1",
        publishedAt: new Date(),
        category: "macro",
        content: "texto"
      }
    ];

    expect(deduplicateNews(items).length).toBe(1);
  });

  it("scores by relevance keywords", () => {
    const ranked = rankNews([
      {
        title: "Juros e inflação nos EUA",
        sourceName: "A",
        sourceUrl: "https://x.com/2",
        publishedAt: new Date(),
        category: "macro",
        content: "Fed e treasury"
      }
    ]);
    expect((ranked[0].relevanceScore ?? 0) > 20).toBeTruthy();
  });
});
