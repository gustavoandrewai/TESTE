import { generateMockCharts } from "@/lib/assets/chart-generation";
import type { EditorialDraft, EditorialInput } from "./types";

const fallbackExecutiveSummary = [
  "Mercados globais operam com atenção a dados macroeconômicos e sinalizações de política monetária, mantendo viés cauteloso para ativos de risco.",
  "Investidores monitoram bancos centrais, inflação e juros em busca de direção para curvas, câmbio e custo de capital global.",
  "Risco geopolítico e decisões governamentais seguem como vetores relevantes para sentimento, volatilidade e pricing intermercados."
];

const fallbackMonitor = [
  "Comunicações de bancos centrais e autoridades fiscais com potencial de ajuste de expectativas.",
  "Dinâmica de yields longas, spreads de crédito e comportamento do dólar global.",
  "Movimento de commodities energéticas e metálicas em contexto geopolítico."
];

const fallbackAgenda = [
  "Indicadores de inflação e atividade das principais economias.",
  "Leilões de títulos soberanos e impactos sobre condições financeiras.",
  "Eventos políticos com potencial de repercussão relevante em mercados."
];

const defaultSections = [
  "Macro e Bancos Centrais",
  "Mercados Globais",
  "Política e Geopolítica",
  "Commodities, Moedas e Rates"
];

const fallbackSectionItem = {
  title: "Mercados monitoram sinais de política monetária e atividade global",
  summary:
    "Investidores seguem atentos a dados macroeconômicos, trajetória de juros e riscos geopolíticos, com impacto direto sobre sentimento e precificação de ativos.",
  whyItMatters: "Importa por influenciar prêmio de risco, curvas de juros, dólar e alocação entre classes de ativos.",
  sourceName: "Editorial fallback",
  sourceUrl: "https://example.com/editorial-fallback"
};

function uniqueNonEmpty(items: unknown[]): string[] {
  return items
    .map((item) => String(item ?? "").trim())
    .filter(Boolean)
    .filter((item, index, array) => array.indexOf(item) === index);
}

function chunk<T>(arr: T[], size: number) {
  const out: T[][] = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

type SectionItem = {
  title: string;
  summary: string;
  whyItMatters: string;
  sourceName: string;
  sourceUrl: string;
};

function sanitizeSectionItems(items: unknown[]): SectionItem[] {
  const normalized = (items || [])
    .map((entry) => (typeof entry === "object" && entry !== null ? (entry as Partial<SectionItem>) : null))
    .filter(Boolean)
    .map((entry) => ({
      title: String(entry?.title || "").trim(),
      summary: String(entry?.summary || "").trim(),
      whyItMatters: String(entry?.whyItMatters || "").trim(),
      sourceName: String(entry?.sourceName || "").trim(),
      sourceUrl: String(entry?.sourceUrl || "").trim()
    }))
    .filter((item) => item.title && item.summary && item.whyItMatters && item.sourceName && /^https?:\/\//.test(item.sourceUrl));

  const deduped = normalized.filter(
    (item, idx, arr) => arr.findIndex((x) => `${x.title}|${x.sourceUrl}` === `${item.title}|${item.sourceUrl}`) === idx
  );

  return deduped;
}

function sanitizeSections(candidateSections: unknown, autoSections: Array<{ section: string; items: SectionItem[] }>) {
  const candidate = Array.isArray(candidateSections)
    ? candidateSections
        .map((section) => (typeof section === "object" && section !== null ? section : null))
        .filter(Boolean)
        .map((section) => {
          const raw = section as { section?: string; items?: unknown[] };
          const sectionTitle = String(raw.section || "").trim();
          const items = sanitizeSectionItems(Array.isArray(raw.items) ? raw.items : []);
          return sectionTitle ? { section: sectionTitle, items } : null;
        })
        .filter(Boolean)
    : [];

  const nonEmpty = candidate
    .map((section) => {
      const safeItems = section!.items.length ? section!.items : [fallbackSectionItem];
      return { section: section!.section, items: safeItems };
    })
    .filter((section) => section.items.length > 0);

  const baseSections = nonEmpty.length ? nonEmpty : autoSections;

  const completed = baseSections.map((section) => ({
    section: section.section,
    items: section.items.length ? section.items : [fallbackSectionItem]
  }));

  while (completed.length < 3) {
    completed.push({
      section: defaultSections[completed.length] || `Seção ${completed.length + 1}`,
      items: [fallbackSectionItem]
    });
  }

  return completed;
}

export function sanitizeDraft(candidate: Partial<EditorialDraft> | undefined, input: EditorialInput): Partial<EditorialDraft> {
  const sourceSummary = uniqueNonEmpty([
    ...(Array.isArray(candidate?.executiveSummary) ? candidate.executiveSummary : []),
    ...input.news.slice(0, 6).map((n) => `${n.title} — ${n.content}`),
    ...fallbackExecutiveSummary
  ]).slice(0, 6);

  while (sourceSummary.length < 3) sourceSummary.push(fallbackExecutiveSummary[sourceSummary.length % 3]);

  const autoSections = chunk(input.news.slice(0, 12), 3).map((items, idx) => ({
    section: defaultSections[idx] || `Seção ${idx + 1}`,
    items: items.map((item) => ({
      title: item.title,
      summary: item.content,
      whyItMatters: "Importa por influenciar expectativas de juros, prêmio de risco, fluxos globais e precificação relativa de ativos.",
      sourceName: item.sourceName,
      sourceUrl: item.sourceUrl
    }))
  }));

  const safeAutoSections = autoSections.map((section) => ({
    section: section.section,
    items: section.items.length ? section.items : [fallbackSectionItem]
  }));

  const sections = sanitizeSections(candidate?.sections, safeAutoSections);

  return {
    subject: candidate?.subject?.trim() || "Global Market Morning Brief | Macro, política monetária e ativos no radar",
    preheader: candidate?.preheader || "Leitura executiva para decisões de mercado: macro, risco, fluxos e agenda.",
    executiveSummary: sourceSummary,
    sections,
    marketSnapshot: candidate?.marketSnapshot?.length
      ? candidate.marketSnapshot
      : [
          { asset: "S&P 500", price: "5.245", change: "+0,4%", period: "D-1" },
          { asset: "US 10Y", price: "4,25%", change: "+6 bps", period: "D-1" },
          { asset: "DXY", price: "103,9", change: "+0,3%", period: "D-1" },
          { asset: "Brent", price: "US$ 87", change: "+1,1%", period: "D-1" }
        ],
    tables: candidate?.tables?.length
      ? candidate.tables
      : [
          {
            title: "Performance de ativos (mock)",
            columns: ["Ativo", "Preço", "Var. D-1", "Comentário"],
            rows: [
              ["S&P 500", "5.245", "+0,4%", "Tecnologia sustenta o índice."],
              ["US 10Y", "4,25%", "+6 bps", "Mercado precifica juros altos por mais tempo."],
              ["DXY", "103,9", "+0,3%", "Busca por proteção favorece dólar."],
              ["Brent", "US$ 87", "+1,1%", "Risco geopolítico mantém prêmio."]
            ]
          }
        ],
    charts: candidate?.charts?.length ? candidate.charts : generateMockCharts(),
    images: candidate?.images?.length
      ? candidate.images
      : [
          {
            title: "Mapa de risco geopolítico",
            url: "https://picsum.photos/960/420",
            caption: "Imagem ilustrativa para contexto macro/político."
          }
        ],
    monitorToday: uniqueNonEmpty(Array.isArray(candidate?.monitorToday) ? candidate.monitorToday : fallbackMonitor).slice(0, 6),
    agenda: uniqueNonEmpty(Array.isArray(candidate?.agenda) ? candidate.agenda : fallbackAgenda).slice(0, 6),
    conclusion:
      candidate?.conclusion ||
      "Em síntese, o regime de mercado permanece dominado por trajetória de inflação, reação dos bancos centrais e riscos geopolíticos. A leitura de curto prazo favorece gestão ativa de risco, atenção à curva de juros e seletividade entre classes de ativos.",
    sources: uniqueNonEmpty(input.news.map((n) => n.sourceUrl)).slice(0, 12)
  };
}
