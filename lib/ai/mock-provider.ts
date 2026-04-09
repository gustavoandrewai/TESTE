import { newsletterDraftSchema } from "@/lib/validation/schemas";
import { sanitizeDraft } from "./sanitize-draft";
import type { AIProvider, EditorialDraft, EditorialInput } from "./types";

export class MockAIProvider implements AIProvider {
  async generateEditorial(input: EditorialInput): Promise<EditorialDraft> {
    const top = input.news.slice(0, 5);

    const candidate: Partial<EditorialDraft> = {
      subject: "Morning Brief: juros globais, petróleo e dólar no radar",
      executiveSummary: top.map((n) => `${n.title} — ${n.content}`),
      sections: [
        {
          section: "Mercados globais",
          items: top.map((n) => ({
            title: n.title,
            summary: n.content,
            whyItMatters: "Impacta expectativa para ativos globais e percepção de risco.",
            sourceName: n.sourceName,
            sourceUrl: n.sourceUrl
          }))
        }
      ],
      monitorToday: ["Discursos de dirigentes de BC", "Abertura dos Treasuries", "DXY e commodities"],
      agenda: ["CPI EUA", "Leilão de títulos", "Produção industrial China"]
    };

    const sanitized = sanitizeDraft(candidate, input);
    return newsletterDraftSchema.parse(sanitized);
  }
}
