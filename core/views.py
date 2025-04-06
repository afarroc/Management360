from datetime import timedelta, timezone
from pyexpat.errors import messages
from django.shortcuts import get_object_or_404, render
from events.views import statuses_get

def home_view(request):
    page_title = 'Home 2.0'
    return render(request, 'core/home.html', {
        "page_title":page_title,
        })

def about_view(request):
    return render(request, 'core/about.html')

def contact_view(request):
    return render(request, 'core/contact.html')

def about(request):
    username = "Nano"
    return render(request, "about/about.html",{
        'username':username
    })

def faq(request):
    page_title = "F.A.Q."
    return render(request, "faq/faq.html",{
        'page_title':page_title
    })

def contact(request):
    page_title = "Contact"
    return render(request, "contact/contact.html",{
        'page_title':page_title
    })

def blank(request):
        page_title="Blank Page"
        return render(request, "layouts/blank.html",{
            'page_title':page_title
    })