
# DatabaseVersion.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, 
#                Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# version management helper class

from sqlobject import sqlhub
from sutekh.SutekhObjects import PhysicalCardSet, AbstractCardSet, PhysicalCard,\
                                 AbstractCard, VersionTable

dTableMap={
        "PhysicalCardSet" : PhysicalCardSet.sqlmeta.table,
        "AbstractCardSet" : AbstractCardSet.sqlmeta.table,
        "AbstractCard"    : AbstractCard.sqlmeta.table,
        "PhysicalCard"    : PhysicalCard.sqlmeta.table
        }

class DatabaseVersion(object):
    def __init__(self,connection=None):
        if connection is None:
            connection=sqlhub.processConnection
        VersionTable.createTable(ifNotExists=True,connection=connection)

    def setVersion(self,oTable,iTableVersion,connection=None):
        if connection is None:
            connection=sqlhub.processConnection
        sTableName=oTable.sqlmeta.table
        aVer=VersionTable.selectBy(TableName=sTableName,connection=connection)
        if aVer.count()==0:
            VersionTable(TableName=sTableName,
                    Version=iTableVersion,connection=connection)
        elif aVer.count()==1:
            for version in aVer:
                if version.Version!=iTableVersion:
                    VersionTable.delete(version.id,connection=connection)
                    VersionTable(TableName=sTableName,
                       Version=iTableVersion,connection=connection)
        elif aVer.count()>1:
            print "Multiple version entries for ",sTableName," in the database"
            print "Giving up. I suggest dumping and reloading everything"
            return False
        return True

    def getVersion(self,oTable,connection=None):
        if connection is None:
            connection=sqlhub.processConnection
        ver=-1
        # Define PyProtocols adaptor for this??
        if type(oTable) is str:
            sName=dTableMap[oTable]
        else:
            sName=oTable.sqlmeta.table
        aVer=VersionTable.selectBy(TableName=sName,connection=connection)
        if aVer.count()<1:
            ver=-1
        elif aVer.count()==1:
            for version in aVer:
                ver=version.Version
        else:
            print "Multiple version entries for ",oTable.sqlmeta.table," in the database"
            print "Giving up. I suggest dumping and reloading everything"
            # Should this be an exception?
            ver=-999
        return ver

    def checkVersions(self,aTable,aTableVersion,connection=None):
        bRes=True
        for oTable,iVersion in zip(aTable,aTableVersion):
            bRes=bRes and self.getVersion(oTable,connection=connection)==iVersion
        return bRes

    def getBadTables(self,aTable,aTableVersion,connection=None):
        aBadTables=[]
        for oTable,iVersion in zip(aTable,aTableVersion):
            if not self.getVersion(oTable,connection=connection)==iVersion:
                aBadTables.append(oTable.sqlmeta.table)
        return aBadTables

