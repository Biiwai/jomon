from __future__ import division, absolute_import, print_function, unicode_literals
from builtins import *

from collections import OrderedDict
import sys
import time
import random
import sqlite3

DAYS_AGE_STALE_ENTRIES = 7
UPDATE_MAX = sys.maxsize

TIMESTAMP = "last_update"
DELIMITER = ";"

updateSchema = OrderedDict([
    ("update_id", "integer primary key"),
])


# Reformat nested dictionary to flatten it (for DB storage)
def flattenDict(source, copyKeys, mappedKeys = {}):
    newData = dict()
    if copyKeys == None:
        copyKeys = []

    # Directly copy from keys in the copyKeys container.
    for sourceKey in copyKeys:
        if sourceKey in source:
            if type(source[sourceKey]) is list or type(source[sourceKey]) is tuple:
                newData[sourcekey] = DELIMITER.join(source[sourceKey])
            else:
                newData[sourceKey] = source[sourceKey]
        else:
            newData[sourceKey] = None

    # For mapped keys, recurse down using the key set and then assign the final value.
    for destKey, sourceKeySet in mappedKeys.iteritems():
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


# Get the size of a table
def getRecordCount(db, table):
    cursor = db.cursor()
    cursor.execute("select count(*) from {}".format(table))    
    return(cursor.fetchall()[0][0])


# Get a specific set of columns
def getColumns(theDb, tableName, columns, condition = None, isDistinct=False, suffix=""):
    query = "select " + ("distinct " if isDistinct else '') + ", ".join(columns) + " from " + tableName
    query += (" where " + condition if condition else '') + suffix

    cursor = theDb.cursor()
    cursor.execute(query, conditionValues)
    return cursor.fetchall()


# Write a set of dictionary values to a table (strips out timestamp)
def readDatabase(schema, db, table):
    keyName = schema.keys()[0]
    valueNames = schema.keys()[1:]

    dataSet = dict()
    rows = getColumns(db, table, schema.keys())

    for row in rows:
        row = list(row)
        key = row.pop(0)
        entry = dataSet[key] = dict()

        for vName in valueNames:
            entry[vName] = row.pop(0)

    return dataSet


# Implementation of "upsert" (missing from sqlite; specific to our routines, including adding of timestamp)
def upsert(cursor, table, keyName, valueNames, key, values):
    try:
        queryString = "insert into " + table + " values(" + "?, " * (len(values) + 1) + "?)"
        cursor.execute(queryString, [key] + values + [str(time.time())])
    except sqlite3.IntegrityError:
        query = ",".join(["{0}=?".format(name) for name in valueNames]) + "," if valueNames else ""
        query = ("{}{}={!s}").format(query, TIMESTAMP, time.time())
        cursor.execute("update {} set {} where {}={}".format(table, query, keyName, key), values)


# Write a set of dictionary values to a table (including timestamp)
def updateDatabase(dataSet, schema, db, table):
    keyName = schema.keys()[0]
    valueNames = schema.keys()[1:]

    cursor = db.cursor()
    tableDesc = ", ".join(([" ".join((c, t)) for c, t in schema.iteritems()] + [TIMESTAMP + " real"]))
    cursor.execute("create table if not exists {}({})".format(table, tableDesc))

    for key, data in dataSet.iteritems():
        if not data == None:
            values = [str(data[vName]) for vName in valueNames]
        else:
            values = []
        upsert(cursor, table, keyName, valueNames, int(key), values)

    db.commit()


def deleteKeySet(db, table, primaryKey, keysToDelete):
    cursor = db.cursor()

    for key in keysToDelete:
        cursor.execute("delete from {} where {}={}".format(table, primaryKey, key))

    db.commit()


# Write new entries to the update database
def identifyNewEntries(db, table, updateTable, key, newKeys):
    # Get a list of keys that are pre-existing (in the database)
    query = "select {0!s} from {1} where {0!s} in ".format(key, table)
    query = "{} ({})".format(query, ",".join([str(entry) for entry in newKeys]))
    cursor = db.cursor()
    cursor.execute(query)

    # Find new keys not in the list from the database
    updates = set(newKeys) - {row[0] for row in cursor.fetchall()}
    updates = dict([(entry, None) for entry in updates])
    
    # Write out the updates to the database and return the list of keys
    updateDatabase(updates, updateSchema, db, updateTable)
    return updates.keys()


# Write updates to the database (after randomizing order)
def identifyUpdates(db, sourceTable, updateTable, primaryKey, maxFetch = UPDATE_MAX):
    staleKeys = []
    recentKeys = []
    currentInfo = dict(getColumns(db, sourceTable, [primaryKey, TIMESTAMP]))

    # Separate stale entries from recent ones.
    for key, timestamp in currentInfo.iteritems():
        ageInDays = (time.time() - timestamp) / (3600 * DAYS_AGE_STALE_ENTRIES);
        if ageInDays > 7:
            staleKeys.append(key)
        else:
            recentKeys.append(key)

    random.shuffle(staleKeys)
    random.shuffle(recentKeys)

    updates = (staleKeys + recentKeys)[:maxFetch]
    updates = dict([(key, None) for key in updates])
    updateDatabase(updates, updateSchema, db, updateTable)
    return updates.keys()
