# Global Market Morning Brief

MVP full-stack (Next.js + Prisma) com execução **portátil para Windows corporativo sem Node global**.

## Zero-config no Windows (sem admin)

1. Clone ou extraia o projeto.
2. Dê duplo clique em **`start.bat`**.
3. O script faz automaticamente:
   - valida/download do Node portátil em `runtime/node`
   - criação de `.env` padrão (se não existir)
   - `npm install`
   - `prisma generate`
   - `prisma migrate dev`
   - `npm run dev`
4. O navegador abre em: `http://localhost:3000/dashboard`

> Sem instalação global de Node/npm/npx.

## Scripts portáteis

- `setup.bat`: baixa e extrai Node oficial (`zip`) para `runtime/node`.
- `start.bat`: bootstrap completo + start da aplicação.

## Ambiente local padrão

`.env` automático (quando ausente):

- `DATABASE_URL="sqlite:./dev.db"`
- `DATABASE_URL_PRISMA="file:./dev.db"`
- `ADMIN_EMAIL="admin@local"`
- `ADMIN_PASSWORD="admin123"`
- demais variáveis com defaults seguros para dev.

## Banco de dados

- Prisma configurado com **SQLite** por padrão.
- Arquivo local: `dev.db` na raiz do projeto.
- Não requer PostgreSQL para rodar local.

## Stack

- Next.js App Router + TypeScript
- Prisma ORM
- Tailwind CSS
- Zod
- OpenAI Responses API (opcional, via `AI_PROVIDER=openai`)
- Resend (opcional, via `EMAIL_PROVIDER=resend`)

## Fluxos principais

- Login: `/login`
- Dashboard: `/dashboard`
- Destinatários: `/recipients`
- Histórico: `/newsletters`
- Preview: `/newsletters/[id]`
- Rodar agora: botão no dashboard (`POST /api/newsletters/run`)
- Enviar agora: página de detalhe (`POST /api/newsletters/send?id=...`)
- Agendado: `GET /api/cron/daily` com header `x-cron-secret`

## Observações

- Provider de notícias real ainda está em scaffold (`RSSNewsProvider`).
- Em ambiente sem internet corporativa, `npm install` pode falhar por política de rede; nesse caso libere acesso ao registry interno/externo.
