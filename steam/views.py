import random
from . import update

from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django_ajax.decorators import ajax

recommendations = {} # Our UNSORTED dict of recommendations
temp_recommendations = {}
sorted_recommendations = [] # Our SORTED list of recommendations

followed_curator_ids = [] # Our array of followed curator ids ('clanID')
curators = {} # Our dict of all steam curators
five_random_curators = [] # Our list of 5 random suggested curators to follow
random_curators = [] # list of random curators

def index(request):
	return HttpResponse("Hello, world. You're at the Steam index.")

@ajax
def mymethod(request):
	print("Getting curator info...")

	# Get curator id
	id = request.get_full_path().split("id=")[1]

	# Get curator from 'curators' dict
	curator = curators[id];
	print(curator)
	# Add curator id to list if not already in list
	if id not in followed_curator_ids:
		
		global recommendations
		global sorted_recommendations
		
		followed_curator_ids.append(id);

		temp_recommendations = update.steam_api.getRecommendationsSet((curator))

		if len(followed_curator_ids) > 0:
			recommendations = update.steam_api.updateRecommendationCount(recommendations, temp_recommendations)
			sorted_recommendations = update.steam_api.sortRecommendations(recommendations)
		else:
			recommendations = temp_recommendations
		
		print(sorted_recommendations)
		
	return {"message": "hello PLUTO!"}

def steamView(request):
	# Get all steam curators
	global curators
	curators = update.steam_api.getCurators()

	# Get 5 random curators and append to our list to be passed to 'Suggested Curators'

	five_random_curators.append(curators[random.choice(list(curators.keys()))])
	five_random_curators.append(curators[random.choice(list(curators.keys()))])
	five_random_curators.append(curators[random.choice(list(curators.keys()))])
	five_random_curators.append(curators[random.choice(list(curators.keys()))])
	five_random_curators.append(curators[random.choice(list(curators.keys()))])

	mylist = [{'id': '346110', 'desc': 'jim is cool'}, {'id': '730', 'desc': 'bob is cooler'}]

	#return render(request,'../templates/steamView.html',{"list1": sorted_recommendations, "list2": five_random_curators})

	return render(request,'../templates/steamView.html',{"list1": mylist, "list2": five_random_curators})

