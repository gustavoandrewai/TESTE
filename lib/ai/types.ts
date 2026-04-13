import type { ChartAsset } from "@/lib/assets/chart-generation";
import type { NormalizedNews } from "@/lib/news/types";

export type EditorialInput = { news: NormalizedNews[] };

export type EditorialDraft = {
  subject: string;
  preheader?: string;
  executiveSummary: string[];
  sections: Array<{
    section: string;
    items: Array<{
      title: string;
      summary: string;
      whyItMatters: string;
      sourceName: string;
      sourceUrl: string;
    }>;
  }>;
  marketSnapshot?: Array<{
    asset: string;
    price: string;
    change: string;
    period: string;
  }>;
  tables?: Array<{
    title: string;
    columns: string[];
    rows: string[][];
  }>;
  charts?: ChartAsset[];
  images?: Array<{ title: string; url: string; caption?: string }>;
  monitorToday: string[];
  agenda: string[];
  conclusion?: string;
  sources?: string[];
};

export interface AIProvider {
  generateEditorial(input: EditorialInput): Promise<EditorialDraft>;
}
