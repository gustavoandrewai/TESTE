import { z } from "zod";

export const recipientSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  tags: z.array(z.string()).default([]),
  active: z.boolean().default(true)
});

export const normalizedNewsSchema = z.object({
  title: z.string(),
  sourceName: z.string(),
  sourceUrl: z.string().url(),
  publishedAt: z.date(),
  category: z.string(),
  content: z.string()
});

export const newsletterDraftSchema = z.object({
  subject: z.string(),
  executiveSummary: z.array(z.string()).min(3).max(6),
  sections: z.array(
    z.object({
      section: z.string(),
      items: z.array(
        z.object({
          title: z.string(),
          summary: z.string(),
          whyItMatters: z.string(),
          sourceName: z.string(),
          sourceUrl: z.string().url()
        })
      )
    })
  ),
  monitorToday: z.array(z.string()),
  agenda: z.array(z.string())
});
