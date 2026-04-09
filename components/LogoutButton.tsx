"use client";

export function LogoutButton() {
  return (
    <button
      className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
      onClick={async () => {
        await fetch("/api/auth/logout", { method: "POST" });
        window.location.href = "/login";
      }}
    >
      Sair
    </button>
  );
}
