import { cookies } from "next/headers";
import { fail, ok } from "@/lib/utils/api";

export async function POST() {
  try {
    cookies().delete("admin_session");
    return ok({ message: "Logout realizado" });
  } catch (error) {
    console.error("/api/auth/logout error", error);
    return fail("Falha ao sair", 500);
  }
}
