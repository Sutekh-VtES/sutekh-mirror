# AbstractCardSetIndependence.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import *
from gui.PluginManager import CardListPlugin

class AbstractCardSetIndependence(CardListPlugin):
    def __init__(self,*args,**kws):
        super(AbstractCardSetIndependence,self).__init__(*args,**kws)

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        iDF = gtk.MenuItem("Test Abstract Card Set Independence")
        iDF.connect("activate", self.activate)
        return iDF
        
    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()
    
        self.oDlg = gtk.Dialog("Choose Abstract Card Sets to Test",parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))     
        self.oDlg.connect("response", self.handleResponse)
        
        self.oDlg.show_all()
        
        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
       if oResponse ==  gtk.RESPONSE_OK:
          self.testAbstractCardSets(aAbstractCardSetNames)
          
       self.oDlg.destroy()
          
    def testAbstractCardSets(self,aAbstractCardSetNames):
        print "Testing the following Abstract Card Sets",aAbstractCardSetNames
        pass

plugin = AbstractCardSetIndependence
