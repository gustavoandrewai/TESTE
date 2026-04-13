import { describe, expect, it } from "vitest";
import { renderNewsletterHtml } from "@/lib/render/newsletter";

describe("render", () => {
  it("creates html content", () => {
    const html = renderNewsletterHtml({
      subject: "Teste",
      executiveSummary: [
        "Mercados globais monitoram inflação e juros.",
        "Fluxo para dólar pressiona ativos de risco.",
        "Geopolítica segue no radar de volatilidade."
      ],
      sections: [
        {
          section: "Mercados",
          items: [{ title: "x", summary: "y", whyItMatters: "z", sourceName: "n", sourceUrl: "https://a.com" }]
        }
      ],
      monitorToday: ["1", "2", "3"],
      agenda: ["2", "3", "4"],
      conclusion: "Conclusão"
    });

    expect(html.includes("Top Takeaways")).toBeTruthy();
  });
});
