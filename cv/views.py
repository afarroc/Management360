# cv/views.py (Versión corregida)
from io import BytesIO
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.views.decorators.http import require_POST
from openpyxl import load_workbook
from .models import Curriculum, Experience, Education, Skill
from .forms import CurriculumForm, ExperienceForm, EducationForm, SkillForm
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

from .models import Document, Image, Database
from .forms import DocumentForm, ImageForm, DatabaseForm

def document_view(request):
    documents = Document.objects.all()  # Obtiene todos los documentos
    images = Image.objects.all()        # Obtiene todas las imágenes
    databases = Database.objects.all()        # Obtiene todas las imágenes
    context = {
        'documents': documents,
        'images': images,
        'databases': databases,
    }
    return render(request, 'documents/docsview.html', context)

def delete_file(request, file_id, file_type):
    if file_type == 'document':
        file_model = Document
    elif file_type == 'image':
        file_model = Image
    else:
        messages.error(request, 'Tipo de archivo no válido.')
        return redirect('docsview')

    file_instance = get_object_or_404(file_model, id=file_id)
    if request.method == 'POST':
        file_instance.upload.delete()  # Esto elimina el archivo del sistema de archivos.
        file_instance.delete()         # Esto elimina la instancia del modelo de la base de datos.
        messages.success(request, f'El {file_type} ha sido eliminado exitosamente.')
        return redirect('docsview')
    else:
        # Si no es una solicitud POST, muestra la página de confirmación.
        return render(request, 'documents/confirmar_eliminacion.html', {'file': file_instance, 'type': file_type})

from django.views.generic import FormView
from django.urls import reverse, reverse_lazy


# Vista para subir documentos
class DocumentUploadView(FormView):
    template_name = 'documents/upload.html' # El nombre del template que quieres usar
    form_class = DocumentForm # El formulario que quieres usar
    success_url = reverse_lazy('docsview')# La url a la que quieres redirigir después de subir el archivo
    def form_valid(self, form):
        # Este método se ejecuta si el formulario es válido
        # Aquí puedes guardar el archivo en tu modelo
        file = form.cleaned_data['file'] # Obtiene el archivo del formulario
        document = Document(upload=file) # Crea una instancia de tu modelo con el archivo
        document.save() # Guarda el archivo en la base de datos
        return super().form_valid(form) # Retorna la vista de éxito

# Vista para subir imágenes
class ImageUploadView(FormView):
    template_name = 'documents/upload.html' # El nombre del template que quieres usar
    form_class = ImageForm # El formulario que quieres usar
    success_url = reverse_lazy('docsview')# La url a la que quieres redirigir después de subir el archivo

    def form_valid(self, form):
        # Este método se ejecuta si el formulario es válido
        # Aquí puedes guardar el archivo en tu modelo
        file = form.cleaned_data['file'] # Obtiene el archivo del formulario
        image = Image(upload=file) # Crea una instancia de tu modelo con el archivo
        image.save() # Guarda el archivo en la base de datos
        return super().form_valid(form) # Retorna la vista de éxito
    
    # Vista para subir db

# Vista para subir bases de datos
class UploadDatabase(FormView):
    template_name = 'documents/upload.html' # El nombre del template que quieres usar
    form_class = DatabaseForm # El formulario que quieres usar
    success_url = reverse_lazy('docsview')# La url a la que quieres redirigir después de subir el archivo

    def form_valid(self, form):
        # Este método se ejecuta si el formulario es válido
        # Aquí puedes guardar el archivo en tu modelo
        file = form.cleaned_data['file'] # Obtiene el archivo del formulario
        db = Database(upload=file) # Crea una instancia de tu modelo con el archivo
        db.save() # Guarda el archivo en la base de datos
        return super().form_valid(form) # Retorna la vista de éxito

# Vista para subir bases de datos

# views.py

def upload_xlsx(request):
    if request.method == 'POST':
        form = DatabaseForm(request.POST, request.FILES)
        if form.is_valid():
            file_in_memory = request.FILES['file'].read()
            wb = load_workbook(filename=BytesIO(file_in_memory))
            print('Form is valid')
            # Procesa el archivo y realiza las operaciones necesarias
            # (filtrar columnas, cambiar títulos, etc.)
            # Luego, crea un nuevo archivo o modelo con los datos finales.
            # ...
            # Devuelve una respuesta al usuario (descargar archivo o mostrar datos).
    else:
        form = DatabaseForm()
    return render(request, 'documents/upload_xlsx.html', {'form': form})

# about upload

def upload_image(request):
    if request.method == 'POST':
        try:
            image = request.FILES['image']
            fs = FileSystemStorage()
            filename = fs.save(image.name, image)
            uploaded_file_url = fs.url(filename)
            messages.success(request, 'Imagen subida con éxito.')
            return redirect('about')
        except KeyError:
            messages.error(request, 'Por favor, selecciona una imagen para subir.')
    return render(request, 'about/about.html')