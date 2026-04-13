import { hashPassword } from "@/lib/auth/session";
import { prisma } from "@/lib/db/prisma";

async function main() {
  const email = process.env.ADMIN_EMAIL || "admin@example.com";
  const password = process.env.ADMIN_PASSWORD || "admin123";

  await prisma.user.upsert({
    where: { email },
    update: {},
    create: {
      email,
      name: "Admin",
      passwordHash: hashPassword(password),
      role: "ADMIN"
    }
  });

  const defaults: Record<string, string> = {
    SEND_MODE: process.env.SEND_MODE || "mock",
    PREVIEW_MODE: process.env.PREVIEW_MODE || "true",
    EMAIL_PROVIDER: process.env.EMAIL_PROVIDER || "mock",
    EMAIL_PROVIDER_STATUS: "pending",
    MAX_ITEMS: "15",
    ENABLE_CHARTS: "true",
    ENABLE_IMAGES: "true",
    ENABLE_MARKET_SNAPSHOT: "true"
  };

  await Promise.all(
    Object.entries(defaults).map(([key, value]) =>
      prisma.appSetting.upsert({ where: { key }, update: { value }, create: { key, value } })
    )
  );
}

main().finally(async () => {
  await prisma.$disconnect();
});
