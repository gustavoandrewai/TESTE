export type RawNewsItem = {
  title: string;
  url: string;
  source: string;
  publishedAt: string;
  snippet: string;
  category?: string;
};

export type NormalizedNews = {
  title: string;
  sourceName: string;
  sourceUrl: string;
  publishedAt: Date;
  category: string;
  content: string;
  relevanceScore?: number;
};

export interface NewsProvider {
  fetchLatestNews(): Promise<RawNewsItem[]>;
}
