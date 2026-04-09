import { sendNewsletter } from "@/lib/pipeline/run-newsletter";
import { fail, ok } from "@/lib/utils/api";

export async function POST(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");
    if (!id) return fail("id obrigatório", 400);

    await sendNewsletter(id);
    return ok({ message: "Envio concluído" });
  } catch (error) {
    console.error("/api/newsletters/send error", error);
    return fail(error instanceof Error ? error.message : "Falha no envio", 500);
  }
}
