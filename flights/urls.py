"""Bind views to endpoints"""
from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

urlpatterns = [
    path('', views.flights, name='flights'),
    path('reserve', login_required(views.reserve), name='reserve'),
    path('REST/flights', views.get_flights, name='REST/flights'),
    path('REST/crews', views.get_crews, name='REST/crews'),
    path('REST/setCrew', views.set_crew, name='REST/setCrew'),
    path('details/<int:pkey>', views.details, name='details'),
]
