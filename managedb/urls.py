from django.urls import path

from . import views

urlpatterns = [
        path('', views.index, name='index'),
        path('select/', views.select, name='select'),
        path('setup/', views.setup, name='setup'),
]
