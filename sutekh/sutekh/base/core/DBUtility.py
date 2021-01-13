# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Misc Useful functions needed in several places. Mainly to do with database
# management. Seperated out from SutekhCli and other places, NM, 2006

"""Misc functions that influence the database in various ways."""

import datetime
import logging

from sqlobject import SQLObjectNotFound

from .BaseTables import VersionTable, PhysicalCardSet, AbstractCard, Metadata
from .BaseAdapters import Adapter
from .BaseAbbreviations import DatabaseAbbreviation
from .DatabaseVersion import DatabaseVersion
from .CachedRelatedJoin import SOCachedRelatedJoin
from ..Utility import find_subclasses

CARDLIST_UPDATE_DATE = "last cardlist update"


def make_adapter_caches():
    """Flush all adapter and abbreviation caches.

       This assumes that everything that needs to be cached has already
       been imported before make_adapter_caches is called, since this
       uses introspection to find the adapters to cache."""

    for cAbbrev in find_subclasses(DatabaseAbbreviation):
        cAbbrev.make_lookup()

    aCachedAdapters = [x for x in find_subclasses(Adapter)
                       if hasattr(x, 'make_object_cache')]
    for cAdapter in aCachedAdapters:
        cAdapter.make_object_cache()


def flush_cache(bMakeCache=True):
    """Flush all the object caches - needed before importing new card lists
       and such"""
    for oJoin in AbstractCard.sqlmeta.joins:
        if isinstance(oJoin, SOCachedRelatedJoin):
            oJoin.flush_cache()
    # pylint: disable=no-member
    # AbstractCard confuses pylint
    for oChild in AbstractCard.__subclasses__():
        for oJoin in oChild.sqlmeta.joins:
            if isinstance(oJoin, SOCachedRelatedJoin):
                oJoin.flush_cache()
    if bMakeCache:
        make_adapter_caches()


def init_cache():
    """Initiliase the cached join tables."""
    for oJoin in AbstractCard.sqlmeta.joins:
        if isinstance(oJoin, SOCachedRelatedJoin):
            oJoin.init_cache()
    # pylint: disable=no-member
    # AbstractCard confuses pylint
    for oChild in AbstractCard.__subclasses__():
        for oJoin in oChild.sqlmeta.joins:
            if isinstance(oJoin, SOCachedRelatedJoin):
                oJoin.init_cache()
    make_adapter_caches()


def refresh_tables(aTables, oConn, bMakeCache=True):
    """Drop and recreate the given list of tables"""
    aTables.reverse()
    for cCls in aTables:
        cCls.dropTable(ifExists=True, connection=oConn)
    aTables.reverse()
    oVerHandler = DatabaseVersion(oConn)
    # Make sure we recreate the database version table
    oVerHandler.expire_table_conn(oConn)
    oVerHandler.ensure_table_exists(oConn)
    if not oVerHandler.set_version(VersionTable, VersionTable.tableversion,
                                   oConn):
        return False
    for cCls in aTables:
        cCls.createTable(connection=oConn)
        if not oVerHandler.set_version(cCls, cCls.tableversion, oConn):
            return False
    flush_cache(bMakeCache)
    return True


# Utility function to help with config management and such
def get_cs_id_name_table():
    """Returns a dictionary id : name for all the card sets.

       We do this so we can have the old info available to fix the config
       after a database reload, etc."""
    dMapping = {}
    for oCS in PhysicalCardSet.select():
        dMapping[oCS.id] = oCS.name
    return dMapping


def get_metadata_date(sKey):
    """Read a date from the metadata date and return a datetime.date object,
       or return None if the object can't be found or interpreted as a date."""
    try:
        # pylint: disable=no-member
        # SQLObject confuses pylint
        oObj = Metadata.byDataKey(sKey)
        sDate = oObj.value
        return datetime.datetime.strptime(sDate, '%Y-%m-%d').date()
    except (SQLObjectNotFound, ValueError) as oErr:
        # Log this for debugging purposes
        logging.warning('Failed to find a valid date for %s '
                        '(err %s) - returning None', sKey, oErr)
    return None


def set_metadata_date(sKey, oDate):
    """Write a datetime object as a string in the metadata table, creating the
       object if needed"""
    sDate = oDate.strftime('%Y-%m-%d')
    try:
        # pylint: disable=no-member
        # SQLObject confuses pylint
        oObj = Metadata.byDataKey(sKey)
        oObj.value = sDate
        oObj.syncUpdate()
    except SQLObjectNotFound:
        oObj = Metadata(dataKey=sKey, value=sDate)
