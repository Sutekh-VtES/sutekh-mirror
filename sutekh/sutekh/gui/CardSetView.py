# CardSetView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""View object for card sets."""

import gtk
from sutekh.gui.CellRendererSutekhButton import CellRendererSutekhButton
from sutekh.gui.CellRendererIcons import CellRendererIcons
from sutekh.gui.CardListView import CardListView
from sutekh.gui.CardSetListModel import CardSetCardListModel
from sutekh.core.SutekhObjects import PhysicalCardSet

_dNumKeys = {
        gtk.gdk.keyval_from_name('1') : 1,
        gtk.gdk.keyval_from_name('KP_1') : 1,
        gtk.gdk.keyval_from_name('2') : 2,
        gtk.gdk.keyval_from_name('KP_2') : 2,
        gtk.gdk.keyval_from_name('3') : 3,
        gtk.gdk.keyval_from_name('KP_3') : 3,
        gtk.gdk.keyval_from_name('4') : 4,
        gtk.gdk.keyval_from_name('KP_4') : 4,
        gtk.gdk.keyval_from_name('5') : 5,
        gtk.gdk.keyval_from_name('KP_5') : 5,
        gtk.gdk.keyval_from_name('6') : 6,
        gtk.gdk.keyval_from_name('KP_6') : 6,
        gtk.gdk.keyval_from_name('7') : 7,
        gtk.gdk.keyval_from_name('KP_7') : 7,
        gtk.gdk.keyval_from_name('8') : 8,
        gtk.gdk.keyval_from_name('KP_8') : 8,
        gtk.gdk.keyval_from_name('9') : 9,
        gtk.gdk.keyval_from_name('KP_9') : 9
        }

_aPlusKeys = [
        gtk.gdk.keyval_from_name('plus'),
        gtk.gdk.keyval_from_name('KP_Add')
        ]
_aMinusKeys = [
        gtk.gdk.keyval_from_name('minus'),
        gtk.gdk.keyval_from_name('KP_Subtract')
        ]


class CardSetView(CardListView):
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - We need to track a fair amount of state, so many attributes
    """Subclass of CardListView specific to the Card Sets

       Adds editing support, and other specific to the card sets.
       The database interactions are handled by the controller,
       this just manages the GUI side of things, passing info to
       the controller when needed.
       """

    # Initialise key ranges for key tests
    # pylint: disable-msg=R0915
    # We need a lot of setup here, so this is long
    def __init__(self, oMainWindow, oController, sName):
        oModel = CardSetCardListModel(sName)
        # The only path here is via the main window, so config_file exists
        super(CardSetView, self).__init__(oController, oMainWindow,
                oModel, oMainWindow.config_file)

        self.sSetName = sName
        self.sDragPrefix = PhysicalCardSet.sqlmeta.table + ":" + self.sSetName

        # Setup columns for default view
        self.oNumCell = gtk.CellRendererText()
        self.oNameCell = CellRendererIcons(5)

        oColumn1 = gtk.TreeViewColumn("#", self.oNumCell, markup=1)
        oColumn1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn1.set_fixed_width(60)
        oColumn1.set_sort_column_id(1)
        oColumn1.set_resizable(True)
        self.append_column(oColumn1)

        oParentCell = gtk.CellRendererText()
        self.oParentCol = gtk.TreeViewColumn("Par #", oParentCell,
                markup=2)
        self.oParentCol.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.oParentCol.set_fixed_width(60)
        self.oParentCol.set_sort_column_id(2)
        self.append_column(self.oParentCol)
        self.oParentCol.set_visible(False)
        self.oParentCol.set_resizable(True)

        oColumn2 = gtk.TreeViewColumn("Cards", self.oNameCell, text=0,
                textlist=5, icons=6)
        oColumn2.set_min_width(100)
        oColumn2.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn2.set_sort_column_id(0)
        oColumn2.set_expand(True)
        oColumn2.set_resizable(True)
        self.append_column(oColumn2)
        self.set_expander_column(oColumn2)

        # Inc/Dec cells
        oCell3 = CellRendererSutekhButton()
        oCell3.load_icon(gtk.STOCK_ADD, self)
        oCell4 = CellRendererSutekhButton()
        oCell4.load_icon(gtk.STOCK_REMOVE, self)

        oColumn3 = gtk.TreeViewColumn("", oCell3, showicon=3)
        oColumn3.set_fixed_width(22)
        oColumn3.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn3.set_resizable(False)
        self.append_column(oColumn3)

        oColumn4 = gtk.TreeViewColumn("", oCell4, showicon=4)
        oColumn4.set_fixed_width(22)
        oColumn4.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn4.set_resizable(False)
        self.append_column(oColumn4)

        oCell3.connect('clicked', self.inc_card)
        oCell4.connect('clicked', self.dec_card)

        self.__iMapID = self.connect('map-event', self.mapped)
        self.connect('key-press-event', self.key_press)

        self._oMenu = None

        self.oCellColor = None

        self.set_fixed_height_mode(True)
        # Set sort functions so numerical sorts work as expected
        # Card numbers
        self._oModel.set_sort_func(1, self._oModel.num_col_sort_func, 1)
        # Parent counts
        self._oModel.set_sort_func(2, self._oModel.num_col_sort_func, 2)

    # pylint: enable-msg=R0915

    def process_selection(self):
        """Create a dictionary from the selection.

           Entries are of the form sCardName : {sExpansion1 : iCount1, ... }
           for use in drag-'n drop and elsewhere.
           """
        oModel, oPathList = self._oSelection.get_selected_rows()
        dSelectedData = {}
        for oPath in oPathList:
            sCardName, sExpansion, iCount, iDepth = \
                    oModel.get_drag_info_from_path(oPath)
            if not sCardName:
                # Not a card in this card set, so we skip
                continue
            dSelectedData.setdefault(sCardName, {})
            if iDepth == 1:
                # this is treated as selecting all the children in this
                # card set
                # Remove anything already assigned to this
                dSelectedData[sCardName].clear()
                for sExpName, iCnt in \
                        oModel.get_drag_child_info(oPath).iteritems():
                    dSelectedData[sCardName][sExpName] = iCnt
            elif not sExpansion:
                # If the expansion is none, see if there are interesting
                # children
                # This may well not to the right thing with complex
                # selections, but it avoids issues when the same card is
                # selected multiple times because it's in different groupings
                dChildInfo = oModel.get_drag_child_info(oPath)
                if dChildInfo:
                    for sExpName, iCnt in dChildInfo.iteritems():
                        dSelectedData[sCardName][sExpName] = iCnt
                else:
                    if sExpansion in dSelectedData[sCardName]:
                        # We already have this info
                        continue
                    dSelectedData[sCardName][sExpansion] = iCount
            else:
                if sExpansion in dSelectedData[sCardName]:
                    # We already have this info
                    continue
                dSelectedData[sCardName][sExpansion] = iCount
        return dSelectedData

    def process_edit_selection(self):
        """Create a dictionary from the selection, suitable for the quick
           key based edits.

           Entries are of the form
               sCardName : { (sExpansion1, sCardSet) : iCount1, ... }
           In addition to adding information about card sets, this
           differs from process_selection in the way card level items
           are handled. Here, these are treated as selecting the expansion
           None, and ignoring other expansions.
           """
        oModel, oPathList = self._oSelection.get_selected_rows()
        dSelectedData = {}
        for oPath in oPathList:
            sCardSet = None
            sCardName, sExpansion, iCount, iDepth = \
                    oModel.get_drag_info_from_path(oPath)
            if not sCardName:
                sCardName, sExpansion, sCardSet = \
                        oModel.get_all_names_from_path(oPath)
            dSelectedData.setdefault(sCardName, {})
            if iDepth == 1:
                # this is treated as selecting all the entries of this card
                # in this card set
                # Remove anything already assigned to this
                dSelectedData[sCardName].clear()
                dSelectedData[sCardName][('All', None)] = iCount
            else:
                if (sExpansion, sCardSet) in dSelectedData[sCardName] or \
                        ('All', None) in dSelectedData[sCardName]:
                    # We already have this info
                    continue
                dSelectedData[sCardName][(sExpansion, sCardSet)] = iCount
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
            bSkip = False
            if sSource == "Sutekh Pane:" or sSource == "Card Set:":
                self._oController.frame.drag_drop_handler(oWidget, oContext,
                        iXPos, iYPos, oData, oInfo, oTime)
            elif not self._oModel.bEditable:
                # Don't accept cards when not editable
                bSkip = True
            elif sSource == self.sDragPrefix:
                # Can't drag to oneself
                bSkip = True
            if not bSkip and self._oController.add_paste_data(sSource,
                    aCardInfo):
                oContext.finish(True, False, oTime) # paste successful
            else:
                oContext.finish(False, False, oTime) # not successful

    # pylint: enable-msg=R0913

    # pylint: disable-msg=W0613
    # arguments as required by the function signature
    def inc_card(self, oCell, oPath):
        """Called to increment the count for a card."""
        if self._oModel.bEditable:
            # pylint: disable-msg=W0612
            # only interested in bInc
            bInc, bDec = self._oModel.get_inc_dec_flags_from_path(oPath)
            if bInc:
                sCardName, sExpansion, sCardSetName = \
                        self._oModel.get_all_names_from_path(oPath)
                self._oController.inc_card(sCardName, sExpansion, sCardSetName)

    def dec_card(self, oCell, oPath):
        """Called to decrement the count for a card"""
        if self._oModel.bEditable:
            # pylint: disable-msg=W0612
            # only interested in bDec
            bInc, bDec = self._oModel.get_inc_dec_flags_from_path(oPath)
            if bDec:
                sCardName, sExpansion, sCardSetName = \
                        self._oModel.get_all_names_from_path(oPath)
                self._oController.dec_card(sCardName, sExpansion, sCardSetName)

    def key_press(self, oWidget, oEvent):
        """Change the number if 1-9 is pressed and we're editable or if + or
           - is pressed. We use the lists defined above to handle the keypad
           as well."""
        if oEvent.keyval in _dNumKeys:
            if self._oModel.bEditable:
                iCnt = _dNumKeys[oEvent.keyval]
                dSelectedData = self.process_edit_selection()
                self._oController.set_selected_card_count(dSelectedData, iCnt)
            # if we're not editable, we still ignore this, so we avoid funny
            # search behaviour
            return True
        elif oEvent.keyval in _aPlusKeys and self._oModel.bEditable:
            dSelectedData = self.process_edit_selection()
            self._oController.alter_selected_card_count(dSelectedData, 1)
            return True
        elif oEvent.keyval in _aMinusKeys and self._oModel.bEditable:
            dSelectedData = self.process_edit_selection()
            self._oController.alter_selected_card_count(dSelectedData, -1)
            return True
        return False # propogate event

    # functions related to tweaking widget display

    def mapped(self, oWidget, oEvent):
        """Called when the view has been mapped, so we can twiddle the
           display"""
        # see if we need to be editable
        self.check_editable()
        if self._oModel.bEditable:
            # Ensure hint colour is set correctly
            self.reload_keep_expanded()
        # We only ever need to call this the first time we're mapped.
        # We don't want to redo this if map is called again due to
        # panes moving, etc.
        self.disconnect(self.__iMapID)

    # pylint: enable-msg=W0613

    # Anything that touches the database is based off to the controller
    # We handle the editable checks here though, since the controller methods
    # will be called by other routes than the gui (such as database signals)
    # where the model must change, even if the given card set isn't editable
    # The Controller is responsible for updating the model,
    # since it defines the logic for handling expansions, etc.

    def del_selection(self):
        """try to delete all the cards in the current selection"""
        if self._oModel.bEditable:
            dSelectedData = self.process_selection()
            self._oController.del_selected_cards(dSelectedData)

    def do_paste(self):
        """Try and paste the current selection from the appliction clipboard"""
        if self._oModel.bEditable:
            sSelection = self._oMainWin.get_selection_text()
            sSource, aCards = self.split_selection_data(sSelection)
            if sSource != self.sDragPrefix:
                # Prevent pasting into oneself
                self._oController.add_paste_data(sSource, aCards)

    def load(self):
        """Called when the model needs to be reloaded."""
        if hasattr(self._oMainWin, 'set_busy_cursor'):
            self._oMainWin.set_busy_cursor()
        if self._oModel.get_card_iterator(None).count() == 0:
            self._oModel.bEditable = True
            # We do this before loading, so edit icons are correct
        self.freeze_child_notify()
        self.set_model(None)
        self._oModel.load()
        self.check_editable()
        self.set_model(self._oModel)
        self.thaw_child_notify()
        if hasattr(self._oMainWin, 'restore_cursor'):
            self._oMainWin.restore_cursor()

    def check_editable(self):
        """Set the card list to be editable if it's empty"""
        if self.get_parent() and \
                self._oModel.get_card_iterator(None).count() == 0:
            # This isn't true when creating the view
            self._set_editable(True)

    def set_color_edit_cue(self):
        """Set a visual cue that the card set is editable."""
        if not self._oModel.sEditColour:
            self._determine_edit_colour()
        self.set_name('editable_view')

    def _determine_edit_colour(self):
        """Determine which colour to use for the editable hint"""
        def _compare_colors(oColor1, oColor2):
            """Compare the RGB values for 2 gtk.gdk.Colors. Return True if
               they're the same, false otherwise."""
            return oColor1.to_string() == oColor2.to_string()

        oCurStyle = self.rc_get_style()
        # Styles don't seem to be applied to TreeView text, so we default
        # to black text for non-editable, and work out editable from the
        # style
        self.oCellColor = gtk.gdk.color_parse('black')
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
            # FIXME: rc_parse_string doesn't play nicely with
            # theme changes, which cause a rcfile reparse.
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
        if not _compare_colors(oEditColor, self.oCellColor) or \
                not _compare_colors(oEditBackColor, oCurBackColor):
            # Visiually distinct, so honour user's choice
            self._oModel.sEditColour = oEditColor.to_string()
        else:
            # If the theme change isn't visually distinct here, we go
            # with red  as the default - this is safe,
            # since CellRenderers aren't
            # themed, so the default color will not be red
            # (famous last words)
            # If the default background color is red, too bad
            self._oModel.sEditColour = 'red'

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
        else:
            self.set_color_normal()

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
