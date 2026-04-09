import Link from "next/link";

const links = [
  ["Dashboard", "/dashboard"],
  ["Destinatários", "/recipients"],
  ["Newsletters", "/newsletters"],
  ["Configurações", "/settings"]
];

export function Sidebar() {
  return (
    <aside className="w-64 border-r border-slate-200 bg-white p-4">
      <h1 className="mb-6 text-lg font-semibold">Global Market Morning Brief</h1>
      <nav className="space-y-2">
        {links.map(([label, href]) => (
          <Link className="block rounded-md px-3 py-2 hover:bg-slate-100" key={href} href={href}>
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
