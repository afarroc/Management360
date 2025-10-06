from django.views.generic import View, FormView, DetailView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.forms import modelformset_factory
from django.db import transaction
from .models import Curriculum, Experience, Education, Skill, Language, Certification, Document, Image, Database
from .forms import (
    CurriculumForm, ExperienceForm, EducationForm, SkillForm,
    LanguageForm, CertificationForm, DocumentForm, ImageForm, DatabaseForm
)

# Importar modelos de otras apps para métricas reales
try:
    from events.models import Task, Project, Event, EventAttendee
    EVENTS_MODELS_AVAILABLE = True
except ImportError:
    EVENTS_MODELS_AVAILABLE = False

class CurriculumDetailView(LoginRequiredMixin, DetailView):
    model = Curriculum
    template_name = 'cv/corporate_profile.html'  # Cambiado a vista corporativa
    context_object_name = 'cv'

    def get_object(self):
        return get_object_or_404(Curriculum, user=self.request.user)

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        context = super().get_context_data(**kwargs)
        cv = self.get_object()
        user = self.request.user

        # Métricas corporativas basadas en datos reales
        if EVENTS_MODELS_AVAILABLE:
            # Tareas completadas por el usuario
            context['tasks_completed'] = Task.objects.filter(
                assigned_to=user,
                done=True
            ).count()

            # Proyectos activos asignados al usuario
            context['projects_active'] = Project.objects.filter(
                assigned_to=user,
                done=False
            ).count()

            # Eventos a los que ha asistido
            context['events_attended'] = EventAttendee.objects.filter(
                user=user
            ).count()

            # Proyectos activos reales
            active_projects_queryset = Project.objects.filter(
                assigned_to=user,
                done=False
            ).select_related('project_status')[:5]  # Limitar a 5 proyectos

            context['active_projects'] = []
            for project in active_projects_queryset:
                # Calcular progreso basado en tareas completadas
                total_tasks = Task.objects.filter(project=project).count()
                completed_tasks = Task.objects.filter(project=project, done=True).count()
                progress = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)

                # Determinar color del estado
                status_color_map = {
                    'planning': 'warning',
                    'in_progress': 'primary',
                    'review': 'info',
                    'completed': 'success',
                    'cancelled': 'danger'
                }
                status_color = status_color_map.get(
                    project.project_status.status_name.lower().replace(' ', '_'),
                    'secondary'
                )

                context['active_projects'].append({
                    'name': project.title,
                    'description': project.description or 'Sin descripción',
                    'role': 'Project Manager',  # Podría ser dinámico basado en el rol del usuario
                    'start_date': project.created_at.strftime('%Y-%m-%d'),
                    'status': project.project_status.status_name,
                    'status_color': status_color,
                    'progress': progress
                })

            # Actividades recientes basadas en datos reales
            recent_activities = []

            # Tareas completadas recientemente
            recent_completed_tasks = Task.objects.filter(
                assigned_to=user,
                done=True,
                updated_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).order_by('-updated_at')[:3]

            for task in recent_completed_tasks:
                recent_activities.append({
                    'title': f'Completó tarea: {task.title}',
                    'description': task.description or 'Tarea completada exitosamente',
                    'date': task.updated_at
                })

            # Proyectos actualizados recientemente
            recent_project_updates = Project.objects.filter(
                assigned_to=user,
                updated_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).order_by('-updated_at')[:2]

            for project in recent_project_updates:
                recent_activities.append({
                    'title': f'Actualizó proyecto: {project.title}',
                    'description': f'Proyecto actualizado - Estado: {project.project_status.status_name}',
                    'date': project.updated_at
                })

            # Eventos asistidos recientemente
            recent_events = EventAttendee.objects.filter(
                user=user,
                event__created_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).select_related('event').order_by('-event__created_at')[:2]

            for attendee in recent_events:
                recent_activities.append({
                    'title': f'Asistió a evento: {attendee.event.title}',
                    'description': attendee.event.description or 'Participación en evento corporativo',
                    'date': attendee.registration_time
                })

            # Ordenar actividades por fecha y tomar las más recientes
            recent_activities.sort(key=lambda x: x['date'], reverse=True)
            context['recent_activities'] = recent_activities[:5]  # Máximo 5 actividades

        else:
            # Fallback a datos simulados si no están disponibles las apps
            context['tasks_completed'] = 0
            context['projects_active'] = 0
            context['events_attended'] = 0
            context['active_projects'] = []
            context['recent_activities'] = []

        # Certificaciones (siempre disponible)
        context['certifications_count'] = cv.certifications.count()

        return context

class CurriculumUpdateView(LoginRequiredMixin, View):
    template_name = 'cv/curriculum_form.html'
    success_url = reverse_lazy('cv_detail')

    def get_formsets(self, cv):
        ExperienceFormSet = modelformset_factory(
            Experience, form=ExperienceForm, extra=1, can_delete=True
        )
        EducationFormSet = modelformset_factory(
            Education, form=EducationForm, extra=1, can_delete=True
        )
        SkillFormSet = modelformset_factory(
            Skill, form=SkillForm, extra=1, can_delete=True
        )
        LanguageFormSet = modelformset_factory(
            Language, form=LanguageForm, extra=1, can_delete=True
        )
        CertificationFormSet = modelformset_factory(
            Certification, form=CertificationForm, extra=1, can_delete=True
        )

        return {
            'experience_formset': ExperienceFormSet(
                prefix='experiences',
                queryset=cv.experiences.all()
            ),
            'education_formset': EducationFormSet(
                prefix='education',
                queryset=cv.educations.all()
            ),
            'skill_formset': SkillFormSet(
                prefix='skills',
                queryset=cv.skills_list.all()
            ),
            'language_formset': LanguageFormSet(
                prefix='languages',
                queryset=cv.languages.all()
            ),
            'certification_formset': CertificationFormSet(
                prefix='certifications',
                queryset=cv.certifications.all()
            )
        }

    def get(self, request):
        cv = get_object_or_404(Curriculum, user=request.user)
        context = {
            'form': CurriculumForm(instance=cv),
            'cv': cv,
            **self.get_formsets(cv)
        }
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request):
        cv = get_object_or_404(Curriculum, user=request.user)
        form = CurriculumForm(request.POST, request.FILES, instance=cv)
        formsets = self.get_formsets(cv)

        if form.is_valid() and all(fs.is_valid() for fs in formsets.values()):
            form.save()
            self.save_formsets(cv, formsets)
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect(self.success_url)

        context = {'form': form, 'cv': cv, **formsets}
        return render(request, self.template_name, context)

    def save_formsets(self, cv, formsets):
        for formset in formsets.values():
            instances = formset.save(commit=False)
            for obj in instances:
                obj.cv = cv
                obj.save()
            for obj in formset.deleted_objects:
                obj.delete()

class PublicCurriculumView(DetailView):
    model = Curriculum
    template_name = 'cv/view_curriculum.html'
    context_object_name = 'cv'
    pk_url_kwarg = 'user_id'

    def get_object(self):
        return get_object_or_404(Curriculum, user_id=self.kwargs['user_id'])

class FileUploadView(LoginRequiredMixin, FormView):
    template_name = 'cv/documents/upload.html'
    success_url = reverse_lazy('cv:docsview')

    def form_valid(self, form):
        file = form.cleaned_data['file']
        self.model.objects.create(upload=file, cv=self.get_cv())
        messages.success(self.request, 'Archivo subido correctamente')
        return super().form_valid(form)

    def get_cv(self):
        return get_object_or_404(Curriculum, user=self.request.user)

class DocumentUploadView(FileUploadView):
    form_class = DocumentForm
    model = Document

class ImageUploadView(FileUploadView):
    form_class = ImageForm
    model = Image

class DatabaseUploadView(FileUploadView):
    form_class = DatabaseForm
    model = Database

class FileDeleteView(LoginRequiredMixin, View):
    models = {
        'document': Document,
        'image': Image,
        'database': Database
    }

    def post(self, request, file_type, file_id):
        model = self.models.get(file_type)
        if not model:
            messages.error(request, 'Tipo de archivo no válido')
            return redirect('docsview')

        file_instance = get_object_or_404(model, id=file_id, cv__user=request.user)
        file_instance.delete()
        messages.success(request, 'Archivo eliminado correctamente')
        return redirect('docsview')

class DocumentListView(LoginRequiredMixin, View):
    def get(self, request):
        cv = get_object_or_404(Curriculum, user=request.user)
        context = {
            'documents': cv.documents.all(),
            'images': cv.images.all(),
            'databases': cv.databases.all(),
        }
        return render(request, 'cv/documents/docsview.html', context)