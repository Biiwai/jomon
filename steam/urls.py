from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.steamView, name='steamView'),
    url(r'^$', views.index, name='index'),
]