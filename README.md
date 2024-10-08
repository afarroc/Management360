# Proyecto de Gestión de Eventos y Tareas

Este proyecto forma parte de mi portafolio como analista de datos. A continuación, se describen las características principales y los modelos utilizados en la aplicación:

## Características

1. **Gestión de Eventos**:
   - Creación, edición y visualización de eventos.
   - Cada evento tiene un título, descripción, estado, lugar (venue), categoría, precio de entrada y capacidad máxima de asistentes.

2. **Método Zettelkasten**:
   - Inspirado en el sistema de Niklas Luhmann.
   - Utiliza una estructura de tarjetas (notas) interconectadas para organizar la información.
   - Cada evento se representa como una tarjeta, y se pueden establecer relaciones entre ellos.

3. **Gestor de Tareas**:
   - Permite a los usuarios crear y administrar tareas.
   - Cada tarea tiene un título, descripción, fecha de creación y puede marcarse como importante o completada.

## Modelos

1. **Status**:
   - Representa los estados posibles de un evento (por ejemplo, "pendiente", "en curso", "finalizado").

2. **Project**:
   - Define los proyectos a los que pertenecen las tareas.

3. **Task**:
   - Modelo para las tareas individuales.
   - Incluye título, descripción, importancia, fecha de creación, estado y asignación a un usuario.

4. **EventState**:
   - Registra los estados por los que pasa cada evento, con fechas de inicio y finalización.

5. **EventHistory**:
   - Guarda las ediciones realizadas en los campos de un evento.

6. **Event**:
   - Modelo principal para los eventos.
   - Contiene título, descripción, estado, lugar, anfitrión, categoría, capacidad máxima de asistentes, precio de entrada y asistentes registrados.

## Uso

1. Clona este repositorio.
2. Configura tu entorno virtual y las dependencias necesarias.
3. Ejecuta las migraciones de la base de datos.
4. Inicia el servidor local con `python manage.py runserver`.
5. Accede a la aplicación desde tu navegador.
