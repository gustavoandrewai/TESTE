import type { EmailPayload, EmailProvider, EmailSendResult } from "./types";

export class SendGridProvider implements EmailProvider {
  name = "sendgrid";

  async send(payload: EmailPayload): Promise<EmailSendResult> {
    const apiKey = process.env.SENDGRID_API_KEY;
    if (!apiKey) throw new Error("SENDGRID_API_KEY ausente para envio live.");

    const fromEmail = (process.env.EMAIL_FROM || "").replace(/.*<|>.*/g, "") || "";
    if (!fromEmail.includes("@")) throw new Error("EMAIL_FROM inválido para envio com SendGrid");

    const response = await fetch("https://api.sendgrid.com/v3/mail/send", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        personalizations: [{ to: [{ email: payload.to }] }],
        from: { email: fromEmail },
        subject: payload.subject,
        content: [
          { type: "text/plain", value: payload.text },
          { type: "text/html", value: payload.html }
        ]
      })
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`SendGrid falhou: ${response.status} ${text}`);
    }

    return {
      messageId: response.headers.get("x-message-id") || undefined,
      providerStatus: "queued",
      providerRaw: `status=${response.status}`
    };
  }
}
