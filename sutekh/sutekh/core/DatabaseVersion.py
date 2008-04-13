# DatabaseVersion.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# version management helper class

"""Versioning support for Sutekh"""

from sqlobject import sqlhub
from sutekh.core.SutekhObjects import VersionTable

def _get_connection(oConn):
    """Ensure we have a vaild connection object"""
    if oConn is None:
        return sqlhub.processConnection
    else:
        return oConn

class DatabaseVersion(object):
    """Class to handle all the database manipulation aspects."""
    # pylint: disable-msg=R0201
    # All these are methods for convience

    def __init__(self, oConn=None):
        oConn = _get_connection(oConn)
        VersionTable.createTable(ifNotExists=True, connection=oConn)

    def set_version(self, oTable, iTableVersion, oConn=None):
        """Set the version for oTable to iTableVersion"""
        oConn = _get_connection(oConn)
        try:
            sTableName = oTable.sqlmeta.table
        except AttributeError:
            return False
        aVer = VersionTable.selectBy(TableName=sTableName, connection=oConn)
        if aVer.count() == 0:
            VersionTable(TableName=sTableName,
                         Version=iTableVersion, connection=oConn)
        elif aVer.count() == 1:
            for oVersion in aVer:
                if oVersion.Version != iTableVersion:
                    VersionTable.delete(oVersion.id, connection=oConn)
                    VersionTable(TableName=sTableName,
                                 Version=iTableVersion, connection=oConn)
        elif aVer.count() > 1:
            print "Multiple version entries for %s in the database" \
                    % sTableName
            print "Giving up. I suggest dumping and reloading everything"
            return False
        return True

    def get_table_version(self, oTable, oConn=None):
        """Get the version number for oTable.

           returns -1 if no version info exists.
           """
        oConn = _get_connection(oConn)
        iTableVersion = -1
        try:
            sName = oTable.sqlmeta.table
        except AttributeError:
            return iTableVersion
        aVer = VersionTable.selectBy(TableName=sName, connection=oConn)
        if aVer.count() < 1:
            iTableVersion = -1
        elif aVer.count() == 1:
            for oVersion in aVer:
                iTableVersion = oVersion.Version
        else:
            print "Multiple version entries for %s in the database" \
                    % oTable.sqlmeta.table
            print "Giving up. I suggest dumping and reloading everything"
            # Should this be an exception?
            iTableVersion = -999
        return iTableVersion

    def check_table_versions(self, aTable, aTableVersion, oConn=None):
        """Check version numbers.

           aTable is the list of tables to check
           aTableVersion is a list of version numbers to matched.
           It's assumed that aTable and aTableVersions are sorted the same.
           """
        bRes = True
        for oTable, iVersion in zip(aTable, aTableVersion):
            bRes = bRes and \
                    self.get_table_version(oTable, oConn) == iVersion
        return bRes

    def get_bad_tables(self, aTable, aTableVersion, oConn=None):
        """Get tables that don't match the list of version numbers

           aTable is the list of tables to check
           aTableVersion is a list of version numbers to matched.
           It's assumed that aTable and aTableVersions are sorted the same.
           Returns two lists, aLowerTables and aHigherTables, where
           aLowerTables is those with a lower version number, and
           aHigherTables is those with a higher number.
           """
        oConn = _get_connection(oConn)
        aLowerTables = []
        aHigherTables = []
        for oTable, iVersion in zip(aTable, aTableVersion):
            iCurVersion = self.get_table_version(oTable, oConn)
            if iCurVersion < iVersion:
                aLowerTables.append(oTable.sqlmeta.table)
            elif iCurVersion > iVersion:
                aHigherTables.append(oTable.sqlmeta.table)
        return aLowerTables, aHigherTables

