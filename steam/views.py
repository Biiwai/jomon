#from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView
from django.template.response import TemplateResponse

from . import update

def index(request):
    return HttpResponse("Hello, world. You're at the Steam index.")


def steamView(ListView):

	###### JSON format ######

	# Apps
	# {'appid': '######', 'name': 'APP TITLE'}

	myCurats, myRecs, myApps = update.pull()

	#myCurators = update.steam_api.getCurators()
	#myRecommendations = update.steam_api.getRecommendationsSet(myCurators)
	#myApplications = update.steam_api.getAppsList()

	template_name = 'index.html'

	#return HttpResponse(tempData)