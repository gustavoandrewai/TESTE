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
      }
    ];
  }
}
