import { SettingsForm } from "@/components/SettingsForm";
import { prisma } from "@/lib/db/prisma";

const defaultSettings = [
  ["send_time", "08:00"],
  ["sender_name", "Global Market Morning Brief"],
  ["sender_email", "brief@local"],
  ["send_mode", "mock"],
  ["test_group", "internal"],
  ["max_items", "15"],
  ["enabled_sources", "mock"],
  ["preview_mode", "true"]
] as const;

export default async function SettingsPage() {
  for (const [key, value] of defaultSettings) {
    await prisma.appSetting.upsert({ where: { key }, update: {}, create: { key, value } });
  }

  const settings = await prisma.appSetting.findMany({ orderBy: { key: "asc" } });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Configurações</h1>
      <div className="rounded-xl border bg-white p-4 shadow-sm">
        <SettingsForm initialSettings={settings} />
      </div>
    </div>
  );
}
