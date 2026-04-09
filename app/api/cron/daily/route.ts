import { NextResponse } from "next/server";
import { RunType } from "@prisma/client";
import { runNewsletterPipeline, sendNewsletter } from "@/lib/pipeline/run-newsletter";

export async function GET(req: Request) {
  const token = req.headers.get("x-cron-secret");
  if (token !== process.env.CRON_SECRET) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const newsletter = await runNewsletterPipeline(RunType.SCHEDULED);
  if (process.env.AUTO_SEND === "true") {
    await sendNewsletter(newsletter.id);
  }

  return NextResponse.json({ ok: true, id: newsletter.id });
}
