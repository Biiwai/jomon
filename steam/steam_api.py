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
CURATORS_RECOMMENDATIONS_PATH = "/curators/ajaxgetcuratorrecommendations/%(id)i/"
APP_LIST_PATH = "/ISteamApps/GetAppList/v2"
APP_DETAILS_PATH = "/api/appdetails/"

APP_ID = "app_id"
CURATOR_ID = "curator_id"

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

    curators = [{data.items() + (CURATOR_ID, key)} for key, data in curators.iteritems()]
    return curators


def getRecommendationsSet(curators):
    recommendations = []

    for curatorIndex, curator in enumerate(curators):
        curatorId = curator[CURATOR_ID]
        curatorInfo = str(curatorIndex + 1) + "/" + str(len(curators)) + "] " + curator["name"]
        recommendations.extend(getRecommendations(int(curatorId), curatorInfo))

    return recommendations


def getRecommendations(curatorId, curatorLabel=None):
    curatorLabel = "[" + str(curatorLabel) if curatorLabel else str(curatorId) + "]"
    recIndex = 0
    totalCount = None
    recommendations = []

    while totalCount == None or recIndex < totalCount:
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
        recommendations.extend(newRecs)
        recIndex += len(newRecs)

    return recommendations


def getAppsList():
    path = API_ROOT + APP_LIST_PATH

    try:
        response = requests.get(path).json()
    except ValueError as e:
        response = None

    if response and "applist" in response and "apps" in response["applist"]:
        return response["applist"]["apps"] #edited 'data' to response
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
    curators = soup.select(".steam_curator_row_ctn")
    for curator in curators:
        curatorId = int(curator.a["data-clanid"])
        href = curator.a["href"].strip()
        desc = curator.select(".steam_curator_desc")
        if not href:
            # bad data
            continue
        ret[curatorId] = {
            "page": href,
            "followers": int(curator.select(".num_followers")[0].text.replace(",", "")),
            "name": curator.select(".steam_curator_name")[0].text,
            "desc": desc and desc[0].text.strip(),
            "avatar": curator.select("img.steam_curator_avatar")[0]["src"],
        }
    return ret, data["total_count"]


def _getRecommendations(curatorId, start=0, count=MAX_PER_PAGE):
    path = STORE_API_ROOT + CURATORS_RECOMMENDATIONS_PATH % {"id": curatorId}
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

