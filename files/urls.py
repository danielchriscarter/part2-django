from django.urls import path

from . import views

app_name = 'files'
urlpatterns = [
        path('', views.index, name='index'),
        path('file/<int:file_id>/', views.fileview, name='file'),
        path('dir/<int:dir_id>/', views.dirview, name='directory'),
]
