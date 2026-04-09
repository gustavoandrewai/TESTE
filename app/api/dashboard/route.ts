import { prisma } from "@/lib/db/prisma";
import { fail, ok } from "@/lib/utils/api";

export async function GET() {
  try {
    const [lastRun, lastGenerated, lastSent, activeRecipients, totalNewsletters, failures] = await Promise.all([
      prisma.runLog.findFirst({ orderBy: { createdAt: "desc" } }),
      prisma.newsletter.findFirst({ orderBy: { generatedAt: "desc" } }),
      prisma.newsletter.findFirst({ where: { sentAt: { not: null } }, orderBy: { sentAt: "desc" } }),
      prisma.recipient.count({ where: { active: true } }),
      prisma.newsletter.count(),
      prisma.runLog.count({ where: { status: "FAILED" } })
    ]);

    return ok({ lastRun, lastGenerated, lastSent, activeRecipients, totalNewsletters, failures });
  } catch (error) {
    console.error("/api/dashboard error", error);
    return fail("Falha ao carregar dashboard", 500);
  }
}
