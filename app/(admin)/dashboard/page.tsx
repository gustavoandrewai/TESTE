import Link from "next/link";
import { Header } from "@/components/Header";
import { RunNowButton } from "@/components/RunNowButton";
import { StatCard } from "@/components/StatCard";
import { prisma } from "@/lib/db/prisma";

export default async function DashboardPage() {
  const [lastRun, lastGenerated, lastSent, activeRecipients, totalNewsletters, failures] = await Promise.all([
    prisma.runLog.findFirst({ orderBy: { createdAt: "desc" } }),
    prisma.newsletter.findFirst({ orderBy: { generatedAt: "desc" } }),
    prisma.newsletter.findFirst({ where: { sentAt: { not: null } }, orderBy: { sentAt: "desc" } }),
    prisma.recipient.count({ where: { active: true } }),
    prisma.newsletter.count(),
    prisma.runLog.count({ where: { status: "FAILED" } })
  ]);

  return (
    <div>
      <Header title="Dashboard" subtitle="Visão operacional da newsletter diária" />
      <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-3">
        <StatCard label="Última execução" value={lastRun?.status ?? "-"} />
        <StatCard label="Última geração" value={lastGenerated?.generatedAt.toISOString() ?? "-"} />
        <StatCard label="Último envio" value={lastSent?.sentAt?.toISOString() ?? "-"} />
        <StatCard label="Destinatários ativos" value={activeRecipients} />
        <StatCard label="Newsletters geradas" value={totalNewsletters} />
        <StatCard label="Falhas recentes" value={failures} />
      </div>
      <div className="mb-6 flex gap-2">
        <RunNowButton />
        <Link className="rounded bg-slate-200 px-3 py-2" href="/recipients">Ir para destinatários</Link>
        <Link className="rounded bg-slate-200 px-3 py-2" href="/newsletters">Ir para histórico</Link>
      </div>
    </div>
  );
}
