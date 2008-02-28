# CachedRelatedJoin.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
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

    def initCache(self):
        aJoins = [oJ for oJ in self.otherClass.sqlmeta.joins if oJ.otherClass is self.soClass]
        assert len(aJoins) == 1
        oOtherJoin = aJoins[0]

        for oOther in self.otherClass.select():
            for inst in oOtherJoin.performJoin(oOther):
                self._dJoinCache.setdefault(inst,[])
                self._dJoinCache[inst].append(oOther)

        # Apply ordering (we assume it won't change later)
        for inst in self._dJoinCache:
            self._dJoinCache[inst] = self._applyOrderBy(self._dJoinCache[inst], self.otherClass)

    def performJoin(self, inst):
        if not inst in self._dJoinCache:
            self._dJoinCache[inst] = joins.SORelatedJoin.performJoin(self,inst)
        return self._dJoinCache[inst]

class CachedRelatedJoin(joins.RelatedJoin):
    baseClass = SOCachedRelatedJoin
