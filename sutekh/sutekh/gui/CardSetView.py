# CardSetView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""View object for card sets."""

import gtk
import pango
from sutekh.gui.CellRendererSutekhButton import CellRendererSutekhButton
from sutekh.gui.SutekhDialog import do_complaint_warning
from sutekh.gui.CardListView import CardListView
from sutekh.gui.CardSetListModel import CardSetCardListModel
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.SutekhUtility import delete_physical_card_set

class CardSetView(CardListView):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Subclass of CardListView specific to the Card Sets

       Adds editing support, and other specific to the card sets.
       The database interactions are handled by the controller,
       this just manages the GUI side of things, passing info to
       the controller when needed.
       """

    def __init__(self, oMainWindow, oController, sName):
        oModel = CardSetCardListModel(sName)
        # The only path here is via the main window, so config_file exists
        super(CardSetView, self).__init__(oController, oMainWindow,
                oModel, oMainWindow.config_file)
        self.sSetName = sName
        #self._oModel.cardclass = MapPhysicalCardToPhysicalCardSet
        #self._oModel.basefilter = PhysicalCardSetFilter(self.sSetName)
        self.sDragPrefix = PhysicalCardSet.sqlmeta.table + ":" + self.sSetName

        # Setup columns for default view
        self.oNumCell = gtk.CellRendererText()
        self.oNumCell.set_property('style', pango.STYLE_ITALIC)
        self.oNumCell.set_property('foreground-set', True)
        self.oNameCell = gtk.CellRendererText()
        self.oNameCell.set_property('style', pango.STYLE_ITALIC)

        oColumn1 = gtk.TreeViewColumn("#", self.oNumCell, text=1)
        oColumn1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn1.set_fixed_width(40)
        oColumn1.set_sort_column_id(1)
        self.append_column(oColumn1)

        oParentCell = gtk.CellRendererText()
        oParentCell.set_property('style', pango.STYLE_ITALIC)
        oParentCell.set_property('foreground-set', True)
        self.oParentCol = gtk.TreeViewColumn("Parent #", oParentCell,
                text=2)
        self.oParentCol.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.oParentCol.set_fixed_width(40)
        self.oParentCol.set_sort_column_id(2)
        self.append_column(self.oParentCol)
        self.oParentCol.set_visible(False)

        oColumn2 = gtk.TreeViewColumn("Cards", self.oNameCell, text=0)
        oColumn2.set_expand(True)
        oColumn2.set_sort_column_id(0)
        self.append_column(oColumn2)

        # Arrow cells
        oCell3 = CellRendererSutekhButton()
        oCell3.load_icon(gtk.STOCK_ADD, self)
        oCell4 = CellRendererSutekhButton()
        oCell4.load_icon(gtk.STOCK_REMOVE, self)

        oColumn3 = gtk.TreeViewColumn("", oCell3, showicon=3)
        oColumn3.set_fixed_width(22)
        oColumn3.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn3)

        oColumn4 = gtk.TreeViewColumn("", oCell4, showicon=4)
        oColumn4.set_fixed_width(22)
        oColumn4.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn4)

        oCell3.connect('clicked', self.inc_card)
        oCell4.connect('clicked', self.dec_card)

        self.connect('map-event', self.mapped)

        self._oMenuEditWidget = None

        self.set_expander_column(oColumn2)
        self.oCellColor = None

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

    def load(self):
        """Called when the model needs to be reloaded."""
        if self._oModel.get_card_iterator(None).count() == 0:
            self._oModel.bEditable = True
            # We do this before loading, so edit icons are correct
        self._oModel.load()
        self.check_editable()

    def check_editable(self):
        """Set the card list to be editable if it's empty"""
        if self.get_parent() and \
                self._oModel.get_card_iterator(None).count() == 0:
            # This isn't true when creating the view
            self._set_editable(True)

    # Used by card dragging handlers
    def add_card(self, sCardName, sExpansion):
        """Called to add a card with expansion"""
        if self._oModel.bEditable:
            self._oController.add_card(sCardName, sExpansion)

    # When editing cards, we pass info to the controller to
    # update stuff in the database
    # The Controller is responsible for updating the model,
    # since it defines the logic for handling expansions, etc.

    # pylint: disable-msg=W0613
    # arguments as required by the function signature
    def inc_card(self, oCell, oPath):
        """Called to increment the count for a card."""
        if self._oModel.bEditable:
            # pylint: disable-msg=W0612
            # only interested in bInc
            bInc, bDec = self._oModel.get_inc_dec_flags_from_path(oPath)
            if bInc:
                sCardName = self._oModel.get_card_name_from_path(oPath)
                sExpansion = self._oModel.get_exp_name_from_path(oPath)
                self._oController.inc_card(sCardName, sExpansion)

    def dec_card(self, oCell, oPath):
        """Called to decrement the count for a card"""
        if self._oModel.bEditable:
            # pylint: disable-msg=W0612
            # only interested in bDec
            bInc, bDec = self._oModel.get_inc_dec_flags_from_path(oPath)
            if bDec:
                sCardName = self._oModel.get_card_name_from_path(oPath)
                sExpansion = self._oModel.get_exp_name_from_path(oPath)
                self._oController.dec_card(sCardName, sExpansion)

    # functions related to tweaking widget display

    def mapped(self, oWidget, oEvent):
        """Called when the view has been mapped, so we can twiddle the
           display"""
        # see if we need to be editable
        self.check_editable()

    # pylint: enable-msg=W0613

    def set_color_edit_cue(self):
        """Set a visual cue that the card set is editable."""
        def _compare_colors(oColor1, oColor2):
            """Compare the RGB values for 2 gtk.gdk.Colors. Return True if
               they're the same, false otherwise."""
            return oColor1.to_string() == oColor2.to_string()
        oCurStyle = self.rc_get_style()
        # For card sets that start empty, oNumCell will be the wrong colour,
        # but, because of how CellRenderers interact with styles, oNameCell
        # will be the right one here
        self.oCellColor = self.oNameCell.get_property('foreground-gdk')
        oCurBackColor = oCurStyle.base[gtk.STATE_NORMAL]
        self.set_name('editable_view')
        oDefaultSutekhStyle = gtk.rc_get_style_by_paths(self.get_settings(),
                '', self.class_path(), self)
        # We want the class style for this widget, ignoring set_name effects
        oSpecificStyle = self.rc_get_style()
        if oSpecificStyle == oDefaultSutekhStyle or \
                oDefaultSutekhStyle is None:
            # No specific style set
            sColour = 'red'
            if _compare_colors(gtk.gdk.color_parse(sColour),
                    oCurStyle.fg[gtk.STATE_NORMAL]):
                sColour = 'green'
            sStyleInfo = """
            style "internal_sutekh_editstyle" {
                fg[NORMAL] = "%(colour)s"
                }
            widget "%(path)s" style "internal_sutekh_editstyle"
            """ % { 'colour' : sColour, 'path' : self.path() }
            gtk.rc_parse_string(sStyleInfo)
            # Need to force re-assesment of styles
            self.set_name('editable_view')
        oCurStyle = self.rc_get_style()
        # Force a hint on the number column as well
        oEditColor = oCurStyle.fg[gtk.STATE_NORMAL]
        oEditBackColor = oCurStyle.base[gtk.STATE_NORMAL]
        if _compare_colors(oEditColor, self.oCellColor) and \
                _compare_colors(oEditBackColor, oCurBackColor):
            # Theme change isn't visually distinct here, so we go
            # with red - this is safe, since CellRenderers aren't
            # themed, so the default color will not be red
            # (famous last words)
            # If the default background color is red, too bad
            self.oNumCell.set_property('foreground', 'red')
        else:
            # Theme change is visible
            self.oNumCell.set_property('foreground-gdk', oEditColor)

    def set_color_normal(self):
        """Unset the editable visual cue"""
        self.set_name('normal_view')
        self.oNumCell.set_property('foreground-gdk', self.oCellColor)

    def _set_editable(self, bValue):
        """Update the view and menu when the editable status changes"""
        self._oModel.bEditable = bValue
        if self._oMenuEditWidget is not None:
            self._oMenuEditWidget.set_active(bValue)
        if bValue:
            self.set_color_edit_cue()
        else:
            self.set_color_normal()

    def toggle_editable(self, bValue):
        """Reload the view and update status when editable status changes"""
        self._set_editable(bValue)
        self.reload_keep_expanded()

    def set_edit_menu_item(self, oMenuWidget):
        """Keep track of the menu item, so we can update it's toggled
           status."""
        self._oMenuEditWidget = oMenuWidget

    def set_parent_count_col_vis(self, bVisible):
        """Make the parent count column visible or invisible"""
        self.oParentCol.set_visible(bVisible)
