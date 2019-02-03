import argparse
import datetime
import json
from django.db import transaction

from steam.models import *
from jomon.shared import *
from steam import steam_api

UPDATE_MAXIMUM_CURATORS = 10000
UPDATE_MAXIMUM_APPS = 100000
UPDATE_PORTION_DIVISOR = 7
REC_KEY = "review_id"


def importData(curatorFile = "curators.txt", recFile = "recommendations.txt", appFile = "applications.txt"):
    # Load the data from the Json files
    with open(curatorFile) as inputFile:
        curatorData = json.load(inputFile)
    with open(recFile) as inputFile:
        rawRecData = json.load(inputFile)
    with open(appFile) as inputFile:
        rawAppData = json.load(inputFile)
    return _updateRecords(curatorData, rawRecData, rawAppData)


def exportData(curatorFile = "curators.txt", recFile = "recommendations.txt", appFile = "applications.txt"):
    curators = update.updateCurators()
    recommendations = update.updateRecommendations(curators)
    applications = update.updateApplications(recommendations)

    _writeJsonFile([entry.getDict() for entry in curators], curatorFile)
    _writeJsonFile([entry.getDict() for entry in recommendations], recFile)
    _writeJsonFile([entry.getDict() for entry in recommendations], appFile)	#(ky-edit removed ')

    return curators, recommendations, applications


def pull(download = False):
    # Pull updates, as appropriate, for data entries that are new / stale.
    return _updateRecords(steam_api.getCurators()) if download else updateRecords()

# TODO:
def updateRecords():
	# Method used in 'pull' above but, was never defined.
	return 0

def main():
    parser = argparse.ArgumentParser(description='Pull updated information from web sources as needed.')
    parser.app_help = True
    parser.add_argument("-dc", "--download_curators", dest="downloadCurators",
                        action="store_true", help="Pull latest curator list from the web")
    args = parser.parse_args()
    pull(args.downloadCurators)


def _writeJsonFile(data, filename, **kwargs):
    if len(kwargs) == 0:
        kwargs = { "indent" : 4, "sort_keys" : True, "separators" : (',',':') }
    data = json.dumps(data, **kwargs)

    with open(filename, 'w') as outputFile:
        outputFile.write(data.decode('UTF-8'))


# Update records for Steam (either view dataset(s) or from the web)
def _updateRecords(curatorData = None, recData = None, rawAppData = None):
    # Select curators to be updated from the new and existing data set.
    if curatorData:
        updateKeys = identifyNewEntries(Curator, [data[Curator._meta.pk.name] for data in curatorData])
        curators = [Curator.getFromDict(entry) for entry in curatorData]
        with transaction.atomic():
            [entry.save() for entry in curators]
    else:
        maxFetch = min(Curator.objects.all().count() // UPDATE_PORTION_DIVISOR, UPDATE_MAXIMUM_CURATORS)
        updateKeys = identifyUpdates(Curator, maxFetch)
        curators = Curator.objects.filter(pk__in=updateKeys)
        curatorData = [curator.getDict() for curator in curators]

    # Grab the raw curator recommendation data from Steam if needed.
    if recData == None:
        recData = steam_api.getRecommendationsSet(curatorData)

    # Convert each recommendation into an object and save it in the database.
    recommendations = []
    with transaction.atomic():
        for entry in recData:
            entry[REC_KEY] = (int(entry[steam_api.CURATOR_ID]) << 32) + entry[steam_api.APP_ID]
            newRec = Recommendation.getFromDict(entry)
            recommendations.append(newRec)
            newRec.save()

        # Once we've finished the updates, remove the curator update entries from the database.
        curatorKeys = [int(curator[steam_api.CURATOR_ID]) for curator in curatorData]
        Curator.getUpdateClass().objects.filter(pk__in=curatorKeys).delete()

    # If we have a set of applications to update, go with those; otherwise, pull from the recommendations & records.
    if rawAppData:
        appIdSet = {app[steam_api.APP_ID] for app in rawAppData}        
    else:
        appIdSet = {recommendation.app_id for recommendation in recommendations}
        newKeys = identifyNewEntries(Application, appIdSet)

        maxFetch = min(Application.objects.all().count() // UPDATE_PORTION_DIVISOR, UPDATE_MAXIMUM_APPS)
        maxFetch -= len(newKeys)

        # Sanity check - are there too many new entries being grabbed?
        if maxFetch < 0:
            print("Warning: new apps exceed maximum; probably indicates an issue.")
            maxFetch = 0

        # Identify update entries from preexisting apps.
        updateKeys = identifyUpdates(Application, maxFetch)
        rawAppData = steam_api.getAppDetailsSet(list(newKeys) + list(updateKeys))

    # Idenify new mapping for dictionary of data (to simplify database storage)
    copyKeys = [ "app_id", "name", "background", "is_free", "publishers", "required_age", "type", "website" ]
    mappedKeys = { "about" : ("about_the_game",),
                   "desc" : ("detailed_description",),
                   "header" : ("header_image",),
                   "metacritic_score" : ("metacritic", "score"),
                   "metacritic_page" : ("metacritic", "url"),
                   "recommendations" : ("recommendations", "total"),
                   "coming_soon" : ("release_date", "coming_soon"),
                   "release_date" : ("release_date", "date"),
                   "support_page" : ("support_info", "url") }

    # Flatten the dictionary using the new mapping.
    rawAppData = [flattenDict(appDetails, copyKeys, mappedKeys) for appDetails in rawAppData]

    # Process application details.
    applications = []
    with transaction.atomic():
        for entry in rawAppData:
            try:
                entry["release_date"] = datetime.datetime.strptime(entry["release_date"], "%b %d, %Y")
            except:
                entry["release_date"] = None
            #print(entry)
            newApp = Application.getFromDict(entry)
            #print(newApp.__dict__)
            applications.append(newApp)
            newApp.save()

        # When we're done updating the database, remove the update entries from the database.
        appKeys = [application.app_id for application in applications]
        Application.getUpdateClass().objects.filter(pk__in=appKeys).delete()

    # Return the objects we generated / loaded.
    return curators, recommendations, applications




if __name__ == "__main__":
    main()
