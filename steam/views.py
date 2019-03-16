#from django.shortcuts import render

from django.template import loader
from django.http import HttpResponse

from . import update

def index(request):
	return HttpResponse("Hello, world. You're at the Steam index.")

"""
def jomonView(request):
	# 1) Call functions getCurators(), getRecommendationsSet(...), 
	updateRecommendationCount(...), sortRecommendations(...)
	# 2) Import html page in this file.
	# 3) Pass data to html page
	# 4) On html page, when "follow" has been clicked, add curator to
	followed_curators, increment curatorIndex for  and update current_recommendation_set
	with their recommended games, and finally for displaying purposes
	call sortRecommendations() to get proper order [].
	
	recommendations = {} # Our UNSORTED dict of recommendations
	followed_curator_ids = [] # Our array of followed curator ids ('clanID')
	curators = update.steam_api.getCurators() # Our dict of all steam curators
	# consider converting curators to a list()
	curatorId = 0
	if len(followed_curators) == 0:
		recommendations = update.steam_api.getRecommendationsSet(followed_curators[curatorId])

	
	if request.method == 'GET':
		template_name = 'steamView.html'
		template = loader.get_template(template_name)
		context = {
			'myApps': myApps,
			#'myRecs': myRecs,
			#'myCurats': myCurats,
		}
	return HttpResponse(template.render(context,request))
"""