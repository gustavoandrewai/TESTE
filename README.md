# Global Market Morning Brief

Newsletter premium de mercados globais em Next.js 14 + Prisma (SQLite local), com modos `mock` e `live` para envio real.

## Start local (Windows sem Node global)
1. Execute `start.bat`.
2. Script faz:
   - setup de Node portátil (`runtime/node`)
   - `.env` automático
   - `npm install`
   - `prisma generate`
   - `prisma db push`
   - `npm run dev`
3. Acesse `http://localhost:3000/login`.

## Variáveis de ambiente
```env
DATABASE_URL="file:./dev.db"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="admin123"
AI_PROVIDER="mock"        # mock | openai
NEWS_PROVIDER="mock"      # mock | rss
EMAIL_PROVIDER="mock"     # mock | resend | sendgrid
SEND_MODE="mock"          # mock | live
PREVIEW_MODE="true"       # true bloqueia envio real
EMAIL_FROM="Global Market Morning Brief <brief@local>"
RESEND_API_KEY=""
SENDGRID_API_KEY=""
OPENAI_API_KEY=""
```

## Envio real de email
Para live real:
1. `SEND_MODE=live`
2. `PREVIEW_MODE=false`
3. `EMAIL_PROVIDER=resend` (ou `sendgrid`)
4. Configurar API key (`RESEND_API_KEY` ou `SENDGRID_API_KEY`)
5. Configurar `EMAIL_FROM` válido

Se houver configuração inválida, o envio retorna erro amigável e logs por destinatário.

## Estrutura editorial (premium)
A newsletter gerada inclui:
- Top Takeaways executivos
- Macro e Bancos Centrais
- Mercados Globais
- Política e Geopolítica
- Commodities/Moedas/Rates
- Market Snapshot
- Charts mock embutidos (data URI SVG)
- Tabelas de performance
- Agenda do dia
- Conclusão editorial

## O que fica mockado no modo local
- News feed mock
- AI mock (opcional trocar para OpenAI)
- Email mock (se `SEND_MODE=mock` ou `PREVIEW_MODE=true`)
- Charts com dados mock


## Webhook de status (Resend)
Configure o webhook do Resend para apontar para `POST /api/email/resend/webhook`.
Assim os DeliveryLogs são atualizados com `delivered`, `bounced`, `rejected`, `sent` ou `queued`.
