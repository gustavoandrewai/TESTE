@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0"
set "RUNTIME_DIR=%ROOT_DIR%runtime\node"
set "NODE_EXE=%RUNTIME_DIR%\node.exe"
set "NPM_CMD=%RUNTIME_DIR%\npm.cmd"
set "NPX_CMD=%RUNTIME_DIR%\npx.cmd"
set "ENV_FILE=%ROOT_DIR%.env"

if not exist "%NODE_EXE%" (
  echo [INFO] Node portatil nao encontrado. Executando setup.bat...
  call "%ROOT_DIR%setup.bat"
  if errorlevel 1 (
    echo [ERRO] setup.bat falhou. Encerrando.
    exit /b 1
  )
)

set "PATH=%RUNTIME_DIR%;%PATH%"

if not exist "%ENV_FILE%" (
  echo [INFO] Criando .env padrao...
  >"%ENV_FILE%" echo DATABASE_URL="file:./dev.db"
  >>"%ENV_FILE%" echo OPENAI_API_KEY=""
  >>"%ENV_FILE%" echo OPENAI_MODEL="gpt-4.1-mini"
  >>"%ENV_FILE%" echo AI_PROVIDER="mock"
  >>"%ENV_FILE%" echo NEWS_PROVIDER="mock"
  >>"%ENV_FILE%" echo NEWS_FEEDS=""
  >>"%ENV_FILE%" echo EMAIL_PROVIDER="mock"
  >>"%ENV_FILE%" echo SEND_MODE="mock"
  >>"%ENV_FILE%" echo PREVIEW_MODE="true"
  >>"%ENV_FILE%" echo RESEND_API_KEY=""
  >>"%ENV_FILE%" echo SENDGRID_API_KEY=""
  >>"%ENV_FILE%" echo EMAIL_FROM="Global Market Morning Brief ^<brief@local^>"
  >>"%ENV_FILE%" echo ADMIN_EMAIL="admin@example.com"
  >>"%ENV_FILE%" echo ADMIN_PASSWORD="admin123"
  >>"%ENV_FILE%" echo CRON_SECRET="local-secret"
  >>"%ENV_FILE%" echo APP_BASE_URL="http://localhost:3000"
  >>"%ENV_FILE%" echo AUTO_SEND="false"
)

echo [INFO] Instalando dependencias locais...
call "%NPM_CMD%" install
if errorlevel 1 (
  echo [ERRO] npm install falhou.
  exit /b 1
)

echo [INFO] Gerando Prisma Client...
call "%NPX_CMD%" prisma generate
if errorlevel 1 (
  echo [ERRO] prisma generate falhou.
  exit /b 1
)

echo [INFO] Aplicando schema SQLite (db push)...
call "%NPX_CMD%" prisma db push
if errorlevel 1 (
  echo [ERRO] prisma db push falhou.
  exit /b 1
)

echo [INFO] Abrindo dashboard...
start "" "http://localhost:3000/login"

echo [INFO] Iniciando servidor Next.js...
call "%NPM_CMD%" run dev
if errorlevel 1 (
  echo [ERRO] npm run dev falhou.
  exit /b 1
)

exit /b 0
