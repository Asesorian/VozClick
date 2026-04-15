@echo off
echo Building VozClick.exe ...
pip install pyinstaller >nul 2>&1
pyinstaller --noconfirm --onefile --windowed --name VozClick ^
    --add-data "dashboard/templates;dashboard/templates" ^
    --add-data "assets;assets" ^
    --hidden-import=flask ^
    app.py
echo.
echo Done: dist\VozClick.exe
pause
