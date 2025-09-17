#!/bin/bash
# Script para configurar SSH keys entre Termux y Windows
# Esto elimina la necesidad de ingresar contraseña cada vez

echo "=== Configuración de SSH Keys para Termux ==="
echo "Esto permitirá conexiones SSH sin contraseña"
echo ""

# Verificar que estamos en Termux
if [ ! -d "/data/data/com.termux" ]; then
    echo "❌ Error: Este script debe ejecutarse en Termux"
    exit 1
fi

echo "📍 Ejecutándose en Termux"
echo ""

# Verificar si ya existe una key SSH
if [ -f ~/.ssh/id_rsa.pub ]; then
    echo "✅ Ya existe una clave SSH pública"
    echo "Reutilizando clave existente..."
else
    echo "🔑 Generando nueva clave SSH..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N "" -C "termux-ssh-key"
    echo "✅ Clave SSH generada"
fi

echo ""
echo "📋 Clave pública generada:"
cat ~/.ssh/id_rsa.pub

echo ""
echo "📝 PASOS PARA CONFIGURAR EN WINDOWS:"
echo "===================================="
echo ""
echo "1. Abre PowerShell como Administrador en Windows"
echo ""
echo "2. Crea el directorio .ssh si no existe:"
echo '   New-Item -ItemType Directory -Path $env:USERPROFILE\.ssh -Force'
echo ""
echo "3. Agrega la clave pública al archivo authorized_keys:"
echo '   Add-Content -Path $env:USERPROFILE\.ssh\authorized_keys -Value "'
cat ~/.ssh/id_rsa.pub
echo '"'
echo ""
echo "4. Ajusta permisos:"
echo '   icacls "$env:USERPROFILE\.ssh\authorized_keys" /inheritance:r /grant:r "$env:USERNAME:(R)"'
echo '   icacls "$env:USERPROFILE\.ssh\authorized_keys" /grant:r "NT AUTHORITY\SYSTEM:(R)"'
echo ""
echo "5. Habilita SSH en Windows (si no está habilitado):"
echo '   Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0'
echo '   Start-Service sshd'
echo '   Set-Service -Name sshd -StartupType Automatic'
echo ""
echo "6. Reinicia el servicio SSH:"
echo '   Restart-Service sshd'
echo ""
echo "🔍 PRUEBA LA CONEXIÓN:"
echo "======================"
echo ""
echo "Después de configurar, prueba desde Termux:"
echo "ssh asistente@192.168.18.47 'echo \"SSH sin contraseña funciona!\"'"
echo ""
echo "Si funciona, ya no necesitarás ingresar contraseña."
echo ""
echo "⚠️  NOTA: La contraseña actual 'Peru+123' seguirá siendo válida,"
echo "   pero con SSH keys no necesitarás escribirla cada vez."