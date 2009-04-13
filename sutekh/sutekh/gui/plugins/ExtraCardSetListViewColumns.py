# ExtraCardSetListViewColumns.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# Modified from ExtraCardViewColumns.py
# GPL - see COPYING for details
"""Disply extra columns in the tree view"""

import gtk
import pango
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.CellRendererIcons import CellRendererIcons, SHOW_TEXT_ONLY
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCardSet, \
        MapPhysicalCardToPhysicalCardSet
from sutekh.core.Filters import PhysicalCardSetFilter, MultiCardTypeFilter, \
        FilterAndBox
from sutekh.core.DBSignals import listen_row_destroy, listen_row_update, \
        listen_row_created, listen_changed
from sqlobject import SQLObjectNotFound


SORT_COLUMN_OFFSET = 200 # ensure we don't clash with other extra columns

def _get_number(dInfo, sKey, fQuery):
    """Handle the use query & cache interaction for numbers"""
    if not dInfo.has_key(sKey):
        oCardSet = dInfo['Card Set']
        dInfo[sKey] = fQuery(oCardSet)
    return dInfo[sKey]

def _format_number(iCount):
    """Return suitable list for the given number"""
    if iCount == -1:
        return [""]
    return [str(iCount)]

class ExtraCardSetListViewColumns(CardListPlugin):
    """Add extra columns to the card set list view.

       Allow the card set list to be sorted on these columns
       """
    dTableVersions = {}
    aModelsSupported = ['Card Set List']

    _dWidths = {
            'Total cards' : 100,
            'All Children' : 100,
            'In-Use Children' : 100,
            'Library' : 100,
            'Crypt' : 100,
            'Author' : 300,
            'Description' : 700,
            }

    # Placeholder if we decide to add columns with icons later
    #_dModes = {
    #        'Show Icons and Names' : SHOW_ICONS_AND_TEXT,
    #        'Show Icons only' : SHOW_ICONS_ONLY,
    #        'Show Text only' : SHOW_TEXT_ONLY,
    #        }

    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *args, **kwargs):
        super(ExtraCardSetListViewColumns, self).__init__(*args, **kwargs)
        self._dCols = {}
        self._dCols['Total'] = self._render_total
        self._dCols['All Children'] = self._render_all_children
        self._dCols['In-Use Children'] = self._render_inuse_children
        self._dCols['Library'] = self._render_library
        self._dCols['Crypt'] = self._render_crypt
        self._dCols['Author'] = self._render_author
        self._dCols['Description'] = self._render_description
        # The database lookups are moderately expensive, so cache the results
        self._dCache = {}

        self._dSortDataFuncs = {}
        self._dSortDataFuncs['Total'] = self._get_data_total
        self._dSortDataFuncs['All Children'] = self._get_data_all_children
        self._dSortDataFuncs['In-Use Children'] = self._get_data_inuse_children
        self._dSortDataFuncs['Library'] = self._get_data_library
        self._dSortDataFuncs['Crypt'] = self._get_data_crypt
        self._dSortDataFuncs['Author'] = self._get_data_author
        self._dSortDataFuncs['Description'] = self._get_data_description

        # We may add columns with icons later, like clans in the crypt
        #self._oFirstBut = None
        self._iShowMode = SHOW_TEXT_ONLY

        listen_row_update(self.card_set_changed, PhysicalCardSet)
        listen_row_destroy(self.card_set_added_deleted, PhysicalCardSet)
        listen_row_created(self.card_set_added_deleted, PhysicalCardSet)
        listen_changed(self.card_changed, PhysicalCardSet)
    # pylint: enable-msg=W0142

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
                MultiCardTypeFilter(['Vampire', 'Imbued'])])
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
                MultiCardTypeFilter(['Vampire', 'Imbued'])])
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
            sAuthor = oCardSet.author
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
            sDesc = oCardSet.comment
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
    # Dialog and Menu Item Creation

    def get_menu_item(self):
        """Register on 'Plugins' menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oSelector = gtk.MenuItem("Select Extra Columns")
        oSelector.connect("activate", self.activate)
        return ('Plugins', oSelector)

    def activate(self, _oWidget):
        """Handle menu activation"""
        oDlg = self.make_dialog()
        oDlg.run()

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

    def make_dialog(self):
        """Create the column selection dialog"""
        sName = "Select Extra Columns ..."

        oDlg = SutekhDialog(sName, self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))

        oDlg.connect("response", self.handle_response)

        # pylint: disable-msg=W0201
        # no point in defining this in __init__
        self._aButtons = []
        aColsInUse = self.get_cols_in_use()
        # pylint: disable-msg=E1101
        # pylint doesn't detect vbox's methods
        for sName in self._dCols:
            oBut = gtk.CheckButton(sName)
            oBut.set_active(sName in aColsInUse)
            oDlg.vbox.pack_start(oBut)
            self._aButtons.append(oBut)

        # Icons mode question logic
        #oDlg.vbox.pack_start(gtk.HSeparator())
        #oIter = self._dModes.iterkeys()
        #for sName in oIter:
        #    self._oFirstBut = gtk.RadioButton(None, sName, False)
        #    if self._iShowMode == self._dModes[sName]:
        #        self._oFirstBut.set_active(True)
        #    oDlg.vbox.pack_start(self._oFirstBut, expand=False)
        #    break
        #for sName in oIter:
        #    oBut = gtk.RadioButton(self._oFirstBut, sName)
        #    oDlg.vbox.pack_start(oBut, expand=False)
        #    if self._iShowMode == self._dModes[sName]:
        #        oBut.set_active(True)

        oDlg.show_all()

        return oDlg

    # SQLObject event listeners
    # FIXME: We can be much cleverer here, and update the cache rather than
    # just invalidating it, but this is simpler for the initial implementation
    # (needs care when dealing with large scale changes like importing new WW
    # cardlists which cause lots of signals)

    def card_set_changed(self, _oCardSet, _dChanges):
        """We listen for card set events, and invalidate the cache"""
        self._dCache = {}

    def card_set_added_deleted(self, _oCardSet, _fPostFuncs=None):
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
            for sKey in ['Total Cards', 'Library', 'Crypt']:
                if sKey in dInfo:
                    del dInfo[sKey]
            # queue a redraw
            self.view.queue_draw()

    # Actions

    def handle_response(self, oDlg, oResponse):
        """Handle user response from the dialog"""
        if oResponse == gtk.RESPONSE_CANCEL:
            oDlg.destroy()
        elif oResponse == gtk.RESPONSE_OK:
            aColsInUse = []
            for oBut in self._aButtons:
                if oBut.get_active():
                    sLabel = oBut.get_label()
                    aColsInUse.append(sLabel)
            #for oBut in self._oFirstBut.get_group():
            #    sName = oBut.get_label()
            #    if oBut.get_active():
            #        self._iShowMode = self._dModes[sName]

            self.set_cols_in_use(aColsInUse)
            oDlg.destroy()

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

    def get_cols_in_use(self):
        """Get which extra columns have been added to view"""
        return [oCol.get_property("title") for oCol in self._get_col_objects()]

    def _get_col_objects(self):
        """Get the actual TreeColumn in the view"""
        return [oCol for oCol in self.view.get_columns() if
                oCol.get_property("title") in self._dCols]

plugin = ExtraCardSetListViewColumns
