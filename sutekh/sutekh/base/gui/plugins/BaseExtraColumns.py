# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2009, 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# Modified from ExtraCardSetListViewColumns.py
# GPL - see COPYING for details
"""Display extra columns in the tree view"""

from gi.repository import Gtk
from ..BasePluginManager import BasePlugin
from ..CellRendererIcons import CellRendererIcons, DisplayOption


def get_number(dInfo, sKey, fQuery):
    """Handle the use query & cache interaction for numbers"""
    if sKey not in dInfo:
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


def format_number(iCount):
    """Return suitable list for the given number"""
    if iCount == -1:
        return [""]
    return [str(iCount)]


class BaseExtraColumns(BasePlugin):
    """Base plugin for adding extra columns to one of the views."""

    # Dictionary of column info
    # Entries are of the form:
    #     Column Title: (column width, column data rendering function name,
    #                    column sorting function name)
    COLUMNS = {}

    SORT_COLUMN_OFFSET = 100  # ensure we don't clash with other extra columns

    POS_COLUMN_OFFSET = 1  # Offset to ensure we are correctly positioned

    EXTRA_COLUMNS = "extra columns"

    ICON_MODE = "column mode"
    DEFAULT_MODE = 'Show Icons and Names'

    # Icon modes - may do nothing for some views
    MODES = {
        DEFAULT_MODE: DisplayOption.SHOW_ICONS_AND_TEXT,
        'Show Icons only': DisplayOption.SHOW_ICONS_ONLY,
        'Show Text only': DisplayOption.SHOW_TEXT_ONLY,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dCols = {}
        self._dWidths = {}
        self._dSortDataFuncs = {}

        for sKey, (iWidth, sRender, sData) in self.COLUMNS.items():
            self._dWidths[sKey] = iWidth
            self._dCols[sKey] = getattr(self, sRender)
            self._dSortDataFuncs[sKey] = getattr(self, sData)

        # The database lookups can be moderately expensive, so we
        # provide a cache for the results
        self._dCache = {}

        self._iShowMode = self.MODES[self.DEFAULT_MODE]

        self.perpane_config_updated()

    @classmethod
    def fix_config(cls, dConfig):
        """Helper for the update_config hook.

           Subclasses should call this with the right config dict."""
        sOptions = ", ".join('"%s"' % sKey for sKey in
                             sorted(cls.COLUMNS.keys()))
        dConfig[cls.EXTRA_COLUMNS] = ('option_list(%s, default=list())' %
                                      sOptions)
        sIconOpts = ", ".join('"%s"' % sKey for sKey in
                              sorted(cls.MODES.keys()))
        dConfig[cls.ICON_MODE] = 'option(%s, default="%s")' % (
            sIconOpts, cls.DEFAULT_MODE)

    def _get_iter_data(self, oIter):
        """Return the appropriate object to look up for the
           data queries."""
        raise NotImplementedError('Implement _get_iter_data')

    def sort_column(self, _oModel, oIter1, oIter2, oGetData):
        """Comparision of oIter1 and oIter2.

           Return -1 if oIter1 < oIter, 0 in ==, 1 if >
           """
        oObj1 = self._get_iter_data(oIter1)
        oObj2 = self._get_iter_data(oIter2)
        if oObj1 is None or oObj2 is None:
            # Not comparing like for like, so fall-back to default
            return self.model.sort_equal_iters(oIter1, oIter2)
        oVal1 = oGetData(oObj1, False)[0]
        oVal2 = oGetData(oObj2, False)[0]
        # convert to string for sorting
        if isinstance(oVal1, list):
            oVal1 = " ".join(oVal1)
            oVal2 = " ".join(oVal2)
        if oVal1 < oVal2:
            return -1
        if oVal1 > oVal2:
            return 1
        # Values agree, so do fall back sort
        return self.model.sort_equal_iters(oIter1, oIter2)

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
            oColumn = Gtk.TreeViewColumn(sCol, oCell)
            oColumn.set_cell_data_func(oCell, self._dCols[sCol])
            oColumn.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            oColumn.set_fixed_width(self._dWidths.get(sCol, 100))
            oColumn.set_resizable(True)
            iOffset = iNum + self.POS_COLUMN_OFFSET
            self.view.insert_column(oColumn, iOffset)
            iSortOffset = iOffset + self.SORT_COLUMN_OFFSET
            oColumn.set_sort_column_id(iSortOffset)
            self.model.set_sort_func(iSortOffset, self.sort_column,
                                     self._dSortDataFuncs[sCol])

    def _get_col_objects(self):
        """Get the actual TreeColumn in the view"""
        return [oCol for oCol in self.view.get_columns() if
                oCol.get_property("title") in self._dCols]

    # Config Update

    def perpane_config_updated(self, _bDoReload=True):
        """Called by base class on config updates."""
        aCols = self.get_perpane_item(self.EXTRA_COLUMNS)
        sShowMode = self.get_perpane_item(self.ICON_MODE)
        self._iShowMode = self.MODES.get(sShowMode, self.DEFAULT_MODE)
        if aCols is not None:
            # Need to accept empty lists so we remove columns
            self.set_cols_in_use(aCols)
