import { NextResponse } from "next/server";
import { sendNewsletter } from "@/lib/pipeline/run-newsletter";

export async function POST(req: Request) {
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "id obrigatório" }, { status: 400 });
  await sendNewsletter(id);
  return NextResponse.json({ ok: true });
}
