# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Provide classes to change the way cards are grouped in the display"""

# Base Grouping Class

from sutekh.core.SutekhObjects import CRYPT_TYPES, SutekhAbstractCard
from sutekh.base.core.BaseGroupings import IterGrouping, DEF_GET_CARD


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


class CryptLibraryGrouping(IterGrouping):
    """Group into crypt or library cards"""
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
        iMax = SutekhAbstractCard.select().max(SutekhAbstractCard.q.group)

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
