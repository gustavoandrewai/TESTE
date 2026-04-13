import { describe, expect, it } from "vitest";
import { newsletterDraftSchema } from "@/lib/validation/schemas";

describe("schema", () => {
  it("validates newsletter draft", () => {
    const valid = newsletterDraftSchema.safeParse({
      subject: "Global Market Morning Brief | Teste de validação",
      executiveSummary: [
        "Mercados reprecificam juros globais após dados de inflação acima do esperado.",
        "Bancos centrais mantêm tom cauteloso e sinalizam manutenção de aperto financeiro.",
        "Risco geopolítico eleva prêmio em energia e sustenta volatilidade intermercados."
      ],
      sections: [
        { section: "Macro", items: [{ title: "t", summary: "s", whyItMatters: "w", sourceName: "n", sourceUrl: "https://a.com" }] },
        { section: "Mercados", items: [{ title: "t2", summary: "s2", whyItMatters: "w2", sourceName: "n", sourceUrl: "https://b.com" }] },
        { section: "Política", items: [{ title: "t3", summary: "s3", whyItMatters: "w3", sourceName: "n", sourceUrl: "https://c.com" }] }
      ],
      monitorToday: ["Falas do Fed e BCE com potencial de alterar curva.", "Evolução do dólar global e Treasuries longas.", "Risco geopolítico no mercado de energia."],
      agenda: ["CPI EUA", "Fala de membros do FOMC", "PMI Zona do Euro"]
    });
    expect(valid.success).toBeTruthy();
  });
});
