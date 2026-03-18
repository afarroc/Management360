from django.db import models
from django.conf import settings

class Game(models.Model):
    name = models.CharField(max_length=100, default="Mi ciudad")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='simcity_games',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    money = models.IntegerField(default=20000)
    map_data = models.JSONField(default=list)
    size = models.IntegerField(default=64)
    abm_state = models.JSONField(default=dict)
    engine_game_id = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.map_data:
            self.map_data = [[0] * self.size for _ in range(self.size)]
        else:
            self.size = len(self.map_data)
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'simcity'