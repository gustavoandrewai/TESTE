"use client";

import { useState } from "react";

type Recipient = {
  id: string;
  name: string;
  email: string;
  active: boolean;
  tags: string[];
};

export function RecipientsManager({ initialItems }: { initialItems: Recipient[] }) {
  const [items, setItems] = useState(initialItems);
  const [message, setMessage] = useState<string | null>(null);

  async function patchRecipient(id: string, payload: Partial<Recipient>) {
    const res = await fetch("/api/recipients", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, ...payload })
    });
    const data = await res.json().catch(() => ({ ok: false, error: "Resposta inválida" }));
    if (!res.ok || !data.ok) throw new Error(data.error || "Falha na atualização");
    return data.recipient as Recipient;
  }

  async function removeRecipient(id: string) {
    const res = await fetch(`/api/recipients?id=${id}`, { method: "DELETE" });
    const data = await res.json().catch(() => ({ ok: false, error: "Resposta inválida" }));
    if (!res.ok || !data.ok) throw new Error(data.error || "Falha ao excluir");
  }

  return (
    <div className="space-y-3">
      {message ? <p className="text-sm text-slate-600">{message}</p> : null}
      <div className="rounded-xl border bg-white p-2 shadow-sm">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="p-2 text-left">Nome</th>
              <th className="p-2 text-left">Email</th>
              <th className="p-2 text-left">Status</th>
              <th className="p-2 text-left">Tags</th>
              <th className="p-2 text-left">Ações</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr className="border-b" key={item.id}>
                <td className="p-2">{item.name}</td>
                <td className="p-2">{item.email}</td>
                <td className="p-2">{item.active ? "Ativo" : "Inativo"}</td>
                <td className="p-2">{item.tags.join(", ")}</td>
                <td className="p-2">
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="rounded border px-2 py-1"
                      onClick={async () => {
                        try {
                          const updated = await patchRecipient(item.id, { active: !item.active });
                          setItems((prev) => prev.map((row) => (row.id === item.id ? updated : row)));
                        } catch (e) {
                          setMessage((e as Error).message);
                        }
                      }}
                    >
                      {item.active ? "Desativar" : "Ativar"}
                    </button>

                    <button
                      className="rounded border px-2 py-1"
                      onClick={async () => {
                        const name = prompt("Novo nome", item.name);
                        if (!name) return;
                        try {
                          const updated = await patchRecipient(item.id, { name });
                          setItems((prev) => prev.map((row) => (row.id === item.id ? updated : row)));
                        } catch (e) {
                          setMessage((e as Error).message);
                        }
                      }}
                    >
                      Editar
                    </button>

                    <button
                      className="rounded border border-red-300 px-2 py-1 text-red-700"
                      onClick={async () => {
                        if (!confirm("Excluir destinatário?")) return;
                        try {
                          await removeRecipient(item.id);
                          setItems((prev) => prev.filter((row) => row.id !== item.id));
                        } catch (e) {
                          setMessage((e as Error).message);
                        }
                      }}
                    >
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
