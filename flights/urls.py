from django.urls import path

from . import views

urlpatterns = [
    path('', views.flights, name='flights'),
    path('reserve', views.reserve, name='reserve'),
    path('details/<int:pkey>', views.details, name='details'),
    path('dziwne', views.old, name='old'),
    # path('class', classView.as_view(), name='classView'),
    path('404', views.myErrorPage, name='errorNotFound'),
]

