import { compareSync, hashSync } from "bcryptjs";

export function hashPassword(password: string) {
  return hashSync(password, 10);
}

export function verifyPassword(password: string, hash: string) {
  return compareSync(password, hash);
}

export function buildSessionToken(email: string) {
  return Buffer.from(`${email}:${process.env.CRON_SECRET || "secret"}`).toString("base64");
}
