# PhysicalCardView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Provide a TreeView for the physical card collection"""

from sutekh.gui.CardListView import EditableCardListView
from sutekh.gui.CardListModel import PhysicalCardListModel

class PhysicalCardView(EditableCardListView):
    # pylint: disable-msg=R0904
    # gtk class, so many public methods
    """The card list view for the physical card collection.

       Special cases Editable card list with those properties
       needed for the card collection - the drag prefix, the
       card_drop handling and handling of pasted data.
       """
    sDragPrefix = 'Phys:'

    def __init__(self, oController, oWindow, oConfig):
        oModel = PhysicalCardListModel(
                oWindow.config_file.get_show_zero_count_cards())
        super(PhysicalCardView, self).__init__(oController, oWindow,
                oModel, oConfig)

        self._oController = oController


    # pylint: disable-msg=R0913
    # Number of arguments needed by function signature
    def card_drop(self, oWidget, oContext, iXPos, iYPos, oData, oInfo, oTime):
        """Handle cards being dropped on the View via drag-n-drop.

           Determine the source, and add the cards if the model is editable.
           """
        if not oData or oData.format != 8:
            oContext.finish(False, False, oTime)
        else:
            sSource, aCardInfo = self.split_selection_data(oData.data)
            if sSource == "Sutekh Pane:":
                # Pane being dragged, so pass up to the pane widget
                self._oController.frame.drag_drop_handler(oWidget, oContext,
                        iXPos, iYPos, oData, oInfo, oTime)
            # Don't accept cards when not editable
            elif self._oModel.bEditable and \
                    self.add_paste_data(sSource, aCardInfo):
                oContext.finish(True, False, oTime) # paste successful
            else:
                oContext.finish(False, False, oTime) # not successful

    def add_paste_data(self, sSource, aCards):
        """Helper function for drag+drop + copy+paste.

           We can only drag from the AbstractCard List
           We can't drag from the card sets
           """
        if sSource in ['Abst:']:
            # pylint: disable-msg=W0612
            # iCount is unused
            for iCount, sCardName, sExpansion in aCards:
                # We are adding new cards, so only 1 of each
                self.add_card(sCardName, sExpansion)
            return True
        else:
            return False
