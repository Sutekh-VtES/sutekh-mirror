# AbstractCardSetFromPhysical.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import *
from gui.PluginManager import CardListPlugin

class AbstractCardSetFromPhysical(CardListPlugin):
    """Create a equivilant Abstract Card Set from a given 
       Physical Card Set."""
    def __init__(self,*args,**kws):
        super(AbstractCardSetFromPhysical,self).__init__(*args,**kws)

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        iDF = gtk.MenuItem("Generate a Physical Card Set")
        iDF.connect("activate", self.activate)
        return iDF
        
    def activate(self,oWidget):
        self.createPhysCardSet()

    def createPhysCardSet(self):
        print "Creating a Physical Card Set"
        pass

plugin = AbstractCardSetFromPhysical
