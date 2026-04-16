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

const draftItemSchema = z.object({
  title: z.string(),
  summary: z.string(),
  whyItMatters: z.string(),
  sourceName: z.string(),
  sourceUrl: z.string().url()
});

export const newsletterDraftSchema = z.object({
  subject: z.string().min(10),
  preheader: z.string().optional(),
  executiveSummary: z.array(z.string().min(20)).min(3).max(6),
  sections: z.array(
    z.object({
      section: z.string(),
      items: z.array(draftItemSchema).min(1)
    })
  ).min(3),
  marketSnapshot: z.array(
    z.object({
      asset: z.string(),
      price: z.string(),
      change: z.string(),
      period: z.string()
    })
  ).optional(),
  tables: z.array(
    z.object({
      title: z.string(),
      columns: z.array(z.string()).min(2),
      rows: z.array(z.array(z.string()).min(2)).min(1)
    })
  ).optional(),
  charts: z.array(
    z.object({
      title: z.string(),
      imageUrl: z.string(),
      caption: z.string()
    })
  ).optional(),
  images: z.array(
    z.object({
      title: z.string(),
      url: z.string(),
      caption: z.string().optional()
    })
  ).optional(),
  monitorToday: z.array(z.string().min(10)).min(3),
  agenda: z.array(z.string().min(5)).min(3),
  conclusion: z.string().optional(),
  sources: z.array(z.string().url()).optional()
});
