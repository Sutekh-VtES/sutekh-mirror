# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Provide classes to change the way cards are grouped in the display"""

# Base Grouping Class

from sutekh.core.SutekhTables import CRYPT_TYPES, SutekhAbstractCard
from sutekh.base.core.BaseGroupings import (IterGrouping, DEF_GET_CARD,
                                            BaseExpansionRarityGrouping)


class ClanGrouping(IterGrouping):
    """Group the cards by clan and/or creed. The Imbued creeds are treated
       as if they were clans."""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super().__init__(oIter, self._get_values)
        self.fGetCard = fGetCard

    def _get_values(self, oCard):
        """Get the values to group by for this card"""
        oThisCard = self.fGetCard(oCard)
        if oThisCard.creed:
            return [y.name for y in oThisCard.creed]
        return [y.name for y in oThisCard.clan]


class DisciplineGrouping(IterGrouping):
    """Group by Discipline or Virtue. The Imbued Virtues are treated as if
       they were vampire disciplines."""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super().__init__(oIter, self._get_values)
        self.fGetCard = fGetCard

    def _get_values(self, oCard):
        """Get the values to group by for this card"""
        oThisCard = self.fGetCard(oCard)
        if oThisCard.virtue:
            return [y.fullname for y in oThisCard.virtue]
        return [y.discipline.fullname for y in oThisCard.discipline]


class DisciplineLevelGrouping(IterGrouping):
    """Group by Discipline or Virtue, distinguishing discipline levels.
       This distinguishes between inferior and superior levels of the
       discipline on vampires, but otherwise is the same as the
       _Discipline and Virtues_ grouping."""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super().__init__(oIter, self._get_values)
        self.fGetCard = fGetCard

    def _get_values(self, oCard):
        """Get the values to group by for this card"""
        oThisCard = self.fGetCard(oCard)
        if oThisCard.virtue:
            return [y.fullname for y in oThisCard.virtue]
        return ['%s (%s)' % (y.discipline.fullname, y.level)
                for y in oThisCard.discipline]


class CryptLibraryGrouping(IterGrouping):
    """Group into crypt or library cards"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        # Vampires and Imbued have exactly one card type (we hope that WW
        # don't change that)
        super().__init__(
            oIter, lambda x: [fGetCard(x).cardtype[0].name in CRYPT_TYPES
                              and "Crypt" or "Library"])


class SectGrouping(IterGrouping):
    """Group by Sect"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super().__init__(
            oIter, lambda x: [y.name for y in fGetCard(x).sect])


class TitleGrouping(IterGrouping):
    """Group by the political title of the vampire."""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        super().__init__(
            oIter, lambda x: [y.name for y in fGetCard(x).title])


class CostGrouping(IterGrouping):
    """Group by the Cost of the card."""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):

        def get_values(oCardSrc):
            """Get the values to group by for this card"""
            oCard = fGetCard(oCardSrc)
            if oCard.cost:
                if oCard.cost == -1:
                    return ['X %s' % oCard.costtype]
                return ['%d %s' % (oCard.cost, oCard.costtype)]
            return []

        super().__init__(oIter, get_values)


class GroupGrouping(IterGrouping):
    """Group the cards by their crypt group"""
    def __init__(self, oIter, fGetCard=DEF_GET_CARD):

        def get_values(oCardSrc):
            """Get the group values for this card"""
            oCard = fGetCard(oCardSrc)
            if oCard.group:
                if oCard.group != -1:
                    return ['Group %d' % oCard.group]
                return ['Any Group']
            return []

        super().__init__(oIter, get_values)


class GroupPairGrouping(IterGrouping):
    """Group cards into pairs of adjacent groups. Cards marked as
       *Any Group* are considered to belong to all group pairs."""
    TEXT = "Groups %d, %d"

    def __init__(self, oIter, fGetCard=DEF_GET_CARD):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        iMax = SutekhAbstractCard.select().max(SutekhAbstractCard.q.group)

        def get_values(oCardSrc):
            """Get the group pairs for this card"""
            oCard = fGetCard(oCardSrc)
            if oCard.group:
                if oCard.group != -1:
                    if oCard.group == 1:
                        return [self.TEXT % (oCard.group, oCard.group + 1)]
                    if oCard.group < iMax:
                        return [self.TEXT % (oCard.group - 1, oCard.group),
                                self.TEXT % (oCard.group, oCard.group + 1)]
                    return [self.TEXT % (oCard.group - 1, oCard.group)]
                # Any Group is returned in all pairs
                return [self.TEXT % (x, x + 1) for x in range(1, iMax)]
            return []

        super().__init__(oIter, get_values)


class ExpansionRarityGrouping(BaseExpansionRarityGrouping):
    """Group by expansion and rarity, handling Precon and Demo
       special cases."""

    DEMO_PRECON = ['Third Edition']

    def _handle_extra_expansions(self, oRarity, aRarities, aExpRarities):
        sExp = oRarity.expansion.name
        if oRarity.rarity.name == 'Precon':
            # Check if we're precon only
            if len([x for x in aRarities if x.expansion.name == sExp]) == 1:
                aExpRarities.append('%s : Precon Only' % sExp)
        elif oRarity.rarity.name == 'Demo' and sExp in self.DEMO_PRECON:
            # Add case for cards that are Demo & Precon only
            aNames = [x.rarity.name for x in aRarities
                      if x.expansion.name == sExp]
            if len(aNames) == 2 and 'Demo' in aNames and 'Precon' in aNames:
                aExpRarities.append('%s : Precon and Demo Only' % sExp)
