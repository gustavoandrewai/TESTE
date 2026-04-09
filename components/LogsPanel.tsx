export function LogsPanel({ logs }: { logs: Array<{ id: string; status: string; errorMessage: string | null; createdAt: Date }> }) {
  return (
    <div className="card">
      <h3 className="mb-3 font-medium">Logs</h3>
      <ul className="space-y-2 text-sm">
        {logs.map((log) => (
          <li key={log.id}>
            <span className="font-medium">{log.status}</span> - {log.errorMessage ?? "ok"}
          </li>
        ))}
      </ul>
    </div>
  );
}
