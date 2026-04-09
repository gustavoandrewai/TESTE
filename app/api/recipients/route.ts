import { NextResponse } from "next/server";
import { prisma } from "@/lib/db/prisma";
import { recipientSchema } from "@/lib/validation/schemas";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const q = searchParams.get("q") || "";
  const recipients = await prisma.recipient.findMany({
    where: {
      OR: [{ name: { contains: q, mode: "insensitive" } }, { email: { contains: q, mode: "insensitive" } }]
    },
    orderBy: { createdAt: "desc" }
  });
  return NextResponse.json(recipients);
}

export async function POST(req: Request) {
  const formData = await req.formData();
  const parsed = recipientSchema.parse({
    name: String(formData.get("name")),
    email: String(formData.get("email")),
    tags: String(formData.get("tags") || "")
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
    active: true
  });

  const created = await prisma.recipient.create({ data: parsed });
  return NextResponse.json(created);
}
