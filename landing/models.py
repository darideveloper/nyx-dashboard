from django.db import models


class Text(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    link = models.URLField(max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Texto'
        verbose_name_plural = 'Textos'