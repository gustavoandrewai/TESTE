import { AddRecipientModal } from "@/components/AddRecipientModal";
import { Header } from "@/components/Header";
import { RecipientsManager } from "@/components/RecipientsManager";
import { prisma } from "@/lib/db/prisma";

export default async function RecipientsPage({ searchParams }: { searchParams: { q?: string } }) {
  const q = searchParams.q || "";

  const recipients = await prisma.recipient.findMany({
    where: {
      OR: [{ name: { contains: q } }, { email: { contains: q } }]
    },
    orderBy: { createdAt: "desc" }
  });

  const parsed = recipients.map((r) => ({ ...r, tags: JSON.parse(r.tags || "[]") as string[] }));

  return (
    <div className="space-y-4">
      <Header title="Destinatários" subtitle="Cadastro e gestão da base de envio" />
      <form className="rounded-xl border bg-white p-3 shadow-sm" method="get">
        <div className="flex gap-2">
          <input className="flex-1 rounded-lg border p-2" defaultValue={q} name="q" placeholder="Buscar nome ou email" />
          <button className="rounded-lg bg-slate-900 px-3 py-2 text-white" type="submit">
            Buscar
          </button>
        </div>
      </form>
      <AddRecipientModal />
      <RecipientsManager initialItems={parsed} />
    </div>
  );
}
