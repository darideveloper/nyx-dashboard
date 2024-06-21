from django.db import models


class category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
    
    def __str__(self):
        return self.name
        

class Text(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(category, on_delete=models.CASCADE)
    value = models.TextField()
    link = models.URLField(max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Texto'
        verbose_name_plural = 'Textos'

    def __str__(self):
        return self.key