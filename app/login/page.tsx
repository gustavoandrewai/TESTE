export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <form action="/api/auth/login" className="card w-full max-w-sm space-y-3" method="post">
        <h1 className="text-xl font-semibold">Login Admin</h1>
        <input className="w-full rounded border p-2" name="email" placeholder="Email" required type="email" />
        <input className="w-full rounded border p-2" name="password" placeholder="Senha" required type="password" />
        <button className="w-full rounded bg-slate-900 p-2 text-white" type="submit">
          Entrar
        </button>
      </form>
    </div>
  );
}
