import { MockAIProvider } from "@/lib/ai/mock-provider";
import { OpenAIProvider } from "@/lib/ai/openai-provider";
import { prisma } from "@/lib/db/prisma";
import { getEmailRuntimeConfig } from "@/lib/email/mode";
import { MockEmailProvider } from "@/lib/email/mock-provider";
import { ResendProvider } from "@/lib/email/resend-provider";
import { SendGridProvider } from "@/lib/email/sendgrid-provider";
import type { EmailProvider } from "@/lib/email/types";
import { deduplicateNews } from "@/lib/news/deduplication";
import { FinvizNewsProvider } from "@/lib/news/finviz-provider";
import { MockNewsProvider } from "@/lib/news/mock-provider";
import { normalizeNews } from "@/lib/news/normalization";
import { rankNews } from "@/lib/news/ranking";
import { RSSNewsProvider } from "@/lib/news/rss-provider";
import type { NewsProvider, NormalizedNews } from "@/lib/news/types";
import { renderNewsletterHtml, renderNewsletterText } from "@/lib/render/newsletter";

function selectAIProvider() {
  return process.env.AI_PROVIDER === "openai" ? new OpenAIProvider() : new MockAIProvider();
}

function selectProviderByName(name: "mock" | "resend" | "sendgrid"): EmailProvider {
  if (name === "resend") return new ResendProvider();
  if (name === "sendgrid") return new SendGridProvider();
  return new MockEmailProvider();
}

function parseSources(raw: string | undefined) {
  return (raw || "mock")
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
}

function buildNewsProviders(enabledSources: string[]): NewsProvider[] {
  const providers: NewsProvider[] = [];
  if (enabledSources.includes("mock")) providers.push(new MockNewsProvider());
  if (enabledSources.includes("rss")) providers.push(new RSSNewsProvider((process.env.NEWS_FEEDS || "").split(",").filter(Boolean)));
  if (enabledSources.includes("finviz")) providers.push(new FinvizNewsProvider());
  if (!providers.length) providers.push(new MockNewsProvider());
  return providers;
}

async function fetchMergedNews(enabledSources: string[]) {
  const providers = buildNewsProviders(enabledSources);
  const settled = await Promise.allSettled(providers.map((provider) => provider.fetchLatestNews()));
  const merged = settled.flatMap((result) => (result.status === "fulfilled" ? result.value : []));

  for (const result of settled) {
    if (result.status === "rejected") console.error("news_source_error", result.reason);
  }

  return merged;
}

function expandSourcesForFallback(enabledSources: string[]) {
  const expanded = [...enabledSources];
  if (!expanded.includes("finviz")) expanded.push("finviz");
  if (!expanded.includes("rss")) expanded.push("rss");
  return Array.from(new Set(expanded));
}

function applySourceWeight<T extends { sourceName: string; relevanceScore?: number }>(items: T[], finvizWeight: number, rssWeight: number) {
  return items
    .map((item) => {
      const source = (item.sourceName || "").toLowerCase();
      let bonus = 0;
      if (source.includes("finviz")) bonus = finvizWeight;
      if (source.includes("reuters") || source.includes("bloomberg") || source.includes("cnbc")) bonus = rssWeight;
      return { ...item, relevanceScore: Math.min(100, (item.relevanceScore || 0) + bonus) };
    })
    .sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0));
}

function enrichWithLightDuplication(items: NormalizedNews[], target: number) {
  const selected: NormalizedNews[] = [];
  const byTitleUrl = new Set<string>();
  const byTopicCount = new Map<string, number>();
  const topicKey = (item: NormalizedNews) => {
    const head = `${item.category} ${item.title}`.toLowerCase().replace(/[^a-z0-9à-ÿ\s]/gi, " ");
    return head.split(/\s+/).filter(Boolean).slice(0, 5).join(" ");
  };

  for (const item of items) {
    const identity = `${item.title}|${item.sourceUrl}`;
    if (byTitleUrl.has(identity)) continue;
    selected.push(item);
    byTitleUrl.add(identity);
    byTopicCount.set(topicKey(item), (byTopicCount.get(topicKey(item)) || 0) + 1);
    if (selected.length >= target) return selected;
  }

  for (const item of items) {
    const topic = topicKey(item);
    const used = byTopicCount.get(topic) || 0;
    if (used >= 2) continue;
    selected.push({
      ...item,
      title: `${item.title} (contexto complementar)`,
      content: `${item.content} | Complemento temático para manter cobertura editorial.`
    });
    byTopicCount.set(topic, used + 1);
    if (selected.length >= target) return selected;
  }

  return selected;
}

function ensureHardMinimum(items: NormalizedNews[], hardMin: number) {
  if (items.length >= hardMin) return items;
  if (!items.length) return items;

  const out = [...items];
  let i = 0;
  while (out.length < hardMin) {
    const base = items[i % items.length];
    out.push({
      ...base,
      title: `${base.title} (síntese adicional ${Math.floor(i / items.length) + 1})`,
      content: `${base.content} | Síntese adicional para edição com baixa densidade de dados.`
    });
    i += 1;
  }
  return out;
}

export async function runNewsletterPipeline(runType: "MANUAL" | "SCHEDULED" = "MANUAL") {
  const startedAt = new Date();
  const runLog = await prisma.runLog.create({ data: { jobType: "newsletter_pipeline", status: "RUNNING", startedAt } });

  try {
    const [
      maxItemsSetting,
      minItemsIdealSetting,
      minItemsLegacySetting,
      minItemsHardSetting,
      enableFallbackSetting,
      enabledSourcesSetting,
      finvizWeightSetting,
      rssWeightSetting
    ] = await Promise.all([
      prisma.appSetting.findUnique({ where: { key: "MAX_ITEMS" } }),
      prisma.appSetting.findUnique({ where: { key: "MIN_ITEMS_IDEAL" } }),
      prisma.appSetting.findUnique({ where: { key: "MIN_NEWS_ITEMS" } }),
      prisma.appSetting.findUnique({ where: { key: "MIN_ITEMS_HARD" } }),
      prisma.appSetting.findUnique({ where: { key: "ENABLE_FALLBACK" } }),
      prisma.appSetting.findUnique({ where: { key: "ENABLED_SOURCES" } }),
      prisma.appSetting.findUnique({ where: { key: "FINVIZ_WEIGHT" } }),
      prisma.appSetting.findUnique({ where: { key: "RSS_WEIGHT" } })
    ]);

    const maxItems = Number(maxItemsSetting?.value || "15");
    const minItemsIdeal = Number(minItemsIdealSetting?.value || minItemsLegacySetting?.value || process.env.MIN_ITEMS_IDEAL || "10");
    const minItemsHard = Number(minItemsHardSetting?.value || process.env.MIN_ITEMS_HARD || "5");
    const enableFallback = (enableFallbackSetting?.value || process.env.ENABLE_FALLBACK || "true").toLowerCase() !== "false";
    const enabledSources = parseSources(enabledSourcesSetting?.value || process.env.ENABLED_SOURCES || process.env.NEWS_PROVIDER || "mock");
    const finvizWeight = Number(finvizWeightSetting?.value || "8");
    const rssWeight = Number(rssWeightSetting?.value || "4");
    const safeMaxItems = Number.isNaN(maxItems) ? 15 : Math.max(5, maxItems);
    const safeIdealMin = Number.isNaN(minItemsIdeal) ? 10 : Math.max(5, minItemsIdeal);
    const safeHardMin = Number.isNaN(minItemsHard) ? 5 : Math.max(3, Math.min(minItemsHard, safeIdealMin));

    const raw = await fetchMergedNews(enabledSources);
    const normalized = normalizeNews(raw);
    const deduped = deduplicateNews(normalized);
    const rankedPrimary = applySourceWeight(rankNews(deduped), finvizWeight, rssWeight);
    let ranked = rankedPrimary.slice(0, safeMaxItems);
    let degradedMode = false;
    let fallbackReason: string | null = null;
    let fallbackBefore = ranked.length;
    let fallbackAfter = ranked.length;

    if (ranked.length < safeIdealMin && enableFallback) {
      degradedMode = true;
      fallbackReason = `insufficient_items_${ranked.length}_ideal_${safeIdealMin}`;

      const fallbackSources = expandSourcesForFallback(enabledSources);
      const extraRaw = await fetchMergedNews(fallbackSources);
      const fallbackNormalized = normalizeNews(extraRaw);
      const relaxedPool = applySourceWeight(rankNews(fallbackNormalized), Math.max(2, finvizWeight - 2), Math.max(1, rssWeight - 2));

      const relaxedSelected = enrichWithLightDuplication(relaxedPool, safeMaxItems);
      ranked = ensureHardMinimum(relaxedSelected, safeHardMin).slice(0, safeMaxItems);
      fallbackAfter = ranked.length;

      console.warn("fallback_activated", {
        reason: fallbackReason,
        before: fallbackBefore,
        after: fallbackAfter,
        hardMin: safeHardMin,
        idealMin: safeIdealMin,
        enabledSources: enabledSources.join(","),
        fallbackSources: fallbackSources.join(",")
      });
    }

    if (ranked.length < safeHardMin) {
      degradedMode = true;
      fallbackReason = fallbackReason || "below_hard_min_after_fallback";
      const mockFallback = applySourceWeight(rankNews(normalizeNews(await new MockNewsProvider().fetchLatestNews())), finvizWeight, rssWeight);
      ranked = ensureHardMinimum([...ranked, ...mockFallback], safeHardMin).slice(0, safeMaxItems);
      fallbackAfter = ranked.length;
      console.warn("fallback_activated", {
        reason: fallbackReason,
        before: fallbackBefore,
        after: fallbackAfter,
        hardMin: safeHardMin,
        idealMin: safeIdealMin,
        enabledSources: enabledSources.join(","),
        fallbackSources: "mock"
      });
    }

    const draft = await selectAIProvider().generateEditorial({ news: ranked });
    if (degradedMode) {
      const warningFlag = "Edição com menor densidade de dados";
      draft.preheader = draft.preheader ? `${warningFlag} | ${draft.preheader}` : warningFlag;
      if (!draft.executiveSummary.some((line) => line.includes(warningFlag))) {
        draft.executiveSummary = [warningFlag, ...draft.executiveSummary].slice(0, 6);
      }
    }
    const htmlContent = renderNewsletterHtml(draft);
    const textContent = renderNewsletterText(draft);

    const newsletter = await prisma.newsletter.create({
      data: {
        subject: draft.subject,
        htmlContent,
        textContent,
        status: "GENERATED",
        runType,
        items: {
          create: ranked.map((item) => ({
            section: item.category,
            title: item.title,
            summary: item.content,
            sourceName: item.sourceName,
            sourceUrl: item.sourceUrl,
            publishedAt: item.publishedAt,
            relevanceScore: item.relevanceScore || 0,
            rawData: JSON.stringify(item)
          }))
        }
      }
    });

    await prisma.runLog.update({
      where: { id: runLog.id },
      data: {
        status: "SUCCESS",
        finishedAt: new Date(),
        durationMs: Date.now() - startedAt.getTime(),
        metadata: JSON.stringify({
          items: ranked.length,
          subject: draft.subject,
          sources: enabledSources.join(","),
          degradedMode,
          fallbackActivated: degradedMode,
          fallbackReason,
          fallbackBefore,
          fallbackAfter
        })
      }
    });

    return newsletter;
  } catch (error) {
    await prisma.runLog.update({
      where: { id: runLog.id },
      data: {
        status: "FAILED",
        finishedAt: new Date(),
        durationMs: Date.now() - startedAt.getTime(),
        errorMessage: error instanceof Error ? error.message : "Erro desconhecido"
      }
    });
    throw error;
  }
}

export async function sendNewsletter(newsletterId: string) {
  const newsletter = await prisma.newsletter.findUnique({ where: { id: newsletterId } });
  if (!newsletter) throw new Error("Newsletter não encontrada");

  const recipients = await prisma.recipient.findMany({ where: { active: true } });
  if (!recipients.length) throw new Error("Sem destinatários ativos");

  const emailConfig = await getEmailRuntimeConfig();

  if (emailConfig.previewMode) {
    await Promise.all(
      recipients.map((recipient) =>
        prisma.deliveryLog.create({
          data: {
            newsletterId,
            recipientId: recipient.id,
            provider: emailConfig.provider,
            status: "blocked_preview",
            errorMessage: "PREVIEW_MODE=true bloqueia qualquer envio"
          }
        })
      )
    );
    throw new Error("Envio bloqueado: PREVIEW_MODE=true");
  }

  const shouldMockSend = emailConfig.sendMode === "mock" || emailConfig.provider === "mock";
  const provider = shouldMockSend ? new MockEmailProvider() : selectProviderByName(emailConfig.provider);

  if (!shouldMockSend && !emailConfig.validForLive) {
    const reason = emailConfig.reasons.join("; ") || "Configuração de envio live inválida";

    await Promise.all(
      recipients.map((recipient) =>
        prisma.deliveryLog.create({
          data: {
            newsletterId,
            recipientId: recipient.id,
            provider: emailConfig.provider,
            status: "config_error",
            errorMessage: reason
          }
        })
      )
    );

    throw new Error(`Configuração de envio inválida: ${reason}`);
  }

  let sent = 0;
  let failed = 0;
  const failures: Array<{ recipient: string; reason: string }> = [];
  const statusCount: Record<string, number> = { queued: 0, sent: 0, delivered: 0, bounced: 0, rejected: 0, mock_sent: 0, failed: 0 };

  for (const recipient of recipients) {
    try {
      const result = await provider.send({
        to: recipient.email,
        subject: newsletter.subject,
        html: newsletter.htmlContent,
        text: newsletter.textContent
      });

      const status = result.providerStatus;
      statusCount[status] = (statusCount[status] || 0) + 1;

      if (["sent", "delivered", "mock_sent"].includes(status)) {
        sent += 1;
      }

      await prisma.deliveryLog.create({
        data: {
          newsletterId,
          recipientId: recipient.id,
          provider: provider.name,
          status,
          providerMessageId: result.messageId,
          sentAt: ["sent", "delivered", "mock_sent", "queued"].includes(status) ? new Date() : null,
          errorMessage: result.providerRaw || (status === "mock_sent" ? "Simulação de envio (modo/provider mock explícito)" : null)
        }
      });

      console.log("delivery", { recipient: recipient.email, provider: provider.name, status, messageId: result.messageId });
    } catch (error) {
      failed += 1;
      statusCount.failed = (statusCount.failed || 0) + 1;
      const reason = error instanceof Error ? error.message : "Erro desconhecido";
      failures.push({ recipient: recipient.email, reason });

      await prisma.deliveryLog.create({
        data: {
          newsletterId,
          recipientId: recipient.id,
          provider: provider.name,
          status: "failed",
          errorMessage: reason
        }
      });

      console.error("delivery_failed", { recipient: recipient.email, provider: provider.name, reason });
    }
  }

  const providerConfirmed = statusCount.sent + statusCount.delivered;
  const hasQueueOnly = statusCount.queued > 0 && providerConfirmed === 0;

  await prisma.newsletter.update({
    where: { id: newsletterId },
    data: {
      status: failed > 0 ? "FAILED" : providerConfirmed > 0 || statusCount.mock_sent > 0 ? "SENT" : hasQueueOnly ? "SCHEDULED" : "GENERATED",
      sentAt: providerConfirmed > 0 || statusCount.mock_sent > 0 ? new Date() : null
    }
  });

  return {
    provider: provider.name,
    mode: shouldMockSend ? "mock" : "live",
    previewMode: emailConfig.previewMode,
    sent,
    failed,
    failures,
    deliveryStatus: statusCount
  };
}
