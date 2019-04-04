from django.conf.urls import url
from django.urls import re_path
from . import views

urlpatterns = [
    url(r'^$', views.steamView, name='steamView'),
    url(r'^$', views.index, name='index'),
	url(r'^FollowCurator', views.followClick,name='followClick'),
]