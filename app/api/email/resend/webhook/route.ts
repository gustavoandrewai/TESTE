import { prisma } from "@/lib/db/prisma";
import { fail, ok } from "@/lib/utils/api";

const allowed = new Set(["delivered", "bounced", "rejected", "sent", "queued"]);

export async function POST(req: Request) {
  try {
    const payload = (await req.json()) as {
      data?: { email_id?: string; id?: string; status?: string; reason?: string; error?: string };
      type?: string;
    };

    const messageId = payload?.data?.email_id || payload?.data?.id;
    const status = (payload?.data?.status || payload?.type || "").toLowerCase();
    const reason = payload?.data?.reason || payload?.data?.error || null;

    if (!messageId) return fail("messageId ausente", 400);
    if (!allowed.has(status)) return fail("status inválido", 400);

    await prisma.deliveryLog.updateMany({
      where: { providerMessageId: messageId },
      data: {
        status,
        errorMessage: reason
      }
    });

    return ok({ message: "Webhook processado", messageId, status });
  } catch (error) {
    console.error("/api/email/resend/webhook error", error);
    return fail("Falha ao processar webhook", 500);
  }
}
