from __future__ import division, absolute_import, print_function, unicode_literals
from builtins import *
import json
import steam

def getAppIdsFromRecommendations(recommendations):
    appIdList = []

    for recSet in recommendations.itervalues():
        for recommendation in recSet:
            appIdList.append(recommendation["appid"])

    return sorted(appIdList)


def writeJsonFile(data, filename, **kwargs):
    if len(kwargs) == 0:
        kwargs = { "indent" : 4, "sort_keys" : True, "separators" : (',',':') }
    data = json.dumps(data, **kwargs)

    with open(filename, 'w') as outputFile:
        outputFile.write(data.decode('UTF-8'))


def main():
    curators = steam.getCurators()
    writeJsonFile(curators, 'curators.txt')

    recommendations = steam.getRecommendationsSet(curators)
    writeJsonFile(recommendations, 'recommendations.txt')

    appIdList = getAppIdsFromRecommendations(recommendations)
    gameData = steam.getAppDetailsSet(appIdList)
    writeJsonFile(gameData, 'games.txt')

#    with open('curators.txt') as inputFile:
#        curators = json.load(inputFile)

#    with open('recommendations.txt') as inputFile:
#        recommendations = json.load(inputFile)


if __name__ == "__main__":
    main()
