import type { EditorialDraft } from "@/lib/ai/types";

export function renderNewsletterHtml(draft: EditorialDraft): string {
  return `
    <div style="font-family:Arial,sans-serif;max-width:680px;margin:0 auto;padding:24px">
      <h1>${draft.subject}</h1>
      <h2>Abertura executiva</h2>
      <ul>${draft.executiveSummary.map((b) => `<li>${b}</li>`).join("")}</ul>
      ${draft.sections
        .map(
          (s) =>
            `<h2>${s.section}</h2>${s.items
              .map(
                (i) => `<h3>${i.title}</h3><p>${i.summary}</p><p><strong>Por que importa:</strong> ${i.whyItMatters}</p>`
              )
              .join("")}`
        )
        .join("")}
      <h2>O que monitorar hoje</h2>
      <ul>${draft.monitorToday.map((m) => `<li>${m}</li>`).join("")}</ul>
      <h2>Agenda</h2>
      <ul>${draft.agenda.map((a) => `<li>${a}</li>`).join("")}</ul>
    </div>
  `;
}

export function renderNewsletterText(draft: EditorialDraft): string {
  return `${draft.subject}\n\n${draft.executiveSummary.join("\n")}`;
}
