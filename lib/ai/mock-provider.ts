import { newsletterDraftSchema } from "@/lib/validation/schemas";
import { sanitizeDraft } from "./sanitize-draft";
import type { AIProvider, EditorialDraft, EditorialInput } from "./types";

export class MockAIProvider implements AIProvider {
  async generateEditorial(input: EditorialInput): Promise<EditorialDraft> {
    const top = input.news.slice(0, 12);

    const candidate: Partial<EditorialDraft> = {
      subject: "Global Market Morning Brief | Inflação, juros e risco geopolítico no foco",
      preheader: "Leitura institucional de macro, mercados e política com impacto em ativos.",
      executiveSummary: top.slice(0, 5).map((n) => `${n.title} — ${n.content}`),
      sections: [
        {
          section: "Macro e Bancos Centrais",
          items: top.slice(0, 3).map((n) => ({
            title: n.title,
            summary: n.content,
            whyItMatters: "Afeta expectativas de taxa terminal, valuation e custo de capital.",
            sourceName: n.sourceName,
            sourceUrl: n.sourceUrl
          }))
        },
        {
          section: "Mercados Globais",
          items: top.slice(3, 6).map((n) => ({
            title: n.title,
            summary: n.content,
            whyItMatters: "Muda leitura de risco, fluxo para dólar e inclinação de curvas.",
            sourceName: n.sourceName,
            sourceUrl: n.sourceUrl
          }))
        },
        {
          section: "Política e Geopolítica",
          items: top.slice(6, 9).map((n) => ({
            title: n.title,
            summary: n.content,
            whyItMatters: "Pode alterar prêmio de risco e perspectiva de crescimento global.",
            sourceName: n.sourceName,
            sourceUrl: n.sourceUrl
          }))
        }
      ],
      monitorToday: [
        "Comunicações de bancos centrais e mudanças no guidance de política monetária.",
        "Evolução de Treasuries longas, dólar e spreads de crédito.",
        "Novos eventos geopolíticos com potencial de choque em energia e risco."
      ],
      agenda: [
        "CPI EUA e componentes de inflação de serviços.",
        "Discursos de dirigentes do Fed e BCE.",
        "Indicadores de atividade e confiança na Europa e Ásia."
      ],
      conclusion:
        "O pano de fundo continua combinando política monetária restritiva com incerteza geopolítica. A consequência prática é seletividade de risco, atenção à curva e disciplina na alocação entre classes de ativos."
    };

    const sanitized = sanitizeDraft(candidate, input);
    return newsletterDraftSchema.parse(sanitized);
  }
}
