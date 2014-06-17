# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""Display extra columns in the tree view"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.core.BaseObjects import PhysicalCard, PhysicalCardSet
from sutekh.base.gui.CellRendererIcons import SHOW_TEXT_ONLY
from sutekh.base.gui.plugins.BaseExtraColumns import format_number
from sutekh.base.gui.plugins.BaseExtraCardViewColumns import (
    BaseExtraCardViewColumns)
from sqlobject import SQLObjectNotFound


class ExtraCardViewColumns(SutekhPlugin, BaseExtraCardViewColumns):
    """Add extra columns to the card list view.

       Allow the card list to be sorted on these columns
       """

    COLUMNS = BaseExtraCardViewColumns.COLUMNS.copy()

    COLUMNS.update({
        'Clans and Creeds': (100, '_render_clan', '_get_data_clan'),
        'Disciplines and Virtues': (150, '_render_disciplines',
                                    '_get_data_disciplines'),
        'Group': (40, '_render_group', '_get_data_group'),
        'Title': (100, '_render_title', '_get_data_title'),
        'Sect': (100, '_render_sect', '_get_data_sect'),
        'Capacity or Life': (40, '_render_capacity', '_get_data_capacity'),
        'Cost': (100, '_render_cost', '_get_data_cost_sortkey'),
    })

    # pylint: disable-msg=R0201
    # Making these functions for clarity
    # several unused paramaters due to function signatures
    # The bGetIcons parameter is needed to avoid icon lookups, etc when
    # sorting
    def _get_data_clan(self, oCard, bGetIcons=True):
        """get the clan for the card"""
        if not oCard is None:
            aClans = [x.name for x in oCard.clan]
            aIcons = []
            if aClans:
                aClans.sort()
                if bGetIcons:
                    dIcons = self.icon_manager.get_icon_list(oCard.clan)
                    if dIcons:
                        aIcons = [dIcons[x] for x in aClans]
                return " /|".join(aClans).split("|"), aIcons
            else:
                aCreed = [x.name for x in oCard.creed]
                aCreed.sort()
                if bGetIcons:
                    dIcons = self.icon_manager.get_icon_list(oCard.creed)
                    if dIcons:
                        aIcons = [dIcons[x] for x in aCreed]
                return " /|".join(aCreed).split("|"), aIcons
        return [], []

    def _render_clan(self, _oColumn, oCell, _oModel, oIter):
        """display the clan"""
        oCard = self._get_iter_data(oIter)
        aText, aIcons = self._get_data_clan(oCard)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_disciplines(self, oCard, bGetIcons=True):
        """get discipline info for card"""
        if not oCard is None:
            # There are better ways of doing this, but this is 1st draft
            # attempt, so we'll do the firt that occurs to me
            aInfo = [((oP.level != 'superior') and oP.discipline.name or
                      oP.discipline.name.upper(), oP.discipline.name)
                     for oP in oCard.discipline]
            if aInfo:
                # We sort inf before SUP, so swapcase
                aInfo.sort(key=lambda x: x[0].swapcase())
                if bGetIcons:
                    dIcons = self.icon_manager.get_icon_list(oCard.discipline)
                    aIcons = [dIcons[x[1]] for x in aInfo]
                else:
                    aIcons = []
                aDis = ", ".join([x[0] for x in aInfo]).split(" ")
                return aDis, aIcons
            else:
                aInfo = [oV.name for oV in oCard.virtue]
                if aInfo:
                    aInfo.sort()
                    if bGetIcons:
                        dIcons = self.icon_manager.get_icon_list(oCard.virtue)
                        aIcons = [dIcons[x] for x in aInfo]
                    else:
                        aIcons = []
                    aVirt = ", ".join(aInfo).split(" ")
                    return aVirt, aIcons
        return [], []

    def _render_disciplines(self, _oColumn, oCell, _oModel, oIter):
        """display the card disciplines"""
        oCard = self._get_iter_data(oIter)
        aText, aIcons = self._get_data_disciplines(oCard)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_group(self, oCard, _bGetIcons=True):
        """get the group info for the card"""
        if not oCard is None and not oCard.group is None:
            return oCard.group, [None]
        # We use -1 for the any group, so flag with a very different number
        return -100, [None]

    def _render_group(self, _oColumn, oCell, _oModel, oIter):
        """Display the group info"""
        oCard = self._get_iter_data(oIter)
        iGrp, aIcons = self._get_data_group(oCard)
        if iGrp != -100:
            if iGrp == -1:
                oCell.set_data(['Any'], aIcons, SHOW_TEXT_ONLY)
            else:
                oCell.set_data([str(iGrp)], aIcons, SHOW_TEXT_ONLY)
        else:
            oCell.set_data([""], aIcons, SHOW_TEXT_ONLY)

    def _get_data_capacity(self, oCard, _bGetIcons=True):
        """Get the card's capacity"""
        if not oCard is None and not oCard.capacity is None:
            return oCard.capacity, [None]
        if not oCard is None and not oCard.life is None:
            return oCard.life, [None]
        return -1, [None]

    def _render_capacity(self, _oColumn, oCell, _oModel, oIter):
        """Display capacity in the column"""
        oCard = self._get_iter_data(oIter)
        iCap, aIcons = self._get_data_capacity(oCard)
        aText = format_number(iCap)
        oCell.set_data(aText, aIcons, SHOW_TEXT_ONLY)

    def _get_data_cost(self, oCard, _bGetIcons=True):
        """Get the card's cost"""
        if not oCard is None and not oCard.cost is None:
            return oCard.cost, oCard.costtype, [None]
        return 0, "", [None]

    def _get_data_cost_sortkey(self, oCard, bGetIcons=True):
        """Get the sort key for sorting by cost.

           We want to group the cost types together, since the different
           types aren't comparable, hence the key is constructed as
           costtype + cost.
           We ensure that cost X cards sort after other values.
           """
        iCost, sCostType, aIcons = self._get_data_cost(oCard, bGetIcons)
        if iCost > 0:
            sKey = "%s %d" % (sCostType, iCost)
        elif iCost == -1:
            sKey = "%s X" % sCostType
        else:
            sKey = ""
        return sKey, aIcons

    def _render_cost(self, _oColumn, oCell, _oModel, oIter):
        """Display cost in the column"""
        oCard = self._get_iter_data(oIter)
        iCost, sCostType, aIcons = self._get_data_cost(oCard)
        if iCost > 0:
            oCell.set_data(["%d %s" % (iCost, sCostType)], aIcons,
                           SHOW_TEXT_ONLY)
        elif iCost == -1:
            oCell.set_data(["X %s" % sCostType], aIcons,
                           SHOW_TEXT_ONLY)
        else:
            oCell.set_data([""], aIcons, SHOW_TEXT_ONLY)

    def _get_data_title(self, oCard, bGetIcons=True):
        """Get the card's title."""
        if not oCard is None:
            aTitles = [oT.name for oT in oCard.title]
            aTitles.sort()
            aIcons = []
            if bGetIcons:
                aIcons = [None] * len(aTitles)
            return aTitles, aIcons
        return [], []

    def _render_title(self, _oColumn, oCell, _oModel, oIter):
        """Display title in the column"""
        oCard = self._get_iter_data(oIter)
        aTitles, aIcons = self._get_data_title(oCard)
        oCell.set_data(aTitles, aIcons, SHOW_TEXT_ONLY)

    def _get_data_sect(self, oCard, bGetIcons=True):
        """Get the card's sect."""
        if not oCard is None:
            aSects = [oS.name for oS in oCard.sect]
            aSects.sort()
            aIcons = []
            if bGetIcons:
                aIcons = [None] * len(aSects)
            return aSects, aIcons
        return [], []

    def _render_sect(self, _oColumn, oCell, _oModel, oIter):
        """Display sect in the column"""
        oCard = self._get_iter_data(oIter)
        aSects, aIcons = self._get_data_sect(oCard)
        oCell.set_data(aSects, aIcons, SHOW_TEXT_ONLY)


plugin = ExtraCardViewColumns
