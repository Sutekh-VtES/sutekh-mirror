import gtk

class PopupMenu(gtk.Menu):
   def __init__(self,view,path):
      super(PopupMenu,self).__init__()
      self.iInc=gtk.Action("IncCard","Increase Card Count",None,None)
      self.iDec=gtk.Action("DecCard","Decrease Card Count",None,None)
      self.iInc.connect("activate",view.incCard,path)
      self.iDec.connect("activate",view.decCard,path)
      self.iInc.set_sensitive(True)
      self.iDec.set_sensitive(True)
      self.add(self.iInc.create_menu_item())
      self.add(self.iDec.create_menu_item())
