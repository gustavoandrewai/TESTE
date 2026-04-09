import { runNewsletterPipeline, sendNewsletter } from "@/lib/pipeline/run-newsletter";
import { fail, ok } from "@/lib/utils/api";

export async function GET(req: Request) {
  try {
    const token = req.headers.get("x-cron-secret");
    if (token !== process.env.CRON_SECRET) return fail("unauthorized", 401);

    const newsletter = await runNewsletterPipeline("SCHEDULED");
    if (process.env.AUTO_SEND === "true") await sendNewsletter(newsletter.id);

    return ok({ id: newsletter.id, status: newsletter.status });
  } catch (error) {
    console.error("/api/cron/daily error", error);
    return fail("Falha na execução agendada", 500);
  }
}
