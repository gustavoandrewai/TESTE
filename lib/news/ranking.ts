import type { NormalizedNews } from "./types";

const keywords = ["juros", "inflação", "fed", "bce", "dólar", "treasury", "commodities", "guerra", "fiscal"];

export function rankNews(items: NormalizedNews[]): NormalizedNews[] {
  return items
    .map((item) => {
      const text = `${item.title} ${item.content}`.toLowerCase();
      const score = keywords.reduce((acc, keyword) => (text.includes(keyword) ? acc + 12 : acc), 20);
      return { ...item, relevanceScore: Math.min(100, score) };
    })
    .sort((a, b) => (b.relevanceScore ?? 0) - (a.relevanceScore ?? 0));
}
