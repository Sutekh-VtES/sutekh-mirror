# CardSetExportArdbXML.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, IAbstractCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.io.WriteArdbXML import WriteArdbXML

class CardSetExportArdbXML(CardListPlugin):
    dTableVersions = { AbstractCardSet: [2,3],
                       PhysicalCardSet: [2,3]}
    aModelsSupported = [AbstractCardSet, PhysicalCardSet]

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iDF = gtk.MenuItem("Export Card Set to ARDB XML")
        iDF.connect("activate", self.activate)
        return iDF

    def get_desired_menu(self):
        return "Plugins"

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()
        oDlg.destroy()

    def makeDialog(self):
        self.oDlg = SutekhDialog("Choose FileName for Exported CardSet", self.parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oFileChooser = gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_SAVE)
        self.oFileChooser.set_do_overwrite_confirmation(True)
        self.oDlg.vbox.pack_start(self.oFileChooser)
        self.oDlg.connect("response", self.handleResponse)
        self.oDlg.show_all()
        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
        if oResponse ==  gtk.RESPONSE_OK:
            sFileName = self.oFileChooser.get_filename()
            if sFileName is not None:
                if self.view.cSetType == PhysicalCardSet:
                    oCardSet = PhysicalCardSet.byName(self.view.sSetName)
                elif self.view.cSetType == AbstractCardSet:
                    oCardSet = AbstractCardSet.byName(self.view.sSetName)
                else:
                    return
                sAuthor = oCardSet.author
                sComment = oCardSet.comment
                oW = WriteArdbXML()
                fOut = file(sFileName,"w")
                oW.write(fOut,self.view.sSetName,\
                        sAuthor,\
                        sComment,\
                        self.getCards())
                fOut.close()

    def getCards(self):
        dDict = {}
        for oCard in self.model.getCardIterator(None):
            oACard = IAbstractCard(oCard)
            dDict.setdefault((oACard.id,oACard.name),0)
            dDict[(oACard.id,oACard.name)] += 1
        return dDict

plugin = CardSetExportArdbXML
