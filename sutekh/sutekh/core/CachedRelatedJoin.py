# CachedRelatedJoin.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sqlobject import joins

class SOCachedRelatedJoin(joins.SORelatedJoin):
    """Version of RelatedJoin that caches the lookup of related objects.
     
       Updates to the database require explicitly flushing the cache on
       each join. E.g.:
       
       for oJoin in AbstractCard.sqlmeta.joins:
         if type(oJoin) is SOCachedRelatedJoin:
            oJoin.flushCache()
       """

    def __init__(self,*args,**kws):
        super(SOCachedRelatedJoin,self).__init__(*args,**kws)
        self._dJoinCache = {}

    def flushCache(self):
        self._dJoinCache = {}

    def performJoin(self, inst):
        if not inst in self._dJoinCache:
            self._dJoinCache[inst] = joins.SORelatedJoin.performJoin(self,inst)
        return self._dJoinCache[inst]

class CachedRelatedJoin(joins.RelatedJoin):
    baseClass = SOCachedRelatedJoin
