import { LogsPanel } from "@/components/LogsPanel";
import { NewsletterPreview } from "@/components/NewsletterPreview";
import { SendNewsletterButton } from "@/components/SendNewsletterButton";
import { prisma } from "@/lib/db/prisma";

export default async function NewsletterDetails({ params }: { params: { id: string } }) {
  const newsletter = await prisma.newsletter.findUnique({
    where: { id: params.id },
    include: { items: true, deliveryLogs: true }
  });

  if (!newsletter) return <div>Newsletter não encontrada.</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">{newsletter.subject}</h1>
      <p className="text-sm text-slate-500">Status: {newsletter.status.toLowerCase()}</p>
      <div className="flex gap-2">
        <SendNewsletterButton newsletterId={newsletter.id} />
      </div>
      <NewsletterPreview html={newsletter.htmlContent} />
      <LogsPanel
        logs={newsletter.deliveryLogs.map((log) => ({
          id: log.id,
          status: log.status,
          provider: log.provider,
          providerMessageId: log.providerMessageId,
          errorMessage: log.errorMessage,
          createdAt: log.createdAt
        }))}
      />
    </div>
  );
}
