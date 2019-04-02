from django.conf.urls import url
from django.urls import re_path
from . import views

urlpatterns = [
    url(r'^$', views.steamView, name='steamView'),
    url(r'^$', views.index, name='index'),
	re_path(r'^Mymethod', views.mymethod,name='mymethod'),
]