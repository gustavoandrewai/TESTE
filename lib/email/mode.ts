import { prisma } from "@/lib/db/prisma";

export type EmailRuntimeConfig = {
  provider: "mock" | "resend" | "sendgrid";
  sendMode: "mock" | "live";
  previewMode: boolean;
  from: string;
  validForLive: boolean;
  reasons: string[];
};

function parseBoolean(value: string | undefined, fallback = false) {
  if (value === undefined) return fallback;
  return ["1", "true", "yes", "on"].includes(value.toLowerCase());
}

export async function getEmailRuntimeConfig(): Promise<EmailRuntimeConfig> {
  const settings = await prisma.appSetting.findMany({ where: { key: { in: ["SEND_MODE", "PREVIEW_MODE", "EMAIL_PROVIDER", "SENDER_EMAIL"] } } });
  const map = Object.fromEntries(settings.map((s) => [s.key, s.value]));

  const provider = (map.EMAIL_PROVIDER || process.env.EMAIL_PROVIDER || "mock").toLowerCase() as EmailRuntimeConfig["provider"];
  const sendMode = (map.SEND_MODE || process.env.SEND_MODE || "mock").toLowerCase() as EmailRuntimeConfig["sendMode"];
  const previewMode = parseBoolean(map.PREVIEW_MODE || process.env.PREVIEW_MODE, true);
  const from = map.SENDER_EMAIL || process.env.EMAIL_FROM || "";

  const reasons: string[] = [];
  if (sendMode === "live") {
    if (previewMode) reasons.push("PREVIEW_MODE=true bloqueia envio real");
    if (!from || !from.includes("@")) reasons.push("EMAIL_FROM/SENDER_EMAIL inválido");
    if (provider === "resend" && !process.env.RESEND_API_KEY) reasons.push("RESEND_API_KEY ausente");
    if (provider === "sendgrid" && !process.env.SENDGRID_API_KEY) reasons.push("SENDGRID_API_KEY ausente");
  }

  return {
    provider: ["mock", "resend", "sendgrid"].includes(provider) ? provider : "mock",
    sendMode: sendMode === "live" ? "live" : "mock",
    previewMode,
    from,
    validForLive: reasons.length === 0,
    reasons
  };
}
