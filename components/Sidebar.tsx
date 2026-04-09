import Link from "next/link";

const links = [
  ["Dashboard", "/dashboard"],
  ["Destinatários", "/recipients"],
  ["Newsletters", "/newsletters"],
  ["Configurações", "/settings"]
];

export function Sidebar() {
  return (
    <aside className="w-64 border-r border-slate-200 bg-white px-4 py-6">
      <h1 className="mb-1 text-lg font-semibold">Global Market</h1>
      <p className="mb-6 text-xs text-slate-500">Morning Brief Admin</p>
      <nav className="space-y-1">
        {links.map(([label, href]) => (
          <Link className="block rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100" href={href} key={href}>
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
