@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0"
set "RUNTIME_DIR=%ROOT_DIR%runtime\node"
set "NODE_EXE=%RUNTIME_DIR%\node.exe"
set "NODE_VERSION=v20.19.0"
set "NODE_ZIP=node-%NODE_VERSION%-win-x64.zip"
set "NODE_FOLDER=node-%NODE_VERSION%-win-x64"
set "DOWNLOAD_URL=https://nodejs.org/dist/%NODE_VERSION%/%NODE_ZIP%"
set "TMP_ZIP=%ROOT_DIR%runtime\%NODE_ZIP%"
set "TMP_EXTRACT=%ROOT_DIR%runtime\node_extract"

if exist "%NODE_EXE%" (
  echo [OK] Node portatil ja existe em runtime\node
  exit /b 0
)

echo [INFO] Baixando Node portatil: %DOWNLOAD_URL%
if not exist "%ROOT_DIR%runtime" mkdir "%ROOT_DIR%runtime"

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%TMP_ZIP%' -UseBasicParsing } catch { Write-Error $_; exit 1 }"
if errorlevel 1 (
  echo [ERRO] Falha ao baixar Node portatil.
  exit /b 1
)

echo [INFO] Extraindo pacote...
if exist "%TMP_EXTRACT%" rmdir /s /q "%TMP_EXTRACT%"
mkdir "%TMP_EXTRACT%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Expand-Archive -Path '%TMP_ZIP%' -DestinationPath '%TMP_EXTRACT%' -Force } catch { Write-Error $_; exit 1 }"
if errorlevel 1 (
  echo [ERRO] Falha ao extrair Node portatil.
  exit /b 1
)

if not exist "%TMP_EXTRACT%\%NODE_FOLDER%\node.exe" (
  echo [ERRO] node.exe nao encontrado no zip extraido.
  exit /b 1
)

if exist "%RUNTIME_DIR%" rmdir /s /q "%RUNTIME_DIR%"
mkdir "%RUNTIME_DIR%"
xcopy /e /i /y "%TMP_EXTRACT%\%NODE_FOLDER%\*" "%RUNTIME_DIR%\" >nul
if errorlevel 1 (
  echo [ERRO] Falha ao copiar Node para runtime\node.
  exit /b 1
)

del /q "%TMP_ZIP%" >nul 2>&1
rmdir /s /q "%TMP_EXTRACT%" >nul 2>&1

echo [INFO] Configurando npm local...
"%RUNTIME_DIR%\npm.cmd" config set cache "%ROOT_DIR%runtime\npm-cache" --global >nul 2>&1
"%RUNTIME_DIR%\npm.cmd" config set prefix "%ROOT_DIR%runtime\npm-global" --global >nul 2>&1

echo [OK] Node portatil configurado com sucesso.
exit /b 0
