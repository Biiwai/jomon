#from django.shortcuts import render

from django.template import loader
from django.http import HttpResponse

from . import update

def index(request):
	return HttpResponse("Hello, world. You're at the Steam index.")

"""
def steamCuratorGames(request):

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
"""