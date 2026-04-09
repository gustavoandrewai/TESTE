import { NewsletterStatus, RunStatus, RunType } from "@prisma/client";
import { MockAIProvider } from "@/lib/ai/mock-provider";
import { OpenAIProvider } from "@/lib/ai/openai-provider";
import { MockEmailProvider } from "@/lib/email/mock-provider";
import { ResendProvider } from "@/lib/email/resend-provider";
import { prisma } from "@/lib/db/prisma";
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

function selectEmailProvider() {
  return process.env.EMAIL_PROVIDER === "resend" ? new ResendProvider() : new MockEmailProvider();
}

export async function runNewsletterPipeline(runType: RunType = RunType.MANUAL) {
  const startedAt = new Date();
  const runLog = await prisma.runLog.create({ data: { jobType: "newsletter_pipeline", status: RunStatus.RUNNING, startedAt } });

  try {
    const raw = await selectNewsProvider().fetchLatestNews();
    const normalized = normalizeNews(raw);
    const deduped = deduplicateNews(normalized);
    const ranked = rankNews(deduped).slice(0, 15);
    if (!ranked.length) throw new Error("Nenhuma notícia relevante encontrada.");

    const draft = await selectAIProvider().generateEditorial({ news: ranked });
    const htmlContent = renderNewsletterHtml(draft);
    const textContent = renderNewsletterText(draft);

    const newsletter = await prisma.newsletter.create({
      data: {
        subject: draft.subject,
        htmlContent,
        textContent,
        status: NewsletterStatus.GENERATED,
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
            rawData: item
          }))
        }
      }
    });

    await prisma.runLog.update({
      where: { id: runLog.id },
      data: { status: RunStatus.SUCCESS, finishedAt: new Date(), durationMs: Date.now() - startedAt.getTime() }
    });

    return newsletter;
  } catch (error) {
    await prisma.runLog.update({
      where: { id: runLog.id },
      data: {
        status: RunStatus.FAILED,
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

  const provider = selectEmailProvider();
  for (const recipient of recipients) {
    try {
      const result = await provider.send({
        to: recipient.email,
        subject: newsletter.subject,
        html: newsletter.htmlContent,
        text: newsletter.textContent
      });

      await prisma.deliveryLog.create({
        data: {
          newsletterId,
          recipientId: recipient.id,
          provider: provider.name,
          status: "sent",
          providerMessageId: result.messageId,
          sentAt: new Date()
        }
      });
    } catch (error) {
      await prisma.deliveryLog.create({
        data: {
          newsletterId,
          recipientId: recipient.id,
          provider: provider.name,
          status: "failed",
          errorMessage: error instanceof Error ? error.message : "Erro desconhecido"
        }
      });
    }
  }

  await prisma.newsletter.update({ where: { id: newsletterId }, data: { status: NewsletterStatus.SENT, sentAt: new Date() } });
}
