import { prisma } from "@/lib/db/prisma";

export default async function SettingsPage() {
  const settings = await prisma.appSetting.findMany({ orderBy: { key: "asc" } });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Configurações</h1>
      <form
        action="/api/settings"
        className="card space-y-3"
        method="post"
        onSubmit={(e) => {
          e.preventDefault();
        }}
      >
        {settings.map((setting) => (
          <div key={setting.id}>
            <label className="mb-1 block text-sm font-medium">{setting.key}</label>
            <input className="w-full rounded border p-2" defaultValue={setting.value} name={setting.key} />
          </div>
        ))}
      </form>
      <p className="text-sm text-slate-500">Use endpoint /api/settings com JSON para salvar ajustes.</p>
    </div>
  );
}
