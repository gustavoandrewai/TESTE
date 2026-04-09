import { prisma } from "@/lib/db/prisma";
import { fail, ok } from "@/lib/utils/api";

export async function GET() {
  try {
    const rows = await prisma.appSetting.findMany({ orderBy: { key: "asc" } });
    return ok({ settings: rows });
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

    return ok({ message: "Configurações salvas" });
  } catch (error) {
    console.error("/api/settings POST error", error);
    return fail("Falha ao salvar configurações", 500);
  }
}
