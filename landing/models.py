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
    
    
class Image(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/')
    link = models.URLField(max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Imagen'
        verbose_name_plural = 'Imágenes'
    
    def __str__(self):
        return self.key


class Video(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(category, on_delete=models.CASCADE)
    video = models.FileField(upload_to='videos/')
    
    class Meta:
        verbose_name = 'Video'
        verbose_name_plural = 'Videos'
    
    def __str__(self):
        return self.key