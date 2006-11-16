# PhysicalCardSetExportArdbXML.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import *
from Filters import *
from gui.PluginManager import CardListPlugin
from WriteArdbXML import WriteArdbXML

class PhysicalCardSetExportArdbXML(CardListPlugin):
    def __init__(self,*args,**kws):
        super(PhysicalCardSetExportArdbXML,self).__init__(*args,**kws)

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        iDF = gtk.MenuItem("Export Physical Card Set to ARDB XML")
        iDF.connect("activate", self.activate)
        try:
            if self.view.sSetType != 'Physical':
                iDF.set_sensitive(False)
        except AttributeError:
            iDF.set_sensitive(False)
        return iDF
        
    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()
        oDlg.destroy()

    def makeDialog(self):
        parent = self.view.getWindow()
        self.oDlg = gtk.Dialog("Choose PhysicalCardSets to Test",parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oFileChooser=gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_SAVE)
        self.oFileChooser.set_do_overwrite_confirmation(True)
        oAuthorLabel=gtk.Label("Author : ")
        oDescLabel=gtk.Label("Description : ")
        self.oAuthor=gtk.Entry(50)
        self.oDescription=gtk.Entry(550)
        self.oDlg.vbox.pack_start(self.oFileChooser)
        self.oDlg.vbox.pack_start(oAuthorLabel)
        self.oDlg.vbox.pack_start(self.oAuthor)
        self.oDlg.vbox.pack_start(oDescLabel)
        self.oDlg.vbox.pack_start(self.oDescription)
        self.oDlg.connect("response", self.handleResponse)
        self.oDlg.show_all()
        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
        if oResponse ==  gtk.RESPONSE_OK:
            sFileName=self.oFileChooser.get_filename()
            if sFileName is not None:
                oW=WriteArdbXML()
                fOut=file(sFileName,"w")
                oW.write(fOut,self.view.sSetName,\
                        self.oAuthor.get_text(),\
                        self.oDescription.get_text(),\
                        self.getCards())
                fOut.close()

    def getCards(self):
        dDict = {}
        for oCard in self.model.getCardIterator(None):
            print oCard.abstractCard
            oAbstractCard=oCard.abstractCard
            dDict.setdefault((oAbstractCard.id,oAbstractCard.name),0)
            dDict[(oAbstractCard.id,oAbstractCard.name)]+=1
        return dDict

plugin = PhysicalCardSetExportArdbXML
