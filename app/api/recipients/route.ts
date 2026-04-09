import { NextResponse } from "next/server";
import { prisma } from "@/lib/db/prisma";
import { recipientSchema } from "@/lib/validation/schemas";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const q = searchParams.get("q") || "";

  const recipients = await prisma.recipient.findMany({
    where: {
      OR: [{ name: { contains: q } }, { email: { contains: q } }]
    },
    orderBy: { createdAt: "desc" }
  });

  return NextResponse.json(
    recipients.map((item) => ({
      ...item,
      tags: JSON.parse(item.tags || "[]")
    }))
  );
}

export async function POST(req: Request) {
  const formData = await req.formData();
  const parsed = recipientSchema.parse({
    name: String(formData.get("name") || "").trim(),
    email: String(formData.get("email") || "").trim().toLowerCase(),
    tags: String(formData.get("tags") || "")
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
    active: true
  });

  const created = await prisma.recipient.create({
    data: {
      name: parsed.name,
      email: parsed.email,
      tags: JSON.stringify(parsed.tags),
      active: parsed.active
    }
  });

  return NextResponse.json({ ...created, tags: parsed.tags });
}
