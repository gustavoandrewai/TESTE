import { normalizedNewsSchema } from "@/lib/validation/schemas";
import type { NormalizedNews, RawNewsItem } from "./types";

export function normalizeNews(items: RawNewsItem[]): NormalizedNews[] {
  return items.map((item) =>
    normalizedNewsSchema.parse({
      title: item.title.trim(),
      sourceName: item.source,
      sourceUrl: item.url,
      publishedAt: new Date(item.publishedAt),
      category: item.category ?? "geral",
      content: item.snippet
    })
  );
}
