# ExtraCardSetListViewColumns.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# Modified from ExtraCardViewColumns.py
# GPL - see COPYING for details
"""Display extra columns in the tree view"""

import gtk
import pango
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.CellRendererIcons import CellRendererIcons, SHOW_TEXT_ONLY
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCardSet, \
        MapPhysicalCardToPhysicalCardSet
from sutekh.core.Filters import PhysicalCardSetFilter, CryptCardFilter, \
        FilterAndBox
from sutekh.core.DBSignals import listen_row_destroy, listen_row_update, \
        listen_row_created, listen_changed, disconnect_changed, \
        disconnect_row_destroy, disconnect_row_update, disconnect_row_created
from sqlobject import SQLObjectNotFound

SORT_COLUMN_OFFSET = 200  # ensure we don't clash with other extra columns


def _get_number(dInfo, sKey, fQuery):
    """Handle the use query & cache interaction for numbers"""
    if not dInfo.has_key(sKey):
        try:
            oCardSet = dInfo['Card Set']
            if oCardSet:
                dInfo[sKey] = fQuery(oCardSet)
            else:
                # We have an earlier failed lookup
                return -1
        except KeyError:
            # This can arise if we're called while reloading a backup or
            # similiar
            return -1
    return dInfo[sKey]


def _format_number(iCount):
    """Return suitable list for the given number"""
    if iCount == -1:
        return [""]
    return [str(iCount)]


class ExtraCardSetListViewColumns(SutekhPlugin):
    """Add extra columns to the card set list view.

       Allow the card set list to be sorted on these columns
       """
    dTableVersions = {}
    aModelsSupported = ('Card Set List',)

    # Dictionary of column info - width, render function name, data func name
    COLUMNS = {
            'Total cards': (100, '_render_total', '_get_data_total'),
            'All Children': (100, '_render_all_children',
                '_get_data_all_children'),
            'In-Use Children': (100, '_render_inuse_children',
                '_get_data_inuse_children'),
            'Library': (100, '_render_library', '_get_data_library'),
            'Crypt': (100, '_render_crypt', '_get_data_crypt'),
            'Author': (300, '_render_author', '_get_data_author'),
            'Description': (700, '_render_description',
                '_get_data_description'),
            }

    OPTION_STR = ", ".join('"%s"' % sKey for sKey in sorted(COLUMNS.keys()))
    EXTRA_COLUMNS = "extra columns"

    dCardSetListConfig = {
        EXTRA_COLUMNS: 'option_list(%s, default=list())' % OPTION_STR,
    }

    # Placeholder if we decide to add columns with icons later
    #_dModes = {
    #        'Show Icons and Names': SHOW_ICONS_AND_TEXT,
    #        'Show Icons only': SHOW_ICONS_ONLY,
    #        'Show Text only': SHOW_TEXT_ONLY,
    #        }

    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *args, **kwargs):
        super(ExtraCardSetListViewColumns, self).__init__(*args, **kwargs)
        self._dCols = {}
        self._dWidths = {}
        self._dSortDataFuncs = {}

        for sKey, (iWidth, sRender, sData) in self.COLUMNS.iteritems():
            self._dWidths[sKey] = iWidth
            self._dCols[sKey] = getattr(self, sRender)
            self._dSortDataFuncs[sKey] = getattr(self, sData)

        # The database lookups are moderately expensive, so cache the results
        self._dCache = {}

        # We may add columns with icons later, like clans in the crypt
        self._iShowMode = SHOW_TEXT_ONLY

        if self.check_versions() and self.check_model_type():
            listen_row_update(self.card_set_changed, PhysicalCardSet)
            listen_row_destroy(self.card_set_added_deleted, PhysicalCardSet)
            listen_row_created(self.card_set_added_deleted, PhysicalCardSet)
            listen_changed(self.card_changed, PhysicalCardSet)
            self.perpane_config_updated()
    # pylint: enable-msg=W0142

    def cleanup(self):
        """Disconnect the database listeners"""
        if self.check_versions() and self.check_model_type():
            disconnect_changed(self.card_changed, PhysicalCardSet)
            disconnect_row_update(self.card_set_changed, PhysicalCardSet)
            disconnect_row_destroy(self.card_set_added_deleted,
                    PhysicalCardSet)
            disconnect_row_created(self.card_set_added_deleted,
                    PhysicalCardSet)
        super(ExtraCardSetListViewColumns, self).cleanup()

    # Rendering Functions

    def _get_card_set(self, oIter):
        """For the given iterator, get the associated physical card set"""
        try:
            # Strip markup from model
            sCardSetName = pango.parse_markup(
                    self.model.get_value(oIter, 0))[1]
            # Cache lookups, so we don't hit the database so hard when
            # sorting
            if not self._dCache.has_key(sCardSetName):
                # pylint: disable-msg=E1101
                # pylint + AbstractCard method wierdness
                self._dCache[sCardSetName] = {}
                self._dCache[sCardSetName]['Card Set'] = \
                        IPhysicalCardSet(sCardSetName)
            return sCardSetName
        except SQLObjectNotFound:
            self._dCache[sCardSetName] = {}
            # Cache failed lookup so we don't repeat it later
            self._dCache[sCardSetName]['Card Set'] = None
            return None

    # pylint: disable-msg=R0201
    # Making these functions for clarity
    # several unused paramaters due to function signatures
    # The bGetIcons parameter is needed to avoid icon lookups, etc when
    # sorting

    def _get_data_total(self, sCardSet, bGetIcons=True):
        """Return the total number of cards in the card set"""
        def query(oCardSet):
            """Query the database"""
            return MapPhysicalCardToPhysicalCardSet.selectBy(
                    physicalCardSetID=oCardSet.id).count()

        if sCardSet:
            # lookup totals
            dInfo = self._dCache[sCardSet]
            aIcons = []
            iTotal = _get_number(dInfo, 'Total Cards', query)
            if bGetIcons:
                aIcons = [None]
            return iTotal, aIcons
        return -1, []

    def _render_total(self, _oColumn, oCell, _oModel, oIter):
        """display the total"""
        sCardSet = self._get_card_set(oIter)
        iCount, aIcons = self._get_data_total(sCardSet, True)
        aText = _format_number(iCount)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_all_children(self, sCardSet, bGetIcons=True):
        """Return the number of children card sets"""
        def query(oCardSet):
            """Query the database"""
            return PhysicalCardSet.selectBy(parentID=oCardSet.id).count()

        if sCardSet:
            # lookup totals
            dInfo = self._dCache[sCardSet]
            aIcons = []
            iTotal = _get_number(dInfo, 'All Children', query)
            if bGetIcons:
                aIcons = [None]
            return iTotal, aIcons
        return -1, []

    def _render_all_children(self, _oColumn, oCell, _oModel, oIter):
        """display the the number of children"""
        sCardSet = self._get_card_set(oIter)
        iCount, aIcons = self._get_data_all_children(sCardSet, True)
        aText = _format_number(iCount)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_inuse_children(self, sCardSet, bGetIcons=True):
        """Return the number of In-Use children card sets"""
        def query(oCardSet):
            """Query the database"""
            return PhysicalCardSet.selectBy(parentID=oCardSet.id,
                    inuse=True).count()
        if sCardSet:
            # lookup totals
            dInfo = self._dCache[sCardSet]
            aIcons = []
            iTotal = _get_number(dInfo, 'In-Use Children', query)
            if bGetIcons:
                aIcons = [None]
            return iTotal, aIcons
        return -1, []

    def _render_inuse_children(self, _oColumn, oCell, _oModel, oIter):
        """display the the number of In-Use children"""
        sCardSet = self._get_card_set(oIter)
        iCount, aIcons = self._get_data_inuse_children(sCardSet, True)
        aText = _format_number(iCount)
        oCell.set_data(aText, aIcons, self._iShowMode)

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
            iTotal = _get_number(dInfo, 'Library', query)
            if bGetIcons:
                aIcons = [None]
            return iTotal, aIcons
        return -1, []

    def _render_library(self, _oColumn, oCell, _oModel, oIter):
        """display the library count"""
        sCardSet = self._get_card_set(oIter)
        iCount, aIcons = self._get_data_library(sCardSet, True)
        aText = _format_number(iCount)
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
            iTotal = _get_number(dInfo, 'Crypt', query)
            if bGetIcons:
                aIcons = [None]
            return iTotal, aIcons
        return -1, []

    def _render_crypt(self, _oColumn, oCell, _oModel, oIter):
        """display the crypt count"""
        sCardSet = self._get_card_set(oIter)
        iCount, aIcons = self._get_data_crypt(sCardSet, True)
        aText = _format_number(iCount)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_author(self, sCardSet, bGetIcons=True):
        """Get the card set author info"""
        if sCardSet:
            oCardSet = self._dCache[sCardSet]['Card Set']
            if oCardSet:
                sAuthor = oCardSet.author
            else:
                sAuthor = ''
            if not sAuthor:
                # Handle None sensibly
                sAuthor = ''
            aIcons = []
            if bGetIcons:
                aIcons = [None]
            return [sAuthor], aIcons
        return [], []

    def _render_author(self, _oColumn, oCell, _oModel, oIter):
        """Display the author column"""
        sCardSet = self._get_card_set(oIter)
        aText, aIcons = self._get_data_author(sCardSet, True)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_description(self, sCardSet, bGetIcons=True):
        """Get the card set description"""
        if sCardSet:
            oCardSet = self._dCache[sCardSet]['Card Set']
            if oCardSet:
                sDesc = oCardSet.comment
            else:
                sDesc = ''
            if not sDesc:
                # Handle None sensibly
                sDesc = ''
            aIcons = []
            if bGetIcons:
                aIcons = [None]
            return [sDesc], aIcons
        return [], []

    def _render_description(self, _oColumn, oCell, _oModel, oIter):
        """Display the card set comment"""
        sCardSet = self._get_card_set(oIter)
        aText, aIcons = self._get_data_description(sCardSet, True)
        oCell.set_data(aText, aIcons, self._iShowMode)

    # pylint: enable-msg=R0201

    def sort_column(self, _oModel, oIter1, oIter2, oGetData):
        """Stringwise comparision of oIter1 and oIter2.

           Return -1 if oIter1 < oIter, 0 in ==, 1 if >
           """
        sCardSet1 = self._get_card_set(oIter1)
        sCardSet2 = self._get_card_set(oIter2)
        oVal1 = oGetData(sCardSet1, False)[0]
        oVal2 = oGetData(sCardSet2, False)[0]
        # convert to string for sorting
        if isinstance(oVal1, list):
            oVal1 = " ".join(oVal1)
            oVal2 = " ".join(oVal2)
        iRes = cmp(oVal1, oVal2)
        if iRes == 0:
            # Values agree, so do fall back sort
            iRes = cmp(sCardSet1, sCardSet2)
        return iRes

    # SQLObject event listeners
    # While we can try to be clever and update the cache, there are enough
    # complex cases (importing backups, etc.) that need to be considered
    # that simply invalidating the cache is significanly simpler and safer

    def card_set_changed(self, _oCardSet, _dChanges):
        """We listen for card set events, and invalidate the cache"""
        self._dCache = {}

    def card_set_added_deleted(self, _oCardSet, _dKW=None, _fPostFuncs=None):
        """We listen for card set additions & deletions, and
           invalidate the cache when that occurs"""
        self._dCache = {}

    def card_changed(self, oCardSet, _oPhysCard, _iChg):
        """Listen for card changes.

           We invalidate card counts for the card set if it's in the cache.
           """
        sName = oCardSet.name
        if sName in self._dCache:
            dInfo = self._dCache[sName]
            for sKey in ('Total Cards', 'Library', 'Crypt'):
                if sKey in dInfo:
                    del dInfo[sKey]
            # queue a redraw
            self.view.queue_draw()

    # Actions

    def set_cols_in_use(self, aCols):
        """Add columns to the view"""
        iSortCol, _iDir = self.model.get_sort_column_id()
        if iSortCol is not None and iSortCol > 1:
            # We're changing the columns, so restore sorting to default
            self.model.set_sort_column_id(0, 0)

        for oCol in self._get_col_objects():
            self.view.remove_column(oCol)

        for iNum, sCol in enumerate(aCols):
            oCell = CellRendererIcons()
            oColumn = gtk.TreeViewColumn(sCol, oCell)
            oColumn.set_cell_data_func(oCell, self._dCols[sCol])
            oColumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            oColumn.set_fixed_width(self._dWidths.get(sCol, 100))
            oColumn.set_resizable(True)
            self.view.insert_column(oColumn, iNum + 1)
            oColumn.set_sort_column_id(iNum + 1 + SORT_COLUMN_OFFSET)
            self.model.set_sort_func(iNum + 1 + SORT_COLUMN_OFFSET,
                    self.sort_column, self._dSortDataFuncs[sCol])

    def _get_col_objects(self):
        """Get the actual TreeColumn in the view"""
        return [oCol for oCol in self.view.get_columns() if
                oCol.get_property("title") in self._dCols]

    # Config Update

    def perpane_config_updated(self, _bDoReload=True):
        """Called by base class on config updates."""
        aCols = None
        if self.check_versions() and self.check_model_type():
            aCols = self.get_perpane_item(self.EXTRA_COLUMNS)
        if aCols is not None:
            # Need to accept empty lists so we remove columns
            self.set_cols_in_use(aCols)


plugin = ExtraCardSetListViewColumns
