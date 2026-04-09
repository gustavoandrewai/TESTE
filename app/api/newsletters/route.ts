import { prisma } from "@/lib/db/prisma";
import { fail, ok } from "@/lib/utils/api";

export async function GET() {
  try {
    const rows = await prisma.newsletter.findMany({
      include: { items: true, deliveryLogs: true },
      orderBy: { createdAt: "desc" }
    });
    return ok({ newsletters: rows });
  } catch (error) {
    console.error("/api/newsletters error", error);
    return fail("Falha ao listar newsletters", 500);
  }
}
