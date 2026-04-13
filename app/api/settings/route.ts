import { prisma } from "@/lib/db/prisma";
import { getEmailRuntimeConfig } from "@/lib/email/mode";
import { fail, ok } from "@/lib/utils/api";

export async function GET() {
  try {
    const rows = await prisma.appSetting.findMany({ orderBy: { key: "asc" } });
    const emailStatus = await getEmailRuntimeConfig();
    return ok({ settings: rows, emailStatus });
  } catch (error) {
    console.error("/api/settings GET error", error);
    return fail("Falha ao carregar configurações", 500);
  }
}

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as Record<string, string>;
    const entries = Object.entries(body || {});
    if (!entries.length) return fail("Nenhuma configuração enviada", 400);

    await Promise.all(
      entries.map(([key, value]) =>
        prisma.appSetting.upsert({ where: { key }, update: { value: String(value) }, create: { key, value: String(value) } })
      )
    );

    const status = await getEmailRuntimeConfig();
    await prisma.appSetting.upsert({
      where: { key: "EMAIL_PROVIDER_STATUS" },
      update: { value: status.validForLive ? "valid" : `invalid: ${status.reasons.join("; ")}` },
      create: { key: "EMAIL_PROVIDER_STATUS", value: status.validForLive ? "valid" : `invalid: ${status.reasons.join("; ")}` }
    });

    return ok({ message: "Configurações salvas", emailStatus: status });
  } catch (error) {
    console.error("/api/settings POST error", error);
    return fail("Falha ao salvar configurações", 500);
  }
}
