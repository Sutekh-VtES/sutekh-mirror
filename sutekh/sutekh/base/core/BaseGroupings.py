# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Provide classes to change the way cards are grouped in the display"""

# Base Grouping Class


class IterGrouping:
    """Bass class for the groupings"""
    def __init__(self, oIter, fKeys):
        """Create the grouping

           oIter: Iterable to group.
           fKeys: Function which maps an item from the iterable
                  to a list of keys. Keys must be hashable.
           """
        self.__oIter = oIter
        self.__fKeys = fKeys

    def __iter__(self):
        dKeyItem = {}
        for oItem in self.__oIter:
            aSet = set(self.__fKeys(oItem))
            if aSet:
                for oKey in aSet:
                    dKeyItem.setdefault(oKey, []).append(oItem)
            else:
                dKeyItem.setdefault(None, []).append(oItem)

        aList = list(dKeyItem.keys())
        aList.sort(key=lambda x: x if x else "")

        for oKey in aList:
            yield oKey, dKeyItem[oKey]

# Individual Groupings
#
# If you need to group PhysicalCards,
# set fGetCard to lambda x: x.abstractCard

# pylint: disable=undefined-variable
# pylint is confused by the lambda x: x construction
DEF_GET_CARD = lambda x: x
# pylint: enable=undefined-variable


# pylint: disable=missing-docstring
# class names are pretty self-evident, so skip docstrings
class CardTypeGrouping(IterGrouping):
    """Group by card type. This is the default grouping. This grouping
       places cards with multiple types in each group to which it belongs."""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super().__init__(
            oIter, lambda x: [y.name for y in fGetCard(x).cardtype])


class MultiTypeGrouping(IterGrouping):
    """Group by card type, but make separate groupings for
       cards which have multiple types."""

    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        # pylint: disable=invalid-name
        # we accept x here for consistency with other groupings
        def multitype(x):
            """Return a list of one string with slash separated card types."""
            aTypes = [y.name for y in fGetCard(x).cardtype]
            aTypes.sort()
            return [" / ".join(aTypes)]
        super().__init__(oIter, multitype)


class ExpansionGrouping(IterGrouping):
    """Group by the expansions in which the cards have been printed."""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super().__init__(
            oIter, lambda x: [y.expansion.name for y in fGetCard(x).rarity])


class RarityGrouping(IterGrouping):
    """ Group the cards by the published rarity."""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super().__init__(
            oIter, lambda x: [y.rarity.name for y in fGetCard(x).rarity])


class BaseExpansionRarityGrouping(IterGrouping):
    """Groups cards by both expansion and rarity."""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        def expansion_rarity(oCard):
            aExpRarities = []
            aRarities = list(fGetCard(oCard).rarity)
            for oRarity in aRarities:
                if oRarity.expansion.name.startswith('Promo'):
                    aExpRarities.append('Promo')
                else:
                    aExpRarities.append('%s : %s' % (oRarity.expansion.name,
                                                     oRarity.rarity.name))
                self._handle_extra_expansions(oRarity, aRarities, aExpRarities)
            return aExpRarities
        super().__init__(oIter, expansion_rarity)

    def _handle_extra_expansions(self, oRarity, aRarities, aExpRarities):
        # Hook for subclasses to add extra fake expansion / rarity
        # combinations
        pass  # pragma: no cover


class ArtistGrouping(IterGrouping):
    """Group by Artist"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super().__init__(
            oIter, lambda x: [y.name for y in fGetCard(x).artists])


class KeywordGrouping(IterGrouping):
    """Group by Keyword"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super().__init__(
            oIter, lambda x: [y.keyword for y in fGetCard(x).keywords])


class NullGrouping(IterGrouping):
    """Group everything into a single group named 'All'."""
    def __init__(self, oIter, _fGetCard=DEF_GET_CARD):
        super().__init__(oIter, lambda x: ["All"])
