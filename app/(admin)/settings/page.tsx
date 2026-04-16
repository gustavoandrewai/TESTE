import { SettingsForm } from "@/components/SettingsForm";
import { prisma } from "@/lib/db/prisma";
import { getEmailRuntimeConfig } from "@/lib/email/mode";

const defaultSettings = [
  ["ENABLED_SOURCES", "rss,finviz"],
  ["MAX_ITEMS", "15"],
  ["MIN_NEWS_ITEMS", "10"],
  ["FINVIZ_WEIGHT", "8"],
  ["RSS_WEIGHT", "4"],
  ["PREVIEW_MODE", "true"],
  ["SEND_MODE", "mock"],
  ["SEND_TIME", "08:00"],
  ["SENDER_EMAIL", "brief@local"],
  ["SENDER_NAME", "Global Market Morning Brief"],
  ["TEST_GROUP", "internal"],
  ["BRAND_NAME", "Global Market Morning Brief"],
  ["NEWSLETTER_TITLE", "Global Market Morning Brief"],
  ["ENABLE_CHARTS", "true"],
  ["ENABLE_IMAGES", "true"],
  ["ENABLE_MARKET_SNAPSHOT", "true"],
  ["EXECUTIVE_SUMMARY_MIN_ITEMS", "3"],
  ["MAX_SECTION_ITEMS", "4"],
  ["EMAIL_PROVIDER", "mock"],
  ["EMAIL_PROVIDER_STATUS", "pending"],
  ["DEFAULT_LOCALE", "pt-BR"],
  ["DEFAULT_TIMEZONE", "America/Sao_Paulo"]
] as const;

export default async function SettingsPage() {
  await prisma.$transaction(
    defaultSettings.map(([key, value]) => prisma.appSetting.upsert({ where: { key }, update: {}, create: { key, value } }))
  );

  const settings = await prisma.appSetting.findMany({ orderBy: { key: "asc" } });
  const mailStatus = await getEmailRuntimeConfig();
  const realEnabled = !mailStatus.previewMode && mailStatus.sendMode === "live" && mailStatus.provider !== "mock" && mailStatus.validForLive;
  const blockReason = mailStatus.previewMode
    ? "PREVIEW_MODE=true"
    : mailStatus.sendMode !== "live"
      ? "SEND_MODE não está live"
      : mailStatus.provider === "mock"
        ? "EMAIL_PROVIDER=mock"
        : !mailStatus.validForLive
          ? mailStatus.reasons.join(" | ")
          : "";

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Configurações</h1>
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
        <p><strong>Modo:</strong> {mailStatus.sendMode.toUpperCase()} {mailStatus.previewMode ? "(PREVIEW ativo)" : ""}</p>
        <p><strong>Provider:</strong> {mailStatus.provider}</p>
        <p><strong>Status live:</strong> {realEnabled ? "habilitado" : "bloqueado"}</p>
        <p><strong>Envio real ativo:</strong> {realEnabled ? "sim" : "não"}</p>
        {!realEnabled ? <p><strong>Motivo de bloqueio:</strong> {blockReason}</p> : null}
      </div>
      <div className="rounded-xl border bg-white p-4 shadow-sm">
        <SettingsForm initialSettings={settings} />
      </div>
    </div>
  );
}
