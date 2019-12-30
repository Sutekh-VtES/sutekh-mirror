# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# Modified from ExtraCardViewColumns.py
# GPL - see COPYING for details
"""Display extra columns in the tree view"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.core.BaseTables import MapPhysicalCardToPhysicalCardSet
from sutekh.base.core.BaseFilters import PhysicalCardSetFilter, FilterAndBox
from sutekh.core.Filters import CryptCardFilter
from sutekh.base.gui.plugins.BaseExtraColumns import (get_number,
                                                      format_number)
from sutekh.base.gui.plugins.BaseExtraCSListViewColumns import (
    BaseExtraCSListViewColumns)


class ExtraCardSetListViewColumns(SutekhPlugin, BaseExtraCSListViewColumns):
    """Add extra columns to the card set list view.

       Allow the card set list to be sorted on these columns
       """
    COLUMNS = BaseExtraCSListViewColumns.COLUMNS.copy()
    # Dictionary of column info - width, render function name, data func name
    COLUMNS.update({
        'Library': (100, '_render_library', '_get_data_library'),
        'Crypt': (100, '_render_crypt', '_get_data_crypt'),
    })

    CS_KEYS = ('Total Cards', 'Library', 'Crypt')

    sMenuName = "Extra Columns -- card set list view"

    sHelpCategory = "card_set_list:profile"

    sHelpText = """Only card set names are shown in the card set list by \
                   default as well.  You can select additional columns \
                   to display as part of the card set list profile.

                   The possible extra columns are:

                   * _Author_: Show the card set author.
                   * _Description_: Show the card set description.
                   * _Total cards_: Show the total number of cards in the \
                     card set.
                   * _Crypt_: Show the number of crypt cards in the card set.
                   * _Library_: Show the number of library cards in the \
                     card set.
                   * _All Children_: Show the number of child card sets each \
                     card set has
                   * _In-Use Children_: Show the number of child card sets \
                     marked as in use.

                   The display can be sorted on these columns by clicking on \
                   the column headers."""

    # pylint: disable=no-self-use
    # Making these functions for clarity

    @classmethod
    def get_help_list_text(cls):
        return """ Select which extra columns of data are shown. \
                   See the *Extra Columns -- card set list* section \
                   for more details."""

    # several unused paramaters due to function signatures
    # The bGetIcons parameter is needed to avoid icon lookups, etc when
    # sorting

    def _get_data_library(self, sCardSet, bGetIcons=True):
        """Return the number of library cards in the card set"""
        def query(oCardSet):
            """Query the database"""
            oFilter = FilterAndBox([PhysicalCardSetFilter(oCardSet.name),
                                    CryptCardFilter()])
            iCrypt = oFilter.select(
                MapPhysicalCardToPhysicalCardSet).distinct().count()
            iTot = MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardSetID=oCardSet.id).count()
            return iTot - iCrypt

        if sCardSet:
            # lookup totals
            dInfo = self._dCache[sCardSet]
            aIcons = []
            iTotal = get_number(dInfo, 'Library', query)
            if bGetIcons:
                aIcons = [None]
            return iTotal, aIcons
        return -1, []

    def _render_library(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """display the library count"""
        sCardSet = self._get_iter_data(oIter)
        iCount, aIcons = self._get_data_library(sCardSet, True)
        aText = format_number(iCount)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_crypt(self, sCardSet, bGetIcons=True):
        """Return the number of crypt cards in the card set"""
        def query(oCardSet):
            """Query the database"""
            oFilter = FilterAndBox([PhysicalCardSetFilter(oCardSet.name),
                                    CryptCardFilter()])
            return oFilter.select(
                MapPhysicalCardToPhysicalCardSet).distinct().count()

        if sCardSet:
            # lookup totals
            dInfo = self._dCache[sCardSet]
            aIcons = []
            iTotal = get_number(dInfo, 'Crypt', query)
            if bGetIcons:
                aIcons = [None]
            return iTotal, aIcons
        return -1, []

    def _render_crypt(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """display the crypt count"""
        sCardSet = self._get_iter_data(oIter)
        iCount, aIcons = self._get_data_crypt(sCardSet, True)
        aText = format_number(iCount)
        oCell.set_data(aText, aIcons, self._iShowMode)


plugin = ExtraCardSetListViewColumns
