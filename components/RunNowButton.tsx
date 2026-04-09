"use client";

import { useState } from "react";

export function RunNowButton() {
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleRun() {
    setRunning(true);
    setMessage(null);

    try {
      const res = await fetch("/api/newsletters/run", { method: "POST" });
      const bodyText = await res.text();
      const data = bodyText ? JSON.parse(bodyText) : { ok: false, error: "Resposta vazia do servidor" };

      if (!res.ok || !data.ok) {
        setMessage(data.error || "Não foi possível gerar a newsletter.");
        return;
      }

      if (!data.id) {
        setMessage("Newsletter gerada sem ID de retorno.");
        return;
      }

      window.location.href = `/newsletters/${data.id}`;
    } catch {
      setMessage("Falha ao processar geração. Tente novamente.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <button className="rounded-lg bg-blue-600 px-4 py-2 text-white" disabled={running} onClick={handleRun}>
        {running ? "Rodando..." : "Rodar agora"}
      </button>
      {message ? <p className="mt-2 text-sm text-red-600">{message}</p> : null}
    </div>
  );
}
