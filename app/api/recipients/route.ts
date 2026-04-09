import { prisma } from "@/lib/db/prisma";
import { fail, ok } from "@/lib/utils/api";
import { recipientSchema } from "@/lib/validation/schemas";

function parseTags(value: string) {
  try {
    return JSON.parse(value || "[]") as string[];
  } catch {
    return [];
  }
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const q = searchParams.get("q") || "";

    const recipients = await prisma.recipient.findMany({
      where: {
        OR: [{ name: { contains: q } }, { email: { contains: q } }]
      },
      orderBy: { createdAt: "desc" }
    });

    return ok({ recipients: recipients.map((item) => ({ ...item, tags: parseTags(item.tags) })) });
  } catch (error) {
    console.error("/api/recipients GET error", error);
    return fail("Falha ao listar destinatários", 500);
  }
}

export async function POST(req: Request) {
  try {
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

    return ok({ recipient: { ...created, tags: parsed.tags } }, 201);
  } catch (error) {
    console.error("/api/recipients POST error", error);
    return fail("Falha ao criar destinatário", 500);
  }
}

export async function PATCH(req: Request) {
  try {
    const body = (await req.json()) as {
      id?: string;
      name?: string;
      email?: string;
      tags?: string[];
      active?: boolean;
    };

    if (!body.id) return fail("id obrigatório", 400);

    const updated = await prisma.recipient.update({
      where: { id: body.id },
      data: {
        ...(body.name ? { name: body.name.trim() } : {}),
        ...(body.email ? { email: body.email.trim().toLowerCase() } : {}),
        ...(typeof body.active === "boolean" ? { active: body.active } : {}),
        ...(body.tags ? { tags: JSON.stringify(body.tags) } : {})
      }
    });

    return ok({ recipient: { ...updated, tags: parseTags(updated.tags) } });
  } catch (error) {
    console.error("/api/recipients PATCH error", error);
    return fail("Falha ao atualizar destinatário", 500);
  }
}

export async function DELETE(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");
    if (!id) return fail("id obrigatório", 400);

    await prisma.recipient.delete({ where: { id } });
    return ok({ message: "Destinatário excluído" });
  } catch (error) {
    console.error("/api/recipients DELETE error", error);
    return fail("Falha ao excluir destinatário", 500);
  }
}
