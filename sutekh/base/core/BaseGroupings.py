# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Provide classes to change the way cards are grouped in the display"""

# Base Grouping Class


class IterGrouping(object):
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
            if len(aSet) == 0:
                dKeyItem.setdefault(None, []).append(oItem)
            else:
                for oKey in aSet:
                    dKeyItem.setdefault(oKey, []).append(oItem)

        aList = dKeyItem.keys()
        aList.sort()

        for oKey in aList:
            yield oKey, dKeyItem[oKey]

# Individual Groupings
#
# If you need to group PhysicalCards,
# set fGetCard to lambda x: x.abstractCard

# pylint: disable-msg=E0602
# pylint is confused by the lambda x: x construction
DEF_GET_CARD = lambda x: x
# pylint: enable-msg=E0602


# pylint: disable-msg=C0111
# class names are pretty self-evident, so skip docstrings
class CardTypeGrouping(IterGrouping):
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(CardTypeGrouping, self).__init__(
            oIter, lambda x: [y.name for y in fGetCard(x).cardtype])


class MultiTypeGrouping(IterGrouping):
    """Group by card type, but make separate groupings for
       cards which have multiple types, e.g. Action Modifier / Reaction.
       """

    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        # pylint: disable-msg=C0103
        # we accept x here for consistency with other groupings
        def multitype(x):
            """Return a list of one string with slash separated card types."""
            aTypes = [y.name for y in fGetCard(x).cardtype]
            aTypes.sort()
            return [" / ".join(aTypes)]
        super(MultiTypeGrouping, self).__init__(oIter, multitype)


class ExpansionGrouping(IterGrouping):
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(ExpansionGrouping, self).__init__(oIter,
                                                lambda x: [y.expansion.name
                                                           for y in
                                                           fGetCard(x).rarity])


class RarityGrouping(IterGrouping):
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(RarityGrouping, self).__init__(oIter,
                                             lambda x: [y.rarity.name for y in
                                                        fGetCard(x).rarity])


class ExpansionRarityGrouping(IterGrouping):
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
                    if oRarity.rarity.name == 'Precon':
                        # Check if we're precon only
                        if len([x for x in aRarities if x.expansion.name ==
                                oRarity.expansion.name]) == 1:
                            aExpRarities.append('%s : Precon Only' %
                                                oRarity.expansion.name)
            return aExpRarities
        super(ExpansionRarityGrouping, self).__init__(oIter,
                                                      expansion_rarity)


class ArtistGrouping(IterGrouping):
    """Group by Artist"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(ArtistGrouping, self).__init__(oIter,
                                             lambda x: [y.name for y in
                                                        fGetCard(x).artists])


class KeywordGrouping(IterGrouping):
    """Group by Keyword"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(KeywordGrouping, self).__init__(
            oIter, lambda x: [y.keyword for y in fGetCard(x).keywords])


class NullGrouping(IterGrouping):
    """Group everything into a single group named 'All'."""
    def __init__(self, oIter, _fGetCard=DEF_GET_CARD):
        super(NullGrouping, self).__init__(oIter, lambda x: ["All"])
