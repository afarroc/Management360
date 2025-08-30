from django import template

register = template.Library()

@register.filter
def youtube_embed_url(url):
    """
    Converts a YouTube URL into an embed URL.
    """
    import re
    
    # Pattern for YouTube watch URLs
    watch_pattern = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    
    match = re.match(watch_pattern, url)
    if match:
        video_id = match.group(6)
        return f'https://www.youtube.com/embed/{video_id}'
    
    return url