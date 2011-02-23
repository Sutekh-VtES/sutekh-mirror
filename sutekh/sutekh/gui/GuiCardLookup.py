# GuiCardLookup.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Lookup AbstractCards for a list of card names, presenting the user with a
   GUI to pick unknown cards from.  """

import re
import gtk
import pango
import gobject
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCard, IExpansion, \
        Expansion, IPhysicalCard, IAbstractCard
from sutekh.core.CardLookup import AbstractCardLookup, PhysicalCardLookup, \
        ExpansionLookup, LookupFailed, best_guess_filter
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.CellRendererSutekhButton import CellRendererSutekhButton
from sutekh.gui.PhysicalCardView import PhysicalCardView
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.FilterModelPanes import add_accel_to_button


NO_CARD = "  No Card"


def _sort_replacement(oModel, oIter1, oIter2):
    """Sort replacement, honouring spaces"""
    oVal1 = oModel.get_value(oIter1, 2)
    oVal2 = oModel.get_value(oIter2, 2)
    return cmp(oVal1, oVal2)


class DummyController(object):
    """Dummy controller class, so we can use the card views directly"""
    def __init__(self, sFilterType):
        self.sFilterType = sFilterType

    filtertype = property(fget=lambda self: self.sFilterType)

    def set_card_text(self, _oCard):
        """Ignore card text updates."""
        pass


class ACLLookupView(PhysicalCardView):
    """Specialised version for the Card Lookup."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods.

    def __init__(self, oDialogWindow, oConfig):
        oController = DummyController('PhysicalCard')
        super(ACLLookupView, self).__init__(oController, oDialogWindow,
                oConfig)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)
        self._oModel.bExpansions = False

    def get_selected_card(self):
        """Return the selected card with a dummy expansion of ''."""
        sNewName = NO_CARD
        oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            sNewName, _sExpansion, _iCount, _iDepth = \
                oModel.get_all_from_path(oPath)
        return sNewName, ''

    def cleanup(self):
        """Call model cleanup to remove listeners, etc."""
        self._oModel.cleanup()


class PCLLookupView(PhysicalCardView):
    """Also show current allocation of cards in the physical card view."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods.

    def __init__(self, oDialogWindow, oConfig):
        oController = DummyController('PhysicalCard')
        super(PCLLookupView, self).__init__(oController, oDialogWindow,
                oConfig)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def get_selected_card(self):
        """Return the selected card and expansion."""
        sNewName = NO_CARD
        sExpansion = '  Unpecified Expansion'
        oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            sNewName, sExpansion, _iCount, _iDepth = \
                oModel.get_all_from_path(oPath)
        if sExpansion is None:
            sExpansion = ''
        return sNewName, sExpansion

    def cleanup(self):
        """Call model cleanup to remove listeners, etc."""
        self._oModel.cleanup()


class ReplacementTreeView(gtk.TreeView):
    """A TreeView which tracks the current set of replacement cards."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods.

    def __init__(self, oCardListView, oFilterToggleButton):
        """Construct a gtk.TreeView object showing the current
           card replacements.

           For abstract cards, the card names are stored as is.
           For physical cards, the card names have " [<expansion>]"
           appended.
           """
        # ListStore: count, missing card, replacement

        self._dToolTips = {}

        oModel = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING,
                               gobject.TYPE_STRING, gobject.TYPE_INT)

        super(ReplacementTreeView, self).__init__(oModel)
        self.oCardListView = oCardListView
        self.oModel = oModel
        self.oFilterToggleButton = oFilterToggleButton
        self.set_enable_search(False)  # Not much point searching this tree

        self._create_text_column('Missing Card', 1)
        self._create_text_column('Replace Card', 2)

        self._create_button_column(gtk.STOCK_OK, 'Set',
                'Use the selected card',
                self._set_to_selection)  # use selected card
        self._create_button_column(gtk.STOCK_REMOVE, 'Ignore',
                'Ignore the current card',
                self._set_ignore)  # ignore current card
        self._create_button_column(gtk.STOCK_FIND, 'Filter',
                'Filter on best guess',
                self._set_filter)  # filter out best guesses

        self.set_property('has-tooltip', True)
        self.connect('query-tooltip', self._show_tooltip)

        oModel.set_sort_func(2, _sort_replacement)
        oModel.set_sort_column_id(2, 0)

    # utility methods to simplify column creation
    def _create_button_column(self, oIcon, sLabel, sToolTip, fClicked):
        """Create a column with a button, usin oIcon and the function
           fClicked."""
        oCell = CellRendererSutekhButton(bShowIcon=True)
        oCell.load_icon(oIcon, self)
        oLabel = gtk.Label(sLabel)
        oColumn = gtk.TreeViewColumn("", oCell)
        oColumn.set_widget(oLabel)
        oColumn.set_fixed_width(22)
        oColumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn)
        oCell.connect('clicked', fClicked)
        self._dToolTips[oColumn] = sToolTip

    # pylint: disable-msg=R0913
    # Need this many arguments from function signature
    # Show tooltips for the column buttons
    def _show_tooltip(self, _oWidget, _iXPos, _iYPos, _bKeyboard, oToolTip):
        """Test if a tooltip should be shown"""
        sToolTip = None
        # The positions passed in aren't relative to the right window for
        # get_path, so we query position directly
        iXPos, iYPos, _oIgnore = self.get_bin_window().get_pointer()
        tRes = self.get_path_at_pos(iXPos, iYPos)
        if tRes:
            # path returned may be none
            sToolTip = self._dToolTips.get(tRes[1], None)
        if sToolTip:
            oToolTip.set_markup(sToolTip)
            return True
        return False

    # pylint: enable-msg=R0913

    def _create_text_column(self, sLabel, iColumn):
        """Create a text column, using iColumn from the model"""
        oCell = gtk.CellRendererText()
        oCell.set_property('style', pango.STYLE_ITALIC)
        oColumn = gtk.TreeViewColumn(sLabel, oCell, text=iColumn, weight=3)
        oColumn.set_expand(True)
        oColumn.set_sort_column_id(iColumn)
        self.append_column(oColumn)

    def _fix_selection(self, sName):
        """Fix the cursor position to accomodate the result of the rows
           being sorted"""
        oIter = self.oModel.get_iter_first()
        while oIter:
            sCurName = self.oModel.get_value(oIter, 1)
            if sName == sCurName:
                self.set_cursor(self.oModel.get_path(oIter))
                return
            oIter = self.oModel.iter_next(oIter)

    def _set_to_selection(self, _oCell, oPath):
        """Set the replacement card to the selected entry"""

        # We handle PhysicalCards on a like-for-like matching case.
        # For cases where the user selects an expansion with too few
        # cards, but where there are enough physical cards, we do the
        # best we can

        oIter = self.oModel.get_iter(oPath)
        sName = self.oModel.get_value(oIter, 1)

        sNewName, sExpansion = self.oCardListView.get_selected_card()
        if sNewName == NO_CARD:
            do_complaint_error("Please select a card")
            return

        if sExpansion != '':
            sReplaceWith = sNewName + " [%s]" % (sExpansion,)
        else:
            sReplaceWith = sNewName

        self.oModel.set_value(oIter, 2, sReplaceWith)
        self.oModel.set_value(oIter, 3, pango.WEIGHT_NORMAL)
        gobject.timeout_add(1, self._fix_selection, sName)

    def _set_ignore(self, _oCell, oPath):
        """Mark the card as not having a replacement."""
        oIter = self.oModel.get_iter(oPath)
        sName = self.oModel.get_value(oIter, 1)
        self.oModel.set_value(oIter, 2, NO_CARD)
        self.oModel.set_value(oIter, 3, pango.WEIGHT_BOLD)
        gobject.timeout_add(1, self._fix_selection, sName)

    def _set_filter(self, _oCell, oPath):
        """Set the card list filter to the best guess filter for this card."""
        oIter = self.oModel.get_iter(oPath)
        sFullName = self.oModel.get_value(oIter, 1)
        sName, _sExp = self.parse_card_name(sFullName)

        oFilter = best_guess_filter(sName)
        self.oCardListView.get_model().selectfilter = oFilter

        if not self.oFilterToggleButton.get_active():
            self.oFilterToggleButton.set_active(True)
        else:
            self.oCardListView.load()

    def run_filter_dialog(self, _oButton):
        """Display the filter dialog and apply results."""
        self.oCardListView.get_filter(None, "CardName in $var0")
        self.oFilterToggleButton.set_active(
            self.oCardListView.get_model().applyfilter)

    def toggle_apply_filter(self, _oButton):
        """Toggle whether the filter is applied."""
        self.oCardListView.get_model().applyfilter = \
            self.oFilterToggleButton.get_active()
        self.oCardListView.load()

    def toggle_show_illegal(self, oButton):
        """Toggle whether the filter is applied."""
        self.oCardListView.get_model().hideillegal = not oButton.get_active()
        self.oCardListView.load()

    def show_search(self, _oButton):
        """Popup the search dialog"""
        self.oCardListView.emit('start-interactive-search')

    NAME_RE = re.compile(r"^(?P<name>.*?)( \[(?P<exp>[^]]+)\])?$")

    @classmethod
    def parse_card_name(cls, sName):
        """Parser the card name and expansion out of the string."""
        oMatch = cls.NAME_RE.match(sName)
        assert oMatch is not None
        return oMatch.group('name'), oMatch.group('exp')


class GuiLookup(AbstractCardLookup, PhysicalCardLookup, ExpansionLookup):
    """Lookup AbstractCards. Use the user as the AI if a simple lookup fails.
       """

    def __init__(self, oConfig):
        super(GuiLookup, self).__init__()
        self._oConfig = oConfig

    def lookup(self, aNames, sInfo):
        """Lookup missing abstract cards.

           Provides an implementation for AbstractCardLookup.
           """
        # pylint: disable-msg=R0912
        # Lots of different cases to consider, to several branches
        dCards = {}
        dUnknownCards = {}

        aNewNames = []  # If we need to recode the name

        for sName in aNames:
            if not sName:
                # None here is an explicit ignore from the lookup cache
                dCards[sName] = None
            else:
                # Check we can encode the name properly
                try:
                    _sTemp = sName.encode('utf8')
                except UnicodeDecodeError:
                    # Wrong assumptions somewhere - let the user sort it
                    # out
                    # We bounce through unicode to ensure
                    # we have something usable everywhere
                    # FIXME: Fix best guess filter and card lookup
                    # code so we don't need to encode back to ascii
                    sName = sName.decode('ascii', 'replace').encode('ascii',
                            'replace')

                try:
                    # Use IAbstractCard to cover more variations
                    oAbs = IAbstractCard(sName.encode('utf8'))
                    dCards[sName] = oAbs
                except SQLObjectNotFound:
                    dUnknownCards[sName] = None

                aNewNames.append(sName)

        if dUnknownCards:
            if not self._handle_unknown_abstract_cards(dUnknownCards, sInfo):
                raise LookupFailed("Lookup of missing cards aborted by the"
                                   " user.")

        for sName, sNewName in dUnknownCards.items():
            if sNewName is None:
                continue
            try:
                # pylint: disable-msg=E1101
                # SQLObject methods confuse pylint
                oAbs = AbstractCard.byCanonicalName(
                        sNewName.encode('utf8').lower())
                # pylint: enable-msg=E1101
                dUnknownCards[sName] = oAbs
            except SQLObjectNotFound:
                raise RuntimeError("Unexpectedly encountered missing"
                        " abstract card '%s'." % sNewName)

        def new_card(sName):
            """emulate python 2.5's a = x if C else y"""
            if sName in dCards:
                return dCards[sName]
            else:
                return dUnknownCards[sName]

        return [new_card(sName) for sName in aNewNames]

    def physical_lookup(self, dCardExpansions, dNameCards, dNameExps, sInfo):
        """Lookup missing physical cards.

           Provides an implementation for PhysicalCardLookup.
           """
        aCards = []
        dUnknownCards = {}

        for sName in dCardExpansions:
            oAbs = dNameCards[sName]
            if oAbs is None:
                continue
            for sExpansionName in dCardExpansions[sName]:
                iCnt = dCardExpansions[sName][sExpansionName]
                oExpansion = dNameExps[sExpansionName]
                if iCnt > 0:
                    try:
                        aCards.extend(
                                [IPhysicalCard((oAbs, oExpansion))] * iCnt)
                    except SQLObjectNotFound:
                        dUnknownCards[(oAbs.name, sExpansionName)] = iCnt

        if dUnknownCards:
            # We need to lookup cards in the physical card view
            if not self._handle_unknown_physical_cards(dUnknownCards,
                                                       aCards, sInfo):
                raise LookupFailed("Lookup of missing cards aborted by the" \
                                   " user.")

        return aCards

    def expansion_lookup(self, aExpansionNames, sInfo):
        """Lookup missing expansions.

           Provides an implementation for ExpansionLookup.
           """
        dExps = {}
        dUnknownExps = {}

        for sExp in aExpansionNames:
            if not sExp:
                dExps[sExp] = None
            else:
                try:
                    oExp = IExpansion(sExp)
                    dExps[sExp] = oExp
                except SQLObjectNotFound:
                    dUnknownExps[sExp] = None

        if dUnknownExps:
            if not self._handle_unknown_expansions(dUnknownExps, sInfo):
                raise LookupFailed("Lookup of missing expansions aborted by" \
                                   " the user.")

        for sName, sNewName in dUnknownExps.items():
            if sNewName is None:
                continue
            try:
                oExp = IExpansion(sNewName)
                dUnknownExps[sName] = oExp
            except SQLObjectNotFound:
                raise RuntimeError("Unexpectedly encountered" \
                                   " missing expansion '%s'." % sNewName)

        def new_exp(sName):
            """emulate python 2.5's a = x if C else y"""
            if sName in dExps:
                return dExps[sName]
            else:
                return dUnknownExps[sName]

        return [new_exp(sName) for sName in aExpansionNames]

    def _handle_unknown_physical_cards(self, dUnknownCards, aPhysCards, sInfo):
        """Handle unknwon physical cards

           We allow the user to select the correct replacements from the
           Physical Card List
           """
        # pylint: disable-msg=R0914
        # we use lots of variables for clarity

        oUnknownDialog, oHBox = self._create_dialog(sInfo,
                "The following card and expansion combinations could not "
                "be found:")

        # pylint: disable-msg=E1101
        # vbox confuses pylint

        oPhysCardView = PCLLookupView(oUnknownDialog, self._oConfig)
        oReplacementView = self._fill_dialog(oHBox, oPhysCardView)
        oModel = oReplacementView.get_model()

        # Populate the model with the card names and best guesses
        for (sName, sExpName), iCnt in dUnknownCards.items():
            sBestGuess = NO_CARD
            sFullName = "%s [%s]" % (sName, sExpName)

            oIter = oModel.append(None)
            oModel.set(oIter, 0, iCnt, 1, sFullName, 2, sBestGuess,
                    3, pango.WEIGHT_BOLD)

        oUnknownDialog.vbox.show_all()
        oPhysCardView.load()

        iResponse = oUnknownDialog.run()
        oUnknownDialog.destroy()

        oPhysCardView.cleanup()

        if iResponse == gtk.RESPONSE_OK:
            # For cards marked as replaced, add them to the list of
            # Physical Cards
            oIter = oModel.get_iter_root()
            while not oIter is None:
                sFullName, sNewFullName = oModel.get(oIter, 1, 2)
                sName, sExpName = oReplacementView.parse_card_name(sFullName)

                sNewName, sNewExpName = \
                    oReplacementView.parse_card_name(sNewFullName)

                if sNewName != NO_CARD:
                    iCnt = dUnknownCards[(sName, sExpName)]

                    # Find First physical card that matches this name
                    # that's not in aPhysCards
                    oPhys = self._lookup_new_phys_card(sNewName, sNewExpName)
                    aPhysCards.extend([oPhys] * iCnt)

                oIter = oModel.iter_next(oIter)
            return True
        else:
            return False

    # pylint: disable-msg=R0201
    # These are methods for convenience
    def _create_dialog(self, sInfo, sMsg):
        """Create the dialog to present to the user.

           This is common to the abstract + physical card cases"""
        oUnknownDialog = SutekhDialog( \
                "Unknown cards found importing %s" % sInfo, None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        # pylint: disable-msg=E1101
        # vbox confuses pylint
        sLabelText = "While importing %s\n%s\n" \
          "Choose how to handle these cards?\n" % (sInfo, sMsg)

        oMesgLabel1 = gtk.Label(sLabelText)
        oUnknownDialog.vbox.pack_start(oMesgLabel1, False, False)

        oHBox = gtk.HBox()
        oUnknownDialog.vbox.pack_start(oHBox, True, True)

        oMesgLabel2 = gtk.Label("OK creates the card set, Cancel "
                "aborts the creation of the card set")
        oUnknownDialog.vbox.pack_start(oMesgLabel2)

        return oUnknownDialog, oHBox

    def _fill_dialog(self, oHBox, oView):
        """Handle the view setup and default buttons for the lookup
           dialog."""
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oViewWin = AutoScrolledWindow(oView)
        oViewWin.set_size_request(200, 600)
        oHBox.pack_start(oViewWin, True, True)

        oVBox = gtk.VBox()
        oHBox.pack_start(oVBox)

        # Add same shortcuts as the pane menus
        oAccelGroup = gtk.AccelGroup()
        # oHBox is a child of a vbox which is a child of the dialog
        oHBox.get_parent().get_parent().add_accel_group(oAccelGroup)

        oFilterDialogButton = gtk.Button('Specify Filter')
        oFilterApplyButton = gtk.CheckButton("Apply Filter")
        oLegalButton = gtk.CheckButton("Show illegal cards")
        oSearchButton = gtk.Button("Search List")
        add_accel_to_button(oFilterDialogButton, "<Ctrl>s", oAccelGroup,
                'Open the Filter Editing Dialog.\nShortcut :<b>Ctrl-S</b>')
        add_accel_to_button(oFilterApplyButton, "<Ctrl>t", oAccelGroup,
                'Toggle the applied state of the filter.\n'
                'Shortcut : <b>Ctrl-T</b>')
        add_accel_to_button(oLegalButton, "<Ctrl>l", oAccelGroup,
                'Toggle the display of cards not legal for tournament play.\n'
                'Shortcut : <b>Ctrl-L</b>')
        add_accel_to_button(oSearchButton, "<Ctrl>f", oAccelGroup,
                'Open the search dailog for the cards.\n'
                'Shortcut : <b>Ctrl-F</b>')

        oReplacementView = ReplacementTreeView(oView,
            oFilterApplyButton)

        oReplacementWin = AutoScrolledWindow(oReplacementView)
        oReplacementWin.set_size_request(600, 600)
        oVBox.pack_start(oReplacementWin, True, True)

        oFilterButtons = gtk.HBox(spacing=2)
        oVBox.pack_start(gtk.HSeparator())
        oVBox.pack_start(oFilterButtons)

        oFilterButtons.pack_start(oFilterDialogButton)
        oFilterButtons.pack_start(oFilterApplyButton)
        oFilterButtons.pack_start(oLegalButton)
        oFilterButtons.pack_start(oSearchButton)

        oFilterDialogButton.connect("clicked",
            oReplacementView.run_filter_dialog)
        oFilterApplyButton.connect("toggled",
            oReplacementView.toggle_apply_filter)
        oLegalButton.connect("toggled",
            oReplacementView.toggle_show_illegal)
        oSearchButton.connect("clicked",
            oReplacementView.show_search)

        return oReplacementView

    def _lookup_new_phys_card(self, sNewName, sNewExpName):
        """Lookup the physical card, given the correct name + expansion
           name."""
        # pylint: disable-msg=E1101
        # SQLObject + pyprotocols confuse pylint
        if sNewExpName is not None:
            try:
                iExpID = IExpansion(sNewExpName).id
            except SQLObjectNotFound:
                iExpID = None
            except SQLObjectNotFound:
                iExpID = None
        else:
            iExpID = None

        oAbs = AbstractCard.byCanonicalName(sNewName.encode('utf8').lower())
        oPhys = PhysicalCard.selectBy(abstractCardID=oAbs.id,
                    expansionID=iExpID).getOne()
        return oPhys

    # pylint: enable-msg=R0201

    def _handle_unknown_abstract_cards(self, dUnknownCards, sInfo):
        """Handle the list of unknown abstract cards.

           We allow the user to select the correct replacements from the
           Abstract Card List.
           """
        # pylint: disable-msg=R0914
        # we use lots of variables for clarity
        oUnknownDialog, oHBox = self._create_dialog(sInfo,
                "The following card names could not be found")
        # pylint: disable-msg=E1101
        # vbox confuses pylint

        oAbsCardView = ACLLookupView(oUnknownDialog, self._oConfig)
        oReplacementView = self._fill_dialog(oHBox, oAbsCardView)
        oModel = oReplacementView.get_model()

        # Populate the model with the card names and best guesses
        for sName in dUnknownCards:
            oBestGuessFilter = best_guess_filter(sName)
            aCards = list(oBestGuessFilter.select(AbstractCard))
            if len(aCards) == 1:
                sBestGuess = aCards[0].name
                iWeight = pango.WEIGHT_NORMAL
            else:
                sBestGuess = NO_CARD
                iWeight = pango.WEIGHT_BOLD

            oIter = oModel.append(None)
            # second 1 is the dummy card count
            oModel.set(oIter, 0, 1, 1, sName, 2, sBestGuess, 3, iWeight)

        oUnknownDialog.vbox.show_all()
        oAbsCardView.load()

        iResponse = oUnknownDialog.run()
        oUnknownDialog.destroy()

        oAbsCardView.cleanup()

        if iResponse == gtk.RESPONSE_OK:
            # For cards marked as replaced, add them to the Holder
            oIter = oModel.get_iter_root()
            while not oIter is None:
                sName, sNewName = oModel.get(oIter, 1, 2)
                if sNewName != NO_CARD:
                    dUnknownCards[sName] = sNewName
                oIter = oModel.iter_next(oIter)
            return True
        else:
            return False

    @staticmethod
    def _handle_unknown_expansions(dUnknownExps, sInfo):
        """Handle the list of unknown expansions.

           We allow the user to select the correct replacements from the
           expansions listed in the database.
           """
        oUnknownDialog = SutekhDialog(
            "Unknown expansions found importing %s" % sInfo, None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK,
             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        aKnownExpansions = list(Expansion.select())
        aKnownExpansions.sort(key=lambda x: x.name)

        oMesgLabel1 = gtk.Label("While importing %s\n"
                "The following expansions could not be found:\n"
                "Choose how to handle these expansions?\n" % (sInfo))
        oMesgLabel2 = gtk.Label("OK continues the card set creation process, "
                "Cancel aborts the creation of the card set")

        # pylint: disable-msg=E1101
        # vbox confuses pylint

        oUnknownDialog.vbox.pack_start(oMesgLabel1, False, False)

        oButtonBox = gtk.VBox()

        # Fill in the Expansions and options
        dReplacement = {}
        for sName in dUnknownExps:
            oBox = gtk.HBox()
            oLabel = gtk.Label("%s is Unknown: Replace with " % sName)
            oBox.pack_start(oLabel)

            oSelector = gtk.combo_box_new_text()
            oSelector.append_text("No Expansion")
            for oExp in aKnownExpansions:
                oSelector.append_text(oExp.name)

            dReplacement[sName] = oSelector

            oBox.pack_start(dReplacement[sName])
            oButtonBox.pack_start(oBox)

        oUnknownDialog.vbox.pack_start(oButtonBox, True, True)

        oUnknownDialog.vbox.pack_start(oMesgLabel2)
        oUnknownDialog.vbox.show_all()

        iResponse = oUnknownDialog.run()

        oUnknownDialog.destroy()

        if iResponse == gtk.RESPONSE_OK:
            # For cards marked as replaced, add them to the Holder
            for sName in dUnknownExps:
                sNewName = dReplacement[sName].get_active_text()
                if sNewName != "No Expansion":
                    dUnknownExps[sName] = sNewName
            return True
        else:
            return False
