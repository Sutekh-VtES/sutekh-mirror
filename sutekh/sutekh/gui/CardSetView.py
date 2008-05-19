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
from sutekh.gui.CardSetListModel import CardSetCardListModel
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.SutekhUtility import delete_physical_card_set

class CardSetView(EditableCardListView):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Subclass of EditableCardListView specific to the Card Sets

       This is common to both Physical and Abstract Card Sets. The
       differences are embedded in the associated controller object
       and the database object used for filters."""
    def __init__(self, oMainWindow, oController, sName):
        oModel = CardSetCardListModel(sName)
        # The only path here is via the main window, so config_file exists
        super(CardSetView, self).__init__(oController, oMainWindow,
                oModel, oMainWindow.config_file)
        self.sSetName = sName
        #self._oModel.cardclass = MapPhysicalCardToPhysicalCardSet
        #self._oModel.basefilter = PhysicalCardSetFilter(self.sSetName)
        self.sDragPrefix = PhysicalCardSet.sqlmeta.table + ":" + self.sSetName

    def process_selection(self):
        """Create a dictionary from the selection.

           Entries are of the form sCardName : {sExpansion1 : iCount1, ... }
           for use in drag-'n drop and elsewhere.
           """
        oModel, oPathList = self._oSelection.get_selected_rows()
        dSelectedData = {}
        for oPath in oPathList:
            sCardName, sExpansion, iCount, iDepth = \
                    oModel.get_all_from_path(oPath)
            if iDepth == 0:
                # Skip top level items, since they're meaningless for the
                # selection
                continue
            # if a card is selected, then it's children (which are
            # the expansions) which are selected are ignored, since
            # We always treat this as all cards selected
            dSelectedData.setdefault(sCardName, {})
            if iDepth == 1:
                # Remove anything already assigned to this,
                # since parent overrides all
                dSelectedData[sCardName].clear()
                # We need to loop over all the children, and add
                # their expansion counts, so we do the expected thing
                oIter = oModel.get_iter(oPath)
                for iChildCount in range(oModel.iter_n_children(oIter)):
                    oChildIter = oModel.iter_nth_child(oIter, iChildCount)
                    oPath = oModel.get_path(oChildIter)
                    sCardName, sExpansion, iCount, iDepth = \
                            oModel.get_all_from_path(oPath)
                    dSelectedData[sCardName][sExpansion] = iCount
            else:
                if sExpansion in dSelectedData[sCardName]:
                    continue
                dSelectedData[sCardName][sExpansion] = iCount
        return dSelectedData


    # pylint: disable-msg=R0913, W0613
    # elements required by function signature
    def card_drop(self, oWidget, oContext, iXPos, iYPos, oData, oInfo, oTime):
        """Handle drag-n-drop events."""
        if not oData or oData.format != 8:
            # Don't accept invalid data
            oContext.finish(False, False, oTime)
        else:
            sSource, aCardInfo = self.split_selection_data(oData.data)
            if sSource == "Sutekh Pane:" or sSource == "Card Set:":
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
                if aSources[0] == "Phys":
                    # Only ever add 1 when dragging from physiscal card list
                    self.add_card(sCardName, sExpansion)
                else:
                    for iLoop in range(iCount):
                        self.add_card(sCardName, sExpansion)
            return True
        else:
            return False

    def delete_card_set(self):
        """Delete this card set from the database."""
        # Check if CardSet is empty
        # pylint: disable-msg=E1101
        # sqlobject confuses pylint
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

    def del_selection(self):
        """try to delete all the cards in the current selection"""
        if self._oModel.bEditable:
            dSelectedData = self.process_selection()
            for sCardName in dSelectedData:
                for sExpansion, iCount in dSelectedData[sCardName].iteritems():
                    # pylint: disable-msg=W0612
                    # iAttempt is loop counter
                    for iAttempt in range(iCount):
                        if sExpansion != 'None':
                            self._oController.dec_card(sCardName, sExpansion)
                        else:
                            self._oController.dec_card(sCardName, None)

    def do_paste(self):
        """Try and paste the current selection from the appliction clipboard"""
        if self._oModel.bEditable:
            sSelection = self._oMainWin.get_selection_text()
            sSource, aCards = self.split_selection_data(sSelection)
            if sSource != self.sDragPrefix:
                # Prevent pasting into oneself
                self.add_paste_data(sSource, aCards)

