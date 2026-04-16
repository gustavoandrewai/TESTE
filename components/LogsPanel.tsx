export function LogsPanel({
  logs
}: {
  logs: Array<{ id: string; status: string; provider: string; providerMessageId?: string | null; errorMessage: string | null; createdAt: Date }>;
}) {
  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <h3 className="mb-3 font-medium">Logs de entrega</h3>
      <ul className="space-y-2 text-sm">
        {logs.map((log) => (
          <li className="rounded border p-2" key={log.id}>
            <p>
              <strong>Status:</strong> {log.status} | <strong>Provider:</strong> {log.provider}
            </p>
            {log.providerMessageId ? <p><strong>Message ID:</strong> {log.providerMessageId}</p> : null}
            <p><strong>Erro:</strong> {log.errorMessage ?? "-"}</p>
            <p className="text-xs text-slate-500">{log.createdAt.toISOString()}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
