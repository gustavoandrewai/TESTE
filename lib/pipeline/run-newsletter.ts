import { MockAIProvider } from "@/lib/ai/mock-provider";
import { OpenAIProvider } from "@/lib/ai/openai-provider";
import { prisma } from "@/lib/db/prisma";
import { getEmailRuntimeConfig } from "@/lib/email/mode";
import { MockEmailProvider } from "@/lib/email/mock-provider";
import { ResendProvider } from "@/lib/email/resend-provider";
import { SendGridProvider } from "@/lib/email/sendgrid-provider";
import type { EmailProvider } from "@/lib/email/types";
import { deduplicateNews } from "@/lib/news/deduplication";
import { MockNewsProvider } from "@/lib/news/mock-provider";
import { normalizeNews } from "@/lib/news/normalization";
import { rankNews } from "@/lib/news/ranking";
import { RSSNewsProvider } from "@/lib/news/rss-provider";
import { renderNewsletterHtml, renderNewsletterText } from "@/lib/render/newsletter";

function selectNewsProvider() {
  return process.env.NEWS_PROVIDER === "rss"
    ? new RSSNewsProvider((process.env.NEWS_FEEDS || "").split(",").filter(Boolean))
    : new MockNewsProvider();
}

function selectAIProvider() {
  return process.env.AI_PROVIDER === "openai" ? new OpenAIProvider() : new MockAIProvider();
}

function selectProviderByName(name: "mock" | "resend" | "sendgrid"): EmailProvider {
  if (name === "resend") return new ResendProvider();
  if (name === "sendgrid") return new SendGridProvider();
  return new MockEmailProvider();
}

export async function runNewsletterPipeline(runType: "MANUAL" | "SCHEDULED" = "MANUAL") {
  const startedAt = new Date();
  const runLog = await prisma.runLog.create({ data: { jobType: "newsletter_pipeline", status: "RUNNING", startedAt } });

  try {
    const maxItemsSetting = await prisma.appSetting.findUnique({ where: { key: "MAX_ITEMS" } });
    const maxItems = Number(maxItemsSetting?.value || "15");

    const raw = await selectNewsProvider().fetchLatestNews();
    const normalized = normalizeNews(raw);
    const deduped = deduplicateNews(normalized);
    const ranked = rankNews(deduped).slice(0, Number.isNaN(maxItems) ? 15 : maxItems);

    if (!ranked.length) throw new Error("Nenhuma notícia relevante encontrada.");

    const draft = await selectAIProvider().generateEditorial({ news: ranked });
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
        metadata: JSON.stringify({ items: ranked.length, subject: draft.subject })
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

  // 1) Preview sempre bloqueia envio real/simulado
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

  // 2) Modo mock explícito OU provider mock explícito
  const shouldMockSend = emailConfig.sendMode === "mock" || emailConfig.provider === "mock";
  const provider = shouldMockSend ? new MockEmailProvider() : selectProviderByName(emailConfig.provider);

  // 3) Caminho live exige configuração válida (sem fallback silencioso)
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

  for (const recipient of recipients) {
    try {
      const result = await provider.send({
        to: recipient.email,
        subject: newsletter.subject,
        html: newsletter.htmlContent,
        text: newsletter.textContent
      });

      sent += 1;
      await prisma.deliveryLog.create({
        data: {
          newsletterId,
          recipientId: recipient.id,
          provider: provider.name,
          status: shouldMockSend ? "mock_sent" : "sent",
          providerMessageId: result.messageId,
          sentAt: new Date(),
          errorMessage: shouldMockSend ? "Simulação de envio (modo/provider mock explícito)" : null
        }
      });
    } catch (error) {
      failed += 1;
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
    }
  }

  await prisma.newsletter.update({ where: { id: newsletterId }, data: { status: failed ? "FAILED" : "SENT", sentAt: new Date() } });

  return {
    provider: provider.name,
    mode: shouldMockSend ? "mock" : "live",
    previewMode: emailConfig.previewMode,
    sent,
    failed,
    failures
  };
}
