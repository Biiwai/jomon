###################################################################
#
# Steam API data collector (including store/curation)
#
# Original version by Jerome Leclanche; used under CC0 license.
# https://github.com/jleclanche/scrape-scripts
#
# Latest version by Jeremiah Blanchard, 2016/12/21
#
###################################################################

from __future__ import division, absolute_import, print_function, unicode_literals
from builtins import *
import sys
import time

import bs4
import requests
import requests_cache
import json

# Cache all requests
requests_cache.install_cache()

API_ROOT = "https://api.steampowered.com"
STORE_API_ROOT = "https://store.steampowered.com"

CURATORS_PATH = "/curators/ajaxgetcurators/render/"
CURATORS_RECOMMENDATIONS_PATH = "/curator/%(id)i/ajaxgetcuratorrecommendations/"

APP_LIST_PATH = "/ISteamApps/GetAppList/v2"
APP_DETAILS_PATH = "/api/appdetails/"

APP_ID = "app_id"
CURATOR_ID = "clanID"

MAX_PER_PAGE = 50
RETRY_ATTEMPTS = 10
PAUSE_TIME_IN_SEC = 60


def getCurators():
    curatorIndex = 0
    totalCount = None
    curators = dict()

    while totalCount == None or curatorIndex < totalCount:
        retryAttempts = 0
        newData, totalCount = _getCurators(curatorIndex, MAX_PER_PAGE)
        while not newData:
            if retryAttempts > RETRY_ATTEMPTS:
                print("EMPTY RESPONSE. Exceeded retry attempts; giving up.")
                return None

            print("EMPTY RESPONSE. Waiting...")
            time.sleep(PAUSE_TIME_IN_SEC)
            newData, totalCount = _getCurators(curatorIndex, MAX_PER_PAGE)
            retryAttempts += 1

        print("[" + str(curatorIndex) + "/" + str(totalCount) + "] - Grabbed",len(newData),"curator profiles.")
        curators.update(newData)
        curatorIndex += len(newData)

    #curators = [{data.items() + (CURATOR_ID, key)} for key, data in curators.iteritems()]

    return curators


def getRecommendationsSet(curators):
    recommendations = {}
    recommendations = (getRecommendations(curators["id"], curators["name"]))

#    for curatorIndex, curator in enumerate(curators):
#        curatorId = curator[CURATOR_ID]
#        curatorInfo = str(curatorIndex + 1) + "/" + str(len(curators)) + "] " + curator["name"]
#        recommendations.extend(getRecommendations(int(curatorId), curatorInfo))

    return recommendations


def getRecommendations(curatorId, curatorLabel=None):
    curatorLabel = "[" + str(curatorLabel) if curatorLabel else str(curatorId) + "]"
    recIndex = 0
    totalCount = None
    recommendations = {}

    while totalCount == None:
        retryAttempts = 0
        print(curatorLabel, "- From #" + str(recIndex), "- ", end="")
        newRecs, totalCount = _getRecommendations(curatorId, recIndex, MAX_PER_PAGE)

        while newRecs == None:
            if retryAttempts > RETRY_ATTEMPTS:
                print("EMPTY RESPONSE. Exceeded retry attempts; giving up.")
                return None

            print("EMPTY RESPONSE for " + str(curatorId) + ". Waiting...")
            print(curatorLabel, "- From #" + str(recIndex), "- ", end="")
            time.sleep(PAUSE_TIME_IN_SEC)
            newRecs, totalCount = _getRecommendations(curatorId, recIndex, MAX_PER_PAGE)
            retryAttempts += 1

        print("Grabbed", len(newRecs), "recommendations.")
        recommendations = newRecs
        recIndex += len(newRecs)

    return recommendations


def getAppsList():
    path = API_ROOT + APP_LIST_PATH

    try:
        response = requests.get(path).json()
    except ValueError as e:
        response = None

    if response and "applist" in response and "apps" in response["applist"]:
        return response["applist"]["apps"]
    else:
        return None


def getAppDetailsSet(appIds):
    appIds = set(appIds)
    games = []

    for gameIndex, appId in enumerate(appIds):
        print("[" + str(gameIndex + 1) + "/" + str(len(appIds)) + "]", format(appId, "06d"), "- ", end="")
        newEntry = getAppDetails(appId)

        while not newEntry:
            print("EMPTY RESPONSE for " + str(appId) + ". Waiting...")
            print("[" + str(gameIndex + 1) + "/" + str(len(appIds)) + "]", format(appId, "06d"), "- ", end="")
            time.sleep(PAUSE_TIME_IN_SEC)
            newEntry = getAppDetails(appId)

        if 'name' in newEntry.keys():
            print(newEntry['name'])
        else:
            print("EMPTY DATA SET.")

        games.append(newEntry)

    return games


def getAppDetails(appId):
    path = STORE_API_ROOT + APP_DETAILS_PATH
    try:
        response = requests.get(path, params={ "appids": str(appId) }).json()
    except ValueError as e:
        response = None

    if not response or not str(appId) in response:
        return None
    else:
        response = response[str(appId)]

    if 'success' in response and response['success'] and 'data' in response:
        response['data'][APP_ID] = appId
        return response['data']
    else:
        return {APP_ID : appId}


def _getCurators(start=0, count=MAX_PER_PAGE):
    ret = {}
    params = {
        "start": start,
        "count": count,
    }
    path = STORE_API_ROOT + CURATORS_PATH
    try:
        data = requests.get(path, params=params).json()
    except ValueError as e:
        return None

    if data == None:
        return None

    soup = bs4.BeautifulSoup(data["results_html"], "html.parser")

	#increment 'start' to get the next group of curators
	#https://store.steampowered.com/curators/ajaxgetcurators/render?start=0&count=50

	# g_rgTopCurators = [{},{},{}] 			PRIMARY ARRAY THAT STORES CURATORS

    curators = []

    text = soup.find_all('script')[1].text
    curators = json.loads(text[text.index("var g_rgTopCurators = ") + len("var g_rgTopCurators = ") : text.index("var fnCreateCapsule")].strip().rstrip(';'))

    for curator in curators:
        curatorId = curator['clanID']
        desc = curator['curator_description']
        ret[curatorId] = {
            "page": curator['link'],
            "followers": curator['total_followers'],
            "name": curator['name'],
            "desc": desc,
            "avatar": curator['strAvatarHash'],
			"id": curator['clanID']
        }
    return ret, data["total_count"]

def _getRecommendations(curatorId, start=0, count=MAX_PER_PAGE):
    ret = {}
    params = {
        "start": start,
        "count": count,
    }
    path = STORE_API_ROOT + CURATORS_RECOMMENDATIONS_PATH % {"id": int(curatorId)}
    print(path)
    print()

    try:
        response = requests.get(path, params=params).json()
    except ValueError as e:
        return None

    if not response or not "results_html" in response:
        return None, None
    if "total_count" in response:
        totalCount = response["total_count"]
    else:
        totalCount = None

    soup = bs4.BeautifulSoup(response["results_html"], "html.parser")

    #Example of current API Endpoint of Recommendations
    #https://store.steampowered.com/curator/6883279/ajaxgetcuratorrecommendations/render?start=0&count=50

    found = False
    recommendations = {}
    reviewed_apps = soup.findAll("div", ["recommendation"])

    for rec in reviewed_apps:
        appid = rec['data-ds-appid']
        current_price = []
        temp_discount = rec.find("div",["discount_pct"])

        try:
            current_price = rec.find("div",["discount_final_price"])
            if current_price != None:
                current_price = current_price.text
            else:
                current_price = None
        except KeyError as k:
           current_price = None

        app_details = getAppDetails(int(appid))
		
        if temp_discount != None:
            discount = True
            discount_percent = temp_discount.text
            original_price = rec.find("div",["discount_original_price"]).text
        else:
            discount = False
            discount_percent = None
            original_price = current_price

        if rec.find("span")['class'][0] == "color_recommended":
            try:
                recommendations[appid] = {
                    "appid": appid,
                    "name": app_details['name'],
                    "desc": app_details['short_description'],
                    "app_src": rec.find("a")['href'].split("?snr=")[0],
					"discounted": discount,
                    "discount_percent": discount_percent,
                    "original_price": original_price,
                    "current_price": current_price,
                    "image_src": rec.find("img")['src'],
                    "recommendation_count": int(1),
                }
            except ValueError:
                print("Couldn't process entry:", rec)

    return recommendations, totalCount

def updateRecommendationCount(currentRecSet, newRecSet):
    unordered_dict = currentRecSet

    for key,value in newRecSet.items():
        if key not in unordered_dict:
            unordered_dict[key] = value
        else:
            unordered_dict[key]['recommendation_count']+=1

    return unordered_dict

def sortRecommendations(unsorted_dict):
    sorted_list = []
    temp_list = list(unsorted_dict.values())
    sorted_list = sorted(temp_list, key=lambda x: x['recommendation_count'],reverse=True)
    return sorted_list

# TESTING
#bob = getCurators()
#print(bob)
#print(bob['26436129'])
#print(bob['8788493'])
#bill = {'8788493': {'page': 'https://store.steampowered.com/curator/8788493-Crimeshot-Entertainment/', 'followers': 0, 'name': 'Crimeshot Entertainment', 'desc': 'Here can u see the games i recommend!', 'avatar': '456d68634fe56ac2b918ca9bc88028805548c9fe'}}
#jim = {'26436129': {'page': 'https://store.steampowered.com/curator/26436129-RealGoodGames/', 'followers': 33, 'name': 'RealGoodGames', 'desc': 'Sometimes you just need a bit of clarity and sincerity in your reviews...\nYou might find that here.', 'avatar': 'd7cacb3ebb6e97c5ede36cbfbc6e58a313e51eee'}}
#print(type(bill))
#print(type(jim))
#recbill = getRecommendationsSet(bill)
#recjim = getRecommendationsSet(jim)
#merged = updateRecommendationCount(recjim,recbill)
#sort = sortRecommendations(merged)
#print(merged)
#print()
#print(sort)
#print()
#temp = updateRecommendationCount(merged,recbill)
#print(sortRecommendations(temp))
#print(type(merged))
#print("HELLO WORLD !!!")
#print(getAppDetails(883710)['short_description'])

"""
def _getRecommendations(curatorId, start=0, count=MAX_PER_PAGE):
    path = STORE_API_ROOT + CURATORS_RECOMMENDATIONS_PATH % {"id": int(curatorId)}
    try:
        response = requests.get(path, params={ "start": start, "count": count }).json()
    except ValueError as e:
        response = None

    if not response or not "results_html" in response:
        return None, None
    if "total_count" in response:
        totalCount = response["total_count"]
    else:
        totalCount = None

    soup = bs4.BeautifulSoup(response["results_html"], "html.parser")
    rawRecommendations = soup.select(".recommendation")
    recommendations = []

    for rec in rawRecommendations:
        readmore = rec.select(".recommendation_readmore")
        stats = rec.select(".recommendation_stats")[0].find_all("div")
        likes = 0
        comments = 0
        date = ""
        for div in stats:
            if div.get("class") == "recommendation_stat":
                img = div.img
                if img["src"].endswith("icon_btn_rateup.png"):
                    likes = int(div.text.strip())
                elif img["src"].endswith("comment_quoteicon.png"):
                    comments = int(div.text.strip())
            else:
                date = div.text.strip().lstrip("Recommended: ")
        try:    
            recommendations.append({
                CURATOR_ID : curatorId,
                APP_ID : int(rec["data-ds-appid"]),
                "price": rec.select(".recommendation_app_price")[0].text.strip(),
                "desc": rec.select(".recommendation_desc")[0].text.strip(),
                "review_page": readmore and readmore[0].a["href"],
                "comments": comments,
                "likes": likes,
                "date": date,
            })
        except ValueError:
            print("Couldn't process entry:", rec)

    return recommendations, totalCount

"""