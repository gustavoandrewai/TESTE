import { Resend } from "resend";
import type { EmailPayload, EmailProvider } from "./types";

export class ResendProvider implements EmailProvider {
  name = "resend";
  private client = new Resend(process.env.RESEND_API_KEY);

  async send(payload: EmailPayload): Promise<{ messageId?: string }> {
    const result = await this.client.emails.send({
      from: process.env.EMAIL_FROM || "brief@example.com",
      to: payload.to,
      subject: payload.subject,
      html: payload.html,
      text: payload.text
    });
    return { messageId: result.data?.id };
  }
}
