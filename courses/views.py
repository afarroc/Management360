from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count, Prefetch
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import (
    Course, Module, Lesson, Enrollment, 
    Progress, Review, CourseCategory,
    CourseLevelChoices, EnrollmentStatusChoices, LessonTypeChoices
)
from .forms import CourseForm, ModuleForm, LessonForm, ReviewForm

# ======================
# VISTAS PÚBLICAS
# ======================

def course_list(request):
    """Lista todos los cursos disponibles con optimización de consultas"""
    courses = Course.objects.filter(is_published=True).select_related(
        'category', 'tutor'
    ).prefetch_related(
        Prefetch('reviews', queryset=Review.objects.select_related('student'))
    )
    
    # Filtros
    category = request.GET.get('category')
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
    
    context = {
        'courses': courses,
        'categories': CourseCategory.objects.all(),
        'levels': CourseLevelChoices.choices,
        'selected_category': category,
        'selected_level': level,
        'search_query': search or ''
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
    }
    return render(request, 'courses/course_detail.html', context)

# ======================
# VISTAS DE ESTUDIANTES
# ======================

@login_required
def enroll(request, course_id):
    """Inscribir a un usuario en un curso"""
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
    
    return redirect('courses:course_detail', slug=course.slug)


@login_required
def dashboard(request):
    """Panel de control del usuario optimizado"""
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
    
    context = {
        'enrollment_stats': enrollment_stats,
        'taught_courses': taught_courses,
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
    
    return render(request, 'courses/manage_courses.html', {'courses': courses})


@login_required
def create_course(request):
    """Crear un nuevo curso"""
    if not hasattr(request.user, 'cv'):
        messages.error(request, 'Necesitas un perfil de tutor')
        return redirect('cv:detail')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.tutor = request.user
            course.save()
            messages.success(request, 'Curso creado exitosamente')
            return redirect('courses:manage_courses')
    else:
        form = CourseForm()
    
    return render(request, 'courses/course_form.html', {
        'form': form,
        'title': 'Crear Nuevo Curso',
    })


@login_required
def edit_course(request, slug):
    """Editar un curso existente"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado exitosamente')
            return redirect('courses:manage_courses')
    else:
        form = CourseForm(instance=course)
    
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