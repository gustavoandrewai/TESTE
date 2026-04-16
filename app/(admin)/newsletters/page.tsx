import Link from "next/link";
import { DataTable } from "@/components/DataTable";
import { Header } from "@/components/Header";
import { StatusBadge } from "@/components/StatusBadge";
import { prisma } from "@/lib/db/prisma";

export default async function NewslettersPage() {
  const rows = await prisma.newsletter.findMany({ include: { items: true, deliveryLogs: true }, orderBy: { createdAt: "desc" } });

  return (
    <div className="space-y-4">
      <Header title="Histórico de newsletters" />
      <DataTable headers={["Data", "Assunto", "Status", "Execução", "Itens", "Entregas", "Detalhes"]}>
        {rows.map((n) => (
          <tr className="border-b" key={n.id}>
            <td className="px-3 py-2">{n.generatedAt.toISOString()}</td>
            <td className="px-3 py-2">{n.subject}</td>
            <td className="px-3 py-2"><StatusBadge status={n.status.toLowerCase()} /></td>
            <td className="px-3 py-2">{n.runType.toLowerCase()}</td>
            <td className="px-3 py-2">{n.items.length}</td>
            <td className="px-3 py-2">{n.deliveryLogs.length}</td>
            <td className="px-3 py-2"><Link className="text-blue-600" href={`/newsletters/${n.id}`}>Abrir</Link></td>
          </tr>
        ))}
      </DataTable>
    </div>
  );
}
