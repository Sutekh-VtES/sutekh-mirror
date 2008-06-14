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
            oJoin.flush_cache()
       """

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(SOCachedRelatedJoin, self).__init__(*aArgs, **kwargs)
        self._dJoinCache = {}
        self._oOtherJoin = None
        self._bOtherJoinCached = None

    def _find_other_join(self):
        """Locate the equivalent join on the other class."""
        if self._oOtherJoin is None:
            aJoins = [oJ for oJ in self.otherClass.sqlmeta.joins
                        if oJ.otherClass is self.soClass]
            assert len(aJoins) == 1
            self._oOtherJoin = aJoins[0]

            self._bOtherJoinCached = isinstance(self._oOtherJoin,
                                                SOCachedRelatedJoin)

    def flush_cache(self):
        """Flush the contents of the cache."""
        self._dJoinCache = {}

    def init_cache(self):
        """Initialise the cache with the data from the database."""
        self._find_other_join()

        for oOther in self.otherClass.select():
            for oInst in self._oOtherJoin.performJoin(oOther):
                self._dJoinCache.setdefault(oInst, [])
                self._dJoinCache[oInst].append(oOther)

        # Apply ordering (we assume it won't change later)
        for oInst in self._dJoinCache:
            self._dJoinCache[oInst] = self._applyOrderBy(
                    self._dJoinCache[oInst], self.otherClass)

    def invalidate_cache_item(self, oInst, oOther, bDoOther=True):
        """Invalidate a cache item and its equivalent in the other join."""
        if oInst in self._dJoinCache:
            del self._dJoinCache[oInst]
        if self._bOtherJoinCached:
            self._find_other_join()
            self._oOtherJoin.invalidate_cache_item(oOther, oInst,
                                                   bDoOther=False)

    # pylint: disable-msg=C0103
    # Name must match SQLObject conventions
    def performJoin(self, oInst):
        """Return the join the result, from the cache if possible."""
        if not oInst in self._dJoinCache:
            self._dJoinCache[oInst] = joins.SORelatedJoin.performJoin(self,
                    oInst)
        return self._dJoinCache[oInst]

    def add(self, oInst, oOther):
        """Add an item to the join."""
        self.invalidate_cache_item(oInst, oOther)
        super(SOCachedRelatedJoin, self).add(oInst, oOther)

    def remove(self, oInst, oOther):
        """Remove an item from the join."""
        self.invalidate_cache_item(oInst, oOther)
        super(SOCachedRelatedJoin, self).remove(oInst, oOther)

class CachedRelatedJoin(joins.RelatedJoin):
    """Provide CacheRelatedJoin object to Sutekh"""
    baseClass = SOCachedRelatedJoin
