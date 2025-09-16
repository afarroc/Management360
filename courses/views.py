from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q, Avg, Count, Prefetch
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import (
    Course, Module, Lesson, Enrollment, 
    Progress, Review, CourseCategory,
    CourseLevelChoices, EnrollmentStatusChoices, LessonTypeChoices
)
from .forms import CourseForm, ModuleForm, LessonForm, ReviewForm, CategoryForm

# ======================
# VISTAS PÚBLICAS
# ======================

def index(request):
    """Página principal de la app de cursos - Muestra contenido general, noticias, nuevos cursos, etc."""
    # Estadísticas generales
    total_courses = Course.objects.filter(is_published=True).count()
    total_students = sum(course.students_count for course in Course.objects.filter(is_published=True))
    total_categories = CourseCategory.objects.count()

    # Cursos destacados (featured)
    featured_courses = Course.objects.filter(
        is_published=True,
        is_featured=True
    ).select_related('category', 'tutor').order_by('-created_at')[:6]

    # Cursos más recientes
    recent_courses = Course.objects.filter(
        is_published=True
    ).select_related('category', 'tutor').order_by('-created_at')[:8]

    # Categorías populares
    popular_categories = CourseCategory.objects.annotate(
        course_count=Count('courses', filter=Q(courses__is_published=True))
    ).filter(course_count__gt=0).order_by('-course_count')[:6]

    # Estadísticas de usuarios (si hay usuarios autenticados)
    if request.user.is_authenticated:
        user_enrollments = Enrollment.objects.filter(
            student=request.user,
            status=EnrollmentStatusChoices.ACTIVE
        ).count()
        user_completed = Enrollment.objects.filter(
            student=request.user,
            status=EnrollmentStatusChoices.COMPLETED
        ).count()
    else:
        user_enrollments = 0
        user_completed = 0

    context = {
        'total_courses': total_courses,
        'total_students': total_students,
        'total_categories': total_categories,
        'featured_courses': featured_courses,
        'recent_courses': recent_courses,
        'popular_categories': popular_categories,
        'user_enrollments': user_enrollments,
        'user_completed': user_completed,
        'categories': CourseCategory.objects.all(),
    }
    return render(request, 'courses/index.html', context)


def course_list(request, category_slug=None):
    """Lista todos los cursos disponibles con optimización de consultas"""
    courses = Course.objects.filter(is_published=True).select_related(
        'category', 'tutor'
    ).prefetch_related(
        Prefetch('reviews', queryset=Review.objects.select_related('student'))
    )

    # Filtros
    category = request.GET.get('category') or category_slug
    level = request.GET.get('level')
    search = request.GET.get('search')

    if category:
        courses = courses.filter(category__slug=category)
    if level:
        courses = courses.filter(level=level)
    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(short_description__icontains=search)
        )

    # Calcular estadísticas
    total_students = sum(course.students_count for course in courses)
    average_rating = 0
    if courses:
        ratings = [course.average_rating for course in courses if course.average_rating > 0]
        if ratings:
            average_rating = sum(ratings) / len(ratings)

    context = {
        'courses': courses,
        'categories': CourseCategory.objects.all(),
        'levels': CourseLevelChoices.choices,
        'selected_category': category,
        'selected_level': level,
        'search_query': search or '',
        'total_students': total_students,
        'average_rating': average_rating
    }
    return render(request, 'courses/course_list.html', context)


def course_detail(request, slug):
    """Detalle de un curso específico con optimización de consultas"""
    course = get_object_or_404(
        Course.objects.select_related('category', 'tutor').prefetch_related(
            Prefetch('modules__lessons', queryset=Lesson.objects.order_by('order'))
        ),
        slug=slug, 
        is_published=True
    )
    
    # Obtener reseñas por separado para evitar el problema del slice
    reviews = Review.objects.filter(
        course=course
    ).select_related('student').order_by('-created_at')[:5]
    
    # Verificar si el usuario está inscrito
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(
            student=request.user, 
            course=course, 
            status=EnrollmentStatusChoices.ACTIVE
        ).exists()
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'reviews': reviews,
        'categories': CourseCategory.objects.all(),
    }
    return render(request, 'courses/course_detail.html', context)

# ======================
# VISTAS DE ESTUDIANTES
# ======================

@login_required
def enroll(request, course_id):
    """Inscribir a un usuario en un curso"""
    try:
        course = get_object_or_404(Course, id=course_id, is_published=True)

        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'status': EnrollmentStatusChoices.ACTIVE}
        )

        if created:
            messages.success(request, f'Te has inscrito correctamente en "{course.title}"')
        else:
            messages.info(request, f'Ya estás inscrito en el curso "{course.title}"')

    except Exception as e:
        messages.error(request, 'Ha ocurrido un error al procesar tu inscripción. Por favor, intenta nuevamente.')
        return redirect('courses:courses_list')

    return redirect('courses:course_detail', slug=course.slug)


@login_required
def dashboard(request):
    """Dashboard personal del usuario - Panel de control con cursos inscritos y progreso"""
    # Cursos como estudiante
    user_enrollments = Enrollment.objects.filter(
        student=request.user,
        status=EnrollmentStatusChoices.ACTIVE
    ).select_related('course')

    # Precalcular estadísticas de progreso
    enrollment_stats = []
    for enrollment in user_enrollments:
        # Obtener estadísticas del curso
        total_lessons = Lesson.objects.filter(module__course=enrollment.course).count()
        completed_lessons = Progress.objects.filter(
            enrollment=enrollment,
            completed=True
        ).count()

        progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

        enrollment_stats.append({
            'enrollment': enrollment,
            'progress_percentage': progress_percentage,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons
        })

    # Cursos como tutor
    taught_courses = Course.objects.filter(tutor=request.user).annotate(
        student_count=Count('enrollments', filter=Q(enrollments__status=EnrollmentStatusChoices.ACTIVE)),
        avg_rating=Avg('reviews__rating')
    )

    # Estadísticas específicas de cursos
    total_available_courses = Course.objects.filter(is_published=True).count()
    user_course_count = user_enrollments.count()
    completed_courses = sum(1 for stat in enrollment_stats if stat['progress_percentage'] == 100)

    # Funciones disponibles en la app de cursos
    course_functions = [
        {
            'name': 'Explorar Cursos',
            'description': 'Ver catálogo completo de cursos',
            'icon': 'fas fa-search',
            'url': 'courses_list',
            'color': 'primary'
        },
        {
            'name': 'Mis Cursos',
            'description': 'Cursos en los que estoy inscrito',
            'icon': 'fas fa-book-reader',
            'url': 'dashboard',
            'color': 'success'
        },
        {
            'name': 'Crear Curso',
            'description': 'Crear un nuevo curso como tutor',
            'icon': 'fas fa-plus',
            'url': 'create_course',
            'color': 'info'
        },
        {
            'name': 'Asistente de Cursos',
            'description': 'Crear curso paso a paso',
            'icon': 'fas fa-magic',
            'url': 'create_course_wizard',
            'color': 'primary'
        },
        {
            'name': 'Gestionar Cursos',
            'description': 'Administrar mis cursos como tutor',
            'icon': 'fas fa-cog',
            'url': 'manage_courses',
            'color': 'warning'
        },
        {
            'name': 'Categorías',
            'description': 'Gestionar categorías de cursos',
            'icon': 'fas fa-tags',
            'url': 'manage_categories',
            'color': 'secondary'
        },
        {
            'name': 'Módulos',
            'description': 'Vista general de módulos',
            'icon': 'fas fa-list',
            'url': 'modules_overview',
            'color': 'dark'
        },
        {
            'name': 'Panel de Administración',
            'description': 'Panel administrativo de cursos',
            'icon': 'fas fa-user-shield',
            'url': 'admin_dashboard',
            'color': 'danger'
        },
        {
            'name': 'Gestión de Usuarios',
            'description': 'Administrar usuarios del sistema',
            'icon': 'fas fa-users-cog',
            'url': 'admin_users',
            'color': 'info'
        }
    ]

    context = {
        'enrollment_stats': enrollment_stats,
        'taught_courses': taught_courses,
        'course_functions': course_functions,
        'total_available_courses': total_available_courses,
        'user_course_count': user_course_count,
        'completed_courses': completed_courses,
        'categories': CourseCategory.objects.all(),
    }
    return render(request, 'courses/dashboard.html', context)

@login_required
def course_learning(request, slug, lesson_id=None):
    """Vista para aprender un curso con optimización de consultas"""
    course = get_object_or_404(
        Course.objects.select_related('tutor').prefetch_related(
            Prefetch('modules__lessons', queryset=Lesson.objects.order_by('order'))
        ),
        slug=slug
    )
    
    enrollment = get_object_or_404(
        Enrollment, 
        student=request.user, 
        course=course, 
        status=EnrollmentStatusChoices.ACTIVE
    )
    
    # Obtener todas las lecciones ordenadas
    all_lessons = Lesson.objects.filter(
        module__course=course
    ).select_related('module').order_by('module__order', 'order')
    
    # Obtener lección actual o redirigir a la primera
    if lesson_id:
        current_lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    else:
        first_lesson = all_lessons.first()
        if first_lesson:
            return redirect('courses:course_learning_lesson', slug=slug, lesson_id=first_lesson.id)
        messages.error(request, "Este curso no tiene lecciones disponibles.")
        return redirect('courses:course_detail', slug=slug)
    
    # Obtener progreso de la lección actual
    lesson_progress, created = Progress.objects.get_or_create(
        enrollment=enrollment,
        lesson=current_lesson
    )
    
    # Determinar lección anterior y siguiente
    lesson_list = list(all_lessons)
    current_index = lesson_list.index(current_lesson) if current_lesson in lesson_list else -1
    
    previous_lesson = lesson_list[current_index - 1] if current_index > 0 else None
    next_lesson = lesson_list[current_index + 1] if current_index < len(lesson_list) - 1 else None
    
    # Obtener lecciones completadas
    completed_lessons = Progress.objects.filter(
        enrollment=enrollment, 
        completed=True
    ).values_list('lesson_id', flat=True)
    
    # Manejar envío de formularios
    if request.method == 'POST':
        _handle_lesson_submission(request, current_lesson, lesson_progress)
    
    context = {
        'course': course,
        'modules': course.modules.all().prefetch_related('lessons'),
        'current_lesson': current_lesson,
        'lesson_progress': lesson_progress,
        'enrollment': enrollment,
        'previous_lesson': previous_lesson,
        'next_lesson': next_lesson,
        'completed_lessons': completed_lessons,
    }
    return render(request, 'courses/course_learning.html', context)


def _handle_lesson_submission(request, lesson, progress):
    """Manejar el envío de formularios según el tipo de lección"""
    if lesson.lesson_type == LessonTypeChoices.QUIZ:
        _handle_quiz_submission(request, lesson, progress)
    elif lesson.lesson_type == LessonTypeChoices.ASSIGNMENT:
        _handle_assignment_submission(request, progress)


def _handle_quiz_submission(request, lesson, progress):
    """Procesar envío de quiz"""
    score = 0
    total_questions = len(lesson.quiz_questions)
    
    for i, question in enumerate(lesson.quiz_questions):
        user_answer = request.POST.get(f'question_{i+1}')
        if user_answer and user_answer == question.get('correct_answer'):
            score += 1
    
    percentage = (score / total_questions * 100) if total_questions > 0 else 0
    progress.score = percentage
    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save()
    
    messages.success(request, f"¡Quiz completado! Puntuación: {score}/{total_questions} ({percentage:.1f}%)")


def _handle_assignment_submission(request, progress):
    """Procesar envío de tarea"""
    if request.FILES.get('submission_file'):
        progress.completed = True
        progress.completed_at = timezone.now()
        progress.save()
        messages.success(request, "¡Tarea enviada correctamente!")
    else:
        messages.error(request, "Debes subir un archivo para completar la tarea.")


@require_POST
@login_required
def mark_lesson_complete(request, lesson_id):
    """Marcar una lección como completada (AJAX/HTTP)"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    enrollment = get_object_or_404(
        Enrollment, 
        student=request.user, 
        course=lesson.module.course, 
        status=EnrollmentStatusChoices.ACTIVE
    )
    
    progress, created = Progress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )
    
    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, f"¡Lección '{lesson.title}' completada!")
    return redirect('courses:course_learning_lesson', 
                   slug=lesson.module.course.slug, 
                   lesson_id=lesson.id)


@login_required
def add_review(request, course_id):
    """Añadir una reseña a un curso"""
    course = get_object_or_404(Course, id=course_id)
    enrollment = get_object_or_404(
        Enrollment, 
        student=request.user, 
        course=course, 
        status=EnrollmentStatusChoices.ACTIVE
    )
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.student = request.user
            review.course = course
            review.save()
            messages.success(request, 'Reseña publicada exitosamente')
            return redirect('courses:course_detail', slug=course.slug)
    else:
        form = ReviewForm()
    
    return render(request, 'courses/add_review.html', {
        'form': form,
        'course': course,
    })


# ======================
# VISTAS PARA TUTORES
# ======================

@login_required
def manage_courses(request):
    """Gestión de cursos para tutores"""
    if not hasattr(request.user, 'cv'):
        messages.error(request, 'Necesitas un perfil de tutor')
        return redirect('cv:detail')

    courses = Course.objects.filter(tutor=request.user).annotate(
        student_count=Count('enrollments', filter=Q(enrollments__status=EnrollmentStatusChoices.ACTIVE)),
        avg_rating=Avg('reviews__rating')
    )

    # Calcular estadísticas agregadas
    total_students = sum(course.student_count for course in courses)
    total_duration = sum(course.duration_hours for course in courses)
    avg_rating = 0
    if courses:
        ratings = [course.avg_rating for course in courses if course.avg_rating is not None]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)

    context = {
        'courses': courses,
        'total_students': total_students,
        'total_duration': total_duration,
        'avg_rating': avg_rating
    }

    return render(request, 'courses/manage_courses.html', context)


@login_required
def create_course(request):
    """Crear un nuevo curso"""
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            course = form.save(commit=False)
            course.tutor = request.user
            course.save()
            messages.success(request, 'Curso creado exitosamente')
            return redirect('courses:manage_content', slug=course.slug)
    else:
        form = CourseForm(user=request.user)

    return render(request, 'courses/course_form.html', {
        'form': form,
        'title': 'Crear Nuevo Curso',
    })


@login_required
def create_course_wizard(request):
    """Asistente paso a paso para crear un curso"""
    if not hasattr(request.user, 'cv'):
        messages.error(request, 'Necesitas un perfil de tutor para crear cursos')
        return redirect('cv:detail')

    step = int(request.GET.get('step', 1))

    if request.method == 'POST':
        if step == 1:
            # Paso 1: Información básica del curso
            form = CourseForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                course = form.save(commit=False)
                course.tutor = request.user
                course.save()
                return redirect(f'{request.path}?step=2&course_id={course.id}')
        elif step == 2:
            # Paso 2: Crear primer módulo
            course_id = request.POST.get('course_id')
            course = get_object_or_404(Course, id=course_id, tutor=request.user)

            form = ModuleForm(request.POST)
            if form.is_valid():
                module = form.save(commit=False)
                module.course = course
                module.save()
                messages.success(request, f'Curso "{course.title}" creado con el módulo "{module.title}"')
                return redirect('courses:manage_content', slug=course.slug)

    # Preparar formulario según el paso
    if step == 1:
        form = CourseForm(user=request.user)
        template = 'courses/course_wizard_step1.html'
        title = 'Crear Curso - Paso 1: Información Básica'
    elif step == 2:
        course_id = request.GET.get('course_id')
        if course_id:
            course = get_object_or_404(Course, id=course_id, tutor=request.user)
            form = ModuleForm()
            template = 'courses/course_wizard_step2.html'
            title = f'Crear Curso - Paso 2: Primer Módulo para "{course.title}"'
        else:
            return redirect('courses:create_course_wizard')
    else:
        return redirect('courses:create_course_wizard')

    context = {
        'form': form,
        'title': title,
        'step': step,
        'course': locals().get('course'),
    }

    return render(request, template, context)


@login_required
def edit_course(request, slug):
    """Editar un curso existente"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado exitosamente')
            return redirect('courses:manage_courses')
    else:
        form = CourseForm(instance=course, user=request.user)

    return render(request, 'courses/course_form.html', {
        'form': form,
        'title': 'Editar Curso',
        'course': course,
    })

@login_required
def course_analytics(request, slug):
    """Analíticas de un curso para el tutor"""
    course = get_object_or_404(
        Course.objects.annotate(
            total_students=Count('enrollments', filter=Q(enrollments__status=EnrollmentStatusChoices.ACTIVE)),
            completed_students=Count('enrollments', filter=Q(enrollments__status=EnrollmentStatusChoices.COMPLETED))
        ),
        slug=slug, 
        tutor=request.user
    )
    
    # Progreso de estudiantes
    progress_data = []
    enrollments = course.enrollments.filter(
        status=EnrollmentStatusChoices.ACTIVE
    ).select_related('student').prefetch_related(
        Prefetch('progress', queryset=Progress.objects.filter(completed=True))
    )
    
    total_lessons = Lesson.objects.filter(module__course=course).count()
    
    for enrollment in enrollments:
        completed_lessons = enrollment.progress.count()
        progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        progress_data.append({
            'student': enrollment.student,
            'progress': progress_percentage,
            'completed_lessons': completed_lessons,
            'total_lessons': total_lessons,
            'enrollment_date': enrollment.enrolled_at,  # Usar enrolled_at en lugar de updated_at
            'status': enrollment.get_status_display()
        })
    
    # Ordenar por progreso (descendente)
    progress_data.sort(key=lambda x: x['progress'], reverse=True)
    
    return render(request, 'courses/course_analytics.html', {
        'course': course,
        'progress_data': progress_data,
        'total_lessons': total_lessons,
    })

# ======================
# VISTAS PARA GESTIÓN DE CONTENIDO
# ======================

@login_required
def manage_content(request, slug):
    """Vista para gestionar el contenido de un curso (módulos y lecciones)"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)

    # Obtener estadísticas del curso
    total_modules = course.modules.count()
    total_lessons = Lesson.objects.filter(module__course=course).count()

    # Obtener módulos con estadísticas calculadas
    modules = course.modules.prefetch_related('lessons').annotate(
        lessons_count=Count('lessons'),
        total_duration=Count('lessons') * 30  # Asumiendo 30 min por lección
    )

    context = {
        'course': course,
        'modules': modules,
        'total_modules': total_modules,
        'total_lessons': total_lessons,
        'categories': CourseCategory.objects.all(),
    }
    return render(request, 'courses/manage_content.html', context)

@login_required
def create_module(request, slug):
    """Crear un nuevo módulo para un curso"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)

    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, 'Módulo creado exitosamente')
            return redirect('courses:manage_content', slug=course.slug)
    else:
        form = ModuleForm()

    return render(request, 'courses/module_form.html', {
        'form': form,
        'course': course,
        'title': 'Crear Nuevo Módulo',
        'module': None,
    })

@login_required
def edit_module(request, slug, module_id):
    """Editar un módulo existente"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)

    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, 'Módulo actualizado exitosamente')
            return redirect('courses:manage_content', slug=course.slug)
    else:
        form = ModuleForm(instance=module)

    return render(request, 'courses/module_form.html', {
        'form': form,
        'course': course,
        'title': 'Editar Módulo',
        'module': module,
    })

@login_required
def delete_module(request, slug, module_id):
    """Eliminar un módulo"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)

    if request.method == 'POST':
        module.delete()
        messages.success(request, 'Módulo eliminado exitosamente')
        return redirect('courses:manage_content', slug=course.slug)

    return render(request, 'courses/delete_module.html', {
        'course': course,
        'module': module,
    })

@login_required
def duplicate_module(request, slug, module_id):
    """Duplicar un módulo con todas sus lecciones"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)

    if request.method == 'POST':
        # Crear nuevo módulo
        new_module = Module.objects.create(
            course=course,
            title=f"{module.title} (Copia)",
            description=module.description,
            order=module.order + 1
        )

        # Duplicar todas las lecciones
        for lesson in module.lessons.all():
            Lesson.objects.create(
                module=new_module,
                title=lesson.title,
                lesson_type=lesson.lesson_type,
                content=lesson.content,
                video_url=lesson.video_url,
                duration_minutes=lesson.duration_minutes,
                order=lesson.order,
                is_free=lesson.is_free,
                quiz_questions=lesson.quiz_questions,
                assignment_instructions=lesson.assignment_instructions,
                assignment_file=lesson.assignment_file,
                assignment_due_date=lesson.assignment_due_date
            )

        messages.success(request, f'Módulo "{module.title}" duplicado exitosamente')
        return redirect('courses:manage_content', slug=course.slug)

    return render(request, 'courses/duplicate_module.html', {
        'course': course,
        'module': module,
    })

@require_POST
@login_required
def reorder_modules(request, slug):
    """Reordenar módulos vía AJAX"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)

    module_order = request.POST.getlist('module_order[]')
    if module_order:
        for index, module_id in enumerate(module_order):
            try:
                module = Module.objects.get(id=module_id, course=course)
                module.order = index + 1
                module.save()
            except Module.DoesNotExist:
                continue

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)

@login_required
def module_statistics(request, slug, module_id):
    """Ver estadísticas detalladas de un módulo"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)

    # Estadísticas del módulo
    total_lessons = module.lessons.count()
    total_students = course.enrollments.filter(status='active').count()

    # Progreso por lección
    lesson_stats = []
    for lesson in module.lessons.all():
        completed_count = Progress.objects.filter(
            lesson=lesson,
            completed=True
        ).count()

        completion_rate = (completed_count / total_students * 100) if total_students > 0 else 0

        lesson_stats.append({
            'lesson': lesson,
            'completed_count': completed_count,
            'completion_rate': completion_rate,
        })

    context = {
        'course': course,
        'module': module,
        'total_lessons': total_lessons,
        'total_students': total_students,
        'lesson_stats': lesson_stats,
    }

    return render(request, 'courses/module_statistics.html', context)

@login_required
def modules_overview(request):
    """Vista general de todos los módulos del tutor"""
    if not hasattr(request.user, 'cv'):
        messages.error(request, 'Necesitas un perfil de tutor')
        return redirect('cv:detail')

    # Obtener todos los cursos del tutor
    courses = Course.objects.filter(tutor=request.user).prefetch_related('modules__lessons')

    # Estadísticas generales
    total_courses = courses.count()
    total_modules = sum(course.modules.count() for course in courses)
    total_lessons = sum(
        sum(module.lessons.count() for module in course.modules.all())
        for course in courses
    )

    # Módulos recientes
    recent_modules = Module.objects.filter(
        course__tutor=request.user
    ).select_related('course').order_by('-id')[:10]

    context = {
        'courses': courses,
        'total_courses': total_courses,
        'total_modules': total_modules,
        'total_lessons': total_lessons,
        'recent_modules': recent_modules,
    }

    return render(request, 'courses/modules_overview.html', context)

@login_required
def module_progress(request, slug, module_id):
    """Ver progreso detallado de estudiantes en un módulo"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)

    # Obtener estudiantes inscritos
    enrollments = course.enrollments.filter(status='active').select_related('student')

    # Calcular progreso por estudiante
    student_progress = []
    for enrollment in enrollments:
        completed_lessons = Progress.objects.filter(
            enrollment=enrollment,
            lesson__module=module,
            completed=True
        ).count()

        total_module_lessons = module.lessons.count()
        progress_percentage = (completed_lessons / total_module_lessons * 100) if total_module_lessons > 0 else 0

        student_progress.append({
            'enrollment': enrollment,
            'completed_lessons': completed_lessons,
            'total_lessons': total_module_lessons,
            'progress_percentage': progress_percentage,
        })

    # Ordenar por progreso descendente
    student_progress.sort(key=lambda x: x['progress_percentage'], reverse=True)

    context = {
        'course': course,
        'module': module,
        'student_progress': student_progress,
        'total_students': len(student_progress),
    }

    return render(request, 'courses/module_progress.html', context)

@login_required
def bulk_module_actions(request, slug):
    """Acciones masivas para módulos de un curso"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        module_ids = request.POST.getlist('module_ids')

        if action == 'delete_selected':
            Module.objects.filter(id__in=module_ids, course=course).delete()
            messages.success(request, f'Se eliminaron {len(module_ids)} módulos')
        elif action == 'duplicate_selected':
            duplicated_count = 0
            for module_id in module_ids:
                try:
                    module = Module.objects.get(id=module_id, course=course)
                    # Duplicar módulo
                    new_module = Module.objects.create(
                        course=course,
                        title=f"{module.title} (Copia)",
                        description=module.description,
                        order=module.order + 1
                    )
                    # Duplicar lecciones
                    for lesson in module.lessons.all():
                        Lesson.objects.create(
                            module=new_module,
                            title=lesson.title,
                            lesson_type=lesson.lesson_type,
                            content=lesson.content,
                            video_url=lesson.video_url,
                            duration_minutes=lesson.duration_minutes,
                            order=lesson.order,
                            is_free=lesson.is_free,
                        )
                    duplicated_count += 1
                except Module.DoesNotExist:
                    continue
            messages.success(request, f'Se duplicaron {duplicated_count} módulos')

        return redirect('courses:manage_content', slug=course.slug)

    modules = course.modules.all()
    return render(request, 'courses/bulk_module_actions.html', {
        'course': course,
        'modules': modules,
    })

@login_required
def create_lesson(request, slug, module_id):
    """Crear una nueva lección para un módulo con soporte para contenido estructurado"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.save()
            messages.success(request, 'Lección creada exitosamente')

            # Si es una petición AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Lección creada exitosamente',
                    'lesson': {
                        'id': lesson.id,
                        'title': lesson.title,
                        'lesson_type': lesson.lesson_type,
                        'has_structured_content': bool(lesson.structured_content),
                        'structured_content_count': len(lesson.structured_content) if lesson.structured_content else 0
                    }
                })

            return redirect('courses:manage_content', slug=course.slug)
        else:
            # Si es AJAX y hay errores, devolver errores
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = LessonForm()

    # Información adicional para el template
    context = {
        'form': form,
        'course': course,
        'module': module,
        'title': 'Crear Nueva Lección',
        'lesson': None,
        'lesson_types': LessonTypeChoices.choices,
    }

    return render(request, 'courses/lesson_form.html', context)

@login_required
def edit_lesson(request, slug, module_id, lesson_id):
    """Editar una lección existente con soporte para contenido estructurado"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            # El formulario maneja automáticamente el contenido estructurado
            form.save()
            messages.success(request, 'Lección actualizada exitosamente')

            # Si es una petición AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Lección actualizada exitosamente',
                    'lesson': {
                        'id': lesson.id,
                        'title': lesson.title,
                        'lesson_type': lesson.lesson_type,
                        'has_structured_content': bool(lesson.structured_content),
                        'structured_content_count': len(lesson.structured_content) if lesson.structured_content else 0
                    }
                })

            return redirect('courses:manage_content', slug=course.slug)
        else:
            # Si es AJAX y hay errores, devolver errores
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = LessonForm(instance=lesson)

    # Información adicional para el template
    context = {
        'form': form,
        'course': course,
        'module': module,
        'title': 'Editar Lección',
        'lesson': lesson,
        'has_structured_content': bool(lesson.structured_content),
        'structured_content_count': len(lesson.structured_content) if lesson.structured_content else 0,
        'lesson_types': LessonTypeChoices.choices,
    }

    return render(request, 'courses/lesson_form.html', context)

@login_required
def delete_lesson(request, slug, module_id, lesson_id):
    """Eliminar una lección"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)

    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Lección eliminada exitosamente')
        return redirect('courses:manage_content', slug=course.slug)

    return render(request, 'courses/delete_lesson.html', {
        'course': course,
        'module': module,
        'lesson': lesson,
    })

# ======================
# VISTAS PARA GESTIÓN DE CATEGORÍAS
# ======================

@login_required
def manage_categories(request):
    """Vista para gestionar categorías de cursos con optimización de consultas"""
    # Solo administradores pueden gestionar categorías
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('courses:courses_list')

    # Optimizar consulta con prefetch_related para evitar N+1 queries
    categories = CourseCategory.objects.prefetch_related(
        'courses'  # Precargar cursos relacionados para contarlos eficientemente
    ).order_by('name')  # Ordenar alfabéticamente

    return render(request, 'courses/manage_categories.html', {
        'categories': categories,
    })

@login_required
def create_category(request):
    """Crear una nueva categoría"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('courses:courses_list')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, 'Categoría creada exitosamente')

            # Si es una petición AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Categoría creada exitosamente',
                    'category': {
                        'id': category.id,
                        'name': category.name,
                        'description': category.description,
                        'slug': category.slug,
                        'courses_count': category.courses.count()
                    }
                })

            return redirect('courses:manage_categories')
        else:
            # Si es AJAX y hay errores, devolver errores
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = CategoryForm()

    return render(request, 'courses/category_form.html', {
        'form': form,
        'title': 'Crear Nueva Categoría',
    })


@login_required
def quick_create_category(request):
    """Crear categorías comunes de manera rápida"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('courses:courses_list')

    # Categorías predefinidas comunes
    common_categories = [
        {'name': 'Programación', 'description': 'Cursos de desarrollo de software y lenguajes de programación'},
        {'name': 'Diseño Gráfico', 'description': 'Herramientas y técnicas de diseño visual'},
        {'name': 'Marketing Digital', 'description': 'Estrategias de marketing en línea y redes sociales'},
        {'name': 'Negocios', 'description': 'Emprendimiento, gestión y administración de empresas'},
        {'name': 'Idiomas', 'description': 'Aprendizaje de idiomas extranjeros'},
        {'name': 'Matemáticas', 'description': 'Cursos de matemáticas y lógica'},
        {'name': 'Ciencias', 'description': 'Biología, química, física y otras ciencias'},
        {'name': 'Arte y Música', 'description': 'Cursos de arte, música y expresión creativa'},
        {'name': 'Salud y Bienestar', 'description': 'Nutrición, ejercicio y salud mental'},
        {'name': 'Tecnología', 'description': 'Innovación, IA, blockchain y nuevas tecnologías'},
    ]

    if request.method == 'POST':
        selected_categories = request.POST.getlist('categories')
        created_count = 0

        for category_name in selected_categories:
            # Verificar si ya existe
            if not CourseCategory.objects.filter(name=category_name).exists():
                # Encontrar la descripción correspondiente
                description = next(
                    (cat['description'] for cat in common_categories if cat['name'] == category_name),
                    f'Cursos relacionados con {category_name.lower()}'
                )

                CourseCategory.objects.create(
                    name=category_name,
                    description=description
                )
                created_count += 1

        if created_count > 0:
            messages.success(request, f'Se crearon {created_count} categorías exitosamente')
        else:
            messages.info(request, 'Todas las categorías seleccionadas ya existen')

        return redirect('courses:manage_categories')

    # Filtrar categorías que ya existen
    existing_categories = CourseCategory.objects.values_list('name', flat=True)
    available_categories = [
        cat for cat in common_categories
        if cat['name'] not in existing_categories
    ]

    return render(request, 'courses/quick_create_category.html', {
        'categories': available_categories,
        'title': 'Crear Categorías Rápidamente',
    })

@login_required
def edit_category(request, category_id):
    """Editar una categoría existente"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('courses:courses_list')

    category = get_object_or_404(CourseCategory, id=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente')
            return redirect('courses:manage_categories')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'courses/category_form.html', {
        'form': form,
        'title': 'Editar Categoría',
        'category': category,
    })

@login_required
def delete_category(request, category_id):
    """Eliminar una categoría"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('courses:courses_list')

    category = get_object_or_404(CourseCategory, id=category_id)

    if request.method == 'POST':
        # Verificar si la categoría tiene cursos asociados
        if category.courses.exists():
            messages.error(request, 'No se puede eliminar una categoría que tiene cursos asociados')
            return redirect('courses:manage_categories')

        category.delete()
        messages.success(request, 'Categoría eliminada exitosamente')
        return redirect('courses:manage_categories')

    return render(request, 'courses/delete_category.html', {
        'category': category,
    })

# ======================
# VISTAS DE ADMINISTRACIÓN
# ======================

@login_required
def admin_dashboard(request):
    """Panel de administración de cursos"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('courses:courses_list')

    # Estadísticas generales
    total_courses = Course.objects.count()
    published_courses = Course.objects.filter(is_published=True).count()
    total_users = User.objects.count()
    total_enrollments = Enrollment.objects.count()

    # Cursos recientes
    recent_courses = Course.objects.select_related('tutor', 'category').order_by('-created_at')[:5]

    # Usuarios recientes
    recent_users = User.objects.order_by('-date_joined')[:5]

    context = {
        'total_courses': total_courses,
        'published_courses': published_courses,
        'total_users': total_users,
        'total_enrollments': total_enrollments,
        'recent_courses': recent_courses,
        'recent_users': recent_users,
    }
    return render(request, 'courses/admin/dashboard.html', context)

@login_required
def admin_users(request):
    """Vista de administración de usuarios"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('courses:courses_list')

    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')

    users = User.objects.all().order_by('-date_joined')

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    if role_filter:
        if role_filter == 'none':
            users = users.filter(cv__isnull=True)
        else:
            users = users.filter(cv__role=role_filter)

    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'users': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'courses/admin/users.html', context)

@login_required
def admin_user_detail(request, user_id):
    """Vista de detalle de un usuario para admin"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('courses:courses_list')

    user = get_object_or_404(User, id=user_id)

    # Información adicional del usuario
    user_courses = Course.objects.filter(tutor=user)
    user_enrollments = Enrollment.objects.filter(student=user).select_related('course')

    context = {
        'user_detail': user,
        'user_courses': user_courses,
        'user_enrollments': user_enrollments,
    }
    return render(request, 'courses/admin/user_detail.html', context)

@login_required
def edit_user(request, user_id):
    """Editar información de un usuario (admin)"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('courses:courses_list')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        messages.success(request, 'Usuario actualizado exitosamente')
        return redirect('courses:admin_user_detail', user_id=user.id)

    return render(request, 'courses/admin/edit_user.html', {
        'user': user,
    })