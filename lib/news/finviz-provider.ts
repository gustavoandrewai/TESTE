import type { NewsProvider, RawNewsItem } from "./types";

type CacheEntry = { expiresAt: number; items: RawNewsItem[] };

const CACHE_TTL_MS = 5 * 60 * 1000;
let cache: CacheEntry | null = null;

function stripHtml(value: string) {
  return value.replace(/<[^>]+>/g, "").replace(/&amp;/g, "&").replace(/&#39;/g, "'").replace(/&quot;/g, '"').trim();
}

function parseFinvizTimestamp(value: string): string {
  const text = value.trim();
  if (!text) return new Date().toISOString();

  const now = new Date();
  const todayMatch = text.match(/^today\s+(\d{1,2}:\d{2}(?:am|pm))$/i);
  if (todayMatch) {
    const date = new Date(now);
    const [time, meridiem] = [todayMatch[1].slice(0, -2), todayMatch[1].slice(-2).toLowerCase()];
    const [hourRaw, minuteRaw] = time.split(":");
    let hour = Number(hourRaw);
    const minute = Number(minuteRaw);
    if (meridiem === "pm" && hour < 12) hour += 12;
    if (meridiem === "am" && hour === 12) hour = 0;
    date.setHours(hour, minute, 0, 0);
    return date.toISOString();
  }

  const absoluteMatch = text.match(/^([a-z]{3})-(\d{1,2})-(\d{2})\s+(\d{1,2}:\d{2}(?:am|pm))$/i);
  if (absoluteMatch) {
    const monthMap: Record<string, number> = {
      jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11
    };
    const [, mon, day, yearShort, timeMeridiem] = absoluteMatch;
    const [time, meridiem] = [timeMeridiem.slice(0, -2), timeMeridiem.slice(-2).toLowerCase()];
    const [hourRaw, minuteRaw] = time.split(":");
    let hour = Number(hourRaw);
    const minute = Number(minuteRaw);
    if (meridiem === "pm" && hour < 12) hour += 12;
    if (meridiem === "am" && hour === 12) hour = 0;
    const date = new Date(2000 + Number(yearShort), monthMap[mon.toLowerCase()] ?? now.getMonth(), Number(day), hour, minute, 0, 0);
    return date.toISOString();
  }

  return new Date().toISOString();
}

function parseFinviz(html: string): RawNewsItem[] {
  const results: RawNewsItem[] = [];

  const rowRegex = /<tr[^>]*>\s*<td[^>]*>(.*?)<\/td>\s*<td[^>]*>(.*?)<\/td>\s*<\/tr>/gms;
  let rowMatch: RegExpExecArray | null;

  while ((rowMatch = rowRegex.exec(html))) {
    const metaCell = rowMatch[1] || "";
    const newsCell = rowMatch[2] || "";

    const linkMatch = newsCell.match(/<a[^>]+href=["']([^"']+)["'][^>]*>(.*?)<\/a>/i);
    if (!linkMatch) continue;

    const url = linkMatch[1].startsWith("http") ? linkMatch[1] : `https://finviz.com/${linkMatch[1].replace(/^\//, "")}`;
    const title = stripHtml(linkMatch[2]);

    const sourceMatch = newsCell.match(/<span[^>]*>([^<]+)<\/span>/i);
    const source = sourceMatch ? stripHtml(sourceMatch[1]) : "Finviz";

    const tsText = stripHtml(metaCell);
    const publishedAt = parseFinvizTimestamp(tsText);

    if (title && url) {
      results.push({
        title,
        url,
        source,
        publishedAt,
        snippet: `Fonte ${source}. Timestamp Finviz: ${tsText || "N/D"}`,
        category: "equities"
      });
    }
  }

  // fallback parser if Finviz structure changes
  if (!results.length) {
    const fallbackRegex = /<a[^>]+href=["'](https?:\/\/[^"']+)["'][^>]*>(.*?)<\/a>/gim;
    let m: RegExpExecArray | null;
    while ((m = fallbackRegex.exec(html))) {
      const title = stripHtml(m[2]);
      if (!title || title.length < 25) continue;
      results.push({
        title,
        url: m[1],
        source: "Finviz",
        publishedAt: new Date().toISOString(),
        snippet: "Notícia coletada via fallback parser do Finviz.",
        category: "macro"
      });
      if (results.length >= 40) break;
    }
  }

  return results.slice(0, 80);
}

export class FinvizNewsProvider implements NewsProvider {
  async fetchLatestNews(): Promise<RawNewsItem[]> {
    const now = Date.now();
    if (cache && cache.expiresAt > now) return cache.items;

    const response = await fetch("https://finviz.com/news.ashx", {
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; GMMB-NewsBot/1.0)",
        Accept: "text/html"
      }
    });

    if (!response.ok) {
      throw new Error(`Finviz indisponível: HTTP ${response.status}`);
    }

    const html = await response.text();
    const items = parseFinviz(html);

    cache = { items, expiresAt: now + CACHE_TTL_MS };
    return items;
  }
}

export const __testing = { parseFinviz };
