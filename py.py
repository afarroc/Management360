import os

def eliminar_lineas(ruta, texto):
    for raiz, dirs, archivos in os.walk(ruta):
        for archivo in archivos:
            ruta_archivo = os.path.join(raiz, archivo)
            with open(ruta_archivo, 'r') as f:
                lineas = f.readlines()
            with open(ruta_archivo, 'w') as f:
                for linea in lineas:
                    if texto not in linea:
                        f.write(linea)

# Reemplaza '/ruta/a/tu/proyecto' con la ruta real a tu directorio de proyecto
eliminar_lineas('/pyvirtual/', '//# sourceMappingURL=skin.js.map')
