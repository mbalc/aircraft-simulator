"""Bind views to endpoints"""
from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

urlpatterns = [
    path('', views.flights, name='flights'),
    path('reserve', login_required(views.reserve), name='reserve'),
    path('RESTflights', views.get_flights, name='REST/flights'),
    path('details/<int:pkey>', views.details, name='details'),
]
