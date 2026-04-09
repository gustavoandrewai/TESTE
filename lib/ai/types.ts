import type { NormalizedNews } from "@/lib/news/types";

export type EditorialInput = { news: NormalizedNews[] };

export type EditorialDraft = {
  subject: string;
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
  monitorToday: string[];
  agenda: string[];
};

export interface AIProvider {
  generateEditorial(input: EditorialInput): Promise<EditorialDraft>;
}
