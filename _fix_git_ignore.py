import re

with open('.gitignore', 'r') as f:
    content = f.read()

# Bloque viejo a reemplazar
old_block = re.search(
    r'# =+\s*# Migraciones.*?# =+\s*# Media',
    content,
    re.DOTALL
)

if not old_block:
    print("ERROR: bloque no encontrado")
    print("Primeras 20 chars del contenido:")
    print(repr(content[1400:1700]))
    exit(1)

new_block = """# ================================
# Migraciones (INCLUIDAS en el repositorio)
# ================================
# IMPORTANTE: regla general primero, excepciones despues
*/migrations/*
!accounts/migrations/
!accounts/migrations/**
!analyst/migrations/
!analyst/migrations/**
!bitacora/migrations/
!bitacora/migrations/**
!board/migrations/
!board/migrations/**
!bots/migrations/
!bots/migrations/**
!campaigns/migrations/
!campaigns/migrations/**
!chat/migrations/
!chat/migrations/**
!core/migrations/
!core/migrations/**
!courses/migrations/
!courses/migrations/**
!cv/migrations/
!cv/migrations/**
!events/migrations/
!events/migrations/**
!help/migrations/
!help/migrations/**
!kpis/migrations/
!kpis/migrations/**
!memento/migrations/
!memento/migrations/**
!rooms/migrations/
!rooms/migrations/**
!sim/migrations/
!sim/migrations/**

# ================================
# Media"""

new_content = content[:old_block.start()] + new_block + content[old_block.end():]

with open('.gitignore', 'w') as f:
    f.write(new_content)

print("OK - .gitignore actualizado")
print("\nVerificacion:")
import subprocess
result = subprocess.run(['grep', '-n', 'migr', '.gitignore'], capture_output=True, text=True)
print(result.stdout)
