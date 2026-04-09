# Global Market Morning Brief

Projeto Next.js 14 + Prisma + SQLite com execução local em Windows corporativo usando Node portátil dentro do repositório.

## Rodar local (sem Node global)

1. Clique em `start.bat`.
2. O script executa automaticamente:
   - `setup.bat` (se `runtime/node` não existir)
   - cria `.env` local (se não existir)
   - `npm install`
   - `prisma generate`
   - `prisma db push`
   - `npm run dev`
3. Abra `http://localhost:3000/login`.

Credenciais padrão:
- `admin@example.com`
- `admin123`

## Ambiente local (SQLite)

Use `.env` com:

```env
DATABASE_URL="file:./dev.db"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="admin123"
AI_PROVIDER="mock"
NEWS_PROVIDER="mock"
EMAIL_PROVIDER="mock"
APP_BASE_URL="http://localhost:3000"
```

## Fluxo funcional

- Login em `/login`
- Dashboard em `/dashboard`
- Recipients em `/recipients` (listar/criar/editar/ativar/desativar/excluir)
- Settings em `/settings`
- Geração manual via botão **Rodar agora**
- Preview e envio manual mock em `/newsletters/[id]`

## Modo mock

- News provider: mock
- AI provider: mock
- Email provider: mock

Sem chave externa, o fluxo ponta-a-ponta local continua funcionando.
