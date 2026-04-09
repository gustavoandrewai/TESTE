import { NextResponse } from "next/server";
import { runNewsletterPipeline } from "@/lib/pipeline/run-newsletter";

export async function POST() {
  const newsletter = await runNewsletterPipeline("MANUAL");
  return NextResponse.json({ id: newsletter.id });
}
