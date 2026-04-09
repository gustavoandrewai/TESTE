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

  await prisma.appSetting.upsert({
    where: { key: "send_time" },
    update: { value: "08:00" },
    create: { key: "send_time", value: "08:00" }
  });
}

main().finally(async () => {
  await prisma.$disconnect();
});
