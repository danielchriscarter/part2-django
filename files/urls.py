from django.urls import path

from . import views

app_name = 'files'
urlpatterns = [
        path('', views.index, name='index'),
        path('file/<int:file_id>/', views.fileview, name='file'),
        path('file/<int:file_id>/edit', views.fileedit, name='fileedit'),
        path('dir/<int:dir_id>/', views.dirview, name='directory'),
        path('newfile/<int:dir_id>/', views.newfile, name='newfile'),
        path('newdir/<int:dir_id>/', views.newdir, name='newdir'),
]
