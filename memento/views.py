from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from datetime import datetime, date
from django.http import Http404
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db import IntegrityError  # <-- Add this import
from django.contrib import messages
from .models import MementoConfig
from .forms import MementoConfigForm

# views.py - Modificar la función memento
def memento(request, frequency=None, birth_date=None, death_date=None):
    # Manejar parámetros GET o URL
    frequency = frequency or request.GET.get('frequency')
    birth_date = birth_date or request.GET.get('birth_date')
    death_date = death_date or request.GET.get('death_date')

    # Mostrar formulario si faltan parámetros
    if not all([frequency, birth_date, death_date]):
        if request.user.is_authenticated:
            try:
                config = MementoConfig.objects.filter(user=request.user).latest('updated_at')
                return redirect('memento', 
                             frequency=config.preferred_frequency,
                             birth_date=config.birth_date.strftime('%Y-%m-%d'),
                             death_date=config.death_date.strftime('%Y-%m-%d'))
            except MementoConfig.DoesNotExist:
                pass
        return render(request, "memento/date_selection.html", {
            'form': MementoConfigForm(),
            'allow_temporary': True  # Nuevo contexto para mostrar opción temporal
        })

    try:
        # Convertir fechas
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        death_date = datetime.strptime(death_date, '%Y-%m-%d').date()
        
        # Validar fechas
        if birth_date >= death_date:
            raise ValueError("La fecha de nacimiento debe ser anterior a la fecha de fallecimiento")
        if death_date <= date.today():
            raise ValueError("La fecha de fallecimiento debe ser en el futuro")
            
    except (ValueError, TypeError) as e:
        form = MementoConfigForm(initial={
            'frequency': frequency,
            'birth_date': birth_date,
            'death_date': death_date
        })
        form.add_error(None, str(e))
        return render(request, "memento/date_selection.html", {
            'form': form,
            'allow_temporary': True
        })

    # Guardar configuración solo si el usuario está autenticado Y quiere guardar
    if request.user.is_authenticated and request.POST.get('save_config') == 'true':
        MementoConfig.objects.update_or_create(
            user=request.user,
            defaults={
                'birth_date': birth_date,
                'death_date': death_date,
                'preferred_frequency': frequency
            }
        )

    # Calcular datos del memento mori
    data = calculate_memento_data(birth_date, death_date)

    # Construir contexto
    context = build_memento_context(frequency, birth_date, death_date, data)
    context['is_temporary'] = not (request.user.is_authenticated and request.POST.get('save_config') == 'true')
    return render(request, "memento/memento_mori.html", context)
    
def calculate_memento_data(birth_date, death_date):
    today = date.today()
    total_days = (death_date - birth_date).days
    passed_days = (today - birth_date).days
    left_days = max(0, total_days - passed_days)
    
    total_weeks = total_days // 7
    passed_weeks = passed_days // 7
    left_weeks = max(0, total_weeks - passed_weeks)
    
    delta = relativedelta(death_date, birth_date)
    delta_passed = relativedelta(today, birth_date)
    
    total_months = delta.years * 12 + delta.months
    passed_months = delta_passed.years * 12 + delta_passed.months
    left_months = max(0, total_months - passed_months)
    
    return {
        'total_days': total_days,
        'passed_days': passed_days,
        'left_days': left_days,
        'total_weeks': total_weeks,
        'passed_weeks': passed_weeks,
        'left_weeks': left_weeks,
        'total_months': total_months,
        'passed_months': passed_months,
        'left_months': left_months,
        'total_years': delta.years,
    }

def build_memento_context(frequency, birth_date, death_date, data):
    base_context = {
        'title': "Calendario de la Muerte",
        'birth_date': birth_date.strftime("%d/%m/%Y"),
        'death_date': death_date.strftime("%d/%m/%Y"),
        'total_years': data['total_years'],
        'frequency': frequency,
        'current_date': date.today().strftime("%d/%m/%Y"),
    }

    if frequency == 'daily':
        return {
            **base_context,
            'title': f'Vista Diaria - {base_context["title"]}',
            'total_days': data['total_days'],
            'passed_days': data['passed_days'],
            'left_days': data['left_days'],
        }
    elif frequency == 'weekly':
        return {
            **base_context,
            'title': f'Vista Semanal - {base_context["title"]}',
            'total_weeks': data['total_weeks'],
            'passed_weeks': data['passed_weeks'],
            'left_weeks': data['left_weeks'],
        }
    elif frequency == 'monthly':
        return {
            **base_context,
            'title': f'Vista Mensual - {base_context["title"]}',
            'total_months': data['total_months'],
            'passed_months': data['passed_months'],
            'left_months': data['left_months'],
            'now': {'year': date.today().year, 'month': date.today().month},
        }
        

@method_decorator(login_required, name='dispatch')
class MementoConfigCreateView(CreateView):
    model = MementoConfig
    form_class = MementoConfigForm
    template_name = 'memento/date_selection.html'
    success_url = reverse_lazy('memento_default')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Check if config already exists
        existing = MementoConfig.objects.filter(
            user=self.request.user,
            birth_date=form.cleaned_data['birth_date'],
            death_date=form.cleaned_data['death_date']
        ).first()

        if existing:
            messages.info(self.request, 
                "Ya existe una configuración con estas fechas. Redirigiendo a la configuración existente.")
            return redirect('memento_update', pk=existing.pk)

        form.instance.user = self.request.user
        self.object = form.save()
        messages.success(self.request, "¡Configuración guardada exitosamente!")
        return super().form_valid(form)

    def get_success_url(self):
        if hasattr(self, 'object') and self.object:
            return reverse('memento', kwargs={
                'frequency': self.object.preferred_frequency,
                'birth_date': self.object.birth_date.strftime('%Y-%m-%d'),
                'death_date': self.object.death_date.strftime('%Y-%m-%d')
            })
        return self.success_url

@method_decorator(login_required, name='dispatch')
class MementoConfigUpdateView(UpdateView):
    model = MementoConfig
    form_class = MementoConfigForm
    template_name = 'memento/date_selection.html'
    
    def get_success_url(self):
        return reverse_lazy('memento', kwargs={
            'frequency': self.object.preferred_frequency,
            'birth_date': self.object.birth_date.strftime('%Y-%m-%d'),
            'death_date': self.object.death_date.strftime('%Y-%m-%d')
        })