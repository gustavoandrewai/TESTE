import { subHours } from "@/lib/utils/time";
import type { NewsProvider, RawNewsItem } from "./types";

export class MockNewsProvider implements NewsProvider {
  async fetchLatestNews(): Promise<RawNewsItem[]> {
    return [
      {
        title: "Fed sinaliza manutenção de juros por mais tempo",
        url: "https://example.com/fed-juros",
        source: "MockWire",
        publishedAt: subHours(2).toISOString(),
        snippet: "Dirigentes reforçam postura cautelosa diante da inflação de serviços.",
        category: "bancos-centrais"
      },
      {
        title: "Petróleo sobe com tensão no Oriente Médio",
        url: "https://example.com/petroleo",
        source: "MockWire",
        publishedAt: subHours(3).toISOString(),
        snippet: "Brent avança e pressiona expectativas de inflação global.",
        category: "commodities"
      },
      {
        title: "Treasuries longas voltam a abrir com dado forte de emprego nos EUA",
        url: "https://example.com/treasuries-emprego",
        source: "MockWire",
        publishedAt: subHours(4).toISOString(),
        snippet: "Mercado recalibra trajetória de corte de juros e volatilidade de risco aumenta.",
        category: "juros"
      },
      {
        title: "BCE reforça dependência de dados para próximos passos de política monetária",
        url: "https://example.com/bce-dados",
        source: "MockWire",
        publishedAt: subHours(5).toISOString(),
        snippet: "Comunicação mantém foco em inflação de serviços e salário na zona do euro.",
        category: "bancos-centrais"
      },
      {
        title: "Dólar ganha força contra emergentes com aversão a risco",
        url: "https://example.com/dolar-emergentes",
        source: "MockWire",
        publishedAt: subHours(6).toISOString(),
        snippet: "Moedas de países importadores de energia sofrem com petróleo e juros elevados.",
        category: "fx"
      },
      {
        title: "China anuncia medidas fiscais direcionadas para sustentar atividade",
        url: "https://example.com/china-fiscal",
        source: "MockWire",
        publishedAt: subHours(7).toISOString(),
        snippet: "Pacote busca estabilizar setor imobiliário e dar suporte ao crédito corporativo.",
        category: "macro"
      }
    ];
  }
}
