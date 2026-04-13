"use client";

import { useState } from "react";
import { RecipientForm } from "./RecipientForm";

export function AddRecipientModal() {
  const [open, setOpen] = useState(false);
  if (!open) {
    return (
      <button className="rounded bg-slate-900 px-3 py-2 text-sm text-white" onClick={() => setOpen(true)}>
        Adicionar email
      </button>
    );
  }
  return (
    <div className="card max-w-md">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-medium">Novo destinatário</h3>
        <button onClick={() => setOpen(false)}>✕</button>
      </div>
      <RecipientForm onDone={() => location.reload()} />
    </div>
  );
}
