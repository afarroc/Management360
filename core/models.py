from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    excerpt = models.CharField(max_length=300)
    publication_date = models.DateTimeField(auto_now_add=True)
    
    def get_absolute_url(self):
        return f'/articles/{self.id}/'  # Ajusta según tus URLs