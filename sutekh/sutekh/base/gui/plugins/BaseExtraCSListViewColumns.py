# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# Modified from ExtraCardViewColumns.py
# GPL - see COPYING for details
"""Display extra columns in the tree view"""

from sqlobject import SQLObjectNotFound

from gi.repository import Pango

from ...core.BaseTables import (PhysicalCardSet,
                                MapPhysicalCardToPhysicalCardSet)
from ...core.BaseAdapters import IPhysicalCardSet
from ...core.DBSignals import (listen_row_destroy, listen_row_update,
                               listen_row_created, listen_changed,
                               disconnect_changed,
                               disconnect_row_destroy,
                               disconnect_row_update,
                               disconnect_row_created)
from ..CellRendererIcons import DisplayOption
from .BaseExtraColumns import (BaseExtraColumns, get_number,
                               format_number)


class BaseExtraCSListViewColumns(BaseExtraColumns):
    """Add extra columns to the card set list view.

       Allow the card set list to be sorted on these columns
       """
    dTableVersions = {}
    aModelsSupported = ('Card Set List',)

    SORT_COLUMN_OFFSET = 200

    DEFAULT_MODE = 'Show Text only'

    # Currently, Sutekh only supports text mode columns here
    MODES = {
        DEFAULT_MODE:  DisplayOption.SHOW_TEXT_ONLY,
    }

    # Dictionary of column info - width, render function name, data func name
    COLUMNS = {
        'Total cards': (100, '_render_total', '_get_data_total'),
        'All Children': (100, '_render_all_children',
                         '_get_data_all_children'),
        'In-Use Children': (100, '_render_inuse_children',
                            '_get_data_inuse_children'),
        'Author': (300, '_render_author', '_get_data_author'),
        'Description': (700, '_render_description',
                        '_get_data_description'),
    }

    # Cache keys to invalidate when the card set changes
    CS_KEYS = ('Total Cards',)

    dCardSetListConfig = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        listen_row_update(self.card_set_changed, PhysicalCardSet)
        listen_row_destroy(self.card_set_added_deleted, PhysicalCardSet)
        listen_row_created(self.card_set_added_deleted, PhysicalCardSet)
        listen_changed(self.card_changed, PhysicalCardSet)

    def cleanup(self):
        """Disconnect the database listeners"""
        disconnect_changed(self.card_changed, PhysicalCardSet)
        disconnect_row_update(self.card_set_changed, PhysicalCardSet)
        disconnect_row_destroy(self.card_set_added_deleted,
                               PhysicalCardSet)
        disconnect_row_created(self.card_set_added_deleted,
                               PhysicalCardSet)
        super().cleanup()

    @classmethod
    def update_config(cls):
        """Fix the config to use the right keys."""
        cls.fix_config(cls.dCardSetListConfig)

    # Manage database signals around upgrades

    def update_to_new_db(self):
        """Reconnect the database signal listeners and queue a refresh"""
        # clear cache
        self._dCache = {}
        # reconnect signals
        listen_row_update(self.card_set_changed, PhysicalCardSet)
        listen_row_destroy(self.card_set_added_deleted, PhysicalCardSet)
        listen_row_created(self.card_set_added_deleted, PhysicalCardSet)
        listen_changed(self.card_changed, PhysicalCardSet)
        # queue a redraw
        self.view.queue_draw()

    def prepare_for_db_update(self):
        """Disconnect the database signals during the upgrade"""
        disconnect_changed(self.card_changed, PhysicalCardSet)
        disconnect_row_update(self.card_set_changed, PhysicalCardSet)
        disconnect_row_destroy(self.card_set_added_deleted,
                               PhysicalCardSet)
        disconnect_row_created(self.card_set_added_deleted,
                               PhysicalCardSet)

    # default data function Functions

    def _get_iter_data(self, oIter):
        """For the given iterator, get the associated physical card set"""
        try:
            # Strip markup from model
            sCardSetName = Pango.parse_markup(
                self.model.get_value(oIter, 0), -1, "\0").text
            # Cache lookups, so we don't hit the database so hard when
            # sorting
            if sCardSetName not in self._dCache:
                self._dCache[sCardSetName] = {}
                self._dCache[sCardSetName]['Card Set'] = \
                    IPhysicalCardSet(sCardSetName)
            return sCardSetName
        except SQLObjectNotFound:
            self._dCache[sCardSetName] = {}
            # Cache failed lookup so we don't repeat it later
            self._dCache[sCardSetName]['Card Set'] = None
            return None

    # pylint: disable=no-self-use
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
            iTotal = get_number(dInfo, 'Total Cards', query)
            if bGetIcons:
                aIcons = [None]
            return iTotal, aIcons
        return -1, []

    def _render_total(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """display the total"""
        sCardSet = self._get_iter_data(oIter)
        iCount, aIcons = self._get_data_total(sCardSet, True)
        aText = format_number(iCount)
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
            iTotal = get_number(dInfo, 'All Children', query)
            if bGetIcons:
                aIcons = [None]
            return iTotal, aIcons
        return -1, []

    def _render_all_children(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """display the the number of children"""
        sCardSet = self._get_iter_data(oIter)
        iCount, aIcons = self._get_data_all_children(sCardSet, True)
        aText = format_number(iCount)
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
            iTotal = get_number(dInfo, 'In-Use Children', query)
            if bGetIcons:
                aIcons = [None]
            return iTotal, aIcons
        return -1, []

    def _render_inuse_children(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """display the the number of In-Use children"""
        sCardSet = self._get_iter_data(oIter)
        iCount, aIcons = self._get_data_inuse_children(sCardSet, True)
        aText = format_number(iCount)
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

    def _render_author(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """Display the author column"""
        sCardSet = self._get_iter_data(oIter)
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

    def _render_description(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """Display the card set comment"""
        sCardSet = self._get_iter_data(oIter)
        aText, aIcons = self._get_data_description(sCardSet, True)
        oCell.set_data(aText, aIcons, self._iShowMode)

    # pylint: enable=no-self-use

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
            for sKey in self.CS_KEYS:
                if sKey in dInfo:
                    del dInfo[sKey]
            # queue a redraw
            self.view.queue_draw()
