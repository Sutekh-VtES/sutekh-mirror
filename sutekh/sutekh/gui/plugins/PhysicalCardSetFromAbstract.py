# PhysicalCardSetFromAbstract.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import *
from gui.PluginManager import CardListPlugin

class PhysicalCardSetFromAbstract(CardListPlugin):
    """Create a (as far as possible) equivilant Physical Card Set 
       from a given Abstract Card Set. 
       Ignores Cards which don't exist in Physical Cards"""
       #Q: How should the user be informed of missing cards?
    def __init__(self,*args,**kws):
        super(PhysicalCardSetFromAbstract,self).__init__(*args,**kws)

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        iDF = gtk.MenuItem("Generate a Physical Card Set")
        iDF.connect("activate", self.activate)
        return iDF
        
    def activate(self,oWidget):
        self.createAbsCardSet()

    def createAbsCardSet(self):
        print "Creating a Physical Card Set"
        pass

plugin = PhysicalCardSetFromAbstract
