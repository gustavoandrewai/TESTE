import { describe, expect, it } from "vitest";
import { renderNewsletterHtml } from "@/lib/render/newsletter";

describe("render", () => {
  it("creates html content", () => {
    const html = renderNewsletterHtml({
      subject: "Teste",
      executiveSummary: ["a", "b", "c"],
      sections: [{ section: "Mercados", items: [{ title: "x", summary: "y", whyItMatters: "z", sourceName: "n", sourceUrl: "https://a.com" }] }],
      monitorToday: ["1"],
      agenda: ["2"]
    });

    expect(html.includes("Mercados")).toBeTruthy();
  });
});
