'''
    This file is part of the EdTech library project at Full Sail University.
    Foobar is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    Foobar is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
    Copyright (C) 2014, 2015 Full Sail University.
'''

def getColumn(theDb, tableName, columnName, condition = None, conditionValues=(), isDistinct=False, suffix=""):
    return getColumns(theDb, tableName, (columnName, ), condition, conditionValues, isDistinct, suffix)

def getColumns(theDb, tableName, columnNames, condition = None, conditionValues=(), isDistinct=False, suffix=""):
    query = "SELECT " + ("DISTINCT " if isDistinct else "") + toQueryList(columnNames) + " FROM " + tableName
    query += ("" if condition == None or condition == "" else (" WHERE " + condition)) + " " + suffix

    cursor = theDb.cursor()
    cursor.execute(query, conditionValues)
    return cursor.fetchall()

def toQueryList(listItems):
    queryList = ""

    for listItem in listItems:
        queryList += listItem + ", "
        
    if len(listItems) != 0:
        queryList = queryList[:-2]  # drop trailing comma and space

    return queryList
