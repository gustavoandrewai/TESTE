# Global Market Morning Brief

MVP full-stack em Next.js + Prisma para geração, preview e envio de newsletter diária de mercados globais em português.

## Arquitetura

- **App Router** com páginas administrativas (`/dashboard`, `/recipients`, `/newsletters`, `/settings`).
- **Pipeline desacoplado** em módulos:
  - `lib/news`: ingestão, normalização, deduplicação, ranking.
  - `lib/ai`: abstração `AIProvider` com implementações `mock` e `openai`.
  - `lib/render`: renderização HTML/texto da newsletter.
  - `lib/email`: abstração `EmailProvider` com `mock` e `resend`.
  - `lib/pipeline`: orquestração ponta a ponta com persistência e logs.
  - `lib/scheduler`: lock simples para evitar concorrência.
- **Persistência** via PostgreSQL + Prisma.
- **Validação** via Zod.
- **Testes** via Vitest.

## Estrutura de pastas

```text
app/
  (admin)/
  api/
  login/
components/
lib/
  ai/
  auth/
  db/
  email/
  news/
  pipeline/
  render/
  scheduler/
  validation/
prisma/
prompts/
tests/
```

## Setup local

1. Instale dependências:
   ```bash
   npm install
   ```
2. Copie variáveis:
   ```bash
   cp .env.example .env
   ```
3. Suba PostgreSQL (ex.: Docker) e ajuste `DATABASE_URL`.
4. Gere cliente e aplique migration:
   ```bash
   npx prisma generate
   npx prisma migrate deploy
   ```
5. Seed do admin e configurações iniciais:
   ```bash
   npx tsx prisma/seed.ts
   ```
6. Rode aplicação:
   ```bash
   npm run dev
   ```

## Fluxos principais

- **Rodar agora**: botão no Dashboard chama `POST /api/newsletters/run` e abre preview.
- **Enviar agora**: em `/newsletters/[id]`, chama `POST /api/newsletters/send?id=...`.
- **Cron diário**: `GET /api/cron/daily` com header `x-cron-secret`.

## Configuração dos providers

- `AI_PROVIDER=mock|openai`
- `NEWS_PROVIDER=mock|rss`
- `EMAIL_PROVIDER=mock|resend`

## Segurança

- Rotas administrativas protegidas por cookie de sessão (`middleware.ts`).
- Login com senha hash no banco.
- Segredos apenas no backend (`.env`).

## Deploy sugerido

- **Vercel** para app Next.js.
- **PostgreSQL gerenciado** (Neon/Supabase/RDS).
- Cron via **Vercel Cron** chamando `/api/cron/daily`.

## Pontos mockados no MVP

- Provider real de notícias ainda simplificado (`RSSNewsProvider` inicial).
- Alguns testes de API são smoke tests para garantir wiring básico.

## Próximos passos recomendados

1. Adicionar edição/ativação/desativação/exclusão de destinatários na UI.
2. Expandir ingestão real (NewsAPI, GDELT, feeds financeiros múltiplos).
3. Criar observabilidade com tracing e métricas.
4. Implementar retries com backoff para envio e IA.
5. Adicionar teste de integração com banco efêmero para rotas.
