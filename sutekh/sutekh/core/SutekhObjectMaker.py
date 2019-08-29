# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""The Sutekh Card and related database objects creation helper"""

from sqlobject import SQLObjectNotFound

from sutekh.base.core.BaseAdapters import IAbstractCard
from sutekh.base.core.BaseObjectMaker import BaseObjectMaker

from sutekh.core.SutekhTables import (SutekhAbstractCard, Clan, Creed,
                                      Discipline, DisciplinePair, Sect,
                                      Title, Virtue)
from sutekh.core.SutekhAdapters import (IClan, ICreed, IDiscipline,
                                        IDisciplinePair, ISect, ITitle,
                                        IVirtue)
from sutekh.core.Abbreviations import (Clans, Creeds, Disciplines, Sects,
                                       Titles, Virtues)


# Object Maker API
# pylint: disable=missing-docstring
# No point in docstrings for these methods, really
class SutekhObjectMaker(BaseObjectMaker):
    """Creates all kinds of SutekhTables from simple strings.

       All the methods will return either a copy of an existing object
       or a new object.
       """
    # pylint: disable=no-self-use, too-many-arguments
    # we want SutekhObjectMaker self-contained, so these are all methods.
    # This needs all these arguments
    def make_clan(self, sClan):
        return self._make_object(Clan, IClan, Clans, sClan, bShortname=True)

    def make_creed(self, sCreed):
        return self._make_object(Creed, ICreed, Creeds, sCreed,
                                 bShortname=True)

    def make_discipline(self, sDis):
        return self._make_object(Discipline, IDiscipline, Disciplines, sDis,
                                 bFullname=True)

    def make_sect(self, sSect):
        return self._make_object(Sect, ISect, Sects, sSect)

    def make_title(self, sTitle):
        return self._make_object(Title, ITitle, Titles, sTitle)

    def make_virtue(self, sVirtue):
        return self._make_object(Virtue, IVirtue, Virtues, sVirtue,
                                 bFullname=True)

    def make_abstract_card(self, sCard):
        try:
            return IAbstractCard(sCard)
        except SQLObjectNotFound:
            sName = sCard.strip()
            sCanonical = sName.lower()
            return SutekhAbstractCard(canonicalName=sCanonical,
                                      name=sName, text="")

    def make_discipline_pair(self, sDiscipline, sLevel):
        try:
            return IDisciplinePair((sDiscipline, sLevel))
        except SQLObjectNotFound:
            oDis = self.make_discipline(sDiscipline)
            return DisciplinePair(discipline=oDis, level=sLevel)
