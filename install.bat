@echo off
setlocal EnableDelayedExpansion
echo.
echo  ========================================
echo         VozClick - Instalacion
echo    Dictado por voz para Windows
echo  ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado.
    echo  Descargalo en https://www.python.org/downloads/
    echo  IMPORTANTE: Marca "Add to PATH" al instalar.
    echo.
    pause
    exit /b 1
)

:: Install dependencies
echo  [1/3] Instalando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] No se pudieron instalar las dependencias.
    pause
    exit /b 1
)
echo  [OK] Dependencias instaladas.
echo.

:: Generate icon
echo  [2/3] Generando icono...
pip install Pillow --quiet
python make_icon.py
if errorlevel 1 (
    echo  [AVISO] No se pudo generar el icono ^(no afecta al funcionamiento^).
) else (
    echo  [OK] Icono generado.
)
echo.

:: Ask for API key if no .env exists
if not exist .env (
    echo  [3/3] Configuracion inicial
    echo.
    echo  Necesitas una API key GRATUITA de Groq para la transcripcion.
    echo  Consiguela en: https://console.groq.com/keys
    echo.
    set /p GROQ_KEY="  Pega tu API key (gsk_...): "
    if not "!GROQ_KEY!"=="" (
        echo GROQ_API_KEY=!GROQ_KEY!> .env
        echo DASHBOARD_PORT=5678>> .env
        echo  [OK] API key guardada.
    ) else (
        echo GROQ_API_KEY=> .env
        echo DASHBOARD_PORT=5678>> .env
        echo  [AVISO] Sin API key. Configurala luego desde la bandeja del sistema.
    )
) else (
    echo  [3/3] Archivo .env ya existe, saltando configuracion.
)
echo.

:: Ask for desktop shortcut
set /p SHORTCUT="  Crear acceso directo en el escritorio? (S/n): "
if /i "!SHORTCUT!"=="n" goto :skip_shortcut

:: Create shortcut via VBScript
echo Set ws = CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
echo Set sc = ws.CreateShortcut(ws.SpecialFolders("Desktop") ^& "\VozClick.lnk") >> "%TEMP%\create_shortcut.vbs"
echo sc.TargetPath = "wscript.exe" >> "%TEMP%\create_shortcut.vbs"
echo sc.Arguments = "%CD%\launch.vbs" >> "%TEMP%\create_shortcut.vbs"
echo sc.WorkingDirectory = "%CD%" >> "%TEMP%\create_shortcut.vbs"
echo sc.IconLocation = "%CD%\assets\icon.ico,0" >> "%TEMP%\create_shortcut.vbs"
echo sc.Description = "VozClick - Dictado por voz" >> "%TEMP%\create_shortcut.vbs"
echo sc.Save >> "%TEMP%\create_shortcut.vbs"
cscript //nologo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"
echo  [OK] Acceso directo creado en el escritorio.

:skip_shortcut
echo.
echo  ========================================
echo      Instalacion completada!
echo.
echo   Para iniciar:
echo     - Doble clic en VozClick (escritorio)
echo     - O ejecuta: python app.py
echo.
echo   Atajos:
echo     Ctrl+Alt (mantener) = grabar
echo     Shift x2 = manos libres
echo     Dashboard: localhost:5678
echo  ========================================
echo.
pause
