#from django.shortcuts import render

from django.template import loader
from django.http import HttpResponse

from . import update

def index(request):
	return HttpResponse("Hello, world. You're at the Steam index.")

def curator(request):
	# TESTING METHODS ONLY

	#myCurats = update.steam_api.getCurators()
	#myRecs = update.steam_api.getRecommendationsSet(myCurats)
	#myApps = update.steam_api.getAppsList()
	#myAppDetails[appid] = update.steam_api.getAppDetails(appid)
	
	###### JSON format ######

	# Applications
	# {'appid': '######', 'name': 'APP TITLE'}

	#myCurats, myRecs, myApps = update.pull()	# Use when pull() works

	

	if request.method == 'GET':
		myApps = update.steam_api.getAppsList()	# testing only

		template_name = 'steamView.html'
		template = loader.get_template(template_name)
		context = {
			'myApps': myApps,
			#'myRecs': myRecs,
			#'myCurats': myCurats,
		}
	return HttpResponse(template.render(context,request))