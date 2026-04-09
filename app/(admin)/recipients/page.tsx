import { AddRecipientModal } from "@/components/AddRecipientModal";
import { DataTable } from "@/components/DataTable";
import { Header } from "@/components/Header";
import { prisma } from "@/lib/db/prisma";

export default async function RecipientsPage({ searchParams }: { searchParams: { q?: string } }) {
  const q = searchParams.q || "";

  const recipients = await prisma.recipient.findMany({
    where: {
      OR: [{ name: { contains: q } }, { email: { contains: q } }]
    },
    orderBy: { createdAt: "desc" }
  });

  return (
    <div className="space-y-4">
      <Header title="Destinatários" subtitle="Cadastro e gestão da base de envio" />
      <form className="card flex gap-2" method="get">
        <input className="flex-1 rounded border p-2" defaultValue={q} name="q" placeholder="Buscar nome ou email" />
        <button className="rounded bg-slate-900 px-3 py-2 text-white" type="submit">
          Buscar
        </button>
      </form>

      <AddRecipientModal />

      <DataTable headers={["Nome", "Email", "Status", "Tags"]}>
        {recipients.map((r) => {
          const tags = JSON.parse(r.tags || "[]") as string[];
          return (
            <tr className="border-b" key={r.id}>
              <td className="px-3 py-2">{r.name}</td>
              <td className="px-3 py-2">{r.email}</td>
              <td className="px-3 py-2">{r.active ? "Ativo" : "Inativo"}</td>
              <td className="px-3 py-2">{tags.join(", ")}</td>
            </tr>
          );
        })}
      </DataTable>
    </div>
  );
}
