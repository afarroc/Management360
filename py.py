import os

def buscar_texto(ruta, texto):
    for raiz, dirs, archivos in os.walk(ruta):
        for archivo in archivos:
            ruta_archivo = os.path.join(raiz, archivo)
            with open(ruta_archivo, 'r') as f:
                lineas = f.readlines()
                for num_linea, linea in enumerate(lineas, start=1):
                    if texto in linea:
                        print(f'Archivo: {ruta_archivo}, Línea: {num_linea}, Texto: {linea.strip()}')

# Reemplaza '/ruta/a/tu/proyecto' con la ruta real a tu directorio de proyecto
buscar_texto('/static', 'js.map')
