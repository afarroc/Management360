# Proyecto de Gestión de Eventos y Tareas

Este proyecto es una aplicación web diseñada para gestionar eventos, tareas y otras funcionalidades complementarias. Su objetivo es ofrecer una solución práctica y eficiente para la organización y administración de datos, con un enfoque en la productividad y la colaboración.

## Resumen del Proyecto

- **Objetivo**: Proveer herramientas para la gestión de eventos, tareas y otras funcionalidades que optimicen procesos y mejoren la toma de decisiones.
- **Tecnologías Clave**: Django, Django REST Framework, Redis, WebSockets, HTML, CSS, JavaScript.
- **Impacto**: Facilita la organización de información, mejora la colaboración y permite un análisis más eficiente de datos.

## Funcionalidades Principales

### Gestión de Eventos
- **Descripción**: Permite crear, editar y visualizar eventos con atributos como título, descripción, estado, lugar, categoría, precio y capacidad máxima.
- **Utilidad**:
  - Facilita la planificación y seguimiento de eventos.
  - Proporciona una estructura clara para la gestión de datos relacionados con eventos.

### Método Zettelkasten
- **Descripción**: Organización de información mediante tarjetas interconectadas, inspirado en el sistema de Niklas Luhmann.
- **Utilidad**:
  - Ayuda a relacionar información para un mejor contexto.
  - Mejora la organización de datos complejos.

### Gestor de Tareas
- **Descripción**: Creación y administración de tareas con opciones para marcar como importantes o completadas.
- **Utilidad**:
  - Permite priorizar actividades y realizar un seguimiento efectivo de las tareas pendientes.


## ¿Qué puedes hacer con Management360?

Management360 es una plataforma modular y escalable que integra múltiples aplicaciones para la gestión eficiente de eventos, tareas, usuarios y recursos. Está pensada para organizaciones, equipos de trabajo, profesionales y entusiastas que buscan optimizar procesos y centralizar información.

### Módulos principales y sus capacidades

- **Gestión de Usuarios (Accounts):**
   - Registro, inicio/cierre de sesión y recuperación de contraseña.
   - Perfiles personalizados y dashboard para cada usuario.
   - Seguridad robusta y control de acceso.
   - Ejemplo de rutas: `/signup/`, `/login/`, `/logout/`.

- **API RESTful:**
   - Endpoints para integración con sistemas externos y apps móviles.
   - Acceso y manipulación de datos de usuarios, eventos, tareas, etc.
   - Ejemplo: `/api/v1/users/`, `/api/v1/events/`.

- **Chat Inteligente:**
   - Mensajería en tiempo real con WebSockets.
   - Asistentes virtuales con IA, historial, exportación y búsqueda avanzada.
   - Moderación automática y subida de archivos.
   - Ejemplo: `/chat/`, `/chat/assistant/`.

- **Currículum Vitae (CV):**
   - Generación, edición y visualización de CVs profesionales.
   - Gestión de experiencias, educación, habilidades y documentos.
   - Vistas públicas y privadas, carga de archivos.
   - Ejemplo: `/cv/`, `/cv/upload/`, `/cv/view/<user_id>/`.

- **Gestión de Eventos y Proyectos:**
   - Creación y seguimiento de eventos, proyectos y tareas.
   - Paneles de control, asignación de responsables, estados personalizados y estadísticas.
   - Ejemplo: `/events/`, `/projects/`, `/tasks/`.

- **Indicadores Clave (KPIs):**
   - Dashboards interactivos, carga y análisis de datos vía CSV.
   - Validación, normalización y exportación de resultados.
   - Ejemplo: `/kpis/upload/`, `/kpis/dashboard/`.

- **Notas y Recordatorios (Memento):**
   - Sistema de notas rápidas, recordatorios y cálculo de fechas clave (memento mori).
   - Visualización de vida restante en días, semanas, meses y años.
   - Ejemplo: `/memento/`, `/memento/config/`.

- **Panel Administrativo:**
   - Gestión centralizada de usuarios, permisos y tokens de conexión.
   - Integración con Redis y autenticación avanzada.
   - Ejemplo: `/panel/`, `/panel/login/`.

- **Generador de Contraseñas (PassGen):**
   - Creación de contraseñas seguras y personalizables.
   - Patrones avanzados, aplicación de acentos y ayuda interactiva.
   - Ejemplo: `/passgen/`, `/passgen/help/`.

- **Salas Virtuales (Rooms):**
   - Creación y navegación entre salas, interacción con objetos, comentarios y evaluaciones.
   - Formularios de entrada/salida, portales y estadísticas.
   - Ejemplo: `/rooms/`, `/rooms/create/`, `/rooms/<id>/`.

- **Herramientas y utilidades (Tools):**
   - Carga y conversión de datos, calculadoras, utilidades para portapapeles y fechas.
   - Panel de administración de cargas y conversión de formatos.
   - Ejemplo: `/tools/upload/`, `/tools/convert/`.

- **Gestión de Archivos Multimedia (Media):**
   - Carga, almacenamiento y descarga eficiente de archivos multimedia.
   - Integración con otras apps para centralizar recursos.
   - Ejemplo: `/media/upload/`, `/media/list/`.

---

Esta estructura facilita la comprensión rápida de las capacidades del sistema, tanto para usuarios finales como para colegas desarrolladores, reclutadores o cualquier persona interesada en el alcance del proyecto.

## Habilidades Técnicas Demostradas
- **Backend**: Desarrollo de APIs RESTful y manejo de bases de datos relacionales.
- **Frontend**: Creación de interfaces de usuario accesibles y funcionales.
- **DevOps**: Configuración de entornos virtuales y despliegue de aplicaciones.
- **Seguridad**: Implementación de autenticación segura y generación de contraseñas robustas.

## Cómo Ejecutar el Proyecto

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

## Por Qué Elegir Este Proyecto
Este proyecto ofrece herramientas prácticas y funcionales que pueden ser aplicadas en diversos contextos, desde la gestión de eventos hasta la optimización de tareas. Su diseño modular y enfoque en la productividad lo convierten en una solución versátil y eficiente.

## Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
