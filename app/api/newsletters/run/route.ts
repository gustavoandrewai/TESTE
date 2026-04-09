import { runNewsletterPipeline } from "@/lib/pipeline/run-newsletter";
import { fail, ok } from "@/lib/utils/api";

export async function POST() {
  try {
    const newsletter = await runNewsletterPipeline("MANUAL");
    return ok({ id: newsletter.id, status: newsletter.status });
  } catch (error) {
    console.error("/api/newsletters/run error", error);
    const details = error instanceof Error ? error.stack : error;
    return fail(error instanceof Error ? error.message : "Falha ao gerar newsletter", 500, details);
  }
}
