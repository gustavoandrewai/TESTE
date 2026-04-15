"use client";

import { useState } from "react";

export function SendNewsletterButton({ newsletterId }: { newsletterId: string }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function onSend() {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`/api/newsletters/send?id=${newsletterId}`, { method: "POST" });
      const text = await res.text();
      const data = text ? JSON.parse(text) : { ok: false, error: "Resposta vazia" };
      if (!res.ok || !data.ok) {
        setMessage(data.error || "Falha ao enviar newsletter");
        return;
      }

      const summary = data.summary;
      const label = summary.mode === "live" ? "Envio real" : "Simulação";
      const breakdown = summary.deliveryStatus
        ? `queued=${summary.deliveryStatus.queued || 0}, delivered=${summary.deliveryStatus.delivered || 0}, bounced=${summary.deliveryStatus.bounced || 0}, rejected=${summary.deliveryStatus.rejected || 0}`
        : "";
      setMessage(`${label}: ${summary.sent} confirmados, ${summary.failed} falhas. Provider: ${summary.provider}. ${breakdown}`);
      setTimeout(() => window.location.reload(), 1000);
    } catch {
      setMessage("Erro inesperado no envio");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button className="rounded-lg bg-emerald-600 px-3 py-2 text-white" disabled={loading} onClick={onSend}>
        {loading ? "Enviando..." : "Enviar agora"}
      </button>
      {message ? <p className="mt-2 text-sm text-slate-600">{message}</p> : null}
    </div>
  );
}
