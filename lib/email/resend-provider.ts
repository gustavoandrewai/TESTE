import { Resend } from "resend";
import type { EmailPayload, EmailProvider, EmailSendResult } from "./types";

export class ResendProvider implements EmailProvider {
  name = "resend";
  private client = new Resend(process.env.RESEND_API_KEY);

  async send(payload: EmailPayload): Promise<EmailSendResult> {
    const from = process.env.EMAIL_FROM || "";
    if (!from.includes("@")) throw new Error("EMAIL_FROM inválido para envio com Resend");

    const result = await this.client.emails.send({
      from,
      to: payload.to,
      subject: payload.subject,
      html: payload.html,
      text: payload.text
    });

    if (result.error) {
      throw new Error(`Resend error: ${result.error.message}`);
    }

    if (!result.data?.id) {
      throw new Error("Resend não retornou message id");
    }

    return {
      messageId: result.data.id,
      providerStatus: "queued",
      providerRaw: JSON.stringify(result.data)
    };
  }
}
