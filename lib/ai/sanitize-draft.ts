import type { EditorialDraft, EditorialInput } from "./types";

const fallbackExecutiveSummary = [
  "Mercados globais operam com atenção a dados macroeconômicos e sinalizações de política monetária.",
  "Investidores monitoram bancos centrais, inflação e juros em busca de direção para os ativos.",
  "Risco geopolítico e decisões governamentais seguem como vetores relevantes para sentimento de mercado."
];

const fallbackMonitor = [
  "Comunicações de bancos centrais e autoridades fiscais.",
  "Dinâmica de yields longas e comportamento do dólar global.",
  "Movimento de commodities e percepção de risco geopolítico."
];

const fallbackAgenda = [
  "Calendário de inflação e atividade das principais economias.",
  "Leilões de títulos soberanos e condições financeiras globais.",
  "Eventos políticos com potencial de impacto nos mercados."
];

function uniqueNonEmpty(items: unknown[]): string[] {
  const cleaned = items
    .map((item) => String(item ?? "").trim())
    .filter(Boolean)
    .filter((item, index, array) => array.indexOf(item) === index);
  return cleaned;
}

function buildNewsBasedSummary(input: EditorialInput): string[] {
  return input.news
    .slice(0, 6)
    .map((item) => `${item.title.trim()} — ${item.content.trim()}`)
    .filter((item) => item.length > 10);
}

export function sanitizeDraft(candidate: Partial<EditorialDraft> | undefined, input: EditorialInput): Partial<EditorialDraft> {
  const sourceSummary = uniqueNonEmpty([
    ...(Array.isArray(candidate?.executiveSummary) ? candidate?.executiveSummary : []),
    ...buildNewsBasedSummary(input),
    ...fallbackExecutiveSummary
  ]);

  const executiveSummary = sourceSummary.slice(0, 6);
  while (executiveSummary.length < 3) {
    const nextFallback = fallbackExecutiveSummary[executiveSummary.length % fallbackExecutiveSummary.length];
    if (!executiveSummary.includes(nextFallback)) executiveSummary.push(nextFallback);
  }

  const defaultSectionItems = input.news.slice(0, 5).map((item) => ({
    title: item.title,
    summary: item.content,
    whyItMatters: "Pode alterar expectativas de juros, câmbio, risco e preço de ativos globais.",
    sourceName: item.sourceName,
    sourceUrl: item.sourceUrl
  }));

  const sections = Array.isArray(candidate?.sections) && candidate.sections.length
    ? candidate.sections
    : [{ section: "Mercados globais", items: defaultSectionItems }];

  return {
    subject: candidate?.subject?.trim() || "Morning Brief: panorama macro e mercados globais",
    executiveSummary,
    sections,
    monitorToday: uniqueNonEmpty(Array.isArray(candidate?.monitorToday) ? candidate.monitorToday : []).length
      ? uniqueNonEmpty(candidate?.monitorToday || []).slice(0, 6)
      : fallbackMonitor,
    agenda: uniqueNonEmpty(Array.isArray(candidate?.agenda) ? candidate.agenda : []).length
      ? uniqueNonEmpty(candidate?.agenda || []).slice(0, 6)
      : fallbackAgenda
  };
}
