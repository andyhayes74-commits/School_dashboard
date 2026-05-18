@echo off
setlocal
if not exist dist\SchoolInformationDashboard.exe call build_exe.bat
if errorlevel 1 exit /b 1
where ISCC >nul 2>nul
if errorlevel 1 (
  echo Inno Setup Compiler ^(ISCC^) was not found. Install Inno Setup and add it to PATH.
  exit /b 1
)
ISCC installer\school_dashboard.iss
