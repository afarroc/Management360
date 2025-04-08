# -*- coding: utf-8 -*-
from django.shortcuts import render

def home_view(request):
    
    page_title = 'Home'    
    return render(request, 'home/home.html', {
        "page_title":page_title,
        }
                  )

def about_view(request):
    page_title = 'About Us'
    return render(request, "about/about.html",{
        'page_title':page_title
    })
    
def contact_view(request):
    page_title = "Contact"
    return render(request, "contact/contact.html",{
        'page_title':page_title
    })

def faq(request):
    page_title = "F.A.Q."
    return render(request, "faq/faq.html",{
        'page_title':page_title
    })

def blank(request):
        page_title="Blank Page"
        message="This is a blank page. You can add your own content here."
        
        return render(request, "blank/blank.html",{
            'page_title':page_title,
            'message':message   
    })