"use client";

import { useState } from "react";

export function RecipientForm({ onDone }: { onDone?: () => void }) {
  const [loading, setLoading] = useState(false);

  async function onSubmit(formData: FormData) {
    setLoading(true);
    await fetch("/api/recipients", { method: "POST", body: formData });
    setLoading(false);
    onDone?.();
  }

  return (
    <form action={onSubmit} className="space-y-3">
      <input className="w-full rounded border p-2" name="name" placeholder="Nome" required />
      <input className="w-full rounded border p-2" name="email" placeholder="email@empresa.com" required type="email" />
      <input className="w-full rounded border p-2" name="tags" placeholder="macro, equities" />
      <button className="rounded bg-slate-900 px-4 py-2 text-white" disabled={loading} type="submit">
        {loading ? "Salvando..." : "Salvar"}
      </button>
    </form>
  );
}
