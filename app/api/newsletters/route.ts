import { NextResponse } from "next/server";
import { prisma } from "@/lib/db/prisma";

export async function GET() {
  const rows = await prisma.newsletter.findMany({
    include: { items: true, deliveryLogs: true },
    orderBy: { createdAt: "desc" }
  });
  return NextResponse.json(rows);
}
