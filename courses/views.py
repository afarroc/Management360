from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.utils import timezone
from .models import (
    Course, Module, Lesson, Enrollment, 
    Progress, Review, CourseCategory,
    CourseLevelChoices, EnrollmentStatusChoices, LessonTypeChoices  # Importar las clases de choices
)
from .forms import CourseForm, ModuleForm, LessonForm, ReviewForm

def course_list(request):
    """Lista todos los cursos disponibles"""
    courses = Course.objects.filter(is_published=True)
    
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
    
    # Obtener categorías para el filtro
    categories = CourseCategory.objects.all()
    
    context = {
        'courses': courses,
        'categories': categories,
        'levels': CourseLevelChoices.choices,  # Ahora está correctamente importado
        'selected_category': category,
        'selected_level': level,
        'search_query': search or ''
    }
    return render(request, 'courses/course_list.html', context)

def course_detail(request, slug):
    """Detalle de un curso específico"""
    course = get_object_or_404(Course, slug=slug, is_published=True)
    
    # Verificar si el usuario está inscrito
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(
            student=request.user, 
            course=course, 
            status=EnrollmentStatusChoices.ACTIVE
        ).exists()
    
    # Obtener reseñas
    reviews = course.reviews.all().order_by('-created_at')[:5]
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'reviews': reviews,
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
def enroll(request, course_id):
    """Inscribir a un usuario en un curso"""
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    # Verificar si ya está inscrito
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'status': EnrollmentStatusChoices.ACTIVE}
    )
    
    if not created:
        messages.info(request, f'Ya estás inscrito en el curso "{course.title}"')
    else:
        messages.success(request, f'Te has inscrito correctamente en "{course.title}"')
    
    return redirect('course_detail', slug=course.slug)

@login_required
def dashboard(request):
    """Panel de control del usuario (tanto estudiante como tutor)"""
    user_enrollments = Enrollment.objects.filter(
        student=request.user, 
        status=EnrollmentStatusChoices.ACTIVE
    ).select_related('course')
    
    # Cursos del usuario como tutor
    taught_courses = Course.objects.filter(tutor=request.user)
    
    # Progreso en cada curso
    for enrollment in user_enrollments:
        total_lessons = Lesson.objects.filter(module__course=enrollment.course).count()
        completed_lessons = Progress.objects.filter(
            enrollment=enrollment, 
            completed=True
        ).count()
        enrollment.progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    context = {
        'enrollments': user_enrollments,
        'taught_courses': taught_courses,
    }
    return render(request, 'courses/dashboard.html', context)

@login_required
def course_learning(request, slug, lesson_id=None):
    """Vista para aprender un curso (acceder a las lecciones)"""
    course = get_object_or_404(Course, slug=slug)
    enrollment = get_object_or_404(
        Enrollment, 
        student=request.user, 
        course=course, 
        status=EnrollmentStatusChoices.ACTIVE
    )
    
    # Obtener módulos y lecciones
    modules = Module.objects.filter(course=course).prefetch_related('lessons')
    
    # Obtener lección actual o la primera lección
    if lesson_id:
        current_lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    else:
        first_lesson = Lesson.objects.filter(module__course=course).order_by('module__order', 'order').first()
        if first_lesson:
            # CORRECCIÓN: Usar el nombre completo con namespace
            return redirect('courses:course_learning_lesson', slug=slug, lesson_id=first_lesson.id)
        current_lesson = None
    
    # Obtener progreso de la lección actual
    lesson_progress = None
    if current_lesson:
        lesson_progress, created = Progress.objects.get_or_create(
            enrollment=enrollment,
            lesson=current_lesson
        )
    
    context = {
        'course': course,
        'modules': modules,
        'current_lesson': current_lesson,
        'lesson_progress': lesson_progress,
        'enrollment': enrollment,
    }
    return render(request, 'courses/course_learning.html', context)

@login_required
def mark_lesson_complete(request, lesson_id):
    """Marcar una lección como completada (AJAX)"""
    if request.method == 'POST' and request.is_ajax():
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
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'})

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
            messages.success(request, 'Tu reseña ha sido publicada')
            return redirect('course_detail', slug=course.slug)
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'courses/add_review.html', context)

# ======================
# VISTAS PARA TUTORES
# ======================
@login_required
def manage_courses(request):
    """Gestión de cursos para tutores"""
    if not hasattr(request.user, 'cv'):
        messages.error(request, 'Necesitas un perfil de tutor para gestionar cursos')
        return redirect('cv:detail')
    
    courses = Course.objects.filter(tutor=request.user)
    context = {
        'courses': courses,
    }
    return render(request, 'courses/manage_courses.html', context)

@login_required
def create_course(request):
    """Crear un nuevo curso"""
    if not hasattr(request.user, 'cv'):
        messages.error(request, 'Necesitas un perfil de tutor para crear cursos')
        return redirect('cv:detail')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.tutor = request.user
            course.save()
            messages.success(request, 'Curso creado exitosamente')
            return redirect('manage_courses')
    else:
        form = CourseForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Curso',
    }
    return render(request, 'courses/course_form.html', context)

@login_required
def edit_course(request, slug):
    """Editar un curso existente"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado exitosamente')
            return redirect('manage_courses')
    else:
        form = CourseForm(instance=course)
    
    context = {
        'form': form,
        'title': 'Editar Curso',
        'course': course,
    }
    return render(request, 'courses/course_form.html', context)

@login_required
def course_analytics(request, slug):
    """Analíticas de un curso para el tutor"""
    course = get_object_or_404(Course, slug=slug, tutor=request.user)
    
    # Estadísticas básicas
    total_students = course.enrollments.filter(status=EnrollmentStatusChoices.ACTIVE).count()
    completed_students = course.enrollments.filter(status=EnrollmentStatusChoices.COMPLETED).count()
    
    # Progreso promedio
    enrollments = course.enrollments.filter(status=EnrollmentStatusChoices.ACTIVE)
    progress_data = []
    
    for enrollment in enrollments:
        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_lessons = Progress.objects.filter(
            enrollment=enrollment, 
            completed=True
        ).count()
        progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        progress_data.append({
            'student': enrollment.student,
            'progress': progress_percentage
        })
    
    context = {
        'course': course,
        'total_students': total_students,
        'completed_students': completed_students,
        'progress_data': progress_data,
    }
    return render(request, 'courses/course_analytics.html', context)