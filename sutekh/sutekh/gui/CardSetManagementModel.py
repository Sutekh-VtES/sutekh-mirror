# CardSetManagementModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeModel class the card sets."""

import gtk, gobject
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.core.Filters import NullFilter

class CardSetManagementModel(gtk.TreeStore):
    # pylint: disable-msg=R0904
    # gtk.Widget, so lots of public methods
    """TreeModel for the card sets"""
    def __init__(self, oMainWindow):
        super(CardSetManagementModel, self).__init__(gobject.TYPE_STRING)
        self._dName2Iter = {}

        self._oMainWin = oMainWindow

        self._bApplyFilter = False # whether to apply the select filter
        # additional filters for selecting from the list
        self._oSelectFilter = None
        self.oEmptyIter = None
        self.set_sort_func(0, self.sort_column)

    # pylint: disable-msg=W0212
    # W0212 - we explicitly allow access via these properties
    applyfilter = property(fget=lambda self: self._bApplyFilter,
            fset=lambda self, x: setattr(self, '_bApplyFilter', x))
    selectfilter = property(fget=lambda self: self._oSelectFilter,
            fset=lambda self, x: setattr(self, '_oSelectFilter', x))
    # pylint: enable-msg=W0212

    # pylint: disable-msg=R0201
    # this should be a method for consistency
    def get_card_set_iterator(self, oFilter):
        """Return an interator over the card set model.

           None may be used to retrieve the entire card set list
           """
        if not oFilter:
            oFilter = NullFilter()
        return oFilter.select(PhysicalCardSet).distinct()
    # pylint: enable-msg=R0201

    def load(self):
        """Load the card sets into the card view"""
        self.clear()
        oCardSetIter = self.get_card_set_iterator(self.get_current_filter())
        self._dName2Iter = {}

        # Loop through the card sets, getting the parent->child relationships
        for oCardSet in oCardSetIter:
            if oCardSet.name in self._dName2Iter:
                # We've already loaded this card set, so skip
                continue
            if oCardSet.parent:
                # Do funky stuff to make sure parent is shown in the view
                oParent = oCardSet
                aToAdd = []
                while oParent and oParent.name not in self._dName2Iter:
                    # FIXME: Add loop detection + raise error on loops
                    aToAdd.insert(0, oParent) # Insert at the head
                    oParent = oParent.parent
                if oParent and oParent.name in self._dName2Iter:
                    oIter = self._dName2Iter[oParent.name]
                else:
                    oIter = None
            else:
                # Just add
                oIter = None
                aToAdd = [oCardSet]
            for oSet in aToAdd:
                oIter = self.append(oIter)
                sName = oSet.name
                if self._oMainWin.find_pane_by_name(sName):
                    sName = '<i>%s</i>' % sName
                if oSet.inuse:
                    # In use sets are in bold
                    sName = '<b>%s</b>' % sName
                self.set(oIter, 0, sName)
                self._dName2Iter[oSet.name] = oIter

        if not self._dName2Iter:
            # Showing nothing
            self.oEmptyIter = self.append(None)
            sText = self._get_empty_text()
            self.set(self.oEmptyIter, 0, sText)

    def get_current_filter(self):
        """Get the current applied filter."""
        if self.applyfilter:
            return self.selectfilter
        else:
            return None

    def get_name_from_iter(self, oIter):
        """Extract the value at oIter from the model, correcting for encoding
           issues."""
        sCardSetName = self.get_value(oIter, 0).decode("utf-8")
        # Strip markup
        if sCardSetName.startswith('<b><i>'):
            sCardSetName = sCardSetName[6:-8]
        elif sCardSetName.startswith('<b>') or sCardSetName.startswith('<i>'):
            sCardSetName = sCardSetName[3:-4]
        return sCardSetName

    def get_name_from_path(self, oPath):
        """Get the card set name at oPath."""
        oIter = self.get_iter(oPath)
        return self.get_name_from_iter(oIter)

    # pylint: disable-msg=W0613
    # oModel required by function signature
    def sort_column(self, oModel, oIter1, oIter2):
        """Custom sort function - ensure that markup doesn't affect sort
           order"""
        oCardSet1 = self.get_name_from_iter(oIter1)
        oCardSet2 = self.get_name_from_iter(oIter2)
        # get_name_from_iter strips markup for us
        return cmp(oCardSet1, oCardSet2)

    def _get_empty_text(self):
        """Get the correct text for an empty model."""
        if self.get_card_set_iterator(None).count() == 0:
            sText = 'Empty'
        else:
            sText = 'No Card Sets found'
        return sText


