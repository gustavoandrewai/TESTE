import { cookies } from "next/headers";
import { buildSessionToken, hashPassword, verifyPassword } from "@/lib/auth/session";
import { prisma } from "@/lib/db/prisma";
import { fail, ok } from "@/lib/utils/api";

type LoginPayload = { email?: string; password?: string };

async function getPayload(req: Request): Promise<LoginPayload> {
  const contentType = req.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await req.json()) as LoginPayload;
  }
  const formData = await req.formData();
  return {
    email: String(formData.get("email") || ""),
    password: String(formData.get("password") || "")
  };
}

async function ensureDefaultAdmin() {
  const defaultEmail = (process.env.ADMIN_EMAIL || "admin@example.com").toLowerCase();
  const defaultPassword = process.env.ADMIN_PASSWORD || "admin123";

  const found = await prisma.user.findUnique({ where: { email: defaultEmail } });
  if (!found) {
    await prisma.user.create({
      data: {
        email: defaultEmail,
        name: "Admin",
        passwordHash: hashPassword(defaultPassword),
        role: "ADMIN"
      }
    });
  }
}

export async function POST(req: Request) {
  try {
    await ensureDefaultAdmin();

    const payload = await getPayload(req);
    const email = String(payload.email || "")
      .trim()
      .toLowerCase();
    const password = String(payload.password || "");

    if (!email || !password) {
      return fail("Email e senha são obrigatórios", 400);
    }

    const user = await prisma.user.findUnique({ where: { email } });
    if (!user || !verifyPassword(password, user.passwordHash)) {
      return fail("Credenciais inválidas", 401);
    }

    cookies().set("admin_session", buildSessionToken(email), {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/"
    });

    return ok({ message: "Login realizado com sucesso" });
  } catch (error) {
    console.error("/api/auth/login error", error);
    return fail("Falha interna no login", 500);
  }
}
