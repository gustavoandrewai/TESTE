import type { EmailPayload, EmailProvider } from "./types";

export class MockEmailProvider implements EmailProvider {
  name = "mock";

  async send(payload: EmailPayload): Promise<{ messageId?: string }> {
    console.log("Mock send", payload.to, payload.subject);
    return { messageId: `mock_${Date.now()}` };
  }
}
