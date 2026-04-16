import type { NormalizedNews } from "./types";

export function deduplicateNews(items: NormalizedNews[]): NormalizedNews[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    const key = `${item.title.toLowerCase().slice(0, 70)}|${item.sourceUrl}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
