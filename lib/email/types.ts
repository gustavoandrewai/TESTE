export type ProviderDeliveryStatus = "mock_sent" | "queued" | "sent" | "delivered" | "bounced" | "rejected" | "failed";

export type EmailPayload = {
  to: string;
  subject: string;
  html: string;
  text: string;
};

export type EmailSendResult = {
  messageId?: string;
  providerStatus: ProviderDeliveryStatus;
  providerRaw?: string;
};

export interface EmailProvider {
  name: string;
  send(payload: EmailPayload): Promise<EmailSendResult>;
}
