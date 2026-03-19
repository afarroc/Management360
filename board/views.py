from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from .models import Board, Card

class BoardListView(LoginRequiredMixin, ListView):
    model = Board
    template_name = 'board/board_list.html'
    context_object_name = 'boards'
    
    def get_queryset(self):
        return Board.objects.filter(owner=self.request.user)

class BoardDetailView(LoginRequiredMixin, DetailView):
    model = Board
    template_name = 'board/board_detail.html'
    context_object_name = 'board'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['card_types'] = Card.CARD_TYPES
        return context

class BoardCreateView(LoginRequiredMixin, CreateView):
    model = Board
    template_name = 'board/board_form.html'
    fields = ['name', 'description', 'layout', 'is_public']
    success_url = reverse_lazy('board:list')
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)