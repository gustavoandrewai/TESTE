import { newsletterDraftSchema } from "@/lib/validation/schemas";
import type { AIProvider, EditorialDraft, EditorialInput } from "./types";

export class MockAIProvider implements AIProvider {
  async generateEditorial(input: EditorialInput): Promise<EditorialDraft> {
    const top = input.news.slice(0, 5);
    return newsletterDraftSchema.parse({
      subject: "Morning Brief: juros globais, petróleo e dólar no radar",
      executiveSummary: top.map((n) => `${n.title} — ${n.content}`),
      sections: [
        {
          section: "Mercados globais",
          items: top.map((n) => ({
            title: n.title,
            summary: n.content,
            whyItMatters: "Impacta expectativa para ativos globais e risco.",
            sourceName: n.sourceName,
            sourceUrl: n.sourceUrl
          }))
        }
      ],
      monitorToday: ["Discursos de dirigentes de BC", "Abertura dos Treasuries", "DXY e commodities"],
      agenda: ["CPI EUA", "Leilão de títulos", "Produção industrial China"]
    });
  }
}
