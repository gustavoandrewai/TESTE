"use client";

import { FormEvent, useMemo, useState } from "react";

type Setting = { id: string; key: string; value: string };

export function SettingsForm({ initialSettings }: { initialSettings: Setting[] }) {
  const [values, setValues] = useState<Record<string, string>>(
    Object.fromEntries(initialSettings.map((s) => [s.key, s.value]))
  );
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const sortedKeys = useMemo(() => Object.keys(values).sort(), [values]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values)
      });

      const json = await res.json().catch(() => ({ ok: false, error: "Resposta inválida" }));
      if (!res.ok || !json.ok) {
        setMessage(json.error || "Falha ao salvar configurações");
        return;
      }

      const extra = json.emailStatus ? ` | envio=${json.emailStatus.sendMode}, provider=${json.emailStatus.provider}, live=${json.emailStatus.validForLive ? "ok" : "inválido"}` : "";
      setMessage(`Configurações salvas com sucesso.${extra}`);
    } catch {
      setMessage("Erro de conexão ao salvar configurações.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      {sortedKeys.map((key) => (
        <div key={key}>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{key}</label>
          <input
            className="w-full rounded-lg border border-slate-300 p-2"
            onChange={(e) => setValues((prev) => ({ ...prev, [key]: e.target.value }))}
            value={values[key] || ""}
          />
        </div>
      ))}

      {message ? <p className="text-sm text-slate-600">{message}</p> : null}

      <button className="rounded-lg bg-slate-900 px-4 py-2 text-white" disabled={loading} type="submit">
        {loading ? "Salvando..." : "Salvar configurações"}
      </button>
    </form>
  );
}
