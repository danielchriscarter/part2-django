from django.contrib import admin

from .models import File, Directory

# Register your models here.

admin.site.register(File)
admin.site.register(Directory)
