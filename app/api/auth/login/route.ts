import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { buildSessionToken, verifyPassword } from "@/lib/auth/session";
import { prisma } from "@/lib/db/prisma";

export async function POST(req: Request) {
  const formData = await req.formData();
  const email = String(formData.get("email") || "");
  const password = String(formData.get("password") || "");

  const user = await prisma.user.findUnique({ where: { email } });
  if (!user || !verifyPassword(password, user.passwordHash)) {
    return NextResponse.redirect(new URL("/login?error=1", req.url));
  }

  cookies().set("admin_session", buildSessionToken(email), { httpOnly: true, secure: true, sameSite: "lax", path: "/" });
  return NextResponse.redirect(new URL("/dashboard", req.url));
}
