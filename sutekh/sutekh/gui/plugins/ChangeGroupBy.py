# ChangeGroupBy.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from Groupings import *
from gui.PluginManager import CardListPlugin

class GroupCardList(CardListPlugin):
    dTableVersions = {}
    aModelsSupported = ["PhysicalCardSet","AbstractCardSet","PhysicalCard"]
    def __init__(self,*args,**kws):
        super(GroupCardList,self).__init__(*args,**kws)
        self._dGrpings = {}
        self._dGrpings['Card Type'] = CardTypeGrouping
        self._dGrpings['Clan'] = ClanGrouping
        self._dGrpings['Discipline'] = DisciplineGrouping
        self._dGrpings['Expansion'] = ExpansionGrouping
        self._dGrpings['Rarity'] = RarityGrouping

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iCluster = gtk.MenuItem("Change Grouping")
        iCluster.connect("activate", self.activate)
        return iCluster
        
    def activate(self,oWidget):
        dlg = self.makeDialog()
        dlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()
        name = "Change Card List Grouping..."
        
        oDlg = gtk.Dialog(name,parent,
                          gtk.DIALOG_DESTROY_WITH_PARENT)
        oDlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        oDlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
                         
        oDlg.connect("response", self.handleResponse)

        oIter = self._dGrpings.iteritems()
        for sName, cGrping in oIter:
            self._oFirstBut = gtk.RadioButton(None,sName,False)
            oDlg.vbox.pack_start(self._oFirstBut)
            break
        for sName, cGrping in oIter:
            oBut = gtk.RadioButton(self._oFirstBut,sName)
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
            
plugin = GroupCardList
