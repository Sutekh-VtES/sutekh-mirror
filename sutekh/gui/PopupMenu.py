# PopupMenu.py
# Simple popup menu to handle card number changing in the views
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class PopupMenu(gtk.Menu):
   def __init__(self,oView,oPath):
      super(PopupMenu,self).__init__()
      self.iInc=gtk.Action("IncCard","Increase Card Count",None,None)
      self.iDec=gtk.Action("DecCard","Decrease Card Count",None,None)
      self.iInc.connect("activate",oView.incCard,oPath)
      self.iDec.connect("activate",oView.decCard,oPath)
      self.iInc.set_sensitive(True)
      self.iDec.set_sensitive(True)
      self.add(self.iInc.create_menu_item())
      self.add(self.iDec.create_menu_item())
