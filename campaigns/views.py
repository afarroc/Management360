from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import ProviderRawData, ContactRecord, DiscadorLoad
from django.db.models import Count, Q


@login_required
def campaign_list(request):
    """Vista para listar todas las campañas"""
    campaigns = ProviderRawData.objects.all().order_by('-upload_date')

    # Filtros
    status_filter = request.GET.get('status')
    if status_filter:
        campaigns = campaigns.filter(status=status_filter)

    # Paginación
    paginator = Paginator(campaigns, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_choices': ProviderRawData.CAMPAIGN_STATUS,
        'current_status': status_filter,
    }
    return render(request, 'campaigns/campaign_list.html', context)


@login_required
def campaign_detail(request, pk):
    """Vista para ver detalle de una campaña"""
    campaign = get_object_or_404(ProviderRawData, pk=pk)

    # Estadísticas de la campaña
    contacts = campaign.contacts.all()
    total_contacts = contacts.count()
    contacts_by_type = contacts.values('contact_type').annotate(count=Count('contact_type'))

    # Información del discador si existe
    discador_load = None
    if hasattr(campaign, 'discador_load'):
        discador_load = campaign.discador_load

    context = {
        'campaign': campaign,
        'contacts': contacts[:50],  # Mostrar solo primeros 50
        'total_contacts': total_contacts,
        'contacts_by_type': contacts_by_type,
        'discador_load': discador_load,
    }
    return render(request, 'campaigns/campaign_detail.html', context)


@login_required
def contact_list(request, campaign_id):
    """Vista para listar contactos de una campaña"""
    campaign = get_object_or_404(ProviderRawData, pk=campaign_id)
    contacts = campaign.contacts.all().order_by('full_name')

    # Filtros
    contact_type_filter = request.GET.get('contact_type')
    if contact_type_filter:
        contacts = contacts.filter(contact_type=contact_type_filter)

    segment_filter = request.GET.get('segment')
    if segment_filter:
        contacts = contacts.filter(segment=segment_filter)

    # Búsqueda
    search_query = request.GET.get('search')
    if search_query:
        contacts = contacts.filter(
            Q(full_name__icontains=search_query) |
            Q(ani__icontains=search_query) |
            Q(dni__icontains=search_query)
        )

    # Paginación
    paginator = Paginator(contacts, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'campaign': campaign,
        'page_obj': page_obj,
        'contact_type_choices': ContactRecord.CONTACT_TYPE,
        'current_contact_type': contact_type_filter,
        'current_segment': segment_filter,
        'search_query': search_query,
    }
    return render(request, 'campaigns/contact_list.html', context)


@login_required
def discador_loads(request):
    """Vista para listar cargas al discador"""
    loads = DiscadorLoad.objects.all().select_related('campaign').order_by('-load_date')

    # Filtros
    status_filter = request.GET.get('status')
    if status_filter:
        loads = loads.filter(status=status_filter)

    # Paginación
    paginator = Paginator(loads, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_choices': DiscadorLoad.STATUS_CHOICES,
        'current_status': status_filter,
    }
    return render(request, 'campaigns/discador_loads.html', context)


@login_required
def discador_load_detail(request, pk):
    """Vista para ver detalle de una carga al discador"""
    load = get_object_or_404(DiscadorLoad, pk=pk)

    context = {
        'load': load,
        'campaign': load.campaign,
    }
    return render(request, 'campaigns/discador_load_detail.html', context)


@login_required
def dashboard(request):
    """Dashboard general de campañas"""
    # Estadísticas generales
    total_campaigns = ProviderRawData.objects.count()
    active_campaigns = ProviderRawData.objects.filter(status='processing').count()
    total_contacts = ContactRecord.objects.count()

    # Campañas recientes
    recent_campaigns = ProviderRawData.objects.all().order_by('-upload_date')[:5]

    # Estadísticas por estado
    campaigns_by_status = ProviderRawData.objects.values('status').annotate(count=Count('status'))

    # Contactos por tipo
    contacts_by_type = ContactRecord.objects.values('contact_type').annotate(count=Count('contact_type'))

    context = {
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'total_contacts': total_contacts,
        'recent_campaigns': recent_campaigns,
        'campaigns_by_status': campaigns_by_status,
        'contacts_by_type': contacts_by_type,
    }
    return render(request, 'campaigns/dashboard.html', context)
