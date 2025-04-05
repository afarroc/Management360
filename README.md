# Proyecto de Gestión de Eventos y Tareas

Este proyecto es una aplicación web diseñada para gestionar eventos, tareas y otras funcionalidades complementarias. Forma parte de mi portafolio como analista de datos.

## Características

1. **Gestión de Eventos**:
   - Creación, edición y visualización de eventos.
   - Cada evento incluye título, descripción, estado, lugar (venue), categoría, precio de entrada y capacidad máxima de asistentes.

2. **Método Zettelkasten**:
   - Inspirado en el sistema de Niklas Luhmann.
   - Organización de información mediante tarjetas interconectadas.
   - Relación entre eventos para un mejor contexto.

3. **Gestor de Tareas**:
   - Creación y administración de tareas.
   - Cada tarea incluye título, descripción, fecha de creación y puede marcarse como importante o completada.

4. **Otras Aplicaciones**:
   - **Chat**: Sistema de mensajería en tiempo real para usuarios registrados. Permite interacción con un asistente virtual basado en IA, con soporte para historial de mensajes y respuestas en tiempo real.
   - **CV**: Generador de currículums personalizados basado en plantillas.
   - **KPIs**: Herramienta para definir y monitorear indicadores clave de desempeño.
   - **Memento**: Sistema de notas rápidas y recordatorios.
   - **PassGen**: Generador de contraseñas seguras con opciones personalizables.
   - **Rooms**: Gestión de salas virtuales para reuniones o eventos.
   - **Tools**: Conjunto de herramientas útiles como calculadoras, convertidores, etc.

## Modelos Principales

- **Status**: Representa los estados posibles de un evento (por ejemplo, "pendiente", "en curso", "finalizado").
- **Project**: Define los proyectos a los que pertenecen las tareas.
- **Task**: Modelo para tareas individuales con atributos como título, descripción, importancia, fecha de creación y estado.
- **EventState**: Registra los estados por los que pasa cada evento, con fechas de inicio y finalización.
- **EventHistory**: Guarda las ediciones realizadas en los campos de un evento.
- **Event**: Modelo principal para los eventos, con atributos como anfitrión, capacidad máxima, precio de entrada y asistentes registrados.

## Tecnologías Utilizadas

- **Backend**: Django y Django REST Framework.
- **Frontend**: HTML, CSS, y JavaScript.
- **Base de Datos**: SQLite (puede configurarse para PostgreSQL o MySQL).
- **Servidor Web**: Daphne para soporte de WebSockets.
- **Otros**: Redis para manejo de tareas en tiempo real.

## Instalación y Configuración

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/Management360.git
   cd Management360
   ```

2. **Configurar el entorno virtual**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar la base de datos**:
   - Edita el archivo `settings.py` para configurar la base de datos según tus necesidades.

5. **Ejecutar migraciones**:
   ```bash
   python manage.py migrate
   ```

6. **Iniciar el servidor local**:
   ```bash
   python manage.py runserver
   ```

7. **Acceder a la aplicación**:
   - Abre tu navegador y ve a `http://127.0.0.1:8000`.

8. **Configurar el sistema de chat**:
   - Asegúrate de que el archivo `ollama_api.py` esté configurado correctamente para interactuar con la API de generación de respuestas.
   - Configura Redis si planeas usarlo para manejar tareas en tiempo real.

## Contribución

Si deseas contribuir a este proyecto, por favor sigue estos pasos:
1. Haz un fork del repositorio.
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz un commit (`git commit -m "Añadir nueva funcionalidad"`).
4. Envía un pull request.

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
