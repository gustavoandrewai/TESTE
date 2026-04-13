import type { EditorialDraft } from "@/lib/ai/types";

function escapeHtml(text: string) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function renderNewsletterHtml(draft: EditorialDraft): string {
  const dateStr = new Intl.DateTimeFormat("pt-BR", { dateStyle: "full" }).format(new Date());

  return `
  <div style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:24px 0;">
      <tr><td align="center">
        <table role="presentation" width="760" cellpadding="0" cellspacing="0" style="max-width:760px;background:#ffffff;border-radius:14px;overflow:hidden;">
          <tr><td style="background:#0f172a;color:#fff;padding:24px 28px;">
            <p style="margin:0;font-size:12px;letter-spacing:.08em;text-transform:uppercase;opacity:.8;">Global Market Morning Brief</p>
            <h1 style="margin:8px 0 6px 0;font-size:26px;line-height:1.25;">${escapeHtml(draft.subject)}</h1>
            <p style="margin:0;font-size:14px;opacity:.9;">${escapeHtml(draft.preheader || "Leitura executiva para decisões de mercado")}</p>
            <p style="margin:10px 0 0 0;font-size:12px;opacity:.7;">${escapeHtml(dateStr)}</p>
          </td></tr>

          <tr><td style="padding:22px 28px;">
            <h2 style="margin:0 0 12px 0;font-size:18px;">Top Takeaways</h2>
            <ul style="margin:0;padding-left:18px;line-height:1.6;">
              ${draft.executiveSummary.map((item) => `<li style="margin-bottom:8px;">${escapeHtml(item)}</li>`).join("")}
            </ul>
          </td></tr>

          <tr><td style="padding:0 28px 20px 28px;">
            <h2 style="margin:0 0 12px 0;font-size:18px;">Market Snapshot</h2>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
              ${
                draft.marketSnapshot
                  ?.map(
                    (row) =>
                      `<tr>
                        <td style="padding:8px 6px;border-bottom:1px solid #e2e8f0;font-weight:600;">${escapeHtml(row.asset)}</td>
                        <td style="padding:8px 6px;border-bottom:1px solid #e2e8f0;">${escapeHtml(row.price)}</td>
                        <td style="padding:8px 6px;border-bottom:1px solid #e2e8f0;">${escapeHtml(row.change)}</td>
                        <td style="padding:8px 6px;border-bottom:1px solid #e2e8f0;color:#64748b;">${escapeHtml(row.period)}</td>
                      </tr>`
                  )
                  .join("") || ""
              }
            </table>
          </td></tr>

          ${draft.sections
            .map(
              (section) => `
              <tr><td style="padding:0 28px 18px 28px;">
                <h2 style="margin:0 0 10px 0;font-size:18px;">${escapeHtml(section.section)}</h2>
                ${section.items
                  .map(
                    (item) => `
                    <div style="padding:12px 14px;border:1px solid #e2e8f0;border-radius:10px;margin-bottom:10px;">
                      <h3 style="margin:0 0 6px 0;font-size:15px;line-height:1.4;">${escapeHtml(item.title)}</h3>
                      <p style="margin:0 0 6px 0;font-size:14px;line-height:1.6;">${escapeHtml(item.summary)}</p>
                      <p style="margin:0;font-size:13px;line-height:1.6;color:#334155;"><strong>Por que importa:</strong> ${escapeHtml(item.whyItMatters)}</p>
                    </div>`
                  )
                  .join("")}
              </td></tr>`
            )
            .join("")}

          ${
            draft.charts?.length
              ? `<tr><td style="padding:0 28px 18px 28px;"><h2 style="margin:0 0 10px 0;font-size:18px;">Charts</h2>
              ${draft.charts
                .map(
                  (chart) => `<div style="margin-bottom:14px;"><img src="${chart.imageUrl}" alt="${escapeHtml(chart.title)}" style="width:100%;max-width:680px;border:1px solid #e2e8f0;border-radius:8px;"/><p style="font-size:12px;color:#64748b;">${escapeHtml(chart.caption)}</p></div>`
                )
                .join("")}
              </td></tr>`
              : ""
          }

          ${
            draft.tables?.length
              ? `<tr><td style="padding:0 28px 18px 28px;">
                ${draft.tables
                  .map(
                    (table) => `<h2 style="margin:0 0 10px 0;font-size:18px;">${escapeHtml(table.title)}</h2>
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-bottom:12px;">
                      <tr>${table.columns.map((c) => `<th style="text-align:left;padding:8px;border-bottom:2px solid #cbd5e1;font-size:12px;color:#334155;">${escapeHtml(c)}</th>`).join("")}</tr>
                      ${table.rows
                        .map((row) => `<tr>${row.map((cell) => `<td style="padding:8px;border-bottom:1px solid #e2e8f0;font-size:13px;">${escapeHtml(cell)}</td>`).join("")}</tr>`)
                        .join("")}
                    </table>`
                  )
                  .join("")}
              </td></tr>`
              : ""
          }

          <tr><td style="padding:0 28px 18px 28px;">
            <h2 style="margin:0 0 10px 0;font-size:18px;">Agenda do Dia</h2>
            <ul style="margin:0;padding-left:18px;line-height:1.6;">${draft.agenda.map((a) => `<li>${escapeHtml(a)}</li>`).join("")}</ul>
          </td></tr>

          <tr><td style="padding:0 28px 24px 28px;">
            <h2 style="margin:0 0 10px 0;font-size:18px;">Conclusão Editorial</h2>
            <p style="margin:0;font-size:14px;line-height:1.7;">${escapeHtml(draft.conclusion || "")}</p>
          </td></tr>

          <tr><td style="padding:16px 28px;background:#f8fafc;border-top:1px solid #e2e8f0;">
            <p style="margin:0 0 6px 0;font-size:12px;color:#64748b;">Fontes: ${(draft.sources || []).slice(0, 8).map((s) => `<a href="${s}" style="color:#2563eb">link</a>`).join(" • ")}</p>
            <p style="margin:0;font-size:11px;color:#94a3b8;">Conteúdo informativo para uso profissional. Não constitui recomendação de investimento.</p>
          </td></tr>
        </table>
      </td></tr>
    </table>
  </div>`;
}

export function renderNewsletterText(draft: EditorialDraft): string {
  return [
    draft.subject,
    "",
    "Top Takeaways:",
    ...draft.executiveSummary.map((b) => `- ${b}`),
    "",
    ...draft.sections.flatMap((s) => [s.section, ...s.items.map((i) => `* ${i.title}: ${i.summary}`), ""]),
    "Agenda:",
    ...draft.agenda.map((a) => `- ${a}`),
    "",
    `Conclusão: ${draft.conclusion || ""}`
  ].join("\n");
}
