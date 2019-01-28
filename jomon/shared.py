import random
import sys

from django.utils import timezone
from django.db import models
from django.db.models.fields.related import ForeignObjectRel, ForeignKey
from django.db import transaction

#Constants
URL_MAX_LENGTH = 2048 # Practically, all URLs from Steam seem to be under 300, but we're being cautious.
CHAR_MAX_LENGTH = 255 # General limitation for use as unique field; however, can be overridden.
TIMESTAMP = "last_update"
DAYS_AGE_STALE_ENTRIES = 7
DELIMITER = ";"
UPDATE_MAX = sys.maxsize
UPDATE_ID = "record"


class SuperModel(models.Model):
    last_update = models.DateTimeField(auto_now=True)


    class Meta:
        abstract = True


    @classmethod
    def getUpdateClass(Target):
        if not hasattr(Target, '_updateClass'):
            attrs = {  
					   UPDATE_ID : models.OneToOneField(Target, primary_key=True, on_delete=models.CASCADE),
                       TIMESTAMP : models.DateTimeField(auto_now=True),
                      '__module__' : Target.__module__
                    }
            Target._updateClass = type(Target.__name__ + "Update", (models.Model,), attrs)
        return Target._updateClass


    @classmethod
    def getFields(Target):
        fields = [fd for fd in Target._meta.get_fields() if not isinstance(fd, ForeignObjectRel)]
        return [fd.name + ("_id" if isinstance(fd, ForeignKey) else "") for fd in fields if fd.name != 'last_update']


    @classmethod
    def getFromDict(Target, data):
        if not isinstance(data, dict):
            raise TypeError("Data must be in dictionary format.")

#        print({param: data[param] for param in Target.getFields() if param in data})
        return Target(**{param: data[param] for param in Target.getFields() if param in data})


    def getDict(self):
        return {attr: self.__dict__[attr] for attr in type(self).getFields()}


# Write new entries to the update database
def identifyNewEntries(RowClass, newKeys):
    # Get a list of keys that are not yet in the records
    newKeys = set(newKeys) - set(RowClass.objects.filter(pk__in=newKeys))

    # Write out the updates to the database and return the list of keys
    with transaction.atomic():
        [RowClass.getUpdateClass()(key).save() for key in newKeys]
    return newKeys


# Write updates to the database (after randomizing order)
def identifyUpdates(RowClass, maxFetch = UPDATE_MAX):
    staleKeys = []
    recentKeys = []

    # Separate stale entries from recent ones.
    for (key, timestamp) in RowClass.objects.values_list(RowClass._meta.pk.name, TIMESTAMP):
        if (timezone.now() - timestamp).days >= DAYS_AGE_STALE_ENTRIES:
            staleKeys.append(key)
        else:
            recentKeys.append(key)

    # Randomize the ordering within the who key sets, then pull entries up to the maximum.
    random.shuffle(staleKeys)
    random.shuffle(recentKeys)

    updateKeys = (staleKeys + recentKeys)[:maxFetch]
    with transaction.atomic():
        [RowClass.getUpdateClass()(key).save() for key in updateKeys]
    return updateKeys



# Reformat nested dictionary to flatten it (for DB storage)
def flattenDict(source, copyKeys, mappedKeys = {}):
    newData = dict()
    if copyKeys == None:
        copyKeys = []

    # Directly copy from keys in the copyKeys container.
    for sourceKey in copyKeys:
        if sourceKey in source:
            if type(source[sourceKey]) is list or type(source[sourceKey]) is tuple:
                newData[sourceKey] = DELIMITER.join(source[sourceKey])
            else:
                newData[sourceKey] = source[sourceKey]
        else:
            newData[sourceKey] = None

    # For mapped keys, recurse down using the key set and then assign the final value.
    for destKey, sourceKeySet in mappedKeys.items():
        if not type(sourceKeySet) is tuple:
            sourceKeySet = [ sourceKeySet ]

        value = source
        for sourceKey in sourceKeySet:
            if sourceKey in value:
                value = value[sourceKey]
            else:
                value = None
                break

        if type(value) is list or type(value) is tuple:
            newData[destKey] = DELIMITER.join(value)
        else:
            newData[destKey] = value

    return newData

