from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db import models
from .models import BitacoraEntry, BitacoraAttachment
from .forms import BitacoraEntryForm, BitacoraAttachmentForm

class StructuredContentMixin:
    """Mixin para manejar contenido estructurado en formularios"""

    def extract_structured_content(self, html_content):
        """Extraer bloques de contenido estructurado desde HTML de TinyMCE usando solo regex"""
        import json
        import re

        structured_blocks = []
        cleaned_html = html_content

        # Buscar JSON en el texto plano usando patrones regex
        json_patterns = [
            r'\[\s*\{.*?\}\s*\]',  # Array de objetos
            r'\[.*?\]',            # Array general (más amplio)
        ]

        for pattern in json_patterns:
            json_matches = re.findall(pattern, cleaned_html, re.DOTALL)
            for json_str in json_matches:
                try:
                    # Limpiar el string JSON - remover caracteres problemáticos
                    cleaned_json = json_str.strip()

                    # Intentar parsear con diferentes estrategias
                    json_data = None

                    # Estrategia 1: Parseo directo con manejo de Unicode
                    try:
                        json_data = json.loads(cleaned_json, strict=False)
                    except json.JSONDecodeError as e1:
                        # Estrategia 2: Limpiar caracteres problemáticos
                        try:
                            # Reemplazar comillas tipográficas por comillas normales
                            cleaned_json = cleaned_json.replace('"', '"').replace('"', '"')
                            cleaned_json = cleaned_json.replace(''', "'").replace(''', "'")
                            json_data = json.loads(cleaned_json, strict=False)
                        except json.JSONDecodeError as e2:
                            # Estrategia 3: Parseo manual más tolerante
                            try:
                                # Usar eval como último recurso (más peligroso pero más tolerante)
                                import ast
                                # Solo si parece seguro (empieza y termina con corchetes)
                                if cleaned_json.strip().startswith('[') and cleaned_json.strip().endswith(']'):
                                    # Intentar evaluar como literal Python
                                    json_data = ast.literal_eval(cleaned_json)
                                    print(f"Parseado con ast.literal_eval")
                            except:
                                print(f"Fallo parseo con ast.literal_eval: {e2}")
                                pass

                    if json_data and isinstance(json_data, list) and json_data:
                        # Filtrar solo los elementos que son diccionarios con 'type'
                        valid_components = [item for item in json_data if isinstance(item, dict) and 'type' in item]
                        if valid_components:
                            # Es contenido publicitario estructurado
                            structured_blocks.extend(valid_components)
                            # Remover del HTML
                            cleaned_html = cleaned_html.replace(json_str, '')
                            print(f"Extraído JSON con {len(valid_components)} componentes válidos de {len(json_data)} totales")
                            break  # Salir del bucle de patrones si encontramos uno válido
                        else:
                            print(f"JSON parseado pero sin componentes válidos: {len(json_data)} elementos, ninguno tiene 'type'")
                    else:
                        print(f"JSON parseado pero no válido: tipo={type(json_data)}, es_lista={isinstance(json_data, list)}, tiene_elementos={bool(json_data) if isinstance(json_data, list) else 'N/A'}")
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Error parseando JSON: {e}")
                    continue

        # Actualizar el contenido del formulario con el HTML limpio
        if hasattr(self, 'request') and self.request.POST.get('contenido'):
            # Solo actualizar si estamos en una vista que tiene request
            mutable_post = self.request.POST.copy()
            mutable_post['contenido'] = cleaned_html
            self.request.POST = mutable_post

        return structured_blocks if structured_blocks else None

class BitacoraListView(LoginRequiredMixin, ListView):
    model = BitacoraEntry
    template_name = 'bitacora/dashboard.html'  # Cambiar a dashboard
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        queryset = BitacoraEntry.objects.filter(autor=self.request.user)

        # Filtro por búsqueda de texto
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                models.Q(titulo__icontains=q) |
                models.Q(contenido__icontains=q) |
                models.Q(tags__name__icontains=q)
            ).distinct()

        # Filtro por categoría
        categoria = self.request.GET.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)

        # Filtro por período
        periodo = self.request.GET.get('periodo')
        if periodo:
            today = timezone.now().date()
            if periodo == 'hoy':
                queryset = queryset.filter(fecha_creacion__date=today)
            elif periodo == 'semana':
                week_start = today - timezone.timedelta(days=today.weekday())
                queryset = queryset.filter(fecha_creacion__date__gte=week_start)
            elif periodo == 'mes':
                month_start = today.replace(day=1)
                queryset = queryset.filter(fecha_creacion__date__gte=month_start)

        # Filtro por visibilidad
        publico = self.request.GET.get('publico')
        if publico:
            queryset = queryset.filter(is_public=publico == '1')

        return queryset.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Estadísticas
        all_entries = BitacoraEntry.objects.filter(autor=user)
        context['stats'] = {
            'total_entries': all_entries.count(),
            'entries_this_month': all_entries.filter(fecha_creacion__month=timezone.now().month).count(),
            'public_entries': all_entries.filter(is_public=True).count(),
            'public_percentage': round(all_entries.filter(is_public=True).count() / max(all_entries.count(), 1) * 100),
            'categories_used': all_entries.values('categoria').distinct().count(),
            'total_categories': len(BitacoraEntry.CATEGORIA_CHOICES),
            'total_attachments': sum(entry.attachments.count() for entry in all_entries),
        }

        # Distribución por categorías
        context['category_stats'] = {}
        total_entries = context['stats']['total_entries']
        for choice_value, choice_label in BitacoraEntry.CATEGORIA_CHOICES:
            count = all_entries.filter(categoria=choice_value).count()
            if count > 0:
                percentage = round((count / total_entries) * 100) if total_entries > 0 else 0
                context['category_stats'][choice_label] = {
                    'count': count,
                    'percentage': percentage
                }

        # Entradas recientes
        context['recent_entries'] = all_entries.order_by('-fecha_creacion')[:10]

        # Integración GTD - Items del inbox relacionados
        try:
            from events.models import InboxItem
            context['gtd_items'] = InboxItem.objects.filter(
                created_by=user,
                is_processed=False
            ).order_by('-created_at')[:5]
        except:
            context['gtd_items'] = []

        # Tareas activas
        try:
            from events.models import Task
            context['active_tasks'] = Task.objects.filter(
                host=user,
                done=False
            ).order_by('-created_at')[:3]
        except:
            context['active_tasks'] = []

        return context

class BitacoraDetailView(LoginRequiredMixin, DetailView):
    model = BitacoraEntry
    template_name = 'bitacora/entry_detail.html'
    context_object_name = 'entry'

    def get_queryset(self):
        return BitacoraEntry.objects.filter(autor=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entry = self.object

        # Procesar contenido estructurado si existe
        if entry.structured_content:
            from .templatetags.bitacora_tags import render_content_block
            rendered_blocks = []
            for block in entry.structured_content:
                if isinstance(block, dict) and 'type' in block:
                    # Renderizar el bloque completo
                    rendered_content = render_content_block(block)
                    block_copy = block.copy()
                    block_copy['rendered_content'] = rendered_content
                    rendered_blocks.append(block_copy)
                else:
                    rendered_blocks.append(block)
            context['rendered_structured_content'] = rendered_blocks

        return context

class BitacoraCreateView(LoginRequiredMixin, StructuredContentMixin, CreateView):
    model = BitacoraEntry
    form_class = BitacoraEntryForm
    template_name = 'bitacora/entry_form.html'
    success_url = reverse_lazy('bitacora:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.autor = self.request.user

        # Procesar contenido estructurado desde el HTML de TinyMCE
        contenido_html = form.cleaned_data.get('contenido', '')
        structured_content = self.extract_structured_content(contenido_html)

        if structured_content:
            form.instance.structured_content = structured_content

        messages.success(self.request, 'Entrada creada exitosamente.')
        return super().form_valid(form)


class BitacoraUpdateView(LoginRequiredMixin, StructuredContentMixin, UpdateView):
    model = BitacoraEntry
    form_class = BitacoraEntryForm
    template_name = 'bitacora/entry_form.html'
    success_url = reverse_lazy('bitacora:list')

    def get_queryset(self):
        return BitacoraEntry.objects.filter(autor=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Procesar contenido estructurado desde el HTML de TinyMCE
        contenido_html = form.cleaned_data.get('contenido', '')
        structured_content = self.extract_structured_content(contenido_html)

        if structured_content:
            form.instance.structured_content = structured_content

        messages.success(self.request, 'Entrada actualizada exitosamente.')
        return super().form_valid(form)

class BitacoraDeleteView(LoginRequiredMixin, DeleteView):
    model = BitacoraEntry
    template_name = 'bitacora/entry_confirm_delete.html'
    success_url = reverse_lazy('bitacora:list')

    def get_queryset(self):
        return BitacoraEntry.objects.filter(autor=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Entrada eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

@login_required
def content_blocks_list(request):
    """Vista para mostrar bloques de contenido disponibles para insertar en bitácora"""
    from courses.models import ContentBlock

    # Obtener bloques públicos y del usuario actual
    content_blocks = ContentBlock.objects.filter(
        models.Q(is_public=True) | models.Q(author=request.user)
    ).order_by('-updated_at')

    # Filtros
    category = request.GET.get('category')
    if category:
        content_blocks = content_blocks.filter(category__icontains=category)

    content_type = request.GET.get('content_type')
    if content_type:
        content_blocks = content_blocks.filter(content_type=content_type)

    # Obtener entrada específica si se proporciona
    entry_id = request.GET.get('entry')
    selected_entry = None
    if entry_id and entry_id != 'current':
        try:
            selected_entry = BitacoraEntry.objects.get(id=int(entry_id), autor=request.user)
        except (BitacoraEntry.DoesNotExist, ValueError):
            pass

    context = {
        'content_blocks': content_blocks,
        'categories': ContentBlock.objects.values_list('category', flat=True).distinct(),
        'content_types': ContentBlock.CONTENT_TYPES,
        'selected_entry': selected_entry,
    }

    return render(request, 'bitacora/content_blocks_list.html', context)

@login_required
def insert_content_block(request, entry_id, block_id):
    """Vista para insertar un bloque de contenido en una entrada de bitácora"""
    from courses.models import ContentBlock

    try:
        entry = BitacoraEntry.objects.get(id=entry_id, autor=request.user)
        block = ContentBlock.objects.get(id=block_id)

        # Verificar permisos
        if not (block.is_public or block.author == request.user):
            messages.error(request, 'No tienes permiso para usar este bloque de contenido.')
            return redirect('bitacora:detail', pk=entry_id)

        # Agregar el bloque al contenido estructurado de la entrada
        structured_content = entry.get_structured_content_blocks()
        structured_content.append({
            'id': block.id,
            'type': 'content_block',
            'title': block.title,
            'content_type': block.content_type,
            'content': block.get_content(),
            'inserted_at': timezone.now().isoformat(),
        })

        entry.structured_content = structured_content
        entry.save()

        # Incrementar contador de uso
        block.increment_usage()

        messages.success(request, f'Bloque "{block.title}" insertado exitosamente.')
        return redirect('bitacora:update', pk=entry_id)

    except (BitacoraEntry.DoesNotExist, ContentBlock.DoesNotExist):
        messages.error(request, 'Entrada o bloque de contenido no encontrado.')
        return redirect('bitacora:list')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required
@csrf_exempt
def upload_image(request):
    """Vista para subir imágenes desde TinyMCE"""
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        # Validar tipo de archivo
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if uploaded_file.content_type not in allowed_types:
            return JsonResponse({'error': 'Tipo de archivo no permitido'}, status=400)

        # Validar tamaño (máximo 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'Archivo demasiado grande (máximo 5MB)'}, status=400)

        # Guardar archivo usando el storage personalizado
        from django.core.files.storage import default_storage
        from django.utils.crypto import get_random_string

        # Generar nombre único
        file_extension = uploaded_file.name.split('.')[-1]
        file_name = f"bitacora_images/{get_random_string(32)}.{file_extension}"

        # Guardar archivo
        file_path = default_storage.save(file_name, uploaded_file)
        file_url = default_storage.url(file_path)

        return JsonResponse({
            'location': file_url,
            'uploaded': 1
        })

    return JsonResponse({'error': 'Método no permitido'}, status=405)
