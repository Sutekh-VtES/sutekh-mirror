# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""View object for card sets."""

from gi.repository import Gdk, Gtk

from .CellRendererSutekhButton import CellRendererSutekhButton
from .CellRendererIcons import CellRendererIcons
from .CardListView import CardListView
from .CardSetListModel import CardSetCardListModel
from ..core.BaseTables import PhysicalCardSet

NUM_KEYS = {
    Gdk.keyval_from_name('1'): 1,
    Gdk.keyval_from_name('KP_1'): 1,
    Gdk.keyval_from_name('2'): 2,
    Gdk.keyval_from_name('KP_2'): 2,
    Gdk.keyval_from_name('3'): 3,
    Gdk.keyval_from_name('KP_3'): 3,
    Gdk.keyval_from_name('4'): 4,
    Gdk.keyval_from_name('KP_4'): 4,
    Gdk.keyval_from_name('5'): 5,
    Gdk.keyval_from_name('KP_5'): 5,
    Gdk.keyval_from_name('6'): 6,
    Gdk.keyval_from_name('KP_6'): 6,
    Gdk.keyval_from_name('7'): 7,
    Gdk.keyval_from_name('KP_7'): 7,
    Gdk.keyval_from_name('8'): 8,
    Gdk.keyval_from_name('KP_8'): 8,
    Gdk.keyval_from_name('9'): 9,
    Gdk.keyval_from_name('KP_9'): 9,
}

PLUS_KEYS = set([
    Gdk.keyval_from_name('plus'),
    Gdk.keyval_from_name('KP_Add'),
])
MINUS_KEYS = set([
    Gdk.keyval_from_name('minus'),
    Gdk.keyval_from_name('KP_Subtract'),
])


class CardSetView(CardListView):
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # Gtk.Widget, so many public methods
    # We need to track a fair amount of state, so many attributes
    # pylint: disable=too-many-ancestors
    # many ancestors, due to our object hierachy on top of the quite
    # deep Gtk one
    """Subclass of CardListView specific to the Card Sets

       Adds editing support, and other specific to the card sets.
       The database interactions are handled by the controller,
       this just manages the GUI side of things, passing info to
       the controller when needed.
       """

    # Initialise key ranges for key tests
    # pylint: disable=too-many-statements
    # We need a lot of setup here, so this is long
    def __init__(self, oMainWindow, oController, sName, bStartEditable):
        oModel = CardSetCardListModel(sName, oMainWindow.config_file)
        oModel.enable_sorting()
        if bStartEditable:
            oModel.bEditable = True
        # The only path here is via the main window, so config_file exists
        super().__init__(oController, oMainWindow,
                         oModel, oMainWindow.config_file)

        self.sSetName = sName
        self.sDragPrefix = PhysicalCardSet.sqlmeta.table + ":" + self.sSetName

        # Setup columns for default view
        self.oNumCell = Gtk.CellRendererText()
        self.oNameCell = CellRendererIcons(5)

        oColumn1 = Gtk.TreeViewColumn("#", self.oNumCell, text=1)
        oColumn1.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        oColumn1.set_min_width(20)
        oColumn1.set_fixed_width(60)
        oColumn1.set_sort_column_id(1)
        oColumn1.set_resizable(True)
        self.append_column(oColumn1)

        oParentCell = Gtk.CellRendererText()
        self.oParentCol = Gtk.TreeViewColumn("Par #", oParentCell, text=2,
                                             foreground_rgba=7)
        self.oParentCol.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.oParentCol.set_min_width(20)
        self.oParentCol.set_fixed_width(60)
        self.oParentCol.set_sort_column_id(2)
        self.append_column(self.oParentCol)
        self.oParentCol.set_visible(False)
        self.oParentCol.set_resizable(True)

        oColumn2 = Gtk.TreeViewColumn("Cards", self.oNameCell, text=0,
                                      textlist=5, icons=6)
        oColumn2.set_min_width(100)
        oColumn2.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        oColumn2.set_sort_column_id(0)
        oColumn2.set_expand(True)
        oColumn2.set_resizable(True)
        self.append_column(oColumn2)
        self.set_expander_column(oColumn2)

        # Inc/Dec cells
        oIncCell = CellRendererSutekhButton()
        oIncCell.load_icon("list-add", self)
        oDecCell = CellRendererSutekhButton()
        oDecCell.load_icon("list-remove", self)

        self.oIncCol = Gtk.TreeViewColumn("", oIncCell, showicon=3)
        self.oIncCol.set_fixed_width(19)
        self.oIncCol.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.oIncCol.set_resizable(False)
        self.oIncCol.set_visible(False)
        self.append_column(self.oIncCol)

        self.oDecCol = Gtk.TreeViewColumn("", oDecCell, showicon=4)
        self.oDecCol.set_fixed_width(19)
        self.oDecCol.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.oDecCol.set_resizable(False)
        self.oDecCol.set_visible(False)
        self.append_column(self.oDecCol)

        oIncCell.connect('clicked', self.inc_card)
        oDecCell.connect('clicked', self.dec_card)

        self.__iMapID = self.connect('map', self.mapped)
        self.connect('key-press-event', self.key_press)

        self._oMenu = None

        self.oCellColor = None

        self.set_fixed_height_mode(True)

    # pylint: enable=too-many-statements

    def process_selection(self):
        """Create a dictionary from the selection.

           Entries are of the form sCardName : {sExpansion1 : iCount1, ... }
           for use in drag-'n drop and elsewhere.
           """
        oModel, oPathList = self._oSelection.get_selected_rows()
        dSelectedData = {}
        for oPath in oPathList:
            iAbsID, iPhysID, iCount, iDepth = \
                oModel.get_drag_info_from_path(oPath)
            if not iAbsID:
                # Not a card in this card set, so we skip
                continue
            dSelectedData.setdefault(iAbsID, {})
            if iDepth == 1:
                # this is treated as selecting all the children in this
                # card set
                # Remove anything already assigned to this
                dSelectedData[iAbsID].clear()
                for iPhysID, iCnt in \
                        oModel.get_drag_child_info(oPath).items():
                    dSelectedData[iAbsID][iPhysID] = iCnt
            elif not iPhysID:
                # If the expansion is unknown, see if there are interesting
                # children
                # This may well not to the right thing with complex
                # selections, but it avoids issues when the same card is
                # selected multiple times because it's in different groupings
                dChildInfo = oModel.get_drag_child_info(oPath)
                if dChildInfo:
                    for iPhysID, iCnt in dChildInfo.items():
                        dSelectedData[iAbsID][iPhysID] = iCnt
                else:
                    # Pass through as unknown
                    if -1 in dSelectedData[iAbsID]:
                        # We already have this info
                        continue
                    dSelectedData[iAbsID][-1] = iCount
            else:
                if iPhysID in dSelectedData[iAbsID]:
                    # We already have this info
                    continue
                dSelectedData[iAbsID][iPhysID] = iCount
        return dSelectedData

    def _process_edit_selection(self, iSetNewCount=None, iChg=None):
        """Create a dictionary from the selection, suitable for the quick
           key based edits.

           Entries are of the form
               oPhysCard : { sCardSetName : [iCount1, iNewCnt1] ... }
           In addition to adding information about card sets, this
           differs from process_selection in the way card level items
           are handled. Here, these are treated as selecting the expansion
           None, and ignoring other expansions.

           Since this isn't going through the drag-n-drop code, we don't
           need to create a string representation, so we can work with the
           card objects directly.

           """
        oModel, oPathList = self._oSelection.get_selected_rows()
        dSelectedData = {}
        aSkip = set()
        iNewCount = 0
        for oPath in oPathList:
            sCardSet = None
            oIter = oModel.get_iter(oPath)
            oPhysCard = oModel.get_physical_card_from_iter(oIter)
            oAbsCard = oModel.get_abstract_card_from_iter(oIter)
            iCount = oModel.get_card_count_from_iter(oIter)
            if iChg:
                iNewCount = max(0, iCount + iChg)
            elif iSetNewCount:
                iNewCount = iSetNewCount
            _sCardName, _sExpansion, sCardSet = \
                oModel.get_all_names_from_iter(oIter)
            dSelectedData.setdefault(oPhysCard, {})
            iDepth = oModel.iter_depth(oIter)
            if iDepth == 1:
                # We handle top-level items differently
                # Remove anything already assigned to this
                dSelectedData[oPhysCard].clear()
                dSelectedData[oPhysCard][None] = [iCount, iNewCount]
                aSkip.add(oAbsCard)
            else:
                if oAbsCard in aSkip:
                    # Top level card was selected, so we ignore the
                    # sub-level items
                    continue
                if sCardSet in dSelectedData[oPhysCard]:
                    # We already have this info (for selections via multiple
                    # groups, etc.)
                    continue
                dSelectedData[oPhysCard][sCardSet] = [iCount, iNewCount]
        return dSelectedData

    # pylint: disable=too-many-arguments, arguments-differ
    # elements required by function signature
    # We change the argument names to match our naming convention
    def card_drop(self, oWidget, oContext, iXPos, iYPos, oData, oInfo, oTime):
        """Handle drag-n-drop events."""
        sData = oData.get_text()
        bDragRes = True
        if not sData:
            # Don't accept invalid data
            bDragRes = False
        else:
            sSource, aCardInfo = self.split_selection_data(sData)
            bSkip = False
            if sSource == "Basic Pane:" or sSource == "Card Set:":
                self._oController.frame.drag_drop_handler(oWidget, oContext,
                                                          iXPos, iYPos, oData,
                                                          oInfo, oTime)
                return
            if not self._oModel.bEditable:
                # Don't accept cards when not editable
                bSkip = True
            elif sSource == self.sDragPrefix:
                # Can't drag to oneself
                bSkip = True
            if bSkip or not self._oController.add_paste_data(sSource,
                                                             aCardInfo):
                bDragRes = False  # paste failed
            # else paste succeeds
        oContext.finish(bDragRes, False, oTime)

    # pylint: enable=too-many-arguments

    def inc_card(self, _oCell, oPath):
        """Called to increment the count for a card."""
        # We ignore the 'invalid path' failure case, since nothing should be
        # able to remove the row out from under us.
        if self._oModel.bEditable:
            bInc, _bDec = self._oModel.get_inc_dec_flags_from_path(oPath)
            if bInc:
                oPhysCard = self._oModel.get_physical_card_from_path(oPath)
                _sCardName, _sExpansion, sCardSetName = \
                    self._oModel.get_all_names_from_path(oPath)
                self._oController.inc_card(oPhysCard, sCardSetName)

    def dec_card(self, _oCell, oPath):
        """Called to decrement the count for a card"""
        # Same assumption as inc_card about invalid path
        if self._oModel.bEditable:
            _bInc, bDec = self._oModel.get_inc_dec_flags_from_path(oPath)
            if bDec:
                oPhysCard = self._oModel.get_physical_card_from_path(oPath)
                _sCardName, _sExpansion, sCardSetName = \
                    self._oModel.get_all_names_from_path(oPath)
                self._oController.dec_card(oPhysCard, sCardSetName)

    def key_press(self, _oWidget, oEvent):
        """Change the number if 1-9 is pressed and we're editable or if + or
           - is pressed. We use the lists defined above to handle the keypad
           as well."""
        oKeyVal = oEvent.get_keyval()[1]
        if oKeyVal in NUM_KEYS:
            if self._oModel.bEditable:
                iCnt = NUM_KEYS[oKeyVal]
                dSelectedData = self._process_edit_selection(iSetNewCount=iCnt)
                self._oController.change_selected_card_count(dSelectedData)
            # if we're not editable, we still ignore this, so we avoid funny
            # search behaviour
            return True
        elif oKeyVal in PLUS_KEYS and self._oModel.bEditable:
            # Special value to indicate we change the count
            dSelectedData = self._process_edit_selection(iChg=+1)
            self._oController.change_selected_card_count(dSelectedData)
            return True
        elif oKeyVal in MINUS_KEYS and self._oModel.bEditable:
            # Special value to indicate we change the count
            dSelectedData = self._process_edit_selection(iChg=-1)
            self._oController.change_selected_card_count(dSelectedData)
            return True
        return False  # propogate event

    # functions related to tweaking widget display

    def mapped(self, _oWidget):
        """Called when the view has been mapped, so we can twiddle the
           display

           In the case when a card set is opened editable, we need to
           load after the pane is mapped, so that the colours are setup
           correctly. We also use the opportunity to ensure the menu
           is in sync."""
        if self._oModel.bEditable:
            self._set_editable(True)
        # We only ever need to call this the first time we're mapped.
        # We don't want to redo this if map is called again due to
        # panes moving, etc.
        self.disconnect(self.__iMapID)
        self.__iMapID = None
        self.reload_keep_expanded()
        # Allow other map signals to run as well (needed for drag-n-drop in
        # some Gtk versions)
        return True

    # Anything that touches the database is based off to the controller
    # We handle the editable checks here though, since the controller methods
    # will be called by other routes than the gui (such as database signals)
    # where the model must change, even if the given card set isn't editable
    # The Controller is responsible for updating the model,
    # since it defines the logic for handling expansions, etc.

    def del_selection(self):
        """try to delete all the cards in the current selection"""
        if self._oModel.bEditable:
            dSelectedData = self._process_edit_selection(iSetNewCount=0)
            self._oController.change_selected_card_count(dSelectedData)

    def do_paste(self):
        """Try and paste the current selection from the application
           clipboard"""
        if self._oModel.bEditable:
            sSelection = self._oMainWin.get_selection_text()
            sSource, aCards = self.split_selection_data(sSelection)
            if sSource != self.sDragPrefix:
                # Prevent pasting into oneself
                self._oController.add_paste_data(sSource, aCards)

    def load(self):
        """Called when the model needs to be reloaded."""
        if self.__iMapID is not None:
            # skip loading until we're mapped, to save double loads in
            # some cases
            return
        if hasattr(self._oMainWin, 'set_busy_cursor'):
            self._oMainWin.set_busy_cursor()
        self.freeze_child_notify()
        self.set_model(None)
        self._oModel.load()
        self.set_model(self._oModel)
        self.oNumCell.set_property('foreground-rgba',
                                   self._oModel.get_count_colour())
        self.thaw_child_notify()
        if hasattr(self._oMainWin, 'restore_cursor'):
            self._oMainWin.restore_cursor()

    def set_color_edit_cue(self):
        """Set a visual cue that the card set is editable."""
        if not self._oModel.oEditColour:
            self._determine_edit_colour()
        self.set_name('editable_view')

    def _determine_edit_colour(self):
        """Determine which colour to use for the editable hint"""
        # For now we go with black and red - at some point we should
        # revist checking the theme / background, but that's more
        # complicated with gtk3.
        self.oCellColor = Gdk.RGBA(0, 0, 0, 1)
        self._oModel.oEditColour = Gdk.RGBA()
        self._oModel.oEditColour.parse('red')

    def set_color_normal(self):
        """Unset the editable visual cue"""
        self.set_name('normal_view')

    def _set_editable(self, bValue):
        """Update the view and menu when the editable status changes"""
        self._oModel.bEditable = bValue
        if self._oMenu is not None:
            self._oMenu.force_editable_mode(bValue)
        if bValue:
            self.set_color_edit_cue()
            self.oIncCol.set_visible(True)
            self.oDecCol.set_visible(True)
        else:
            self.set_color_normal()
            self.oIncCol.set_visible(False)
            self.oDecCol.set_visible(False)

    def toggle_editable(self, bValue):
        """Reload the view and update status when editable status changes"""
        self._set_editable(bValue)
        self.reload_keep_expanded()

    def set_menu(self, oMenu):
        """Keep track of the menu item, so we can update it's toggled
           status."""
        self._oMenu = oMenu

    def set_parent_count_col_vis(self, bVisible):
        """Make the parent count column visible or invisible"""
        self.oParentCol.set_visible(bVisible)

    def update_name(self, sNewName):
        """Handle the renaming of a card set - set the correct new drag prefix,
           etc."""
        self.sSetName = sNewName
        self.sDragPrefix = PhysicalCardSet.sqlmeta.table + ":" + self.sSetName

    def save_iter_state(self, aIters, dStates):
        """Save the expanded state of the list of iters in aIters and their
           children."""
        dStates.setdefault('expanded', set())
        dStates.setdefault('selected', set())
        for oIter in aIters:
            oParIter = self._oModel.iter_parent(oIter)
            sParKey = self.get_iter_identifier(oParIter)
            sKey = self.get_iter_identifier(oIter)
            if self._oSelection.iter_is_selected(oIter):
                dStates['selected'].add(sKey)
            # We want to know if the current row is visible, which requires
            # that the parent is expanded.
            oPath = self._oModel.get_path(oParIter)
            if self.row_expanded(oPath):
                dStates['expanded'].add(sParKey)
            aChildIters = self._oModel.get_all_iter_children(oIter)
            self.save_iter_state(aChildIters, dStates)

    def restore_iter_state(self, aIters, dStates):
        """Restore expanded state of the iters."""
        if not dStates or 'selected' not in dStates:
            return  # Don't do anything if dStates is empty
        for oIter in aIters:
            oParIter = self._oModel.iter_parent(oIter)
            sParKey = self.get_iter_identifier(oParIter)
            sKey = self.get_iter_identifier(oIter)
            if sParKey in dStates['expanded']:
                self.expand_to_path(self._oModel.get_path(oParIter))
            aChildIters = self._oModel.get_all_iter_children(oIter)
            self.restore_iter_state(aChildIters, dStates)
            # selection needs to happen after all the expansions
            if sKey in dStates['selected']:
                self._oSelection.select_iter(oIter)
