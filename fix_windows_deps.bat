@echo off
echo Fixing Windows dependencies...
echo.

echo Uninstalling problematic python-magic...
pip uninstall python-magic -y

echo Installing Windows-compatible python-magic-bin...
pip install python-magic-bin>=0.4.14

echo.
echo Dependencies fixed! You can now run:
echo   start_local.bat
echo   or
echo   python run_local.py
echo.
pause 