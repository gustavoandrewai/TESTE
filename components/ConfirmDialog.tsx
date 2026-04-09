"use client";

export function ConfirmDialog({ message, onConfirm }: { message: string; onConfirm: () => void }) {
  return (
    <button
      className="rounded border border-red-300 px-2 py-1 text-red-700"
      onClick={() => {
        if (confirm(message)) onConfirm();
      }}
    >
      Confirmar
    </button>
  );
}
