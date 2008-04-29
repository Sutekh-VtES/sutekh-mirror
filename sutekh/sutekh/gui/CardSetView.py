# CardSetView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""View object for card sets."""

import gtk
from sutekh.gui.SutekhDialog import do_complaint_warning
from sutekh.gui.CardListView import EditableCardListView
from sutekh.gui.CardListModel import PhysicalCardSetCardListModel, \
        CardListModel
from sutekh.core.SutekhObjects import PhysicalCardSet, \
        MapPhysicalCardToPhysicalCardSet
from sutekh.core.Filters import PhysicalCardSetFilter
from sutekh.SutekhUtility import delete_physical_card_set

class CardSetView(EditableCardListView):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Subclass of EditableCardListView specific to the Card Sets

       This is common to both Physical and Abstract Card Sets. The
       differences are embedded in the associated controller object
       and the database object used for filters."""
    def __init__(self, oMainWindow, oController, sName):
        oModel = PhysicalCardSetCardListModel(sName)
        # The only path here is via the main window, so config_file exists
        super(CardSetView, self).__init__(oController, oMainWindow,
                oModel, oMainWindow.config_file)
        self.sSetName = sName
        #self._oModel.cardclass = MapPhysicalCardToPhysicalCardSet
        #self._oModel.basefilter = PhysicalCardSetFilter(self.sSetName)
        self.sDragPrefix = PhysicalCardSet.sqlmeta.table + ":" + self.sSetName

    # pylint: disable-msg=R0913, W0613
    # elements required by function signature
    def card_drop(self, oWidget, oContext, iXPos, iYPos, oData, oInfo, oTime):
        """Handle drag-n-drop events."""
        if not oData or oData.format != 8:
            # Don't accept invalid data
            oContext.finish(False, False, oTime)
        else:
            sSource, aCardInfo = self.split_selection_data(oData.data)
            if sSource == "Sutekh Pane:":
                self._oController.frame.drag_drop_handler(oWidget, oContext,
                        iXPos, iYPos, oData, oInfo, oTime)
            elif not self._oModel.bEditable:
                # Don't accept cards when editable
                oContext.finish(False, False, oTime)
            elif sSource == self.sDragPrefix:
                # Can't drag to oneself
                oContext.finish(False, False, oTime)
            # pass off to helper function
            if self.add_paste_data(sSource, aCardInfo):
                oContext.finish(True, False, oTime) # paste successful
            else:
                oContext.finish(False, False, oTime) # not successful
    # pylint: enable-msg=R0913, W0613

    def add_paste_data(self, sSource, aCards):
        """Helper function for drag+drop and copy+paste.

           Rules are - we can always drag from the PhysicalCard List and
           from cardsets of the same type, but only ACS's can recieve cards
           from the AbstractCard List
           """
        aSources = sSource.split(':')
        if aSources[0] in ["Phys", PhysicalCardSet.sqlmeta.table]:
            # Add the cards, Count Matters
            for iCount, sCardName, sExpansion in aCards:
                # pylint: disable-msg=W0612
                # iLoop is just loop counter
                for iLoop in range(iCount):
                    self.add_card(sCardName, sExpansion)
            return True
        else:
            return False

    def delete_card_set(self):
        """Delete this card set from the database."""
        # Check if CardSet is empty
        oCS = PhysicalCardSet.byName(self.sSetName)
        if len(oCS.cards)>0:
            iResponse = do_complaint_warning("Card Set Not Empty. "
                    "Really Delete?")
            if iResponse == gtk.RESPONSE_CANCEL:
                return False # not deleting
        # Got this far, so delete the card set
        delete_physical_card_set(self.sSetName)
        # Tell Window to clean up
        return True
