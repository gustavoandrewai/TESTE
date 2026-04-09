import type { NewsProvider, RawNewsItem } from "./types";

export class RSSNewsProvider implements NewsProvider {
  constructor(private readonly feedUrls: string[]) {}

  async fetchLatestNews(): Promise<RawNewsItem[]> {
    if (!this.feedUrls.length) return [];
    return this.feedUrls.map((url, idx) => ({
      title: `Notícia coletada da fonte ${idx + 1}`,
      url,
      source: "ConfiguredFeed",
      publishedAt: new Date().toISOString(),
      snippet: "Implementação inicial pronta para múltiplas fontes.",
      category: "mercados"
    }));
  }
}
