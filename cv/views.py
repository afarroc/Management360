# views.py - Versión con formsets opcionales (extra=0)

from django.views.generic import View, DetailView, FormView, CreateView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.forms import modelformset_factory
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
import logging

from .models import (
    Curriculum, Experience, Education, Skill,
    Language, Certification, Document, Image, Database
)
from .forms import (
    CurriculumForm, ExperienceForm, EducationForm, SkillForm,
    LanguageForm, CertificationForm, DocumentForm, ImageForm, DatabaseForm
)

# Importación de managers (se asume que existen)
from events.management.event_manager import EventManager
from events.management.project_manager import ProjectManager
from events.management.task_manager import TaskManager
from events.models import Task, Project, Event, EventAttendee

logger = logging.getLogger(__name__)


# =============================================================================
# MIXINS - Lógica reutilizable
# =============================================================================

class CorporateDataMixin:
    """
    Mixin para manejar datos corporativos usando los managers específicos.
    """

    def get_user_metrics(self, user):
        """Retorna métricas resumidas del usuario usando los managers."""
        event_manager = EventManager(user)
        project_manager = ProjectManager(user)
        task_manager = TaskManager(user)

        tasks, active_tasks = task_manager.get_all_tasks()
        projects, active_projects = project_manager.get_all_projects()
        events, active_events = event_manager.get_all_events()

        # Calcular tareas completadas
        tasks_completed = sum(1 for task_data in tasks if task_data.get('task') and task_data['task'].done)

        return {
            'tasks_completed': tasks_completed,
            'projects_active': len(active_projects),
            'events_attended': len(active_events),
            'total_tasks': len(tasks),
            'total_projects': len(projects),
            'total_events': len(events),
        }

    def get_active_projects(self, user, limit=5):
        """Retorna proyectos con su progreso."""
        STATUS_COLOR_MAP = {
            'planning': 'warning',
            'in progress': 'primary',
            'in_progress': 'primary',
            'review': 'info',
            'completed': 'success',
            'cancelled': 'danger',
            'to do': 'secondary',
            'todo': 'secondary',
            'draft': 'secondary',
            'created': 'secondary'
        }

        project_manager = ProjectManager(user)
        projects, active_projects = project_manager.get_all_projects()
        
        # Usar TODOS los proyectos, no solo los activos
        all_projects = projects

        active_projects_list = []
        for project_data in all_projects[:limit]:
            project = project_data.get('project')
            if not project:
                continue

            total_tasks = project_data.get('count_tasks', 0)
            completed_tasks = Task.objects.filter(project=project, done=True).count()
            progress = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)

            status_name = ''
            if project.project_status:
                status_name = project.project_status.status_name.lower().replace(' ', '_')
            status_color = STATUS_COLOR_MAP.get(status_name, 'secondary')

            role = self._get_user_project_role(user, project)

            active_projects_list.append({
                'id': project.id,
                'name': project.title,
                'description': project.description or 'Sin descripción',
                'role': role,
                'start_date': project.created_at,
                'status': project.project_status.status_name if project.project_status else 'Activo',
                'status_color': status_color,
                'progress': progress,
                'team_size': project.attendees.count() if hasattr(project, 'attendees') else 0,
                'detail_url': reverse('project_detail', args=[project.id]),
                'edit_url': reverse('project_edit', args=[project.id]),
            })

        return active_projects_list

    def _get_user_project_role(self, user, project):
        """Determina el rol del usuario en el proyecto."""
        if project.host == user:
            return 'Host'
        elif hasattr(project, 'assigned_to') and project.assigned_to == user:
            return 'Responsable'
        elif hasattr(project, 'attendees') and user in project.attendees.all():
            return 'Participante'
        else:
            return 'Colaborador'

    def get_recent_activities(self, user, limit=5, days=30):
        """Retorna actividades recientes del usuario."""
        since = timezone.now() - timezone.timedelta(days=days)
        activities = []

        # Tareas recientes
        task_manager = TaskManager(user)
        tasks, _ = task_manager.get_all_tasks()
        task_count = 0
        for task_data in tasks:
            if task_count >= 3:
                break
            task = task_data.get('task')
            if task and task.updated_at and task.updated_at >= since:
                activities.append(self._create_activity_item(
                    'task',
                    f"Tarea: {task.title}",
                    task.description or 'Tarea actualizada',
                    task.updated_at,
                    'check-circle' if getattr(task, 'done', False) else 'circle',
                    'success' if getattr(task, 'done', False) else 'primary',
                    reverse('tasks_with_id', args=[task.id]) if hasattr(task, 'id') else None
                ))
                task_count += 1

        # Proyectos recientes
        project_manager = ProjectManager(user)
        projects, _ = project_manager.get_all_projects()
        project_count = 0
        for project_data in projects:
            if project_count >= 2:
                break
            project = project_data.get('project')
            if project and project.updated_at and project.updated_at >= since:
                activities.append(self._create_activity_item(
                    'project',
                    f"Proyecto: {project.title}",
                    f"Estado: {project.project_status.status_name if project.project_status else 'Actualizado'}",
                    project.updated_at,
                    'folder',
                    'info',
                    reverse('project_detail', args=[project.id])
                ))
                project_count += 1

        # Eventos recientes
        event_manager = EventManager(user)
        events, _ = event_manager.get_all_events()
        event_count = 0
        for event_data in events:
            if event_count >= 2:
                break
            event = event_data.get('event')
            if event and event.updated_at and event.updated_at >= since:
                activities.append(self._create_activity_item(
                    'event',
                    f"Evento: {event.title}",
                    event.description or 'Participación en evento',
                    event.updated_at,
                    'calendar',
                    'warning',
                    reverse('event_detail', args=[event.id])
                ))
                event_count += 1

        activities.sort(key=lambda x: x['date'], reverse=True)
        return activities[:limit]

    def _create_activity_item(self, type, title, description, date, icon, color, url=None):
        """Crea un item de actividad estructurado."""
        return {
            'type': type,
            'title': title,
            'description': description,
            'date': date,
            'icon': icon,
            'color': color,
            'url': url
        }


class FileManagementMixin(LoginRequiredMixin):
    """
    Mixin para manejo de archivos.
    """
    models_map = {
        'document': Document,
        'image': Image,
        'database': Database
    }

    def get_cv(self, user):
        """Obtiene el CV del usuario."""
        return get_object_or_404(Curriculum, user=user)

    def get_file_model(self, file_type):
        """Retorna el modelo correspondiente al tipo de archivo."""
        return self.models_map.get(file_type)


# =============================================================================
# VISTAS PRINCIPALES DEL CV
# =============================================================================

class CurriculumDetailView(LoginRequiredMixin, DetailView, CorporateDataMixin):
    """
    Vista principal del perfil corporativo.
    Si el usuario no tiene CV, redirige a la página de creación.
    """
    model = Curriculum
    template_name = 'cv/corporate_profile.html'
    context_object_name = 'cv'

    def get_object(self, queryset=None):
        """Intenta obtener el CV o retorna None si no existe."""
        try:
            return Curriculum.objects.get(user=self.request.user)
        except Curriculum.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        """Verifica si existe CV antes de mostrar la vista."""
        self.object = self.get_object()

        if self.object is None:
            messages.warning(request, 'Completa tu perfil profesional para continuar.')
            return redirect('cv:cv_create')

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        """Añade datos corporativos al contexto."""
        context = super().get_context_data(**kwargs)
        cv = self.object
        user = self.request.user

        # Datos corporativos usando managers
        metrics = self.get_user_metrics(user)
        active_projects = self.get_active_projects(user)
        recent_activities = self.get_recent_activities(user)

        context.update({
            'corporate_data_available': True,
            'metrics': metrics,
            'active_projects': active_projects,
            'recent_activities': recent_activities,
        })

        # Datos del CV
        context.update({
            'certifications_count': cv.certifications.count(),
            'education_count': cv.educations.count(),
            'experience_count': cv.experiences.count(),
            'skills_count': cv.skills_list.count(),
            'languages_count': cv.languages.count(),
        })

        return context


class CurriculumCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear un CV cuando el usuario no tiene uno.
    """
    model = Curriculum
    form_class = CurriculumForm
    template_name = 'cv/curriculum_create.html'
    success_url = reverse_lazy('cv:cv_detail')

    def dispatch(self, request, *args, **kwargs):
        """Verifica si el usuario ya tiene CV antes de procesar la request."""
        if Curriculum.objects.filter(user=request.user).exists():
            messages.info(request, 'Ya tienes un perfil profesional creado.')
            return redirect('cv:cv_detail')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Asigna el usuario actual al CV antes de guardar."""
        form.instance.user = self.request.user
        messages.success(self.request, '¡Perfil creado exitosamente! Ahora puedes completar tu información.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_creating'] = True
        context['title'] = 'Crear Perfil Profesional'
        return context


class CurriculumUpdateView(LoginRequiredMixin, View):
    """
    Vista para editar el CV completo con todos sus formsets (AHORA OPCIONALES).
    """
    template_name = 'cv/curriculum_form.html'
    success_url = reverse_lazy('cv:cv_detail')

    def dispatch(self, request, *args, **kwargs):
        """Verifica que el usuario tenga CV antes de editar."""
        if not Curriculum.objects.filter(user=request.user).exists():
            messages.warning(request, 'Debes crear tu perfil profesional primero.')
            return redirect('cv:cv_create')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        cv = self._get_cv(request.user)
        context = self._build_context(cv)
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request):
        cv = self._get_cv(request.user)
        form = CurriculumForm(request.POST, request.FILES, instance=cv)
        
        # Crear formsets con extra=0 para que sean OPCIONALES
        ExperienceFormSet = modelformset_factory(
            Experience, 
            form=ExperienceForm, 
            extra=0,  # ← CAMBIADO: no muestra formularios vacíos
            can_delete=True
        )
        EducationFormSet = modelformset_factory(
            Education, 
            form=EducationForm, 
            extra=0,  # ← CAMBIADO
            can_delete=True
        )
        SkillFormSet = modelformset_factory(
            Skill, 
            form=SkillForm, 
            extra=0,  # ← CAMBIADO
            can_delete=True
        )
        LanguageFormSet = modelformset_factory(
            Language, 
            form=LanguageForm, 
            extra=0,  # ← CAMBIADO
            can_delete=True
        )
        CertificationFormSet = modelformset_factory(
            Certification, 
            form=CertificationForm, 
            extra=0,  # ← CAMBIADO
            can_delete=True
        )
        
        experience_formset = ExperienceFormSet(
            request.POST,
            prefix='experiences',
            queryset=cv.experiences.all()
        )
        education_formset = EducationFormSet(
            request.POST,
            prefix='education',
            queryset=cv.educations.all()
        )
        skill_formset = SkillFormSet(
            request.POST,
            prefix='skills',
            queryset=cv.skills_list.all()
        )
        language_formset = LanguageFormSet(
            request.POST,
            prefix='languages',
            queryset=cv.languages.all()
        )
        certification_formset = CertificationFormSet(
            request.POST,
            prefix='certifications',
            queryset=cv.certifications.all()
        )
        
        formsets = {
            'experience_formset': experience_formset,
            'education_formset': education_formset,
            'skill_formset': skill_formset,
            'language_formset': language_formset,
            'certification_formset': certification_formset
        }

        # Validar formulario principal y todos los formsets
        if form.is_valid() and all(fs.is_valid() for fs in formsets.values()):
            form.save()
            
            # Guardar cada formset (pueden estar vacíos)
            for formset in formsets.values():
                instances = formset.save(commit=False)
                for obj in instances:
                    obj.cv = cv
                    obj.save()
                for obj in formset.deleted_objects:
                    obj.delete()
                    
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect(self.success_url)

        context = self._build_context(cv, form, formsets)
        return render(request, self.template_name, context)

    def _get_cv(self, user):
        """Obtiene o crea 404 si no existe."""
        return get_object_or_404(Curriculum, user=user)

    def _build_context(self, cv, form=None, formsets=None):
        """Construye el contexto para el template."""
        context = {'cv': cv}
        context['form'] = form or CurriculumForm(instance=cv)
        
        if formsets is None:
            # Crear formsets vacíos con extra=0 para la vista GET
            ExperienceFormSet = modelformset_factory(
                Experience, 
                form=ExperienceForm, 
                extra=0,  # ← CAMBIADO
                can_delete=True
            )
            EducationFormSet = modelformset_factory(
                Education, 
                form=EducationForm, 
                extra=0,  # ← CAMBIADO
                can_delete=True
            )
            SkillFormSet = modelformset_factory(
                Skill, 
                form=SkillForm, 
                extra=0,  # ← CAMBIADO
                can_delete=True
            )
            LanguageFormSet = modelformset_factory(
                Language, 
                form=LanguageForm, 
                extra=0,  # ← CAMBIADO
                can_delete=True
            )
            CertificationFormSet = modelformset_factory(
                Certification, 
                form=CertificationForm, 
                extra=0,  # ← CAMBIADO
                can_delete=True
            )
            
            context['experience_formset'] = ExperienceFormSet(
                prefix='experiences',
                queryset=cv.experiences.all()
            )
            context['education_formset'] = EducationFormSet(
                prefix='education',
                queryset=cv.educations.all()
            )
            context['skill_formset'] = SkillFormSet(
                prefix='skills',
                queryset=cv.skills_list.all()
            )
            context['language_formset'] = LanguageFormSet(
                prefix='languages',
                queryset=cv.languages.all()
            )
            context['certification_formset'] = CertificationFormSet(
                prefix='certifications',
                queryset=cv.certifications.all()
            )
        else:
            context.update(formsets)
            
        return context


class PublicCurriculumView(DetailView):
    """
    Vista pública del CV.
    Muestra un mensaje si el usuario no tiene CV.
    """
    model = Curriculum
    template_name = 'cv/view_curriculum.html'
    context_object_name = 'cv'
    pk_url_kwarg = 'user_id'

    def get(self, request, *args, **kwargs):
        """Manejo elegante cuando el CV no existe."""
        try:
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)
        except Curriculum.DoesNotExist:
            return render(request, 'cv/curriculum_not_found.html', {
                'user_id': kwargs.get('user_id'),
                'message': 'El usuario no ha creado su perfil profesional aún.'
            }, status=404)

    def get_object(self, queryset=None):
        return get_object_or_404(Curriculum, user_id=self.kwargs['user_id'])


# =============================================================================
# VISTAS DE GESTIÓN DE ARCHIVOS
# =============================================================================

class FileUploadView(FileManagementMixin, FormView):
    """
    Vista base para subida de archivos.
    """
    template_name = 'cv/documents/upload.html'
    success_url = reverse_lazy('cv:docsview')

    def dispatch(self, request, *args, **kwargs):
        """Verifica que el usuario tenga CV antes de subir archivos."""
        if not Curriculum.objects.filter(user=request.user).exists():
            messages.warning(request, 'Debes crear tu perfil profesional antes de subir archivos.')
            return redirect('cv:cv_create')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        file = form.cleaned_data['file']
        self.model.objects.create(upload=file, cv=self.get_cv(self.request.user))
        messages.success(self.request, 'Archivo subido correctamente')
        return super().form_valid(form)


class DocumentUploadView(FileUploadView):
    """Subida de documentos PDF/DOCX/PPT"""
    form_class = DocumentForm
    model = Document


class ImageUploadView(FileUploadView):
    """Subida de imágenes JPG/PNG"""
    form_class = ImageForm
    model = Image


class DatabaseUploadView(FileUploadView):
    """Subida de archivos de datos CSV/XLSX"""
    form_class = DatabaseForm
    model = Database


class FileDeleteView(FileManagementMixin, View):
    """
    Eliminación de archivos.
    """
    def post(self, request, file_type, file_id):
        model = self.get_file_model(file_type)

        if not model:
            messages.error(request, 'Tipo de archivo no válido')
            return redirect('cv:docsview')

        file_instance = get_object_or_404(
            model, id=file_id, cv__user=request.user
        )
        file_instance.delete()
        messages.success(request, 'Archivo eliminado correctamente')
        return redirect('cv:docsview')


class DocumentListView(LoginRequiredMixin, View):
    """
    Listado de todos los archivos del usuario.
    """
    template_name = 'cv/documents/docsview.html'

    def dispatch(self, request, *args, **kwargs):
        """Verifica que el usuario tenga CV antes de listar archivos."""
        if not Curriculum.objects.filter(user=request.user).exists():
            messages.warning(request, 'Debes crear tu perfil profesional para ver tus archivos.')
            return redirect('cv:cv_create')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        cv = get_object_or_404(Curriculum, user=request.user)
        context = {
            'documents': cv.documents.all(),
            'images': cv.images.all(),
            'databases': cv.databases.all(),
        }
        return render(request, self.template_name, context)


class EditPersonalInfoView(LoginRequiredMixin, UpdateView):
    """Vista para editar información personal"""
    model = Curriculum
    form_class = CurriculumForm
    template_name = 'cv/edit_section.html'
    
    def get_object(self, queryset=None):
        return get_object_or_404(Curriculum, user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Editar Información Personal',
            'form_title': 'Información Personal',
            'form_icon': 'person',
            'required_fields': True,
            'submit_text': 'Guardar y Continuar',
            'current_step': 1,
            'total_steps': 5,
            'progress_percentage': 20,
            'prev_url': None,
        })
        return context
    
    def get_success_url(self):
        return reverse('cv:edit_experience')


class EditExperienceView(LoginRequiredMixin, View):
    """Vista para editar experiencia laboral (AHORA OPCIONAL)"""
    template_name = 'cv/edit_section.html'
    
    def get(self, request):
        cv = get_object_or_404(Curriculum, user=request.user)
        ExperienceFormSet = modelformset_factory(
            Experience, 
            form=ExperienceForm, 
            extra=0,  # ← CAMBIADO: no muestra formularios vacíos
            can_delete=True
        )
        formset = ExperienceFormSet(
            prefix='experiences',
            queryset=cv.experiences.all()
        )
        
        context = {
            'page_title': 'Editar Experiencia Laboral',
            'formset': formset,
            'formset_title': 'Experiencia Laboral',
            'formset_icon': 'briefcase',
            'add_text': 'experiencia',
            'submit_text': 'Guardar y Continuar',
            'current_step': 2,
            'total_steps': 5,
            'progress_percentage': 40,
            'prev_url': reverse('cv:edit_personal'),
            'is_optional_section': True,  # ← NUEVO: indica que es opcional
        }
        return render(request, self.template_name, context)
    
    @transaction.atomic
    def post(self, request):
        cv = get_object_or_404(Curriculum, user=request.user)
        ExperienceFormSet = modelformset_factory(
            Experience, 
            form=ExperienceForm, 
            extra=0,  # ← CAMBIADO
            can_delete=True
        )
        formset = ExperienceFormSet(
            request.POST,
            prefix='experiences',
            queryset=cv.experiences.all()
        )
        
        if formset.is_valid():
            instances = formset.save(commit=False)
            for obj in instances:
                obj.cv = cv
                obj.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, 'Experiencia guardada correctamente')
            return redirect('cv:edit_education')
        
        context = {
            'page_title': 'Editar Experiencia Laboral',
            'formset': formset,
            'formset_title': 'Experiencia Laboral',
            'formset_icon': 'briefcase',
            'add_text': 'experiencia',
            'submit_text': 'Guardar y Continuar',
            'current_step': 2,
            'total_steps': 5,
            'progress_percentage': 40,
            'prev_url': reverse('cv:edit_personal'),
            'is_optional_section': True,
        }
        return render(request, self.template_name, context)


class EditEducationView(LoginRequiredMixin, View):
    """Vista para editar educación (AHORA OPCIONAL)"""
    template_name = 'cv/edit_section.html'
    
    def get(self, request):
        cv = get_object_or_404(Curriculum, user=request.user)
        EducationFormSet = modelformset_factory(
            Education, 
            form=EducationForm, 
            extra=0,  # ← CAMBIADO
            can_delete=True
        )
        formset = EducationFormSet(
            prefix='education',
            queryset=cv.educations.all()
        )
        
        context = {
            'page_title': 'Editar Educación',
            'formset': formset,
            'formset_title': 'Educación',
            'formset_icon': 'mortarboard',
            'add_text': 'educación',
            'submit_text': 'Guardar y Continuar',
            'current_step': 3,
            'total_steps': 5,
            'progress_percentage': 60,
            'prev_url': reverse('cv:edit_experience'),
            'is_optional_section': True,  # ← NUEVO
        }
        return render(request, self.template_name, context)
    
    @transaction.atomic
    def post(self, request):
        cv = get_object_or_404(Curriculum, user=request.user)
        EducationFormSet = modelformset_factory(
            Education, 
            form=EducationForm, 
            extra=0,  # ← CAMBIADO
            can_delete=True
        )
        formset = EducationFormSet(
            request.POST,
            prefix='education',
            queryset=cv.educations.all()
        )
        
        if formset.is_valid():
            instances = formset.save(commit=False)
            for obj in instances:
                obj.cv = cv
                obj.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, 'Educación guardada correctamente')
            return redirect('cv:edit_skills')
        
        context = {
            'page_title': 'Editar Educación',
            'formset': formset,
            'formset_title': 'Educación',
            'formset_icon': 'mortarboard',
            'add_text': 'educación',
            'submit_text': 'Guardar y Continuar',
            'current_step': 3,
            'total_steps': 5,
            'progress_percentage': 60,
            'prev_url': reverse('cv:edit_experience'),
            'is_optional_section': True,
        }
        return render(request, self.template_name, context)


class EditSkillsView(LoginRequiredMixin, View):
    """Vista para editar habilidades (AHORA OPCIONAL)"""
    template_name = 'cv/edit_section.html'
    
    def get(self, request):
        cv = get_object_or_404(Curriculum, user=request.user)
        SkillFormSet = modelformset_factory(
            Skill, 
            form=SkillForm, 
            extra=0,  # ← CAMBIADO
            can_delete=True
        )
        formset = SkillFormSet(
            prefix='skills',
            queryset=cv.skills_list.all()
        )
        
        context = {
            'page_title': 'Editar Habilidades',
            'formset': formset,
            'formset_title': 'Habilidades',
            'formset_icon': 'star',
            'add_text': 'habilidad',
            'submit_text': 'Guardar y Finalizar',
            'current_step': 4,
            'total_steps': 5,
            'progress_percentage': 80,
            'prev_url': reverse('cv:edit_education'),
            'is_optional_section': True,  # ← NUEVO
        }
        return render(request, self.template_name, context)
    
    @transaction.atomic
    def post(self, request):
        cv = get_object_or_404(Curriculum, user=request.user)
        SkillFormSet = modelformset_factory(
            Skill, 
            form=SkillForm, 
            extra=0,  # ← CAMBIADO
            can_delete=True
        )
        formset = SkillFormSet(
            request.POST,
            prefix='skills',
            queryset=cv.skills_list.all()
        )
        
        if formset.is_valid():
            instances = formset.save(commit=False)
            for obj in instances:
                obj.cv = cv
                obj.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, 'Habilidades guardadas correctamente')
            return redirect('cv:cv_detail')
        
        context = {
            'page_title': 'Editar Habilidades',
            'formset': formset,
            'formset_title': 'Habilidades',
            'formset_icon': 'star',
            'add_text': 'habilidad',
            'submit_text': 'Guardar y Finalizar',
            'current_step': 4,
            'total_steps': 5,
            'progress_percentage': 80,
            'prev_url': reverse('cv:edit_education'),
            'is_optional_section': True,
        }
        return render(request, self.template_name, context)


class TraditionalProfileView(LoginRequiredMixin, DetailView):
    """
    Vista del CV en formato tradicional (estilo Harvard/clásico).
    """
    model = Curriculum
    template_name = 'cv/traditional_profile.html'
    context_object_name = 'cv'

    def get_object(self, queryset=None):
        # Permite ver el CV propio o de otro usuario si es público (ajustar según necesidades)
        user_id = self.kwargs.get('user_id')
        if user_id:
            return get_object_or_404(Curriculum, user_id=user_id)
        # Si no se pasa user_id, muestra el del usuario autenticado
        return get_object_or_404(Curriculum, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cv = self.object
        # Agregar datos relacionados (ya están disponibles a través de related names)
        # También podemos agregar alguna lógica adicional si es necesaria
        return context