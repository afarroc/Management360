from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.conf import settings
from .models import Board, Card, Activity

@login_required
@require_http_methods(["GET"])
def board_grid(request, board_id):
    """Vista parcial del grid de cards"""
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    cards = board.cards.all()[:settings.BOARD_CONFIG['CARDS_PER_PAGE']]
    
    return render(request, 'board/partials/card_grid.html', {
        'board': board,
        'cards': cards
    })

@login_required
@require_http_methods(["POST"])
def create_card_htmx(request, board_id):
    """Crear card sin recargar"""
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    
    card_type = request.POST.get('card_type', 'note')
    content = request.POST.get('content', '')
    title = request.POST.get('title', '')
    
    card = Card.objects.create(
        board=board,
        created_by=request.user,
        card_type=card_type,
        content=content,
        title=title or f"Nueva {card_type}"
    )
    
    # Registrar actividad
    Activity.objects.create(
        board=board,
        user=request.user,
        action='created',
        target=card.title,
        target_id=card.id
    )
    
    # Retornar solo la card para insertar al inicio
    return render(request, 'board/partials/card.html', {
        'card': card,
        'is_new': True
    })

@login_required
@require_http_methods(["DELETE"])
def delete_card_htmx(request, card_id):
    """Eliminar card sin recargar"""
    card = get_object_or_404(Card, id=card_id, board__owner=request.user)
    board_id = card.board.id
    card_title = card.title
    card.delete()
    
    # Registrar actividad
    Activity.objects.create(
        board_id=board_id,
        user=request.user,
        action='deleted',
        target=card_title
    )
    
    response = HttpResponse(status=200)
    response['HX-Trigger'] = 'cardDeleted'
    return response

@login_required
@require_http_methods(["POST"])
def toggle_pin_card(request, card_id):
    """Fijar/quitar pin de una card"""
    card = get_object_or_404(Card, id=card_id, board__owner=request.user)
    card.is_pinned = not card.is_pinned
    card.save()
    
    return render(request, 'board/partials/card.html', {'card': card})

@login_required
@require_http_methods(["GET"])
def load_more_cards(request, board_id):
    """Infinite scroll"""
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    offset = int(request.GET.get('offset', 0))
    limit = settings.BOARD_CONFIG['CARDS_PER_PAGE']
    
    cards = board.cards.all()[offset:offset + limit]
    has_more = board.cards.count() > offset + limit
    
    return render(request, 'board/partials/card_grid_items.html', {
        'cards': cards,
        'has_more': has_more,
        'next_offset': offset + limit
    })