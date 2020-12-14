from django.db import models

# Create your models here.

class Directory(models.Model):
    name = models.CharField(max_length=128)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)

class File(models.Model):
    name = models.CharField(max_length=127)
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, null=False)

