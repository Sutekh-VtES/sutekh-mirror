import gtk

class PopupMenu(gtk.Menu):
   def __init__(self,view,path):
      super(PopupMenu,self).__init__()
      iInc=gtk.MenuItem("Increase Card Count")
      iDec=gtk.MenuItem("Decrease Card Count")
      iInc.connect("activate",view.incCard,path)
      iDec.connect("activate",view.decCard,path)
      # Apprantly need these shows as we're using the popup method,
      # which doesn't seem to call them automatically
      iInc.show()
      iDec.show()
      self.add(iInc)
      self.add(iDec)
