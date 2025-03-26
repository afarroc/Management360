# cv/views.py
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django import forms
from django.db import transaction
from django.core.exceptions import PermissionDenied
from .models import Curriculum, Experience, Education, Skill
from .forms import CurriculumForm, ExperienceForm, EducationForm, SkillForm
from django.forms import formset_factory

# Formsets
ExperienceFormSet = formset_factory(ExperienceForm, extra=1, can_delete=True)
EducationFormSet = formset_factory(EducationForm, extra=1, can_delete=True)
SkillFormSet = formset_factory(SkillForm, extra=1, can_delete=True)

@method_decorator(login_required, name='dispatch')
class CurriculumView(View):
    template_name = 'cv/curriculum_form.html'
    success_url = 'cv_detail'

    def get(self, request, user_id=None):
        if user_id and request.user.id != user_id:
            raise PermissionDenied("No tienes permiso para ver este perfil")
        
        try:
            cv = Curriculum.objects.get(user_id=user_id) if user_id else None
            
            if cv:
                form = CurriculumForm(instance=cv)
                experience_formset = ExperienceFormSet(
                    prefix='experiences',
                    initial=[{'cv': cv.id}],
                    queryset=cv.experiences.all()
                )
                education_formset = EducationFormSet(
                    prefix='education',
                    initial=[{'cv': cv.id}],
                    queryset=cv.educations.all()
                )
                skill_formset = SkillFormSet(
                    prefix='skills',
                    initial=[{'cv': cv.id}],
                    queryset=cv.skills_list.all()
                )
            else:
                form = CurriculumForm()
                experience_formset = ExperienceFormSet(prefix='experiences')
                education_formset = EducationFormSet(prefix='education')
                skill_formset = SkillFormSet(prefix='skills')

            return render(request, self.template_name, {
                'form': form,
                'experience_formset': experience_formset,
                'education_formset': education_formset,
                'skill_formset': skill_formset
            })
            
        except Curriculum.DoesNotExist:
            return render(request, 'cv/error.html', {'message': "Perfil no encontrado"})
        except Exception as e:
            return render(request, 'cv/error.html', {'message': str(e)})

    @transaction.atomic
    def post(self, request, user_id=None):
        if user_id and request.user.id != user_id:
            raise PermissionDenied("No tienes permiso para editar este perfil")
        
        try:
            cv = Curriculum.objects.get(user_id=user_id) if user_id else None
            form = CurriculumForm(request.POST, request.FILES, instance=cv)
            experience_formset = ExperienceFormSet(request.POST, prefix='experiences')
            education_formset = EducationFormSet(request.POST, prefix='education')
            skill_formset = SkillFormSet(request.POST, prefix='skills')

            if not all([
                form.is_valid(),
                experience_formset.is_valid(),
                education_formset.is_valid(),
                skill_formset.is_valid()
            ]):
                return render(request, self.template_name, {
                    'form': form,
                    'experience_formset': experience_formset,
                    'education_formset': education_formset,
                    'skill_formset': skill_formset
                })

            cv = form.save(commit=False)
            cv.user = request.user
            cv.save()

            # Procesar experiences
            for exp_form in experience_formset:
                if exp_form.cleaned_data.get('DELETE'):
                    if exp_form.instance.pk:
                        exp_form.instance.delete()
                elif exp_form.has_changed():
                    exp = exp_form.save(commit=False)
                    exp.cv = cv
                    exp.save()

            # Procesar education
            for edu_form in education_formset:
                if edu_form.cleaned_data.get('DELETE'):
                    if edu_form.instance.pk:
                        edu_form.instance.delete()
                elif edu_form.has_changed():
                    edu = edu_form.save(commit=False)
                    edu.cv = cv
                    edu.save()

            # Procesar skills
            for skill_form in skill_formset:
                if skill_form.cleaned_data.get('DELETE'):
                    if skill_form.instance.pk:
                        skill_form.instance.delete()
                elif skill_form.has_changed():
                    skill = skill_form.save(commit=False)
                    skill.cv = cv
                    skill.save()

            return redirect(self.success_url)
        
        except forms.ValidationError as e:
            return render(request, 'cv/error.html', {'message': str(e)})
        except Exception as e:
            return render(request, 'cv/error.html', {'message': str(e)})

@method_decorator(login_required, name='dispatch')
class ViewCurriculumView(View):
    def get(self, request, user_id):
        try:
            cv = get_object_or_404(Curriculum, user_id=user_id)
            experiences = cv.experiences.all()
            education = cv.educations.all()
            skills = cv.skills_list.all()

            return render(request, 'cv/view_curriculum.html', {
                'cv': cv,
                'experiences': experiences,
                'education': education,
                'skills': skills
            })
        except Curriculum.DoesNotExist:
            return render(request, 'cv/error.html', {'message': "Perfil no encontrado"})
        except Exception as e:
            return render(request, 'cv/error.html', {'message': str(e)})

@login_required
def cv_edit(request):
    cv = Curriculum.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        form = CurriculumForm(request.POST, request.FILES, instance=cv)
        if form.is_valid():
            form.save()
            return redirect('cv_detail')
    else:
        form = CurriculumForm(instance=cv)
    
    return render(request, 'cv/edit.html', {'form': form})
    
    # cv/views.py
@login_required
def cv_detail(request):
    cv = Curriculum.objects.filter(user=request.user).first()
    return render(request, 'cv/detail.html', {
        'cv': cv,
        'experiences': cv.experiences.all() if cv else [],
        'educations': cv.educations.all() if cv else [],
        'skills_list': cv.skills_list.all() if cv else [],
    })