# CachedRelatedJoin.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Implement RelatedJoin with caches"""

from sqlobject import joins

class SOCachedRelatedJoin(joins.SORelatedJoin):
    """Version of RelatedJoin that caches the lookup of related objects.

       Updates to the database require explicitly flushing the cache on
       each join. E.g.:

       for oJoin in AbstractCard.sqlmeta.joins:
         if type(oJoin) is SOCachedRelatedJoin:
            oJoin.flushCache()
       """

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(SOCachedRelatedJoin, self).__init__(*aArgs, **kwargs)
        self._dJoinCache = {}

    def flushCache(self):
        self._dJoinCache = {}

    def initCache(self):
        aJoins = [oJ for oJ in self.otherClass.sqlmeta.joins if oJ.otherClass
                is self.soClass]
        assert len(aJoins) == 1
        oOtherJoin = aJoins[0]

        for oOther in self.otherClass.select():
            for oInst in oOtherJoin.performJoin(oOther):
                self._dJoinCache.setdefault(oInst, [])
                self._dJoinCache[oInst].append(oOther)

        # Apply ordering (we assume it won't change later)
        for oInst in self._dJoinCache:
            self._dJoinCache[oInst] = self._applyOrderBy(
                    self._dJoinCache[oInst], self.otherClass)

    def performJoin(self, oInst):
        if not oInst in self._dJoinCache:
            self._dJoinCache[oInst] = joins.SORelatedJoin.performJoin(self,
                    oInst)
        return self._dJoinCache[oInst]

class CachedRelatedJoin(joins.RelatedJoin):
    baseClass = SOCachedRelatedJoin
