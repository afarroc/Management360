#!/usr/bin/env bash
# setup_termux.sh - Configuración inicial de MariaDB en Termux

echo "=== Instalando MariaDB en Termux ==="
pkg update -y
pkg upgrade -y
pkg install mariadb -y

echo "=== Inicializando base de datos ==="
mysql_install_db

echo "=== Iniciando servidor MariaDB ==="
mysqld_safe &

sleep 3

echo "=== Configurando seguridad ==="
mysql_secure_installation <<EOF
y
maria
maria
y
y
y
y
EOF

echo "=== Creando base de datos ==="
mysql -u root -pmaria <<EOF
CREATE DATABASE management360 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'm360user'@'localhost' IDENTIFIED BY 'm360pass';
GRANT ALL PRIVILEGES ON management360.* TO 'm360user'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "=== MariaDB configurado ==="
echo "Usuario: m360user"
echo "Password: m360pass"
echo "Base de datos: management360"
echo "Puerto: 3306"