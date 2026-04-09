import { NextResponse } from "next/server";
import { prisma } from "@/lib/db/prisma";

export async function GET() {
  const [lastRun, lastGenerated, lastSent, activeRecipients, totalNewsletters, failures] = await Promise.all([
    prisma.runLog.findFirst({ orderBy: { createdAt: "desc" } }),
    prisma.newsletter.findFirst({ orderBy: { generatedAt: "desc" } }),
    prisma.newsletter.findFirst({ where: { sentAt: { not: null } }, orderBy: { sentAt: "desc" } }),
    prisma.recipient.count({ where: { active: true } }),
    prisma.newsletter.count(),
    prisma.runLog.count({ where: { status: "FAILED" } })
  ]);

  return NextResponse.json({ lastRun, lastGenerated, lastSent, activeRecipients, totalNewsletters, failures });
}
