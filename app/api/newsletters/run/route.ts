import { NextResponse } from "next/server";
import { RunType } from "@prisma/client";
import { runNewsletterPipeline } from "@/lib/pipeline/run-newsletter";

export async function POST() {
  const newsletter = await runNewsletterPipeline(RunType.MANUAL);
  return NextResponse.json({ id: newsletter.id });
}
