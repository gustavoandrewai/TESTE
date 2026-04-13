export function StatusBadge({ status }: { status: string }) {
  const color =
    status === "sent" || status === "success"
      ? "bg-emerald-100 text-emerald-700"
      : status === "failed"
        ? "bg-red-100 text-red-700"
        : "bg-amber-100 text-amber-700";
  return <span className={`rounded px-2 py-1 text-xs font-medium ${color}`}>{status}</span>;
}
