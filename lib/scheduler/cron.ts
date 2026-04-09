import { RunType } from "@prisma/client";
import { prisma } from "@/lib/db/prisma";
import { runNewsletterPipeline } from "@/lib/pipeline/run-newsletter";

export async function runScheduledJobWithLock() {
  const lockKey = "scheduler_lock";
  const existing = await prisma.appSetting.findUnique({ where: { key: lockKey } });
  if (existing?.value === "running") return { skipped: true };

  await prisma.appSetting.upsert({ where: { key: lockKey }, update: { value: "running" }, create: { key: lockKey, value: "running" } });

  try {
    const n = await runNewsletterPipeline(RunType.SCHEDULED);
    return { skipped: false, newsletterId: n.id };
  } finally {
    await prisma.appSetting.update({ where: { key: lockKey }, data: { value: "idle" } });
  }
}
