@echo off
setlocal

cd /d "%~dp0"

echo =========================================
echo  Calculadora Future Value - Inicializacao
echo =========================================

:after_install
if not exist "node_modules" (
  echo [1/3] Instalando dependencias (npm install)...
  call npm install
  if errorlevel 1 goto :error
) else (
  echo [1/3] Dependencias ja encontradas em node_modules.
)

echo [2/3] Verificando build da aplicacao...
call npm run build
if errorlevel 1 goto :error

echo [3/3] Iniciando servidor Next.js em modo producao...
echo Abra no navegador: http://localhost:3000
call npm run start
if errorlevel 1 goto :error

goto :eof

:error
echo.
echo Ocorreu um erro ao iniciar a calculadora.
echo Revise as mensagens acima e tente novamente.
exit /b 1
