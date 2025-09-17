@echo off
REM Script para sincronizar archivos media desde Windows a Termux
REM Uso: sync_media_to_termux.bat

echo === Sincronización de archivos Media a Termux ===
echo Asegúrate de tener SSH configurado en Termux
echo.

REM Configuración - MODIFICAR SEGÚN TU CONFIGURACIÓN
set TERMUX_IP=192.168.18.46
set TERMUX_PORT=8022
set TERMUX_USER=u0_a211
set TERMUX_PATH=/data/data/com.termux/files/home/projects/Management360/media

REM Verificar que existe el directorio media local
if not exist ".\media" (
    echo ❌ Error: Directorio .\media no encontrado
    pause
    exit /b 1
)

echo 📁 Directorio media local encontrado
echo 🔍 Verificando archivos a sincronizar...
echo.

REM Mostrar archivos que se van a sincronizar
echo Archivos a sincronizar:
for /r ".\media" %%f in (*) do echo   📄 %%~nxf
echo.

REM Contar archivos y calcular tamaño
for /f %%A in ('dir /b /s /a-d ".\media\*" 2^>nul ^| find /c /v ""') do set FILE_COUNT=%%A
for /f %%A in ('powershell -command "Get-ChildItem -Path '.\media' -Recurse -File | Measure-Object -Property Length -Sum | Select-Object -ExpandProperty Sum"') do set TOTAL_SIZE=%%A

echo 📊 Resumen:
echo   - %FILE_COUNT% archivos
echo   - %TOTAL_SIZE% bytes de tamaño total
echo.

REM Confirmar antes de proceder
set /p CONFIRM="¿Continuar con la sincronización? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo ❌ Sincronización cancelada
    pause
    exit /b 1
)

echo.
echo 🚀 Iniciando sincronización...

REM Verificar si scp está disponible
where scp >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Error: SCP no encontrado. Instala OpenSSH for Windows
    echo    https://docs.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse
    pause
    exit /b 1
)

REM Crear directorio remoto si no existe
echo 📁 Creando directorio remoto...
ssh -p %TERMUX_PORT% %TERMUX_USER%@%TERMUX_IP% "mkdir -p %TERMUX_PATH%"

REM Sincronizar archivos usando scp
echo 📤 Sincronizando archivos...
scp -P %TERMUX_PORT% -r .\media\* %TERMUX_USER%@%TERMUX_IP%:%TERMUX_PATH%/

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✅ Sincronización completada exitosamente!
    echo.
    echo 🔍 Verificando archivos en Termux...
    ssh -p %TERMUX_PORT% %TERMUX_USER%@%TERMUX_IP% "ls -la %TERMUX_PATH%"

    echo.
    echo 📋 Instrucciones para verificar:
    echo 1. En Termux: cd /data/data/com.termux/files/home/projects/Management360
    echo 2. Ejecutar: python media_server.py
    echo 3. Probar: curl http://192.168.18.46:8000/
    echo 4. Deberías ver: courses/, profile_pics/
) else (
    echo.
    echo ❌ Error durante la sincronización
)

echo.
pause