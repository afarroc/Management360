# cv/views.py (Versión corregida)
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Curriculum, Experience, Education, Skill
from .forms import CurriculumForm, ExperienceForm, EducationForm, SkillForm
from django.forms import formset_factory
from django.forms import modelformset_factory


# Configuración mejorada de formsets
# Modificar los formsets para usar modelformset_factory
ExperienceFormSet = modelformset_factory(
    Experience, 
    form=ExperienceForm, 
    extra=1, 
    can_delete=True
)

EducationFormSet = modelformset_factory(
    Education,
    form=EducationForm,
    extra=1,
    can_delete=True
)

SkillFormSet = modelformset_factory(
    Skill,
    form=SkillForm,
    extra=1,
    can_delete=True
)

@method_decorator(login_required, name='dispatch')
class CurriculumView(View):
    template_name = 'cv/curriculum_form.html'
    success_url = 'cv_detail'

    def get(self, request, user_id=None):
        if user_id and request.user.id != user_id:
            raise PermissionDenied("Acceso no autorizado")
        
        # Crear o obtener el Curriculum
        cv, created = Curriculum.objects.get_or_create(user=request.user)
        
        # Configurar formsets con datos iniciales
        experience_formset = ExperienceFormSet(
            prefix='experiences',
            instance=cv,
            queryset=cv.experiences.all()
        )
        
        education_formset = EducationFormSet(
            prefix='education',
            instance=cv,
            queryset=cv.educations.all()
        )
        
        skill_formset = SkillFormSet(
            prefix='skills',
            instance=cv,
            queryset=cv.skills_list.all()
        )

        return render(request, self.template_name, {
            'form': CurriculumForm(instance=cv),
            'experience_formset': experience_formset,
            'education_formset': education_formset,
            'skill_formset': skill_formset,
            'cv': cv
        })

    # Actualizar el método post
    @transaction.atomic
    def post(self, request, user_id=None):
        cv = get_object_or_404(Curriculum, user=request.user)
        form = CurriculumForm(request.POST, request.FILES, instance=cv)
        
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

        if all([
            form.is_valid(),
            experience_formset.is_valid(),
            education_formset.is_valid(),
            skill_formset.is_valid()
        ]):
            try:
                form.save()
                # Guardar formsets
                instances = experience_formset.save(commit=False)
                for obj in instances:
                    obj.cv = cv
                    obj.save()
                
                instances = education_formset.save(commit=False)
                for obj in instances:
                    obj.cv = cv
                    obj.save()
                
                instances = skill_formset.save(commit=False)
                for obj in instances:
                    obj.cv = cv
                    obj.save()
                
                # Eliminar marcados para borrar
                for obj in experience_formset.deleted_objects:
                    obj.delete()
                
                for obj in education_formset.deleted_objects:
                    obj.delete()
                
                for obj in skill_formset.deleted_objects:
                    obj.delete()
                
                messages.success(request, 'Perfil actualizado correctamente')
                return redirect('cv_detail')
                
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
        
        return render(request, self.template_name, {
            'form': form,
            'experience_formset': experience_formset,
            'education_formset': education_formset,
            'skill_formset': skill_formset,
            'cv': cv
        })
    # Resto de las vistas permanecen igual...

@method_decorator(login_required, name='dispatch')
class ViewCurriculumView(View):
    def get(self, request, user_id):
        cv = get_object_or_404(Curriculum, user_id=user_id)
        return render(request, 'cv/view_curriculum.html', {
            'cv': cv,
            'experiences': cv.experiences.all(),
            'education': cv.educations.all(),
            'skills': cv.skills_list.all()
        })

@login_required
def cv_edit(request):
    cv = get_object_or_404(Curriculum, user=request.user)
    
    if request.method == 'POST':
        form = CurriculumForm(request.POST, request.FILES, instance=cv)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cambios guardados exitosamente')
            return redirect('cv_detail')
        messages.error(request, 'Error en el formulario')
    
    form = CurriculumForm(instance=cv)
    return render(request, 'cv/edit.html', {'form': form})

@login_required
def cv_detail(request):
    cv = get_object_or_404(Curriculum, user=request.user)
    return render(request, 'cv/detail.html', {
        'cv': cv,
        'experiences': cv.experiences.all(),
        'educations': cv.educations.all(),
        'skills_list': cv.skills_list.all()
    })

@require_POST
@login_required
def delete_profile_picture(request):
    cv = get_object_or_404(Curriculum, user=request.user)
    try:
        if cv.profile_picture:
            cv.profile_picture.delete(save=False)
            cv.profile_picture = None
            cv.save(update_fields=['profile_picture'])
            messages.success(request, 'Imagen eliminada correctamente')
        else:
            messages.warning(request, 'No hay imagen para eliminar')
    except Exception as e:
        messages.error(request, f'Error al eliminar imagen: {str(e)}')
    
    return redirect('cv_detail')