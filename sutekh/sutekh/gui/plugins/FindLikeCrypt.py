# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Finds crypt cards 'like' the selected card"""

from gi.repository import GObject, Gtk, Pango

from sutekh.base.core.BaseTables import (PhysicalCardSet, PhysicalCard,
                                         AbstractCard)
from sutekh.base.core.BaseAdapters import (IAbstractCard, IPhysicalCard,
                                           IPhysicalCardSet)
from sutekh.core.SutekhTables import SutekhAbstractCard
from sutekh.base.core.BaseFilters import CardTypeFilter, FilterAndBox
from sutekh.core.Filters import (MultiGroupFilter, MultiVirtueFilter,
                                 MultiDisciplineFilter,
                                 MultiDisciplineLevelFilter)
from sutekh.SutekhUtility import is_crypt_card, is_vampire
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.SutekhDialog import (SutekhDialog, NotebookDialog,
                                          do_complaint_error)
from sutekh.base.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.base.gui.GuiCardSetFunctions import create_card_set


def _gen_subsets(aData, iSetSize, iDepth=1):
    """Generate subsets of the given size from a list"""
    if iDepth > iSetSize:
        return []
    if iDepth < 1:
        return []
    if iDepth == iSetSize:
        return [set([x]) for x in aData]
    # I'm arguably overly fond of recursion
    aNewSets = []
    aSets = _gen_subsets(aData, iSetSize, iDepth + 1)
    for oVal in aData:
        for oSet in aSets:
            if oVal not in oSet:
                oNewSet = oSet.union(set([oVal]))
                if oNewSet not in aNewSets:
                    aNewSets.append(oNewSet)
    return aNewSets


def _get_groups(oCard):
    """Get compatible groups ranges"""
    # We ignore the any group cases as they are currently uninteresing
    # and excluded by the discipline check
    # If this ever changes, this will need to be revisited.
    # pylint: disable=no-member
    # SQLObject confuses pylint
    iGrp = oCard.group
    iMaxGrp = SutekhAbstractCard.select().max(SutekhAbstractCard.q.group)
    iMax = min(iMaxGrp, iGrp + 1)
    iMin = max(1, iGrp - 1)
    return MultiGroupFilter(range(iMin, iMax + 1))


def make_key(aSet, bSuperior):
    """Create a suitable key"""
    if bSuperior:
        sKey = " & ".join(sorted([x.name.upper() for x in aSet]))
    else:
        sKey = " & ".join(sorted([x.name for x in aSet]))
    return sKey


def _make_superset(oCard, bSuperior, bVampire):
    """Check if all elements of aSet match oCard"""
    if bSuperior:
        return set([oP.discipline for oP in oCard.discipline if
                    oP.level == 'superior'])
    if bVampire:
        return set([oP.discipline for oP in oCard.discipline])
    # Imbued
    return set(oCard.virtue)


class FindLikeVampires(SutekhPlugin):
    """Create a list of vampires 'like' the selected vampire."""

    dTableVersions = {PhysicalCardSet: (5, 6, 7)}
    aModelsSupported = (PhysicalCardSet, PhysicalCard)

    sMenuName = "Find similar crypt cards"

    sHelpCategory = "card_sets:analysis"

    sHelpText = """This allows you to find crypt cards that are similar to the
                   current selected crypt card. It will search for cards in a
                   compatible grouping that share the specified number of
                   disciplines or virtues with the selected crypt card.

                   More complex queries are possible by frist filtering the
                   card set and then using the 'Only match cards visible in
                   this pane' option to restrict the results of the crypt card
                   search to match the filter."""

    def get_menu_item(self):
        """Register on the 'Analyze' Menu"""
        oGenFilter = Gtk.MenuItem(label=self.sMenuName)
        oGenFilter.connect("activate", self.activate)
        return ('Analyze', oGenFilter)

    # pylint: disable=attribute-defined-outside-init
    # we define attributes outside __init__, but it's OK because of plugin
    # structure
    def activate(self, _oWidget):
        """Create the dialog.

           Prompt the user for attributes that are important and so forth
           """
        self.oSelCard = self._get_selected_crypt_card()
        if not self.oSelCard:
            do_complaint_error("Please select only 1 crypt card.")
            return
        # We treat imbued and vampires differently
        # pylint: disable=no-member
        # SQLObject confuses pylint
        if is_vampire(self.oSelCard):
            if not self.oSelCard.discipline:
                do_complaint_error("Please select a vampire with disciplines.")
                return
            dGroups = self.find_vampires_like()
        else:
            if not self.oSelCard.virtue:
                do_complaint_error("Please select an Imbued with virtues.")
                return
            dGroups = self.find_imbued_like()
        if dGroups:
            self.display_results(dGroups)
    # pylint: enable=attribute-defined-outside-init

    # pylint: disable=too-many-arguments
    # need all these arguments to format results nicely
    def _group_cards(self, aCards, iNum, aSubSets, bSuperior, bUseCardSet):
        """Group the cards and return only cards with iNum or more
           instances.

           This works because of our database structure and query, which
           ends up returning a match for each discipline in the discipline
           filter that matches."""
        aDistinct = set(aCards)
        dResults = {}
        aDistinct.remove(self.oSelCard)  # Don't match ourselves
        bVampire = is_vampire(self.oSelCard)
        if bUseCardSet:
            aCardSetCards = set([IAbstractCard(x) for x in
                                 self.model.get_card_iterator(
                                     self.model.get_current_filter())])
        else:
            aCardSetCards = None
        for oCard in list(aDistinct):
            if aCards.count(oCard) < iNum:
                aDistinct.remove(oCard)
            elif bUseCardSet and oCard not in aCardSetCards:
                # Remove cards not in the view from the results
                aDistinct.remove(oCard)
        dResults['all'] = aDistinct
        for oCard in aDistinct:
            aFullSet = _make_superset(oCard, bSuperior, bVampire)
            for aSet in aSubSets:
                # We only add the card if it has all elements of the set
                if aSet.issubset(aFullSet):
                    dResults.setdefault(make_key(aSet, bSuperior),
                                        []).append(oCard)
        return dResults
    # pylint: enable=too-many-arguments

    def _get_selected_crypt_card(self):
        """Extract selected crypt card from the model."""
        # Only interested in distinct cards
        aAbsCards = set(self._get_selected_abs_cards())
        if len(aAbsCards) != 1:
            return None
        oCard = aAbsCards.pop()
        if not is_crypt_card(oCard):
            # Only want crypt cards
            return None
        return oCard

    def find_vampires_like(self):
        """Construct a vampire search from the card"""
        # pylint: disable=no-member
        # SQLObject & Gtk confuse pylint
        aFilters = [CardTypeFilter('Vampire'), _get_groups(self.oSelCard)]
        oDialog = SutekhDialog('Find Vampires like', self.parent,
                               Gtk.DialogFlags.MODAL |
                               Gtk.DialogFlags.DESTROY_WITH_PARENT,
                               ("_OK", Gtk.ResponseType.OK,
                                "_Cancel", Gtk.ResponseType.CANCEL))
        oDialog.vbox.pack_start(
            Gtk.Label(label='Find Vampires like %s' % self.oSelCard.name),
            False, False, 0)
        aDisciplines = [oP.discipline for oP in self.oSelCard.discipline]
        aSuperior = [oP.discipline for oP in self.oSelCard.discipline if
                     oP.level == 'superior']
        oUseCardSet = Gtk.CheckButton("Only match cards visible in this pane")
        oDialog.vbox.pack_start(oUseCardSet, False, True, 0)
        if aSuperior:
            oDisciplines = Gtk.RadioButton(
                group=None, label="Match Disciplines")
            oSuperior = Gtk.RadioButton(
                group=oDisciplines, label="Match Superior Disciplines")
            oDisciplines.set_active(True)
        else:
            oDisciplines = Gtk.Label(label="Match Disciplines")
            oSuperior = None
        oDialog.vbox.pack_start(oDisciplines, False, True, 0)
        oComboBox = Gtk.ComboBoxText()
        if oSuperior:
            oDialog.vbox.pack_start(oSuperior, False, True, 0)
            oDisciplines.connect('toggled', self._update_combo_box,
                                 oComboBox, aDisciplines, aSuperior)
        for iNum in range(1, len(aDisciplines) + 1):
            oComboBox.append_text('%d' % iNum)
        if len(aDisciplines) > 1:
            oComboBox.set_active(1)
        else:
            oComboBox.set_active(0)
        oHBox = Gtk.HBox(False, 2)
        oHBox.pack_start(Gtk.Label(label='Use '), False, True, 0)
        oHBox.pack_start(oComboBox, False, True, 0)
        oHBox.pack_start(Gtk.Label(label=' Disciplines'), False, True, 0)
        oDialog.vbox.pack_start(oHBox, False, True, 0)
        oDialog.show_all()
        iRes = oDialog.run()
        if iRes == Gtk.ResponseType.CANCEL:
            oDialog.destroy()
            return None
        bUseCardSet = oUseCardSet.get_active()
        sText = oComboBox.get_active_text()
        iNum = int(sText)
        bSuperior = oSuperior and oSuperior.get_active()
        if bSuperior:
            oDisciplineFilter = MultiDisciplineLevelFilter(
                [(x.fullname, 'superior') for x in aSuperior])
            aSets = _gen_subsets(aSuperior, iNum)
        else:
            oDisciplineFilter = MultiDisciplineFilter([
                x.fullname for x in aDisciplines])
            aSets = _gen_subsets(aDisciplines, iNum)
        aFilters.append(oDisciplineFilter)
        oFullFilter = FilterAndBox(aFilters)
        oDialog.destroy()
        aCandCards = list(oFullFilter.select(AbstractCard))
        return self._group_cards(aCandCards, iNum, aSets, bSuperior,
                                 bUseCardSet)

    def find_imbued_like(self):
        """Construct a imbued search from the card"""
        # pylint: disable=no-member
        # SQLObject & Gtk confuse pylint
        aFilters = [CardTypeFilter('Imbued'), _get_groups(self.oSelCard)]
        oDialog = SutekhDialog('Find Imbued like', self.parent,
                               Gtk.DialogFlags.MODAL |
                               Gtk.DialogFlags.DESTROY_WITH_PARENT,
                               ("_OK", Gtk.ResponseType.OK,
                                "_Cancel", Gtk.ResponseType.CANCEL))
        oDialog.vbox.pack_start(
            Gtk.Label(label='Find Imbued like %s' % self.oSelCard.name),
            False, False, 0)
        oUseCardSet = Gtk.CheckButton("Only match cards visible in this pane")
        oDialog.vbox.pack_start(oUseCardSet, False, True, 0)
        oDialog.vbox.pack_start(Gtk.Label(label="Match Virtues"),
                                False, True, 0)
        oComboBox = Gtk.ComboBoxText()
        for iNum in range(1, len(self.oSelCard.virtue) + 1):
            oComboBox.append_text('%d' % iNum)
        if len(self.oSelCard.virtue) > 1:
            oComboBox.set_active(1)
        else:
            oComboBox.set_active(0)
        oHBox = Gtk.HBox(False, 2)
        oHBox.pack_start(Gtk.Label(label='Use '), False, True, 0)
        oHBox.pack_start(oComboBox, False, True, 0)
        oHBox.pack_start(Gtk.Label(label=' Virtues'), False, True, 0)
        oDialog.vbox.pack_start(oHBox, False, True, 0)
        oDialog.show_all()
        iRes = oDialog.run()
        if iRes == Gtk.ResponseType.CANCEL:
            oDialog.destroy()
            return None
        bUseCardSet = False
        if oUseCardSet.get_active():
            bUseCardSet = True
        sText = oComboBox.get_active_text()
        iNum = int(sText)
        oVirtueFilter = MultiVirtueFilter([x.fullname for x in
                                           self.oSelCard.virtue])
        aSets = _gen_subsets(self.oSelCard.virtue, iNum)
        aFilters.append(oVirtueFilter)
        oFullFilter = FilterAndBox(aFilters)
        oDialog.destroy()
        aCandCards = list(oFullFilter.select(AbstractCard))
        return self._group_cards(aCandCards, iNum, aSets, False,
                                 bUseCardSet)

    def _update_combo_box(self, oDiscipline, oComboBox, aDisciplines,
                          aSuperior):
        """Update the combo box as required"""
        sText = oComboBox.get_active_text()
        iCurNum = int(sText)
        if oDiscipline.get_active():
            # Set to inf
            iMax = len(aDisciplines)
            iOldMax = len(aSuperior)
        else:
            # set to superior
            iMax = len(aSuperior)
            iOldMax = len(aDisciplines)
        # clear combo box
        oComboBox.remove_all()
        # refill
        for iNum in range(1, iMax + 1):
            oComboBox.append_text('%d' % iNum)
        if iCurNum <= iMax:
            oComboBox.set_active(iCurNum - 1)
        elif iMax >= 2:
            oComboBox.set_active(1)
        else:
            oComboBox.set_active(0)

    def display_results(self, dGroups):
        """Display the results nicely"""
        # pylint: disable=no-member
        # SQLObject and Gtk confuse pylint
        bVampire = is_vampire(self.oSelCard)
        if bVampire:
            sTitle = 'Vampires like %s' % self.oSelCard.name
        else:
            sTitle = 'Imbued like %s' % self.oSelCard.name
        oResults = NotebookDialog(sTitle, self.parent,
                                  Gtk.DialogFlags.MODAL |
                                  Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                  ("_Close", Gtk.ResponseType.CLOSE))

        oResults.set_size_request(700, 600)

        oAllView = LikeCardsView(dGroups['all'], bVampire)
        oResults.add_widget_page(AutoScrolledWindow(oAllView),
                                 'All Matches')
        for sSet in sorted(dGroups):
            if sSet == 'all':
                # Already handled
                continue
            oView = LikeCardsView(dGroups[sSet], bVampire)
            oResults.add_widget_page(AutoScrolledWindow(oView), sSet)
        oActions = Gtk.HBox()
        oToggle = Gtk.CheckButton('Include original card')
        oToggle.connect('toggled', self._update_notebook, oResults)
        oActions.pack_start(oToggle, False, True, 0)
        oCreateCardSet = Gtk.Button(label='Create card set from selection')
        oCreateCardSet.connect('clicked', self._make_cs, oResults)
        oActions.pack_start(oCreateCardSet, False, True, 0)
        oResults.vbox.pack_start(oActions, False, True, 0)
        oResults.show_all()
        oResults.run()
        oResults.destroy()

    def _update_notebook(self, oCheckBox, oDlg):
        """Add or remove the original card as required"""
        bInclude = oCheckBox.get_active()
        for oScroll in oDlg.iter_all_page_widgets():
            oModel = oScroll.get_child().get_model()
            if bInclude:
                oModel.add_card(self.oSelCard)
            else:
                oModel.remove_card(self.oSelCard)

    def _make_cs(self, _oButton, oDlg):
        """Create a card set with the given cards"""
        # pylint: disable=no-member
        # SQLObject confuses pylint
        oView = oDlg.get_cur_widget().get_child()
        aCards = oView.get_selected_cards()
        if not aCards:
            do_complaint_error("No cards selected for card set.")
            return
        sCSName = create_card_set(self.parent)
        if sCSName:
            oCardSet = IPhysicalCardSet(sCSName)
            for oCard in aCards:
                # We add with unknown expansion
                # pylint: disable=no-member
                # SQLObject confuses pylint
                oCardSet.addPhysicalCard(IPhysicalCard((oCard, None)))
            self._open_cs(sCSName, True)


class LikeCardsView(Gtk.TreeView):
    # pylint: disable=too-many-public-methods
    # Gtk classes, so we have lots of public methods
    """TreeView for showing details of matching cards"""

    VAMP_LABELS = ['Name', 'Group', 'Capacity', 'Clan', 'Disciplines']
    IMBUED_LABELS = ['Name', 'Group', 'Life', 'Creed', 'Virtues']

    def __init__(self, aCards, bVampire):
        self._oModel = LikeCardsModel(aCards, bVampire)

        super().__init__(self._oModel)

        oCell = Gtk.CellRendererText()
        oCell.set_property('style', Pango.Style.ITALIC)

        if bVampire:
            aLabels = self.VAMP_LABELS
        else:
            aLabels = self.IMBUED_LABELS

        for iCol, sLabel in enumerate(aLabels):
            oColumn = Gtk.TreeViewColumn(sLabel, oCell, text=iCol)
            oColumn.set_sort_column_id(iCol)
            self.append_column(oColumn)

        # Sort by the name by default
        self._oModel.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        oSelection = self.get_selection()
        oSelection.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.set_grid_lines(Gtk.TreeViewGridLines.BOTH)

    def get_selected_cards(self):
        """Get the currently selected cards"""
        aCards = []
        _oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            aCards.append(self._oModel.get_card(oPath))
        return aCards


class LikeCardsModel(Gtk.ListStore):
    # pylint: disable=too-many-public-methods
    # Gtk classes, so we have lots of public methods
    """ListStore for holding details of the matching cards"""

    def __init__(self, aCards, bVampire):
        super().__init__(GObject.TYPE_STRING, GObject.TYPE_INT,
                         GObject.TYPE_INT, GObject.TYPE_STRING,
                         GObject.TYPE_STRING)

        self.bVampire = bVampire
        for oCard in aCards:
            self.add_card(oCard)

    def add_card(self, oCard):
        """Add the card to the model"""
        oIter = self.append(None)
        self.set(oIter, 0, oCard.name, 1, oCard.group)
        if self.bVampire:
            self.set(oIter, 2, oCard.capacity)
            self.set(oIter, 3, oCard.clan[0].name)
            aDis = [oP.discipline.name.upper() for oP in oCard.discipline
                    if oP.level == 'superior']
            aDis.extend([oP.discipline.name.lower() for oP
                         in oCard.discipline if oP.level != 'superior'])
            aDis.sort()
            self.set(oIter, 4, ' '.join(aDis))
        else:
            self.set(oIter, 2, oCard.life)
            self.set(oIter, 3, oCard.creed[0].name)
            aVirt = [oP.name.lower() for oP in oCard.virtue]
            aVirt.sort()
            self.set(oIter, 4, ' '.join(aVirt))

    def remove_card(self, oCard):
        """Remove the card from the model"""
        oIter = self.get_iter_first()
        while oIter is not None:
            sName = self.get_value(oIter, 0)
            if sName == oCard.name:
                break
            oIter = self.iter_next(oIter)
        if oIter:
            # Delete the card from the view
            self.remove(oIter)

    def get_card(self, oPath):
        """Return the AbstractCard for the given path"""
        oIter = self.get_iter(oPath)
        sName = self.get_value(oIter, 0)
        return IAbstractCard(sName)


plugin = FindLikeVampires
