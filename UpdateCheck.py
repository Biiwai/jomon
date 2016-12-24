from __future__ import division, absolute_import, print_function, unicode_literals
from builtins import *

import argparse
import random
import sqlite3
import json

import SteamApi
import SteamDb
import DbHelper

UPDATE_MAXIMUM_CURATORS = 10000
UPDATE_MAXIMUM_APPS = 100000
UPDATE_PORTION_DIVISOR = 7

DB_FILE = "SteamInfo.sqlite"

APPS = "apps"
CURATORS = "curators"
RECOMMENDATIONS = "recommendations"

APP_KEY = "app_id"
CURATOR_KEY = "curator_id"
RECOMMENDATION_KEY = "review_id"
UPDATE_KEY = "update_id"

UPDATE_APPS = "update_apps"
UPDATE_RECOMMENDATIONS = "update_recommendations"


def updateCurators(db, downloadRequested):
    maxFetch = min(DbHelper.getRecordCount(db, CURATORS) // UPDATE_PORTION_DIVISOR, UPDATE_MAXIMUM_CURATORS)
    newKeys = []
    updateKeys = []

    if downloadRequested:
        # Get recent curator info from Steam if requested and update the databases.
        curators = SteamApi.getCurators()
        newKeys = DbHelper.identifyNewEntries(db, CURATORS, UPDATE_RECOMMENDATIONS, CURATOR_KEY, curators.keys())
        maxFetch -= len(newKeys)

        # Sanity check - are there too many new entries being grabbed?
        if maxFetch < 0:
            print("Warning: new curators exceed maximum; probably indicates an issue.")
            maxFetch = 0

        # Identify update entries from preexisting curators.
        updateKeys = DbHelper.identifyUpdates(db, CURATORS, UPDATE_RECOMMENDATIONS, CURATOR_KEY, maxFetch)
        DbHelper.updateDatabase(curators, SteamDb.curatorSchema, db, CURATORS)

    else:
        # Otherwise, load up the data from the database and select entries to update.
        curators = DbHelper.readDatabase(SteamDb.curatorSchema, db, CURATORS)
        updateKeys = DbHelper.identifyUpdates(db, CURATORS, UPDATE_RECOMMENDATIONS, CURATOR_KEY, maxFetch)

    return dict([(key, curators[key]) for key in (list(newKeys) + list(updateKeys))])


def updateRecommendations(db, curators):
    rawRecData = SteamApi.getRecommendationsSet(curators)
    recommendations = dict()

    # Format updates so that they can be easily processed and stored.
    for curatorId, recSet in rawRecData.iteritems():
        for recommendation in recSet:
            copyKeys = [ APP_KEY, "desc", "readmore" ]
            newEntry = DbHelper.flattenDict(recommendation, copyKeys)
            newEntry[CURATOR_KEY] = curatorId
            recommendations[(int(curatorId) << 32) + recommendation[APP_KEY]] = newEntry

    DbHelper.updateDatabase(recommendations, SteamDb.recommendationSchema, db, RECOMMENDATIONS)
    DbHelper.deleteKeySet(db, UPDATE_RECOMMENDATIONS, UPDATE_KEY, curators.keys())
    return recommendations, rawRecData


def updateAppDetails(db, recommendations):
    maxFetch = min(DbHelper.getRecordCount(db, APPS) // UPDATE_PORTION_DIVISOR, UPDATE_MAXIMUM_APPS)
    appIdSet = list({recommendation["app_id"] for recommendation in recommendations.itervalues()})

    newKeys = DbHelper.identifyNewEntries(db, APPS, UPDATE_APPS, APP_KEY, appIdSet)
    maxFetch -= len(newKeys)

    # Sanity check - are there too many new entries being grabbed?
    if maxFetch < 0:
        print("Warning: new apps exceed maximum; probably indicates an issue.")
        maxFetch = 0

    # Identify update entries from preexisting apps.
    updateKeys = DbHelper.identifyUpdates(db, APPS, UPDATE_APPS, APP_KEY, maxFetch)

    rawAppData = SteamApi.getAppDetailsSet(list(newKeys) + list(updateKeys))
    apps = dict()

    for appId, appDetails in rawAppData.iteritems():
        copyKeys = [ "name", "about_the_game", "detailed_description", "background",
                       "header_image", "is_free", "publishers", "required_age", "type", "website" ]
        mappedKeys = { "metacritic_score" : ("metacritic", "score"),
                       "metacritic_url" : ("metacritic", "url"),
                       "num_recommendations" : ("recommendations", "total"),
                       "coming_soon" : ("release_date", "coming_soon"),
                       "release_date" : ("release_date", "date"),
                       "support_url" : ("support_info", "url") }
        apps[appId] = DbHelper.flattenDict(appDetails, copyKeys, mappedKeys)


    DbHelper.updateDatabase(apps, SteamDb.appSchema, db, APPS)
    DbHelper.deleteKeySet(db, UPDATE_APPS, UPDATE_KEY, apps.keys())
    return apps, rawAppData


def writeJsonFile(data, filename, **kwargs):
    if len(kwargs) == 0:
        kwargs = { "indent" : 4, "sort_keys" : True, "separators" : (',',':') }
    data = json.dumps(data, **kwargs)

    with open(filename, 'w') as outputFile:
        outputFile.write(data.decode('UTF-8'))


def main():
    parser = argparse.ArgumentParser(description='Pull updated information from web sources as needed.')
    parser.app_help = True
    parser.add_argument("-dc", "--download_curators", dest="downloadCurators",
                        action="store_true", help="Pull latest curator list from the web")
    args = parser.parse_args()

    # Pull updates, as appropriate, for data entries that are new / stale.
    db = sqlite3.connect(DB_FILE)    
    curators = updateCurators(db, args.downloadCurators)
    recommendations, rawRecData = updateRecommendations(db, curators)
    apps, rawAppData = updateAppDetails(db, recommendations)

    # Update previous data, as necessary, and rewrite to save raw info (in case of problems.)
    with open('curators.txt') as inputFile:
        curators.update(json.load(inputFile))

    with open('recommendations.txt') as inputFile:
        rawRecData.update(json.load(inputFile))

    with open('apps.txt') as inputFile:
        rawAppData.update(json.load(inputFile))

    writeJsonFile(curators, 'curators.txt')
    writeJsonFile(rawRecData, 'recommendations.txt')
    writeJsonFile(rawAppData, 'apps.txt')

if __name__ == "__main__":
    main()
