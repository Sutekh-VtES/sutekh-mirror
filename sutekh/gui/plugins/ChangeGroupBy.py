# ChangeGroupBy.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCard, \
                                      AbstractCardSet, PhysicalCardSet
from sutekh.core.Groupings import CardTypeGrouping, ClanGrouping, DisciplineGrouping, \
                             ExpansionGrouping, RarityGrouping, CryptLibraryGrouping, \
                             NullGrouping
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog

class GroupCardList(CardListPlugin):
    dTableVersions = {}
    aModelsSupported = [AbstractCard, PhysicalCard, AbstractCardSet, PhysicalCardSet]

    def __init__(self,*args,**kws):
        super(GroupCardList,self).__init__(*args,**kws)
        self._dGrpings = {}
        self._dGrpings['Card Type'] = CardTypeGrouping
        self._dGrpings['Crypt or Library'] = CryptLibraryGrouping
        self._dGrpings['Clan'] = ClanGrouping
        self._dGrpings['Discipline'] = DisciplineGrouping
        self._dGrpings['Expansion'] = ExpansionGrouping
        self._dGrpings['Rarity'] = RarityGrouping
        self._dGrpings['No Grouping'] = NullGrouping

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iGrouping = gtk.MenuItem("Change Grouping")
        iGrouping.connect("activate", self.activate)
        return iGrouping

    def get_desired_menu(self):
        return "Plugins"

    def activate(self,oWidget):
        dlg = self.makeDialog()
        dlg.run()

    def makeDialog(self):
        name = "Change Card List Grouping..."

        oDlg = SutekhDialog(name,self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT)
        oDlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        oDlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

        oDlg.connect("response", self.handleResponse)

        cCurrentGrping = self.getGrouping()
        oIter = self._dGrpings.iteritems()
        for sName, cGrping in oIter:
            self._oFirstBut = gtk.RadioButton(None,sName,False)
            self._oFirstBut.set_active(cGrping is cCurrentGrping)
            oDlg.vbox.pack_start(self._oFirstBut)
            break
        for sName, cGrping in oIter:
            oBut = gtk.RadioButton(self._oFirstBut,sName)
            oBut.set_active(cGrping is cCurrentGrping)
            oDlg.vbox.pack_start(oBut)

        oDlg.show_all()

        return oDlg

    # Actions

    def handleResponse(self,oDlg,oResponse):
        if oResponse == gtk.RESPONSE_CLOSE:
            oDlg.destroy()
        elif oResponse == gtk.RESPONSE_OK:
            for oBut in self._oFirstBut.get_group():
                if oBut.get_active():
                    sLabel = oBut.get_label()
                    cGrping = self._dGrpings[sLabel]
                    self.setGrouping(cGrping)
            oDlg.destroy()

    def setGrouping(self,cGrping):
        self.model.groupby = cGrping
        self.model.load()

    def getGrouping(self):
        return self.model.groupby

plugin = GroupCardList
