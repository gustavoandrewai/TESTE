"use client";

import { useState } from "react";

export function RunNowButton() {
  const [running, setRunning] = useState(false);
  return (
    <button
      className="rounded bg-blue-600 px-3 py-2 text-white"
      disabled={running}
      onClick={async () => {
        setRunning(true);
        const res = await fetch("/api/newsletters/run", { method: "POST" });
        const json = await res.json();
        setRunning(false);
        if (json?.id) window.location.href = `/newsletters/${json.id}`;
      }}
    >
      {running ? "Rodando..." : "Rodar agora"}
    </button>
  );
}
