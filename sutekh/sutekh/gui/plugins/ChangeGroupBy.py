# ChangeGroupBy.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Allow the use to change how the cards are grouped in the CardListView"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCard, PhysicalCardSet
from sutekh.core.Groupings import CardTypeGrouping, ClanGrouping, \
        DisciplineGrouping, ExpansionGrouping, RarityGrouping, \
        CryptLibraryGrouping, NullGrouping, MultiTypeGrouping, \
        SectGrouping, TitleGrouping, CostGrouping
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog

class GroupCardList(CardListPlugin):
    """Plugin to allow the user to change how cards are grouped.

       Show a dialog which allows the user to select from the avail
       groupings of the cards, and changes the setting in the CardListView.
       """
    dTableVersions = {}
    aModelsSupported = [PhysicalCard, PhysicalCardSet]

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(GroupCardList, self).__init__(*aArgs, **kwargs)
        self._dGrpings = {}
        self._dGrpings['Card Type'] = CardTypeGrouping
        self._dGrpings['Multi Card Type'] = MultiTypeGrouping
        self._dGrpings['Crypt or Library'] = CryptLibraryGrouping
        self._dGrpings['Clans and Creeds'] = ClanGrouping
        self._dGrpings['Disciplines and Virtues'] = DisciplineGrouping
        self._dGrpings['Expansion'] = ExpansionGrouping
        self._dGrpings['Rarity'] = RarityGrouping
        self._dGrpings['Sect'] = SectGrouping
        self._dGrpings['Title'] = TitleGrouping
        self._dGrpings['Cost'] = CostGrouping
        self._dGrpings['No Grouping'] = NullGrouping
        self._oFirstBut = None # placeholder for the radio group

    def get_menu_item(self):
        """Register on the 'Plugins' menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oGrouping = gtk.MenuItem("Change Grouping")
        oGrouping.connect("activate", self.activate)
        return ('Plugins', oGrouping)

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def activate(self, oWidget):
        """Response to the menu - create the dialog and run it"""
        oDlg = self.make_dialog()
        oDlg.run()

    # pylint: enable-msg=W0613

    def make_dialog(self):
        """Create the required dialog."""
        sName = "Change Card List Grouping..."

        oDlg = SutekhDialog(sName, self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT)
        oDlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        oDlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

        oDlg.connect("response", self.handle_response)

        cCurrentGrping = self.get_grouping()
        oIter = self._dGrpings.iteritems()
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        for sName, cGrping in oIter:
            self._oFirstBut = gtk.RadioButton(None, sName, False)
            self._oFirstBut.set_active(cGrping is cCurrentGrping)
            oDlg.vbox.pack_start(self._oFirstBut)
            break
        for sName, cGrping in oIter:
            oBut = gtk.RadioButton(self._oFirstBut, sName)
            oBut.set_active(cGrping is cCurrentGrping)
            oDlg.vbox.pack_start(oBut)

        oDlg.show_all()

        return oDlg

    # Actions

    def handle_response(self, oDlg, oResponse):
        """Handle the response from the dialog.

           Change the grouping in the CardListView if appropriate"""
        if oResponse == gtk.RESPONSE_CANCEL:
            oDlg.destroy()
        elif oResponse == gtk.RESPONSE_OK:
            for oBut in self._oFirstBut.get_group():
                if oBut.get_active():
                    sLabel = oBut.get_label()
                    cGrping = self._dGrpings[sLabel]
                    self.set_grouping(cGrping)
            oDlg.destroy()

    def set_grouping(self, cGrping):
        """Set the grouping to that specified by cGrping."""
        self.model.groupby = cGrping
        # Use view.load so we get busy cursor, etc.
        self.view.load()

    def get_grouping(self):
        """Get the current grouping class."""
        return self.model.groupby

# pylint: disable-msg=C0103
# accept plugin name
plugin = GroupCardList
