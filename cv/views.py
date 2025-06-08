from django.views.generic import View, FormView, DetailView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.forms import modelformset_factory
from django.db import transaction
from .models import Curriculum, Experience, Education, Skill, Document, Image, Database
from .forms import (
    CurriculumForm, ExperienceForm, EducationForm, SkillForm,
    DocumentForm, ImageForm, DatabaseForm
)

class CurriculumDetailView(LoginRequiredMixin, DetailView):
    model = Curriculum
    template_name = 'cv/detail.html'
    context_object_name = 'cv'

    def get_object(self):
        return get_object_or_404(Curriculum, user=self.request.user)

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
    template_name = 'documents/upload.html'
    success_url = reverse_lazy('docsview')

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
        return render(request, 'documents/docsview.html', context)