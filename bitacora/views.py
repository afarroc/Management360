import json
import re
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .models import BitacoraAttachment, BitacoraEntry
from .forms import BitacoraAttachmentForm, BitacoraEntryForm
from .utils import extract_structured_content


class BitacoraListView(LoginRequiredMixin, ListView):
    model = BitacoraEntry
    template_name = 'bitacora/dashboard.html'
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        queryset = BitacoraEntry.objects.filter(
            created_by=self.request.user,
            is_active=True,
        )
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(titulo__icontains=q) |
                Q(contenido__icontains=q) |
                Q(tags__name__icontains=q)
            ).distinct()

        categoria = self.request.GET.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)

        periodo = self.request.GET.get('periodo')
        if periodo:
            today = timezone.now().date()
            if periodo == 'hoy':
                queryset = queryset.filter(fecha_creacion__date=today)
            elif periodo == 'semana':
                week_start = today - timedelta(days=today.weekday())
                queryset = queryset.filter(fecha_creacion__date__gte=week_start)
            elif periodo == 'mes':
                month_start = today.replace(day=1)
                queryset = queryset.filter(fecha_creacion__date__gte=month_start)

        publico = self.request.GET.get('publico')
        if publico:
            queryset = queryset.filter(is_public=publico == '1')

        return queryset.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        all_entries = BitacoraEntry.objects.filter(
            created_by=user,
            is_active=True,
        )
        total = all_entries.count()

        total_attachments = BitacoraAttachment.objects.filter(
            entry__created_by=user,
            entry__is_active=True,
        ).count()

        context['stats'] = {
            'total_entries':      total,
            'entries_this_month': all_entries.filter(
                fecha_creacion__month=timezone.now().month,
                fecha_creacion__year=timezone.now().year,
            ).count(),
            'public_entries':     all_entries.filter(is_public=True).count(),
            'public_percentage':  round(
                all_entries.filter(is_public=True).count() / max(total, 1) * 100
            ),
            'categories_used':    all_entries.values('categoria').distinct().count(),
            'total_categories':   len(BitacoraEntry.CategoriaChoices),
            'total_attachments':  total_attachments,
        }

        context['category_stats'] = {}
        for choice in BitacoraEntry.CategoriaChoices:
            count = all_entries.filter(categoria=choice.value).count()
            if count > 0:
                context['category_stats'][choice.label] = {
                    'count':      count,
                    'percentage': round((count / total) * 100) if total > 0 else 0,
                }

        context['recent_entries'] = all_entries.order_by('-fecha_creacion')[:10]

        try:
            from events.models import InboxItem
            context['gtd_items'] = InboxItem.objects.filter(
                created_by=user,
                is_processed=False,
            ).order_by('-created_at')[:5]
        except Exception:
            context['gtd_items'] = []

        try:
            from events.models import Task
            context['active_tasks'] = Task.objects.filter(
                host=user,
                done=False,
            ).order_by('-created_at')[:3]
        except Exception:
            context['active_tasks'] = []
        
        context['categoria_choices'] = BitacoraEntry.CategoriaChoices.choices
        return context


class BitacoraDetailView(LoginRequiredMixin, DetailView):
    model = BitacoraEntry
    template_name = 'bitacora/entry_detail.html'
    context_object_name = 'entry'

    def get_queryset(self):
        return BitacoraEntry.objects.filter(
            created_by=self.request.user,
            is_active=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entry = self.object

        if entry.structured_content:
            from .templatetags.bitacora_tags import render_content_block
            rendered_blocks = []
            for block in entry.structured_content:
                if isinstance(block, dict) and 'type' in block:
                    block_copy = block.copy()
                    block_copy['rendered_content'] = render_content_block(block)
                    rendered_blocks.append(block_copy)
                else:
                    rendered_blocks.append(block)
            context['rendered_structured_content'] = rendered_blocks

        return context


class BitacoraCreateView(LoginRequiredMixin, CreateView):
    model = BitacoraEntry
    form_class = BitacoraEntryForm
    template_name = 'bitacora/entry_form.html'

    def get_success_url(self):
        return reverse_lazy('bitacora:detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        contenido_html = form.cleaned_data.get('contenido', '')
        structured = extract_structured_content(contenido_html)
        if structured:
            form.instance.structured_content = structured
        messages.success(self.request, 'Entrada creada exitosamente.')
        return super().form_valid(form)


class BitacoraUpdateView(LoginRequiredMixin, UpdateView):
    model = BitacoraEntry
    form_class = BitacoraEntryForm
    template_name = 'bitacora/entry_form.html'

    def get_success_url(self):
        return reverse_lazy('bitacora:detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        return BitacoraEntry.objects.filter(
            created_by=self.request.user,
            is_active=True,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        contenido_html = form.cleaned_data.get('contenido', '')
        structured = extract_structured_content(contenido_html)
        if structured:
            form.instance.structured_content = structured
        messages.success(self.request, 'Entrada actualizada exitosamente.')
        return super().form_valid(form)


class BitacoraDeleteView(LoginRequiredMixin, DeleteView):
    model = BitacoraEntry
    template_name = 'bitacora/entry_confirm_delete.html'
    success_url = reverse_lazy('bitacora:list')

    def get_queryset(self):
        return BitacoraEntry.objects.filter(
            created_by=self.request.user,
            is_active=True,
        )

    def form_valid(self, form):
        messages.success(self.request, 'Entrada eliminada exitosamente.')
        return super().form_valid(form)


@login_required
def content_blocks_list(request):
    from courses.models import ContentBlock

    content_blocks = ContentBlock.objects.filter(
        Q(is_public=True) | Q(author=request.user)
    ).order_by('-updated_at')

    category = request.GET.get('category')
    if category:
        content_blocks = content_blocks.filter(category__icontains=category)

    content_type = request.GET.get('content_type')
    if content_type:
        content_blocks = content_blocks.filter(content_type=content_type)

    selected_entry = None
    entry_id = request.GET.get('entry')
    if entry_id and entry_id != 'current':
        try:
            selected_entry = BitacoraEntry.objects.get(
                pk=entry_id,
                created_by=request.user,
                is_active=True,
            )
        except (BitacoraEntry.DoesNotExist, ValueError):
            pass

    context = {
        'content_blocks':  content_blocks,
        'categories':      ContentBlock.objects.values_list('category', flat=True).distinct(),
        'content_types':   ContentBlock.CONTENT_TYPES,
        'selected_entry':  selected_entry,
    }
    return render(request, 'bitacora/content_blocks_list.html', context)


@login_required
def insert_content_block(request, entry_id, block_id):
    from courses.models import ContentBlock

    entry = get_object_or_404(
        BitacoraEntry,
        pk=entry_id,
        created_by=request.user,
        is_active=True,
    )
    block = get_object_or_404(ContentBlock, pk=block_id)

    if not (block.is_public or block.author == request.user):
        messages.error(request, 'No tienes permiso para usar este bloque de contenido.')
        return redirect('bitacora:detail', pk=entry_id)

    structured = entry.get_structured_content_blocks()
    structured.append({
        'id':           block.id,
        'type':         'content_block',
        'title':        block.title,
        'content_type': block.content_type,
        'content':      block.get_content(),
        'inserted_at':  timezone.now().isoformat(),
    })
    entry.structured_content = structured
    entry.save()

    block.increment_usage()
    messages.success(request, f'Bloque "{block.title}" insertado exitosamente.')
    return redirect('bitacora:update', pk=entry_id)


@login_required
def upload_image(request):
    if request.method != 'POST' or not request.FILES.get('file'):
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    uploaded_file = request.FILES['file']

    allowed_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    if uploaded_file.content_type not in allowed_types:
        return JsonResponse({'error': 'Tipo de archivo no permitido'}, status=400)

    if uploaded_file.size > 5 * 1024 * 1024:
        return JsonResponse({'error': 'Archivo demasiado grande (máximo 5MB)'}, status=400)

    file_extension = uploaded_file.name.rsplit('.', 1)[-1].lower()
    file_name = f'bitacora_images/{get_random_string(32)}.{file_extension}'
    file_path = default_storage.save(file_name, uploaded_file)
    file_url  = default_storage.url(file_path)

    return JsonResponse({'location': file_url, 'uploaded': 1})
