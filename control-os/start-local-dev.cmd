@echo off
setlocal
cd /d "%~dp0"

if not exist "node_modules" (
  echo node_modules is missing.
  echo Run "npm install" first, then double-click this launcher again.
  pause
  exit /b 1
)

start "Control OS Local Dev" cmd /k "cd /d ""%~dp0"" && npm run dev:all"
exit /b 0
