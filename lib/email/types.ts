export type EmailPayload = {
  to: string;
  subject: string;
  html: string;
  text: string;
};

export interface EmailProvider {
  name: string;
  send(payload: EmailPayload): Promise<{ messageId?: string }>;
}
