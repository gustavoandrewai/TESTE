"use client";

import { useState } from "react";

export function SendNewsletterButton({ newsletterId }: { newsletterId: string }) {
  const [loading, setLoading] = useState(false);
  return (
    <button
      className="rounded bg-emerald-600 px-3 py-2 text-white"
      disabled={loading}
      onClick={async () => {
        setLoading(true);
        await fetch(`/api/newsletters/send?id=${newsletterId}`, { method: "POST" });
        setLoading(false);
        window.location.reload();
      }}
    >
      {loading ? "Enviando..." : "Enviar agora"}
    </button>
  );
}
