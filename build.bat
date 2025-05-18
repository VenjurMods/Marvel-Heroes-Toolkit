@echo off
cd /d "%~dp0"

REM Clean previous build artifacts
rmdir /s /q build
rmdir /s /q dist
del /q marvel_heroes_gui.spec
del /q marvel_heroes_gui.exe

REM Build with PyInstaller
pyinstaller ^
  --name "marvel_heroes_gui" ^
  --onefile ^
  --windowed ^
  --icon=marvel_toolkit.ico ^
  --add-data "marvel_toolkit.ico;." ^
  marvel_heroes_gui.py

echo.
echo ✅ Build complete!
echo 🔍 Check output: %CD%\dist\marvel_heroes_gui.exe
pause
