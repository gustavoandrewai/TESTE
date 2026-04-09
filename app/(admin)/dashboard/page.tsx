import Link from "next/link";
import { Header } from "@/components/Header";
import { RunNowButton } from "@/components/RunNowButton";
import { StatCard } from "@/components/StatCard";
import { prisma } from "@/lib/db/prisma";

function fmt(date?: Date | null) {
  if (!date) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(date);
}

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
    <div className="space-y-6">
      <Header title="Dashboard" subtitle="Monitoramento diário do pipeline e entregas" />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Última execução" value={lastRun?.status ?? "-"} />
        <StatCard label="Última geração" value={fmt(lastGenerated?.generatedAt)} />
        <StatCard label="Último envio" value={fmt(lastSent?.sentAt)} />
        <StatCard label="Destinatários ativos" value={activeRecipients} />
        <StatCard label="Newsletters geradas" value={totalNewsletters} />
        <StatCard label="Falhas recentes" value={failures} />
      </div>

      <section className="rounded-2xl border bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Ações rápidas</h3>
        <div className="flex flex-wrap gap-2">
          <RunNowButton />
          <Link className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" href="/recipients">
            Ir para destinatários
          </Link>
          <Link className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" href="/newsletters">
            Ir para histórico
          </Link>
          <Link className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" href="/settings">
            Ir para settings
          </Link>
        </div>
      </section>
    </div>
  );
}
