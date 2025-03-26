from cv.forms import CurriculumForm as ProfileForm
from cv.models import Curriculum as Profile
from django.core.exceptions import ValidationError

def create_user_profile(user, bio, location, linkedin_url, github_url, twitter_url, facebook_url, instagram_url, company, job_title, country, address, phone, profile_picture):
    """
    Crea un perfil de usuario.
    
    Args:
        user (User): Instancia de usuario.
        bio (str): Biografía del usuario.
        location (str): Ubicación del usuario.
        linkedin_url (str): URL de LinkedIn.
        github_url (str): URL de GitHub.
        twitter_url (str): URL de Twitter.
        facebook_url (str): URL de Facebook.
        instagram_url (str): URL de Instagram.
        company (str): Compañía.
        job_title (str): Cargo.
        country (str): País.
        address (str): Dirección.
        phone (str): Teléfono.
        profile_picture (File): Imagen de perfil.
    
    Returns:
        Profile: Instancia del perfil creado.
    
    Raises:
        ValidationError: Si los datos son inválidos.
    """
    form = ProfileForm(data={
        'bio': bio,
        'location': location,
        'linkedin_url': linkedin_url,
        'github_url': github_url,
        'twitter_url': twitter_url,
        'facebook_url': facebook_url,
        'instagram_url': instagram_url,
        'company': company,
        'job_title': job_title,
        'country': country,
        'address': address,
        'phone': phone,
    }, files={'profile_picture': profile_picture})

    if form.is_valid():
        profile = form.save(commit=False)
        profile.user = user
        profile.save()
        return profile
    else:
        raise ValidationError(form.errors)