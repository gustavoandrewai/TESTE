"use client";

import { FormEvent, useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json().catch(() => ({ ok: false, error: "Resposta inválida do servidor" }));
      if (!res.ok || !data.ok) {
        setError(data.error || "Não foi possível autenticar");
        return;
      }

      window.location.href = "/dashboard";
    } catch {
      setError("Erro de conexão no login.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-slate-100 to-slate-200 p-6">
      <form className="w-full max-w-sm rounded-2xl border bg-white p-6 shadow-lg" onSubmit={onSubmit}>
        <h1 className="mb-1 text-xl font-semibold">Global Market Morning Brief</h1>
        <p className="mb-4 text-sm text-slate-500">Acesso administrativo</p>

        <div className="space-y-3">
          <input
            className="w-full rounded-lg border p-2"
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            type="email"
            value={email}
          />
          <input
            className="w-full rounded-lg border p-2"
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Senha"
            type="password"
            value={password}
          />
        </div>

        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

        <button className="mt-4 w-full rounded-lg bg-slate-900 p-2 text-white" disabled={loading} type="submit">
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
