@echo off
echo Building DictaFlow.exe ...
pip install pyinstaller >nul 2>&1
pyinstaller --noconfirm --onefile --windowed --name DictaFlow ^
    --add-data "dashboard/templates;dashboard/templates" ^
    --add-data "assets;assets" ^
    --hidden-import=flask ^
    app.py
echo.
echo Done: dist\DictaFlow.exe
pause
