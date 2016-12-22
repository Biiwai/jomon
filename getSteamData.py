from __future__ import division, absolute_import, print_function, unicode_literals
from builtins import *

import json
import sqlite3
import time

import EtDatabase
import steam
import SteamDb

def getAppIdsFromRecommendations(recommendations):
    appIdList = []

    for recSet in recommendations.itervalues():
        for recommendation in recSet:
            appIdList.append(recommendation["appid"])

    return sorted(appIdList)


def reformatAppDetails(apps):
    returnData = dict()
    for appId, appDetails in recommendations.iteritems():
        newEntry = dict()
        copyKeys = [ "name", "about_the_game", "detailed_description", "background",
                       "header_image", "isfree", "required_age", "type", "website" ]
        for key in copyKeys:
            newEntry[key] = appDetails[key]

        newEntry["metacritic_score"] = appDetails["metacritic"]["score"]
        newEntry["metacritic_url"] = appDetails["metacritic"]["url"]
        newEntry["publishers"] = ";".join(appDetails["publishers"])
        newEntry["recommendations"] = appDetails["recommendations"]["total"]
        newEntry["coming_soon"] = appDetails["release_date"]["coming_soon"]
        newEntry["release_date"] = appDetails["release_date"]["date"]
        newEntry["support_url"] = appDetails["support_info"]["url"]

        returnData[appId] = newEntry
    return returnData


def reformatRecommendations(recommendations):
    returnData = dict()
    for curatorId, recSet in recommendations.iteritems():
        for recommendation in recSet:
            newEntry = dict()
            newEntry["curatorId"] = curatorId
            newEntry["appId"] = recommendation["appId"]
            newEntry["desc"] = recommendation["desc"]
            newEntry["readmore"] = recommendation["readmore"]

            # Create a unique primary key from the recommmender and app IDs
            returnData[(curatorId << 32) + recSet["appId"]] = newEntry
    return returnData


def writeJsonFile(data, filename, **kwargs):
    if len(kwargs) == 0:
        kwargs = { "indent" : 4, "sort_keys" : True, "separators" : (',',':') }
    data = json.dumps(data, **kwargs)

    with open(filename, 'w') as outputFile:
        outputFile.write(data.decode('UTF-8'))


def upsert(cursor, table, keyName, valueNames, key, values):
    try:
        queryString = "insert into " + table + " values(" + "?, " * (len(values) + 1) + "?)"
        cursor.execute(queryString, [key] + values + [str(time.time())])
    except sqlite3.IntegrityError:
        varString = ", ".join(["{0}=?".format(name) for name in valueName])
        varString = "{}, last_update={!s}".format(varString, time.time())
        cursor.execute("update {} set {} where {}={}".format(table, varString, keyName, key), values)


def writeToDatabase(dataSet, schema, dbFile, table):
    keyName = schema.keys()[0]
    valueNames = schema.keys()[1:]

    connection = sqlite3.connect(dbFile)
    cursor = connection.cursor()
    tableDesc = ", ".join(([" ".join((c, t)) for c, t in schema.iteritems()] + ["last_update text"]))
    cursor.execute("create table if not exists {}({})".format(table, tableDesc))

    for key, data in dataSet.iteritems():
        values = [str(data[vName]) for vName in valueNames]
        upsert(cursor, table, keyName, valueNames, int(key), values)

    connection.commit()
    connection.close()


def readFromDatabase(schema, dbFile, table):
    keyName = schema.keys()[0]
    valueNames = schema.keys()[1:]
    connection = sqlite3.connect(dbFile)

    dataSet = dict()
    rows = EtDatabase.getColumns(connection, table, schema.keys())# + ["last_update"])

    for row in rows:
        row = list(row)
        key = row.pop(0)
        entry = dataSet[key] = dict()

        for vName in valueNames:
            entry[vName] = row.pop(0)

    return dataSet


def main():
#    curators = steam.getCurators()
#    writeJsonFile(curators, 'curators.txt')
#    writeToDatabase(curators, SteamDb.curatorsSchema, "SteamInfo.sqlite", "curators")

    curators = readFromDatabase(SteamDb.curatorsSchema, "SteamInfo.db", "curators")

    recommendations = steam.getRecommendationsSet(curators)
    writeToDatabase(reformatRecommendations(recommendations), SteamDb.recommendationsSchema, "SteamInfo.sqlite", "recommendations")
    writeJsonFile(recommendations, 'recommendations.txt')

    appIdList = getAppIdsFromRecommendations(recommendations)
    gameData = steam.getAppDetailsSet(appIdList)
    writeToDatabase(reformatAppDetails(gameData), SteamDb.appsSchema, "SteamInfo.sqlite", "apps")
    writeJsonFile(gameData, 'games.txt')

#    with open('curators.txt') as inputFile:
#        curators = json.load(inputFile)

#    with open('recommendations.txt') as inputFile:
#        recommendations = json.load(inputFile)


if __name__ == "__main__":
    main()
