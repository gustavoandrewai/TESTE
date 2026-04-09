import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { buildSessionToken, hashPassword, verifyPassword } from "@/lib/auth/session";
import { prisma } from "@/lib/db/prisma";

async function ensureDefaultAdmin() {
  const defaultEmail = process.env.ADMIN_EMAIL || "admin@local";
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
  await ensureDefaultAdmin();

  const formData = await req.formData();
  const email = String(formData.get("email") || "").trim().toLowerCase();
  const password = String(formData.get("password") || "");

  const user = await prisma.user.findUnique({ where: { email } });
  if (!user || !verifyPassword(password, user.passwordHash)) {
    return NextResponse.redirect(new URL("/login?error=1", req.url));
  }

  cookies().set("admin_session", buildSessionToken(email), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/"
  });

  return NextResponse.redirect(new URL("/dashboard", req.url));
}
