# Groupings.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Provide classes to change the way cards are grouped in the display"""

# Base Grouping Class

from sutekh.core.SutekhObjects import CRYPT_TYPES, AbstractCard


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
        super(CardTypeGrouping, self).__init__(oIter,
                lambda x: [y.name for y in fGetCard(x).cardtype])


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


class ClanGrouping(IterGrouping):
    """Group the cards by clan and/or creed"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(ClanGrouping, self).__init__(oIter, self._get_values)
        self.fGetCard = fGetCard

    def _get_values(self, oCard):
        """Get the values to group by for this card"""
        oThisCard = self.fGetCard(oCard)
        if oThisCard.creed:
            return [y.name for y in oThisCard.creed]
        else:
            return [y.name for y in oThisCard.clan]


class DisciplineGrouping(IterGrouping):
    """Group by Discipline or Virtue"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(DisciplineGrouping, self).__init__(oIter, self._get_values)
        self.fGetCard = fGetCard

    def _get_values(self, oCard):
        """Get the values to group by for this card"""
        oThisCard = self.fGetCard(oCard)
        if oThisCard.virtue:
            return [y.fullname for y in oThisCard.virtue]
        else:
            return [y.discipline.fullname for y in oThisCard.discipline]


class DisciplineLevelGrouping(IterGrouping):
    """Group by Discipline or Virtue, distinguishing discipline levels"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(DisciplineLevelGrouping, self).__init__(oIter, self._get_values)
        self.fGetCard = fGetCard

    def _get_values(self, oCard):
        """Get the values to group by for this card"""
        oThisCard = self.fGetCard(oCard)
        if oThisCard.virtue:
            return [y.fullname for y in oThisCard.virtue]
        else:
            return ['%s (%s)' % (y.discipline.fullname, y.level)
                    for y in oThisCard.discipline]


class ExpansionGrouping(IterGrouping):
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(ExpansionGrouping, self).__init__(oIter,
                lambda x: [y.expansion.name for y in fGetCard(x).rarity])


class RarityGrouping(IterGrouping):
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(RarityGrouping, self).__init__(oIter,
                lambda x: [y.rarity.name for y in fGetCard(x).rarity])


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


class CryptLibraryGrouping(IterGrouping):
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        # Vampires and Imbued have exactly one card type (we hope that WW
        # don't change that)
        super(CryptLibraryGrouping, self).__init__(oIter,
                lambda x: [fGetCard(x).cardtype[0].name in CRYPT_TYPES
                    and "Crypt" or "Library"])


class SectGrouping(IterGrouping):
    """Group by Sect"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(SectGrouping, self).__init__(oIter,
                lambda x: [y.name for y in fGetCard(x).sect])


class TitleGrouping(IterGrouping):
    """Group by Title"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(TitleGrouping, self).__init__(oIter,
            lambda x: [y.name for y in fGetCard(x).title])


class CostGrouping(IterGrouping):
    """Group by Cost"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):

        def get_values(oCardSrc):
            """Get the values to group by for this card"""
            oCard = fGetCard(oCardSrc)
            if oCard.cost:
                if oCard.cost == -1:
                    return ['X %s' % oCard.costtype]
                else:
                    return ['%d %s' % (oCard.cost, oCard.costtype)]
            else:
                return []

        super(CostGrouping, self).__init__(oIter, get_values)


class GroupGrouping(IterGrouping):
    """Group by crypt Group"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):

        def get_values(oCardSrc):
            """Get the group values for this card"""
            oCard = fGetCard(oCardSrc)
            if oCard.group:
                if oCard.group != -1:
                    return ['Group %d' % oCard.group]
                else:
                    return ['Any group']
            else:
                return []

        super(GroupGrouping, self).__init__(oIter, get_values)


class GroupPairGrouping(IterGrouping):
    """Group by crypt adjacent pairs of Group"""
    TEXT = "Groups %d, %d"

    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        iMax = AbstractCard.select().max(AbstractCard.q.group)

        def get_values(oCardSrc):
            """Get the group pairs for this card"""
            oCard = fGetCard(oCardSrc)
            if oCard.group:
                if oCard.group != -1:
                    if oCard.group == 1:
                        return [self.TEXT % (oCard.group, oCard.group + 1)]
                    elif oCard.group < iMax:
                        return [self.TEXT % (oCard.group - 1, oCard.group),
                                self.TEXT % (oCard.group, oCard.group + 1)]
                    else:
                        return [self.TEXT % (oCard.group - 1, oCard.group)]
                else:
                    # Any group is returned in all pairs
                    return [self.TEXT % (x, x + 1) for x in range(1, iMax)]
            else:
                return []

        super(GroupPairGrouping, self).__init__(oIter, get_values)


class ArtistGrouping(IterGrouping):
    """Group by Artist"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(ArtistGrouping, self).__init__(oIter,
            lambda x: [y.name for y in fGetCard(x).artists])


class KeywordGrouping(IterGrouping):
    """Group by Keyword"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super(KeywordGrouping, self).__init__(oIter,
            lambda x: [y.keyword for y in fGetCard(x).keywords])


class NullGrouping(IterGrouping):
    """Group everything into a single group named 'All'."""
    def __init__(self, oIter, _fGetCard=DEF_GET_CARD):
        super(NullGrouping, self).__init__(oIter, lambda x: ["All"])
