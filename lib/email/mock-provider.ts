import type { EmailPayload, EmailProvider, EmailSendResult } from "./types";

export class MockEmailProvider implements EmailProvider {
  name = "mock";

  async send(payload: EmailPayload): Promise<EmailSendResult> {
    console.log("Mock send", payload.to, payload.subject);
    return { messageId: `mock_${Date.now()}`, providerStatus: "mock_sent", providerRaw: "mock delivery" };
  }
}
