from django.urls import path
from . import views

urlpatterns = [
    path('', views.indexView, name='index'),
    path('boardingpass/',views.boardingpass, name ='boardingpass'),
    path('idcard/',views.idcard, name ='idcard'),
    path('verification/',views.verification, name ='verification')
	]
