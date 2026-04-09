-- Initial schema generated for MVP
CREATE TYPE "UserRole" AS ENUM ('ADMIN');
CREATE TYPE "NewsletterStatus" AS ENUM ('DRAFT', 'GENERATED', 'SCHEDULED', 'SENT', 'FAILED');
CREATE TYPE "RunType" AS ENUM ('MANUAL', 'SCHEDULED');
CREATE TYPE "RunStatus" AS ENUM ('RUNNING', 'SUCCESS', 'FAILED');

CREATE TABLE "User" (
  "id" TEXT PRIMARY KEY,
  "email" TEXT UNIQUE NOT NULL,
  "passwordHash" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "role" "UserRole" NOT NULL DEFAULT 'ADMIN',
  "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP NOT NULL
);

CREATE TABLE "Recipient" (
  "id" TEXT PRIMARY KEY,
  "name" TEXT NOT NULL,
  "email" TEXT UNIQUE NOT NULL,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "tags" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP NOT NULL
);

CREATE TABLE "Newsletter" (
  "id" TEXT PRIMARY KEY,
  "subject" TEXT NOT NULL,
  "slug" TEXT UNIQUE,
  "htmlContent" TEXT NOT NULL,
  "textContent" TEXT NOT NULL,
  "status" "NewsletterStatus" NOT NULL DEFAULT 'DRAFT',
  "runType" "RunType" NOT NULL,
  "scheduledFor" TIMESTAMP,
  "generatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "sentAt" TIMESTAMP,
  "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP NOT NULL
);

CREATE TABLE "NewsletterItem" (
  "id" TEXT PRIMARY KEY,
  "newsletterId" TEXT NOT NULL REFERENCES "Newsletter"("id") ON DELETE CASCADE,
  "section" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "summary" TEXT NOT NULL,
  "sourceName" TEXT NOT NULL,
  "sourceUrl" TEXT NOT NULL,
  "publishedAt" TIMESTAMP NOT NULL,
  "relevanceScore" DOUBLE PRECISION NOT NULL,
  "rawData" JSONB,
  "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "DeliveryLog" (
  "id" TEXT PRIMARY KEY,
  "newsletterId" TEXT NOT NULL REFERENCES "Newsletter"("id") ON DELETE CASCADE,
  "recipientId" TEXT NOT NULL REFERENCES "Recipient"("id") ON DELETE CASCADE,
  "provider" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "providerMessageId" TEXT,
  "errorMessage" TEXT,
  "sentAt" TIMESTAMP,
  "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "RunLog" (
  "id" TEXT PRIMARY KEY,
  "jobType" TEXT NOT NULL,
  "status" "RunStatus" NOT NULL,
  "startedAt" TIMESTAMP NOT NULL,
  "finishedAt" TIMESTAMP,
  "durationMs" INTEGER,
  "errorMessage" TEXT,
  "metadata" JSONB,
  "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "AppSetting" (
  "id" TEXT PRIMARY KEY,
  "key" TEXT UNIQUE NOT NULL,
  "value" TEXT NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL
);
