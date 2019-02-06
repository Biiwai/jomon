#from django.shortcuts import render

from django.template import loader
from django.http import HttpResponse

from . import update

def index(request):
    return HttpResponse("Hello, world. You're at the Steam index.")

def steamView(request):
	# TESTING METHODS ONLY
	
	#myCurators = update.steam_api.getCurators()
	#myRecommendations = update.steam_api.getRecommendationsSet(myCurators)
	#myApplications = update.steam_api.getAppsList()
	
	###### JSON format ######

	# Applications
	# {'appid': '######', 'name': 'APP TITLE'}

	#myCurats, myRecs, myApps = update.pull()	# Use when pull() works

	myApplications = update.steam_api.getAppsList()	# testing only
	
	template_name = 'steamView.html'
	template = loader.get_template(template_name)
	context = {
		'myApplications': myApplications,
	}
	return HttpResponse(template.render(context,request))