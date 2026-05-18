@echo off
setlocal
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python -m app.sample_excel
if errorlevel 1 exit /b 1
set ICON_ARG=
if exist assets\app_icon.ico set ICON_ARG=--icon assets\app_icon.ico
if not exist assets\app_icon.ico echo assets\app_icon.ico not found; building without a custom Windows icon.
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name SchoolInformationDashboard ^
  %ICON_ARG% ^
  --add-data "assets;assets" ^
  --add-data "data;data" ^
  app\main.py
if errorlevel 1 exit /b 1
echo Built dist\SchoolInformationDashboard.exe
