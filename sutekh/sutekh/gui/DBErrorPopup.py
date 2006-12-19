# DBErrorPopup.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class DBErrorPopup(gtk.Dialog):
    def __init__(self,aBadTables):
        # Create Dialog
        super(DBErrorPopup,self).__init__("Database Version Error",None,
                gtk.DIALOG_MODAL,(gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE))
        sLabel="Database version error. Cannot continue\n"
        sLabel+="The following tables need to be upgraded:\n"
        sLabel+="\n".join(aBadTables)
        label=gtk.Label(sLabel)
        Icon=gtk.Image()
        Icon.set_from_stock(gtk.STOCK_DIALOG_ERROR,gtk.ICON_SIZE_DIALOG)
        MyHBox=gtk.HBox(False,0)
        MyHBox.pack_start(Icon)
        MyHBox.pack_start(label)
        self.add_button("Attempt Automatic Database Upgrade",1)
        self.set_default_response(gtk.RESPONSE_CLOSE)
        self.vbox.pack_start(MyHBox)
        self.show_all()
