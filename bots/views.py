"""
Vistas para el sistema de gestión de leads y campañas
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator

from .models import LeadCampaign, Lead, LeadDistributionRule, BotInstance
from .lead_distributor import get_lead_distributor, get_bulk_importer
from .utils import get_bot_coordinator

import json
import csv
from io import StringIO

@login_required
def lead_campaign_list(request):
    """Lista de campañas de leads"""
    campaigns = LeadCampaign.objects.all().order_by('-created_at')

    # Estadísticas rápidas
    total_campaigns = campaigns.count()
    active_campaigns = campaigns.filter(is_active=True).count()
    total_leads = Lead.objects.count()
    distributed_leads = Lead.objects.filter(status__in=['assigned', 'in_progress', 'contacted', 'qualified']).count()
    converted_leads = Lead.objects.filter(status='converted').count()

    context = {
        'page_title': 'Campañas de Leads',
        'campaigns': campaigns,
        'stats': {
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'total_leads': total_leads,
            'distributed_leads': distributed_leads,
            'converted_leads': converted_leads,
            'conversion_rate': (converted_leads / total_leads * 100) if total_leads > 0 else 0
        }
    }

    return render(request, 'bots/lead_campaign_list.html', context)

@login_required
def lead_campaign_create(request):
    """Crear nueva campaña de leads"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        distribution_strategy = request.POST.get('distribution_strategy', 'equal_split')
        max_leads_per_bot = int(request.POST.get('max_leads_per_bot', 10))
        leads_per_batch = int(request.POST.get('leads_per_batch', 5))

        # Crear campaña
        campaign = LeadCampaign.objects.create(
            name=name,
            description=description,
            distribution_strategy=distribution_strategy,
            max_leads_per_bot=max_leads_per_bot,
            leads_per_batch=leads_per_batch
        )

        # Asignar bots seleccionados
        bot_ids = request.POST.getlist('assigned_bots')
        if bot_ids:
            bots = BotInstance.objects.filter(id__in=bot_ids)
            campaign.assigned_bots.set(bots)

        messages.success(request, f'Campaña "{name}" creada exitosamente')
        return redirect('bots:campaign_detail', pk=campaign.pk)

    # Obtener bots disponibles
    available_bots = BotInstance.objects.filter(is_active=True)

    context = {
        'page_title': 'Crear Campaña de Leads',
        'available_bots': available_bots,
        'strategies': LeadCampaign._meta.get_field('distribution_strategy').choices
    }

    return render(request, 'bots/lead_campaign_form.html', context)

@login_required
def lead_campaign_detail(request, pk):
    """Detalle de una campaña específica"""
    campaign = get_object_or_404(LeadCampaign, pk=pk)

    # Estadísticas de la campaña
    leads_stats = campaign.leads.aggregate(
        total=Count('id'),
        new=Count('id', filter=Q(status='new')),
        assigned=Count('id', filter=Q(status='assigned')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        contacted=Count('id', filter=Q(status='contacted')),
        qualified=Count('id', filter=Q(status='qualified')),
        converted=Count('id', filter=Q(status='converted')),
        rejected=Count('id', filter=Q(status='rejected'))
    )

    # Leads recientes
    recent_leads = campaign.leads.all()[:10]

    # Distribución por bot
    bot_distribution = campaign.leads.values('assigned_bot__name').annotate(
        count=Count('id')
    ).filter(assigned_bot__isnull=False)

    context = {
        'page_title': f'Campaña: {campaign.name}',
        'campaign': campaign,
        'leads_stats': leads_stats,
        'recent_leads': recent_leads,
        'bot_distribution': bot_distribution,
        'rules': campaign.distribution_rules.filter(is_active=True)
    }

    return render(request, 'bots/lead_campaign_detail.html', context)

@login_required
def lead_upload(request, campaign_pk):
    """Subir leads a una campaña"""
    campaign = get_object_or_404(LeadCampaign, pk=campaign_pk)

    if request.method == 'POST':
        upload_type = request.POST.get('upload_type')

        if upload_type == 'csv':
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                messages.error(request, 'Por favor selecciona un archivo CSV')
                return redirect('bots:lead_upload', campaign_pk=campaign_pk)

            # Procesar CSV
            importer = get_bulk_importer(campaign)
            result = importer.import_from_csv(csv_file)

            if result['success']:
                messages.success(request, f'Se importaron {result["imported"]} leads exitosamente')
                if result['errors']:
                    messages.warning(request, f'Errores en {len(result["errors"])} filas')
            else:
                messages.error(request, f'Error al importar: {result["error"]}')

        elif upload_type == 'manual':
            # Crear lead manualmente
            lead = Lead.objects.create(
                name=request.POST.get('name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                company=request.POST.get('company'),
                notes=request.POST.get('notes'),
                source='Manual',
                campaign=campaign
            )
            messages.success(request, f'Lead "{lead.name}" creado exitosamente')

        # Distribuir automáticamente si está habilitado
        if campaign.auto_distribute:
            distributor = get_lead_distributor(campaign)
            dist_result = distributor.distribute_leads()
            if dist_result['success']:
                messages.info(request, f'Se distribuyeron {dist_result["distributed"]} leads')

        return redirect('bots:campaign_detail', pk=campaign_pk)

    context = {
        'page_title': f'Subir Leads - {campaign.name}',
        'campaign': campaign
    }

    return render(request, 'bots/lead_upload.html', context)

@login_required
def lead_distribution_rules(request, campaign_pk):
    """Gestionar reglas de distribución para una campaña"""
    campaign = get_object_or_404(LeadCampaign, pk=campaign_pk)

    if request.method == 'POST':
        # Crear nueva regla
        LeadDistributionRule.objects.create(
            campaign=campaign,
            condition_field=request.POST.get('condition_field'),
            condition_operator=request.POST.get('condition_operator'),
            condition_value=request.POST.get('condition_value'),
            action_type=request.POST.get('action_type'),
            action_bot_id=request.POST.get('action_bot'),
            action_priority=request.POST.get('action_priority'),
            action_tag=request.POST.get('action_tag'),
            priority=int(request.POST.get('priority', 1))
        )

        messages.success(request, 'Regla de distribución creada')
        return redirect('bots:distribution_rules', campaign_pk=campaign_pk)

    # Obtener reglas existentes
    rules = campaign.distribution_rules.all().order_by('priority')

    # Bots disponibles para asignación
    available_bots = BotInstance.objects.filter(is_active=True)

    context = {
        'page_title': f'Reglas de Distribución - {campaign.name}',
        'campaign': campaign,
        'rules': rules,
        'available_bots': available_bots,
        'condition_fields': ['company', 'source', 'priority', 'email'],
        'condition_operators': LeadDistributionRule._meta.get_field('condition_operator').choices,
        'action_types': LeadDistributionRule._meta.get_field('action_type').choices
    }

    return render(request, 'bots/distribution_rules.html', context)

@login_required
def trigger_distribution(request, campaign_pk):
    """Disparar distribución manual de leads"""
    campaign = get_object_or_404(LeadCampaign, pk=campaign_pk)

    distributor = get_lead_distributor(campaign)
    result = distributor.distribute_leads()

    if result['success']:
        messages.success(request, f'Se distribuyeron {result["distributed"]} leads')
    else:
        messages.error(request, f'Error en distribución: {result.get("error", "Error desconocido")}')

    return redirect('bots:campaign_detail', pk=campaign_pk)

@login_required
def lead_list(request):
    """Lista general de leads con filtros"""
    # Filtros
    campaign_id = request.GET.get('campaign')
    status = request.GET.get('status')
    assigned_bot = request.GET.get('bot')
    search = request.GET.get('search')

    leads = Lead.objects.all().select_related('campaign', 'assigned_bot')

    if campaign_id:
        leads = leads.filter(campaign_id=campaign_id)

    if status:
        leads = leads.filter(status=status)

    if assigned_bot:
        leads = leads.filter(assigned_bot_id=assigned_bot)

    if search:
        leads = leads.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(company__icontains=search)
        )

    # Paginación
    paginator = Paginator(leads.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Estadísticas
    stats = Lead.objects.aggregate(
        total=Count('id'),
        new=Count('id', filter=Q(status='new')),
        assigned=Count('id', filter=Q(status='assigned')),
        converted=Count('id', filter=Q(status='converted'))
    )

    context = {
        'page_title': 'Lista de Leads',
        'page_obj': page_obj,
        'campaigns': LeadCampaign.objects.filter(is_active=True),
        'bots': BotInstance.objects.filter(is_active=True),
        'stats': stats,
        'filters': {
            'campaign': campaign_id,
            'status': status,
            'bot': assigned_bot,
            'search': search
        }
    }

    return render(request, 'bots/lead_list.html', context)

@login_required
def lead_detail(request, pk):
    """Detalle de un lead específico"""
    lead = get_object_or_404(Lead, pk=pk)

    context = {
        'page_title': f'Lead: {lead.name}',
        'lead': lead
    }

    return render(request, 'bots/lead_detail.html', context)

@login_required
def lead_export(request):
    """Exportar leads a CSV"""
    # Filtros similares a lead_list
    campaign_id = request.GET.get('campaign')
    status = request.GET.get('status')

    leads = Lead.objects.all().select_related('campaign', 'assigned_bot')

    if campaign_id:
        leads = leads.filter(campaign_id=campaign_id)
    if status:
        leads = leads.filter(status=status)

    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Nombre', 'Email', 'Teléfono', 'Empresa',
        'Estado', 'Prioridad', 'Campaña', 'Bot Asignado',
        'Fecha Creación', 'Fecha Conversión'
    ])

    for lead in leads:
        writer.writerow([
            lead.id,
            lead.name,
            lead.email,
            lead.phone,
            lead.company,
            lead.get_status_display(),
            lead.get_priority_display(),
            lead.campaign.name,
            lead.assigned_bot.name if lead.assigned_bot else '',
            lead.created_at.strftime('%Y-%m-%d %H:%M'),
            lead.converted_at.strftime('%Y-%m-%d %H:%M') if lead.converted_at else ''
        ])

    return response

# API Endpoints para AJAX

def api_campaign_stats(request, campaign_pk):
    """API para obtener estadísticas de campaña en tiempo real"""
    campaign = get_object_or_404(LeadCampaign, pk=campaign_pk)

    stats = campaign.leads.aggregate(
        total=Count('id'),
        new=Count('id', filter=Q(status='new')),
        assigned=Count('id', filter=Q(status='assigned')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        converted=Count('id', filter=Q(status='converted'))
    )

    # Distribución por bot
    bot_distribution = list(campaign.leads.values('assigned_bot__name').annotate(
        count=Count('id')
    ).filter(assigned_bot__isnull=False))

    return JsonResponse({
        'stats': stats,
        'bot_distribution': bot_distribution,
        'last_updated': timezone.now().isoformat()
    })

def api_trigger_distribution(request, campaign_pk):
    """API para disparar distribución desde JavaScript"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    campaign = get_object_or_404(LeadCampaign, pk=campaign_pk)

    distributor = get_lead_distributor(campaign)
    result = distributor.distribute_leads()

    return JsonResponse(result)
