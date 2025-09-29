from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from help.models import (
    HelpCategory, HelpArticle, FAQ, VideoTutorial, QuickStartGuide
)
from courses.models import Course, Lesson, CourseCategory, ContentBlock
from cv.models import Curriculum
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Configura datos iniciales para el sistema de ayuda'

    def handle(self, *args, **options):
        self.stdout.write('Configurando sistema de ayuda...')

        # Crear usuario admin si no existe
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@management360.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Usuario admin creado')

        # Crear contenido de cursos de ejemplo
        self.create_sample_course_content(admin_user)

        # Crear curso completo sobre rooms
        self.create_rooms_course(admin_user)

        # Crear categorías
        self.create_categories(admin_user)

        # Crear artículos (ahora referenciando contenido real)
        self.create_articles(admin_user)

        # Crear FAQs
        self.create_faqs(admin_user)

        # Crear tutoriales en video
        self.create_video_tutorials(admin_user)

        # Crear guías de inicio rápido
        self.create_quick_start_guides(admin_user)

        self.stdout.write('Sistema de ayuda configurado exitosamente!')
        self.stdout.write('Visita /help/ para explorar el centro de ayuda')

    def create_categories(self, admin_user):
        """Crear categorías de ayuda"""
        categories_data = [
            {
                'name': 'Primeros Pasos',
                'slug': 'getting-started',
                'description': 'Todo lo que necesitas saber para comenzar con Management360',
                'icon': 'bi-rocket-takeoff-fill',
                'color': '#28a745',
                'order': 1
            },
            {
                'name': 'Habitaciones',
                'slug': 'rooms',
                'description': 'Aprende a crear, gestionar y navegar habitaciones',
                'icon': 'bi-house-door-fill',
                'color': '#007bff',
                'order': 2
            },
            {
                'name': 'Transiciones',
                'slug': 'transitions',
                'description': 'Sistema de navegación y movimiento entre habitaciones',
                'icon': 'bi-arrow-left-right',
                'color': '#6f42c1',
                'order': 3
            },
            {
                'name': 'Eventos y Tareas',
                'slug': 'events-tasks',
                'description': 'Gestión de eventos, tareas y programaciones',
                'icon': 'bi-calendar-event-fill',
                'color': '#fd7e14',
                'order': 4
            },
            {
                'name': 'Solución de Problemas',
                'slug': 'troubleshooting',
                'description': 'Soluciones a problemas comunes',
                'icon': 'bi-tools',
                'color': '#dc3545',
                'order': 5
            },
            {
                'name': 'API y Desarrollo',
                'slug': 'api-development',
                'description': 'Documentación para desarrolladores',
                'icon': 'bi-code-slash',
                'color': '#20c997',
                'order': 6
            }
        ]

        for cat_data in categories_data:
            category, created = HelpCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'[CATEGORIA] {category.name}')

    def create_articles(self, admin_user):
        """Crear artículos de ayuda - algunos referencian contenido real"""
        articles_data = [
            {
                'title': 'Bienvenido a Management360',
                'slug': 'welcome-to-management360',
                'category_slug': 'getting-started',
                'excerpt': 'Una introducción completa a la plataforma Management360',
                'content': '''
                <h2>¿Qué es Management360?</h2>
                <p>Management360 es una plataforma integral de gestión que combina habitaciones virtuales,
                eventos, tareas y un sistema de navegación único.</p>

                <h3>Características principales</h3>
                <ul>
                <li><strong>Habitaciones Virtuales:</strong> Espacios personalizables para diferentes propósitos</li>
                <li><strong>Sistema de Transiciones:</strong> Navegación inteligente entre habitaciones</li>
                <li><strong>Gestión de Eventos:</strong> Planificación y seguimiento de actividades</li>
                <li><strong>Tareas y Proyectos:</strong> Organización eficiente del trabajo</li>
                </ul>

                <h3>Primeros pasos</h3>
                <p>Para comenzar, te recomendamos:</p>
                <ol>
                <li>Crear tu primera habitación</li>
                <li>Configurar tus preferencias</li>
                <li>Explorar las habitaciones existentes</li>
                <li>Unirte a eventos de interés</li>
                </ol>
                ''',
                'is_featured': True,
                'difficulty': 'beginner',
                'referenced_course': None
            },
            {
                'title': 'Creando tu Primera Habitación',
                'slug': 'creating-your-first-room',
                'category_slug': 'rooms',
                'excerpt': 'Guía paso a paso para crear y configurar tu primera habitación',
                'content': '''
                <h2>Creando Habitaciones en Management360</h2>
                <p>Las habitaciones son el corazón de Management360. Aquí aprenderás a crear tu primera habitación.</p>

                <h3>Pasos para crear una habitación</h3>
                <ol>
                <li><strong>Accede al menú:</strong> Ve a "Rooms" en el menú principal</li>
                <li><strong>Haz clic en "Crear":</strong> Selecciona "Crear Nueva Habitación"</li>
                <li><strong>Configura los básicos:</strong> Nombre, descripción y tipo de habitación</li>
                <li><strong>Personaliza:</strong> Dimensiones, colores y propiedades físicas</li>
                <li><strong>Guarda:</strong> Tu habitación estará lista para usar</li>
                </ol>

                <h3>Tipos de habitaciones disponibles</h3>
                <ul>
                <li><strong>LOUNGE:</strong> Salas de estar y socialización</li>
                <li><strong>WORKSPACE:</strong> Espacios de trabajo colaborativo</li>
                <li><strong>MEETING:</strong> Salas de reuniones y conferencias</li>
                <li><strong>PRIVATE:</strong> Espacios personales y privados</li>
                </ul>
                ''',
                'is_featured': True,
                'difficulty': 'beginner',
                'referenced_course': None
            },
            {
                'title': 'Sistema de Transiciones Avanzado',
                'slug': 'advanced-transition-system',
                'category_slug': 'transitions',
                'excerpt': 'Entendiendo el sistema de navegación entre habitaciones',
                'content': '',  # Contenido vacío - usará el de la lección referenciada
                'difficulty': 'intermediate',
                'referenced_lesson': True  # Indicador para usar la lección de ejemplo
            },
            {
                'title': 'Componentes de Interfaz',
                'slug': 'ui-components-guide',
                'category_slug': 'api-development',
                'excerpt': 'Guía completa de componentes Bootstrap disponibles',
                'content': '',  # Contenido vacío - usará el del bloque de contenido
                'difficulty': 'intermediate',
                'referenced_content_block': True  # Indicador para usar el bloque de ejemplo
            }
        ]

        for article_data in articles_data:
            try:
                category = HelpCategory.objects.get(slug=article_data['category_slug'])

                # Preparar datos por defecto
                defaults = {
                    'title': article_data['title'],
                    'content': article_data['content'],
                    'excerpt': article_data['excerpt'],
                    'category': category,
                    'author': admin_user,
                    'is_featured': article_data.get('is_featured', False),
                    'difficulty': article_data.get('difficulty', 'beginner'),
                    'is_active': True,
                    'published_at': timezone.now()
                }

                # Asignar referencias a objetos reales si están especificadas
                if article_data.get('referenced_lesson'):
                    defaults['referenced_lesson'] = self.sample_lesson
                if article_data.get('referenced_content_block'):
                    defaults['referenced_content_block'] = self.sample_content_block
                if article_data.get('referenced_course'):
                    defaults['referenced_course'] = self.sample_course

                article, created = HelpArticle.objects.get_or_create(
                    slug=article_data['slug'],
                    defaults=defaults
                )
                if created:
                    self.stdout.write(f'[ARTICULO] {article.title}')
            except HelpCategory.DoesNotExist:
                self.stdout.write(f'[WARNING] Categoria no encontrada para articulo: {article_data["title"]}')

    def create_faqs(self, admin_user):
        """Crear preguntas frecuentes"""
        faqs_data = [
            {
                'question': '¿Cómo creo mi primera habitación?',
                'answer': '''
                <p>Para crear tu primera habitación:</p>
                <ol>
                <li>Ve al menú "Rooms" en la barra de navegación</li>
                <li>Haz clic en "Crear Nueva Habitación"</li>
                <li>Completa el formulario con nombre, descripción y tipo</li>
                <li>Personaliza las dimensiones y apariencia</li>
                <li>Guarda la habitación</li>
                </ol>
                <p>¡Tu habitación estará lista para usar inmediatamente!</p>
                ''',
                'category_slug': 'getting-started',
                'order': 1
            },
            {
                'question': '¿Qué es el sistema de energía?',
                'answer': '''
                <p>El sistema de energía es un mecanismo de gamificación que hace la navegación más estratégica:</p>
                <ul>
                <li><strong>Consumo:</strong> Algunas transiciones requieren energía</li>
                <li><strong>Recuperación:</strong> La energía se recupera automáticamente con el tiempo</li>
                <li><strong>Recompensas:</strong> Completar tareas otorga energía extra</li>
                <li><strong>Estrategia:</strong> Planifica tus movimientos para optimizar recursos</li>
                </ul>
                ''',
                'category_slug': 'transitions',
                'order': 1
            },
            {
                'question': '¿Cómo encuentro habitaciones existentes?',
                'answer': '''
                <p>Para explorar habitaciones existentes:</p>
                <ul>
                <li><strong>Lista de Rooms:</strong> Ve a "Rooms" → "Ver Todas las Habitaciones"</li>
                <li><strong>Búsqueda:</strong> Usa la barra de búsqueda en la parte superior</li>
                <li><strong>Filtros:</strong> Filtra por tipo, propietario o permisos</li>
                <li><strong>Mapa:</strong> Usa el mapa interactivo para navegación visual</li>
                </ul>
                ''',
                'category_slug': 'rooms',
                'order': 1
            }
        ]

        for faq_data in faqs_data:
            try:
                category = HelpCategory.objects.get(slug=faq_data['category_slug'])
                faq, created = FAQ.objects.get_or_create(
                    question=faq_data['question'],
                    defaults={
                        'answer': faq_data['answer'],
                        'category': category,
                        'order': faq_data.get('order', 0),
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'[FAQ] {faq.question[:50]}...')
            except HelpCategory.DoesNotExist:
                self.stdout.write(f'[WARNING] Categoria no encontrada para FAQ: {faq_data["question"][:50]}...')

    def create_video_tutorials(self, admin_user):
        """Crear tutoriales en video"""
        videos_data = [
            {
                'title': 'Introducción a Management360',
                'slug': 'introduction-to-management360',
                'description': 'Un tour completo por la plataforma y sus características principales',
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Placeholder
                'category_slug': 'getting-started',
                'difficulty': 'beginner',
                'duration': '00:05:30',
                'is_featured': True
            },
            {
                'title': 'Creando y Gestionando Habitaciones',
                'slug': 'creating-managing-rooms',
                'description': 'Aprende a crear, configurar y gestionar tus habitaciones virtuales',
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Placeholder
                'category_slug': 'rooms',
                'difficulty': 'beginner',
                'duration': '00:08:15'
            }
        ]

        for video_data in videos_data:
            try:
                category = HelpCategory.objects.get(slug=video_data['category_slug'])
                # Convertir duración de string a timedelta
                duration_str = video_data.get('duration')
                duration = None
                if duration_str:
                    # Parsear formato "HH:MM:SS" o "MM:SS"
                    parts = duration_str.split(':')
                    if len(parts) == 3:
                        duration = timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))
                    elif len(parts) == 2:
                        duration = timedelta(minutes=int(parts[0]), seconds=int(parts[1]))

                video, created = VideoTutorial.objects.get_or_create(
                    slug=video_data['slug'],
                    defaults={
                        'title': video_data['title'],
                        'description': video_data['description'],
                        'video_url': video_data['video_url'],
                        'category': category,
                        'author': admin_user,
                        'difficulty': video_data.get('difficulty', 'beginner'),
                        'duration': duration,
                        'is_featured': video_data.get('is_featured', False),
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'[VIDEO] {video.title}')
            except HelpCategory.DoesNotExist:
                self.stdout.write(f'[WARNING] Categoria no encontrada para video: {video_data["title"]}')

    def create_quick_start_guides(self, admin_user):
        """Crear guías de inicio rápido"""
        guides_data = [
            {
                'title': 'Primeros Pasos en Management360',
                'slug': 'first-steps-management360',
                'description': 'Una guía rápida para comenzar a usar la plataforma',
                'target_audience': 'new_users',
                'estimated_time': 10,
                'prerequisites': 'Cuenta de usuario activa',
                'content': '''
                <h3>Bienvenido a Management360</h3>
                <p>Esta guía te ayudará a dar tus primeros pasos en la plataforma.</p>

                <h4>1. Configura tu perfil</h4>
                <p>Ve a tu perfil y completa tu información básica.</p>

                <h4>2. Explora el lobby</h4>
                <p>El lobby es tu punto de partida. Desde aquí puedes acceder a todas las funciones.</p>

                <h4>3. Crea tu primera habitación</h4>
                <p>Las habitaciones son espacios personalizables para diferentes actividades.</p>

                <h4>4. Únete a eventos</h4>
                <p>Explora los eventos disponibles y únete a aquellos que te interesen.</p>
                ''',
                'order': 1,
                'is_featured': True
            },
            {
                'title': 'Sistema de Navegación',
                'slug': 'navigation-system',
                'description': 'Aprende a moverte eficientemente entre habitaciones',
                'target_audience': 'new_users',
                'estimated_time': 5,
                'prerequisites': 'Haber completado "Primeros Pasos"',
                'content': '''
                <h3>Navegación en Management360</h3>
                <p>La navegación es intuitiva pero tiene características únicas.</p>

                <h4>Transiciones Básicas</h4>
                <ul>
                <li>Las habitaciones se conectan mediante "puertas"</li>
                <li>Algunas transiciones requieren energía</li>
                <li>Puedes ver todas las conexiones disponibles</li>
                </ul>

                <h4>Consejos de Navegación</h4>
                <ul>
                <li>Planifica tus rutas para optimizar energía</li>
                <li>Revisa los requisitos antes de transitar</li>
                <li>Usa el mapa para orientarte</li>
                </ul>
                ''',
                'order': 2
            }
        ]

        for guide_data in guides_data:
            guide, created = QuickStartGuide.objects.get_or_create(
                slug=guide_data['slug'],
                defaults={
                    'title': guide_data['title'],
                    'description': guide_data['description'],
                    'target_audience': guide_data.get('target_audience', 'new_users'),
                    'estimated_time': guide_data.get('estimated_time', 5),
                    'prerequisites': guide_data.get('prerequisites', ''),
                    'content': guide_data['content'],
                    'order': guide_data.get('order', 0),
                    'is_featured': guide_data.get('is_featured', False),
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'[GUIA] {guide.title}')

    def create_sample_course_content(self, admin_user):
        """Crear contenido de ejemplo para cursos si no existe"""
        # Usar objetos existentes o crear datos mínimos
        try:
            # Intentar usar curso existente
            course = Course.objects.filter(is_published=True).first()
            if not course:
                # Crear curso mínimo si no existe ninguno
                course_category, _ = CourseCategory.objects.get_or_create(
                    name='Tutoriales del Sistema',
                    defaults={'description': 'Cursos y tutoriales sobre el uso del sistema Management360'}
                )
                course = Course.objects.create(
                    title='Introducción a Management360',
                    description='Curso completo para aprender a usar todas las funcionalidades de Management360',
                    short_description='Domina la plataforma Management360 desde cero',
                    tutor=admin_user,
                    category=course_category,
                    level='beginner',
                    price=0.00,
                    duration_hours=10,
                    is_published=True,
                    is_featured=True
                )
                self.stdout.write('[CURSO] Introducción a Management360 creado')

            # Intentar usar lección existente
            lesson = Lesson.objects.filter(is_published=True).first()
            if not lesson:
                # Crear lección mínima si no existe ninguna
                lesson = Lesson.objects.create(
                    title='Navegación por Habitaciones',
                    content='<h2>Navegación por Habitaciones</h2><p>Aprende a navegar por el sistema.</p>',
                    lesson_type='text',
                    duration_minutes=15,
                    is_free=True,
                    is_published=True,
                    is_featured=True
                )
                self.stdout.write('[LECCION] Navegación por Habitaciones creada')

            # Intentar usar bloque de contenido existente
            content_block = ContentBlock.objects.filter(is_public=True).first()
            if not content_block:
                # Crear bloque mínimo si no existe ninguno
                content_block = ContentBlock.objects.create(
                    title='Componentes de Bootstrap',
                    description='Ejemplos de componentes Bootstrap',
                    content_type='html',
                    html_content='<p>Ejemplo de contenido HTML</p>',
                    author=admin_user,
                    category='UI Components',
                    tags='bootstrap, componentes',
                    is_public=True,
                    is_featured=True
                )
                self.stdout.write('[BLOQUE CONTENIDO] Componentes de Bootstrap creado')

            # Guardar referencias para usar en artículos
            self.sample_course = course
            self.sample_lesson = lesson
            self.sample_content_block = content_block

        except Exception as e:
            self.stdout.write(f'[WARNING] Error creando contenido de ejemplo: {e}')
            # Usar valores None si hay error
            self.sample_course = None
            self.sample_lesson = None
            self.sample_content_block = None

    def create_rooms_course(self, admin_user):
        """Crear un curso completo sobre el uso de rooms con lecciones dependientes e independientes"""
        from courses.models import Course, Module, Lesson, ContentBlock
        from cv.models import Curriculum

        # Intentar crear perfil de CV para el admin (puede fallar si ya existe o hay problemas)
        try:
            cv_profile, created = Curriculum.objects.get_or_create(
                user=admin_user,
                defaults={
                    'full_name': 'Administrador del Sistema',
                    'profession': 'Administrador',
                    'bio': 'Perfil administrativo para gestión del sistema Management360',
                    'role': 'AD',  # Administrador
                    'email': admin_user.email or 'admin@management360.com'
                }
            )
            if created:
                self.stdout.write('[CV PROFILE] Perfil de CV creado para admin')
        except Exception as e:
            self.stdout.write(f'[WARNING] No se pudo crear perfil CV: {e}')
            # Continuar sin perfil CV

        # Crear curso principal sobre rooms
        rooms_course, created = Course.objects.get_or_create(
            title='Dominando las Rooms en Management360',
            defaults={
                'description': '''Curso completo y práctico para aprender a crear, gestionar y utilizar habitaciones virtuales en Management360.
Desde conceptos básicos hasta técnicas avanzadas de navegación y diseño de espacios colaborativos.

Este curso incluye lecciones independientes (puedes tomarlas en cualquier orden) y dependientes
(requieren completar lecciones previas). Todo el contenido es público y reutilizable.''',
                'short_description': 'Aprende a dominar las habitaciones virtuales de Management360',
                'tutor': admin_user,
                'category': CourseCategory.objects.filter(name='Tutoriales del Sistema').first(),
                'level': 'beginner',
                'price': 0.00,  # Gratuito
                'duration_hours': 6,
                'is_published': True,
                'is_featured': True
            }
        )
        if created:
            self.stdout.write('[CURSO ROOMS] Dominando las Rooms en Management360')

        # Crear módulos con estructura clara
        modules_data = [
            {
                'title': 'Fundamentos Básicos',
                'description': 'Conceptos esenciales y primeros pasos con habitaciones virtuales',
                'order': 1
            },
            {
                'title': 'Creación y Personalización',
                'description': 'Aprende a crear y configurar habitaciones personalizadas',
                'order': 2
            },
            {
                'title': 'Navegación Inteligente',
                'description': 'Sistema de navegación y movimiento entre habitaciones',
                'order': 3
            },
            {
                'title': 'Gestión Avanzada',
                'description': 'Técnicas avanzadas de gestión y optimización',
                'order': 4
            }
        ]

        for module_data in modules_data:
            module, created = Module.objects.get_or_create(
                course=rooms_course,
                title=module_data['title'],
                defaults={
                    'description': module_data['description'],
                    'order': module_data['order']
                }
            )
            if created:
                self.stdout.write(f'[MODULO] {module.title}')

        # Crear bloques de contenido reutilizables y públicos
        content_blocks_data = [
            {
                'title': 'Bienvenido a las Rooms',
                'content_type': 'bootstrap',
                'html_content': '''
<div class="text-center mb-4">
  <i class="bi bi-house-door-fill text-primary" style="font-size: 4rem;"></i>
  <h3 class="mt-3">¡Bienvenido al mundo de las Rooms!</h3>
  <p class="text-muted">Las habitaciones virtuales son el corazón de Management360</p>
</div>
<div class="row">
  <div class="col-md-4">
    <div class="card text-center h-100">
      <div class="card-body">
        <i class="bi bi-palette text-primary fs-1"></i>
        <h6 class="mt-2">Personalizables</h6>
        <small class="text-muted">Cada room es única</small>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card text-center h-100">
      <div class="card-body">
        <i class="bi bi-people text-success fs-1"></i>
        <h6 class="mt-2">Colaborativas</h6>
        <small class="text-muted">Trabaja en equipo</small>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card text-center h-100">
      <div class="card-body">
        <i class="bi bi-geo-alt text-info fs-1"></i>
        <h6 class="mt-2">Conectadas</h6>
        <small class="text-muted">Sistema de navegación</small>
      </div>
    </div>
  </div>
</div>
''',
                'category': 'Rooms Introduction'
            },
            {
                'title': 'Tipos de Habitaciones',
                'content_type': 'bootstrap',
                'html_content': '''
<h5 class="text-center mb-4">Elige el tipo de habitación perfecto</h5>
<div class="row g-3">
  <div class="col-md-6 col-lg-3">
    <div class="card h-100 border-primary">
      <div class="card-body text-center">
        <i class="bi bi-house-door text-primary fs-2"></i>
        <h6 class="mt-2">LOUNGE</h6>
        <small class="text-muted">Relajación y socialización</small>
        <div class="mt-2">
          <span class="badge bg-primary">Público</span>
        </div>
      </div>
    </div>
  </div>
  <div class="col-md-6 col-lg-3">
    <div class="card h-100 border-success">
      <div class="card-body text-center">
        <i class="bi bi-briefcase text-success fs-2"></i>
        <h6 class="mt-2">WORKSPACE</h6>
        <small class="text-muted">Trabajo colaborativo</small>
        <div class="mt-2">
          <span class="badge bg-success">Profesional</span>
        </div>
      </div>
    </div>
  </div>
  <div class="col-md-6 col-lg-3">
    <div class="card h-100 border-info">
      <div class="card-body text-center">
        <i class="bi bi-people text-info fs-2"></i>
        <h6 class="mt-2">MEETING</h6>
        <small class="text-muted">Reuniones y conferencias</small>
        <div class="mt-2">
          <span class="badge bg-info">Formal</span>
        </div>
      </div>
    </div>
  </div>
  <div class="col-md-6 col-lg-3">
    <div class="card h-100 border-warning">
      <div class="card-body text-center">
        <i class="bi bi-lock text-warning fs-2"></i>
        <h6 class="mt-2">PRIVATE</h6>
        <small class="text-muted">Espacios personales</small>
        <div class="mt-2">
          <span class="badge bg-warning">Privado</span>
        </div>
      </div>
    </div>
  </div>
</div>
<div class="alert alert-light mt-3">
  <small><i class="bi bi-info-circle"></i> Cada tipo tiene características y permisos específicos</small>
</div>
''',
                'category': 'Room Types'
            },
            {
                'title': 'Sistema de Energía',
                'content_type': 'bootstrap',
                'html_content': '''
<div class="card">
  <div class="card-header bg-warning text-dark">
    <h6 class="mb-0"><i class="bi bi-lightning-charge"></i> Sistema de Energía</h6>
  </div>
  <div class="card-body">
    <div class="row">
      <div class="col-md-6">
        <h6>¿Cómo funciona?</h6>
        <ul class="small">
          <li>La energía es limitada (máx. 100)</li>
          <li>Se consume en transiciones</li>
          <li>Se recupera automáticamente</li>
          <li>Completar tareas da bonos</li>
        </ul>
      </div>
      <div class="col-md-6">
        <h6>Estrategias</h6>
        <ul class="small">
          <li>Planifica rutas eficientes</li>
          <li>Completa tareas diarias</li>
          <li>Usa atajos cuando sea posible</li>
          <li>Descansa para recuperar energía</li>
        </ul>
      </div>
    </div>
    <div class="progress mt-3" style="height: 8px;">
      <div class="progress-bar bg-warning" style="width: 75%"></div>
    </div>
    <small class="text-muted mt-1">Energía actual: 75/100</small>
  </div>
</div>
''',
                'category': 'Energy System'
            },
            {
                'title': 'Navegación Básica',
                'content_type': 'bootstrap',
                'html_content': '''
<div class="text-center mb-4">
  <h5>Navegación por Habitaciones</h5>
  <p class="text-muted">Cómo moverte entre rooms</p>
</div>
<div class="row">
  <div class="col-md-6">
    <div class="card">
      <div class="card-header">
        <h6>Transiciones Disponibles</h6>
      </div>
      <div class="card-body">
        <div class="d-flex justify-content-around">
          <div class="text-center">
            <i class="bi bi-arrow-up-circle text-primary fs-2"></i>
            <div class="mt-1"><small>Norte</small></div>
          </div>
          <div class="text-center">
            <i class="bi bi-arrow-right-circle text-success fs-2"></i>
            <div class="mt-1"><small>Este</small></div>
          </div>
          <div class="text-center">
            <i class="bi bi-arrow-down-circle text-info fs-2"></i>
            <div class="mt-1"><small>Sur</small></div>
          </div>
          <div class="text-center">
            <i class="bi bi-arrow-left-circle text-warning fs-2"></i>
            <div class="mt-1"><small>Oeste</small></div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card">
      <div class="card-header">
        <h6>Consejos de Navegación</h6>
      </div>
      <div class="card-body">
        <ul class="small mb-0">
          <li>Revisa las salidas disponibles</li>
          <li>Verifica el costo de energía</li>
          <li>Usa el mapa para planificar</li>
          <li>Algunos caminos son más eficientes</li>
        </ul>
      </div>
    </div>
  </div>
</div>
''',
                'category': 'Navigation Basics'
            }
        ]

        for block_data in content_blocks_data:
            block, created = ContentBlock.objects.get_or_create(
                title=block_data['title'],
                defaults={
                    'description': f'Bloque de contenido público para {block_data["title"]}',
                    'content_type': block_data['content_type'],
                    'html_content': block_data['html_content'],
                    'author': admin_user,
                    'category': block_data['category'],
                    'is_public': True,
                    'is_featured': True
                }
            )
            if created:
                self.stdout.write(f'[BLOQUE ROOMS] {block.title}')

        # Crear lecciones con tipos dependientes e independientes
        lessons_data = [
            # Módulo 1: Fundamentos Básicos (Lecciones Independientes)
            {
                'module_title': 'Fundamentos Básicos',
                'title': '¿Qué son las Rooms?',
                'content': '''
<h2>¿Qué son las Habitaciones Virtuales?</h2>
<p>Las <strong>rooms</strong> son espacios virtuales personalizables donde puedes trabajar, socializar y colaborar.</p>

<h3>Características principales</h3>
<ul>
<li><strong>Espacios únicos:</strong> Cada room tiene su propio propósito y diseño</li>
<li><strong>Conectividad:</strong> Sistema de navegación entre habitaciones</li>
<li><strong>Personalización:</strong> Colores, dimensiones y configuraciones</li>
<li><strong>Colaboración:</strong> Trabaja con otros usuarios en tiempo real</li>
</ul>

<h3>¿Por qué son importantes?</h3>
<p>Las rooms permiten crear ambientes específicos para diferentes actividades, desde reuniones formales hasta espacios creativos.</p>

<div class="alert alert-info">
<h6><i class="bi bi-lightbulb"></i> Tip</h6>
<p>Piensa en las rooms como "salas virtuales" donde puedes organizar tu trabajo y socializar con otros usuarios.</p>
</div>
''',
                'lesson_type': 'text',
                'duration_minutes': 8,
                'order': 1,
                'is_free': True,
                'is_dependent': False  # Lección independiente
            },
            {
                'module_title': 'Fundamentos Básicos',
                'title': 'Explorando el Lobby',
                'content': '''
<h2>El Lobby: Tu Punto de Inicio</h2>
<p>El <strong>lobby</strong> es la habitación principal donde comienzas tu experiencia en Management360.</p>

<h3>¿Qué puedes hacer en el lobby?</h3>
<ul>
<li><strong>Ver habitaciones disponibles:</strong> Lista de todas las rooms públicas</li>
<li><strong>Acceder a tus rooms:</strong> Habitaciones que has creado o donde eres administrador</li>
<li><strong>Buscar contenido:</strong> Encuentra rooms por nombre, tipo o propietario</li>
<li><strong>Ver actividad reciente:</strong> Qué está pasando en la plataforma</li>
</ul>

<h3>Navegación básica</h3>
<p>Desde el lobby puedes:</p>
<ol>
<li>Hacer clic en cualquier habitación para entrar</li>
<li>Usar el menú de navegación para acceder a funciones</li>
<li>Buscar rooms específicas usando la barra de búsqueda</li>
<li>Ver estadísticas generales de la plataforma</li>
</ol>

<div class="bg-light p-3 rounded">
<h6><i class="bi bi-check-circle text-success"></i> Checklist del Lobby</h6>
<ul class="list-unstyled small">
<li><i class="bi bi-check text-success"></i> ✅ Explora las habitaciones disponibles</li>
<li><i class="bi bi-circle text-muted"></i> ⭕ Encuentra una habitación interesante</li>
<li><i class="bi bi-circle text-muted"></i> ⭕ Entra a tu primera habitación</li>
</ul>
</div>
''',
                'lesson_type': 'text',
                'duration_minutes': 6,
                'order': 2,
                'is_free': True,
                'is_dependent': False  # Lección independiente
            },

            # Módulo 2: Creación y Personalización (Lecciones Dependientes)
            {
                'module_title': 'Creación y Personalización',
                'title': 'Creando tu Primera Room',
                'content': '''
<h2>Creando tu Primera Habitación</h2>
<p>Aprende a crear una habitación básica paso a paso.</p>

<h3>Acceso al formulario</h3>
<ol>
<li>Ve al menú principal → "Rooms"</li>
<li>Haz clic en "Crear Nueva Habitación"</li>
<li>Completa el formulario básico</li>
</ol>

<h3>Campos esenciales</h3>
<ul>
<li><strong>Nombre:</strong> Identifica tu habitación</li>
<li><strong>Tipo:</strong> Elige el propósito (LOUNGE, WORKSPACE, MEETING, PRIVATE)</li>
<li><strong>Descripción:</strong> Explica qué harás en esta habitación</li>
</ul>

<h3>Configuración rápida</h3>
<p>Para empezar, solo necesitas completar los campos marcados con * (asterisco).</p>

<div class="alert alert-success">
<h6><i class="bi bi-rocket-takeoff"></i> ¡Primer paso completado!</h6>
<p>Has creado tu primera habitación. Ahora puedes personalizarla más o invitar a otros usuarios.</p>
</div>
''',
                'lesson_type': 'text',
                'duration_minutes': 10,
                'order': 1,
                'is_free': True,
                'is_dependent': True  # Requiere completar lecciones básicas
            },
            {
                'module_title': 'Creación y Personalización',
                'title': 'Personalizando tu Room',
                'content': '''
<h2>Personalizando tu Habitación</h2>
<p>Haz que tu habitación sea única con colores, dimensiones y configuraciones especiales.</p>

<h3>Colores y apariencia</h3>
<ul>
<li><strong>Color primario:</strong> El color principal de tu habitación</li>
<li><strong>Color secundario:</strong> Para acentos y detalles</li>
<li><strong>Material:</strong> Textura de las superficies</li>
</ul>

<h3>Dimensiones</h3>
<p>Ajusta el tamaño según tus necesidades:</p>
<ul>
<li><strong>Longitud y anchura:</strong> Espacio disponible</li>
<li><strong>Altura:</strong> Altura del techo</li>
<li><strong>Capacidad:</strong> Número máximo de usuarios</li>
</ul>

<h3>Propiedades especiales</h3>
<p>Configuraciones avanzadas en formato JSON:</p>
<pre><code>{
  "music": "ambient",
  "lighting": "warm",
  "mood": "productive"
}</code></pre>

<div class="alert alert-info">
<h6><i class="bi bi-palette"></i> Consejos de diseño</h6>
<p>Usa colores que reflejen el propósito de tu habitación. Azul para concentración, verde para creatividad.</p>
</div>
''',
                'lesson_type': 'text',
                'duration_minutes': 12,
                'order': 2,
                'is_free': True,
                'is_dependent': True  # Requiere saber crear rooms
            },

            # Módulo 3: Navegación Inteligente (Mixto)
            {
                'module_title': 'Navegación Inteligente',
                'title': 'Movimiento Básico',
                'content': '''
<h2>Movimiento entre Habitaciones</h2>
<p>Aprende a navegar por el sistema de habitaciones de manera eficiente.</p>

<h3>¿Cómo te mueves?</h3>
<p>Cada habitación tiene <strong>salidas</strong> que te conectan con otras rooms:</p>
<ul>
<li><strong>Norte, Sur, Este, Oeste:</strong> Direcciones cardinales</li>
<li><strong>Portales:</strong> Conexiones especiales instantáneas</li>
<li><strong>Transiciones:</strong> Puertas que requieren energía</li>
</ul>

<h3>Sistema de energía</h3>
<p>Algunas transiciones consumen <strong>energía</strong>:</p>
<ul>
<li>Máximo: 100 unidades</li>
<li>Recuperación: +1 cada 5 minutos</li>
<li>Bonos: Completar tareas da energía extra</li>
</ul>

<h3>Estrategias básicas</h3>
<ol>
<li>Revisa las salidas disponibles antes de moverte</li>
<li>Verifica el costo de energía de cada transición</li>
<li>Planifica rutas eficientes</li>
<li>Descansa cuando necesites recuperar energía</li>
</ol>

<div class="bg-light p-3 rounded">
<h6><i class="bi bi-lightning-charge text-warning"></i> Gestión de Energía</h6>
<p class="small mb-0">La energía es limitada. Úsala sabiamente para maximizar tu productividad.</p>
</div>
''',
                'lesson_type': 'text',
                'duration_minutes': 8,
                'order': 1,
                'is_free': True,
                'is_dependent': False  # Independiente - navegación básica
            },
            {
                'module_title': 'Navegación Inteligente',
                'title': 'Navegación Avanzada',
                'content': '''
<h2>Técnicas Avanzadas de Navegación</h2>
<p>Domina el sistema de navegación para moverte como un experto.</p>

<h3>Herramientas de navegación</h3>
<ul>
<li><strong>Mapa general:</strong> Vista completa de todas las habitaciones</li>
<li><strong>Rutas óptimas:</strong> Algoritmos que calculan el mejor camino</li>
<li><strong>Filtros:</strong> Encuentra habitaciones por tipo o propietario</li>
<li><strong>Historial:</strong> Registro de tus movimientos recientes</li>
</ul>

<h3>Optimización de rutas</h3>
<p>Estrategias para minimizar consumo de energía:</p>
<ul>
<li>Usa portales para distancias largas</li>
<li>Evita rutas con alto costo energético</li>
<li>Planifica viajes múltiples</li>
<li>Coordina con otros usuarios</li>
</ul>

<h3>Transiciones especiales</h3>
<p>Algunos tipos de conexiones únicas:</p>
<ul>
<li><strong>Portales dimensionales:</strong> Teletransportación instantánea</li>
<li><strong>Puertas temporales:</strong> Solo disponibles en horarios específicos</li>
<li><strong>Conexiones condicionales:</strong> Requieren items o logros</li>
</ul>

<div class="alert alert-warning">
<h6><i class="bi bi-exclamation-triangle"></i> Importante</h6>
<p>Las transiciones avanzadas pueden tener requisitos especiales. Lee las descripciones cuidadosamente.</p>
</div>
''',
                'lesson_type': 'text',
                'duration_minutes': 15,
                'order': 2,
                'is_free': False,
                'is_dependent': True  # Requiere conocer navegación básica
            },

            # Módulo 4: Gestión Avanzada (Dependientes)
            {
                'module_title': 'Gestión Avanzada',
                'title': 'Administrando tu Room',
                'content': '''
<h2>Administración de Habitaciones</h2>
<p>Aprende a gestionar y mantener tus habitaciones de manera efectiva.</p>

<h3>Permisos y acceso</h3>
<p>Controla quién puede acceder a tu habitación:</p>
<ul>
<li><strong>Público:</strong> Todos pueden entrar</li>
<li><strong>Privado:</strong> Solo con invitación</li>
<li><strong>Restringido:</strong> Usuarios específicos</li>
<li><strong>Temporal:</strong> Acceso limitado en tiempo</li>
</ul>

<h3>Administradores</h3>
<p>Designa ayudantes para gestionar tu habitación:</p>
<ul>
<li>Configurar permisos de acceso</li>
<li>Moderar contenido y usuarios</li>
<li>Gestionar conexiones y transiciones</li>
<li>Monitorear estadísticas</li>
</ul>

<h3>Mantenimiento</h3>
<p>Rutinas para mantener tu habitación funcionando:</p>
<ul>
<li>Limpieza regular de contenido obsoleto</li>
<li>Actualización de configuraciones</li>
<li>Backup de datos importantes</li>
<li>Optimización de rendimiento</li>
</ul>

<div class="alert alert-success">
<h6><i class="bi bi-shield-check"></i> Buenas prácticas</h6>
<p>Mantén tus habitaciones organizadas y actualizadas para ofrecer la mejor experiencia a tus usuarios.</p>
</div>
''',
                'lesson_type': 'text',
                'duration_minutes': 12,
                'order': 1,
                'is_free': False,
                'is_dependent': True  # Requiere experiencia previa
            }
        ]

        for lesson_data in lessons_data:
            try:
                module = Module.objects.get(
                    course=rooms_course,
                    title=lesson_data['module_title']
                )

                lesson, created = Lesson.objects.get_or_create(
                    module=module,
                    title=lesson_data['title'],
                    defaults={
                        'content': lesson_data['content'],
                        'lesson_type': lesson_data['lesson_type'],
                        'duration_minutes': lesson_data['duration_minutes'],
                        'order': lesson_data['order'],
                        'is_free': lesson_data['is_free']
                    }
                )
                if created:
                    self.stdout.write(f'[LECCION ROOMS] {lesson.title} {"(Dependiente)" if lesson_data.get("is_dependent") else "(Independiente)"}')
            except Module.DoesNotExist:
                self.stdout.write(f'[WARNING] Módulo no encontrado: {lesson_data["module_title"]}')

        # Guardar referencia al curso de rooms
        self.rooms_course = rooms_course
        self.stdout.write('[CURSO ROOMS] Completado: Guía Completa de Rooms en Management360')
        self.stdout.write('[CURSO ROOMS] Lecciones independientes: 3 | Lecciones dependientes: 4')