import { NextResponse } from "next/server";
import { prisma } from "@/lib/db/prisma";

export async function GET() {
  const rows = await prisma.appSetting.findMany({ orderBy: { key: "asc" } });
  return NextResponse.json(rows);
}

export async function POST(req: Request) {
  const body = (await req.json()) as Record<string, string>;
  const updates = Object.entries(body).map(([key, value]) =>
    prisma.appSetting.upsert({ where: { key }, update: { value }, create: { key, value } })
  );
  await Promise.all(updates);
  return NextResponse.json({ ok: true });
}
