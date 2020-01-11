# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Manage the icons from the WW site"""

from sutekh.base.core.BaseTables import CardType
from sutekh.base.core.BaseAdapters import ICardType
from sutekh.base.core.BaseGroupings import CardTypeGrouping, MultiTypeGrouping
from sutekh.base.io.BaseIconManager import BaseIconManager

from sutekh.core.SutekhTables import Clan, Creed, DisciplinePair, Virtue
from sutekh.core.SutekhAdapters import IDisciplinePair, IVirtue, ICreed, IClan
from sutekh.core.Groupings import ClanGrouping, DisciplineGrouping


# Utilty functions - convert object to a filename
def _get_clan_filename(oClan):
    """Get the icon filename for the clan"""
    sClanName = oClan.name
    # Fix special cases
    if 'antitribu' in sClanName:
        sClanName = sClanName.replace('antitribu', 'anti')
    elif sClanName == 'Abomination':
        sClanName = 'abo'
    elif sClanName == 'Follower of Set':
        sClanName = 'fos'
    elif sClanName == 'Daughter of Cacophony':
        sClanName = 'daughters'
    elif sClanName == 'Harbinger of Skulls':
        sClanName = 'harbingers'
    elif sClanName == 'Blood Brother':
        sClanName = 'bloodbrothers'
    elif sClanName == 'Ahrimane':
        sClanName = 'ahrimanes'
    sClanName = sClanName.lower()
    sClanName = sClanName.replace(' ', '')
    sFileName = 'clans/iconclan%s.gif' % sClanName
    return sFileName


def _get_card_type_filename(oType):
    """Get the filename for the card type"""
    if oType.name == 'Action Modifier':
        sFileName = 'cardtype/icontypemodifier.gif'
    elif oType.name == 'Political Action':
        sFileName = 'cardtype/icontypepolitical.gif'
    elif oType.name in ('Master', 'Vampire', 'Imbued'):
        # These types have no icon
        sFileName = None
    else:
        sFileName = 'cardtype/icontype%s.gif' % oType.name.lower()
    return sFileName


def _get_creed_filename(oCreed):
    """Get the filename for the creed"""
    sFileName = 'creeds/iconcre%s.gif' % oCreed.name.lower()
    return sFileName


def _get_discipline_filename(oDiscipline):
    """Get the filename for the discipline."""
    if oDiscipline.discipline.name.lower() in ['mal', 'str', 'fli']:
        # These are misc icons
        if oDiscipline.discipline.fullname == 'Flight':
            sFileName = 'misc/iconmiscflight.gif'
        elif oDiscipline.level == 'inferior':
            sFileName = ('misc/iconmisc%s.gif' %
                         oDiscipline.discipline.fullname.lower())
        else:
            sFileName = ('misc/iconmisc%ssup.gif' %
                         oDiscipline.discipline.fullname.lower())
    elif oDiscipline.level == 'inferior':
        sFileName = ('disciplines/icondis%s.gif' %
                     oDiscipline.discipline.fullname.lower())
    else:
        sFileName = ('disciplines/icondis%ssup.gif' %
                     oDiscipline.discipline.fullname.lower())
    return sFileName


def _get_virtue_filename(oVirtue):
    """Get the filename for the virtue"""
    if oVirtue.name != 'jud':
        sFileName = 'virtues/iconvirtue%s.gif' % oVirtue.fullname.lower()
    else:
        # Annoying special case
        sFileName = 'virtues/iconvirtuejustice.gif'
    return sFileName


class IconManager(BaseIconManager):
    """Manager for the VTES Icons.

       Given the text and the tag name, look up the suitable matching icon
       filename for it. Return none if no suitable icon is found.
       Also provide an option to download the icons form the v:ekn
       site.
       """

    sBaseUrl = "http://www.vekn.net/images/stories/icons/"

    def _get_clan_icons(self, aValues):
        """Get the icons for the clans"""
        dIcons = {}
        for oClan in aValues:
            sFileName = _get_clan_filename(oClan)
            dIcons[oClan.name] = self._get_icon(sFileName)
        return dIcons

    def _get_card_type_icons(self, aValues):
        """Get the icons for the card types"""
        dIcons = {}
        for oType in aValues:
            sFileName = _get_card_type_filename(oType)
            dIcons[oType.name] = self._get_icon(sFileName)
        return dIcons

    def _get_creed_icons(self, aValues):
        """Get the icons for the creeds."""
        dIcons = {}
        for oCreed in aValues:
            sFileName = _get_creed_filename(oCreed)
            dIcons[oCreed.name] = self._get_icon(sFileName)
        return dIcons

    def _get_discipline_icons(self, aValues):
        """Get the icons for the disciplines."""
        dIcons = {}
        for oDiscipline in aValues:
            sFileName = _get_discipline_filename(oDiscipline)
            if oDiscipline.level == 'superior':
                oIcon = self._get_icon(sFileName, 14)
            else:
                oIcon = self._get_icon(sFileName)
            dIcons[oDiscipline.discipline.name] = oIcon
        return dIcons

    def _get_virtue_icons(self, aValues):
        """Get the icons for the Virtues."""
        dIcons = {}
        for oVirtue in aValues:
            sFileName = _get_virtue_filename(oVirtue)
            dIcons[oVirtue.name] = self._get_icon(sFileName)
        return dIcons

    def get_icon_by_name(self, sName):
        """Lookup an icon that's a card property"""
        if sName == 'burn option':
            sFileName = 'misc/iconmiscburnoption.gif'
        elif sName == 'advanced':
            sFileName = 'misc/iconmiscadvanced.gif'
        elif sName == 'merged':
            sFileName = 'misc/iconmiscmerged.gif'
        else:
            return None
        return self._get_icon(sFileName)

    def get_info(self, sText, cGrouping):
        """Given the text and the grouping for a card list/set view,
           return the appropriate text array and icons for display."""
        if not sText:
            return [], []
        aText = []
        aIcons = []
        if cGrouping is CardTypeGrouping:
            aText = [sText]
            dIcons = self._get_card_type_icons([ICardType(x) for x in aText])
            # Only 1 icon
            aIcons = list(dIcons.values())
        elif cGrouping is MultiTypeGrouping:
            aText = sText.split(' / ')
            dIcons = self._get_card_type_icons([ICardType(x) for x in aText])
            # Do this since we need to have the same order as aText
            aIcons = [dIcons[x] for x in aText]
            aText = " /|".join(aText).split("|")
        elif cGrouping is DisciplineGrouping:
            aText = [sText]
            try:
                oDisVirt = IDisciplinePair((sText, 'superior'))
                dIcons = self._get_discipline_icons([oDisVirt])
                # We know there's only 1 icon, so this is OK
                aIcons = list(dIcons.values())
            except KeyError:
                try:
                    oDisVirt = IVirtue(sText)
                    dIcons = self._get_virtue_icons([oDisVirt])
                    aIcons = list(dIcons.values())
                except KeyError:
                    aIcons = [None]
        elif cGrouping is ClanGrouping:
            aText = [sText]
            try:
                oClanCreed = IClan(sText)
                dIcons = self._get_clan_icons([oClanCreed])
                # We know there's only 1 icon, so this is OK
                aIcons = list(dIcons.values())
            except KeyError:
                try:
                    oClanCreed = ICreed(sText)
                    dIcons = self._get_creed_icons([oClanCreed])
                    aIcons = list(dIcons.values())
                except KeyError:
                    aIcons = [None]
        return aText, aIcons

    def get_icon_list(self, aValues):
        """Get a dictionary of appropriate (value, icon) pairs for the
           given values"""
        if not aValues:
            return None
        dIcons = None
        if isinstance(aValues[0], CardType):
            dIcons = self._get_card_type_icons(aValues)
        elif isinstance(aValues[0], DisciplinePair):
            dIcons = self._get_discipline_icons(aValues)
        elif isinstance(aValues[0], Virtue):
            dIcons = self._get_virtue_icons(aValues)
        elif isinstance(aValues[0], Clan):
            dIcons = self._get_clan_icons(aValues)
        elif isinstance(aValues[0], Creed):
            dIcons = self._get_creed_icons(aValues)
        return dIcons

    def get_icon_total(self):
        """Total number of icons we must download"""
        return (Creed.select().count() + DisciplinePair.select().count() +
                Clan.select().count() + Virtue.select().count() +
                CardType.select().count() + 2)

    def download_icons(self, oLogHandler=None):
        """Download the icons from the WW site"""
        # We use the names as from the WW site - this is not
        # ideal, but simpler than maintaining multiple names for each
        # icon.
        oLogger = self._make_logger(oLogHandler)
        for oCreed in Creed.select():
            self._download(_get_creed_filename(oCreed), oLogger)
        for oDiscipline in DisciplinePair.select():
            self._download(_get_discipline_filename(oDiscipline), oLogger)
        for oClan in Clan.select():
            self._download(_get_clan_filename(oClan), oLogger)
        for oVirtue in Virtue.select():
            self._download(_get_virtue_filename(oVirtue), oLogger)
        for oType in CardType.select():
            self._download(_get_card_type_filename(oType), oLogger)
        # download the special cases
        self._download('misc/iconmiscburnoption.gif', oLogger)
        self._download('misc/iconmiscadvanced.gif', oLogger)
        self._download('misc/iconmiscmerged.gif', oLogger)
