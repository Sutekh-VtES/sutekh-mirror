# DBUpgradeDialog.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class DBUpgradeDialog(gtk.Dialog):
    def __init__(self):
        # Create Dialog
        super(DBUpgradeDialog,self).__init__("Memory Copy Created",None,
                gtk.DIALOG_MODAL,(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                    gtk.STOCK_OK, gtk.RESPONSE_OK))
        sLabel="Memory Copy successfully created. Commit Changes?"
        label=gtk.Label(sLabel)
        Icon=gtk.Image()
        Icon.set_from_stock(gtk.STOCK_DIALOG_INFO,gtk.ICON_SIZE_DIALOG)
        MyHBox=gtk.HBox(False,0)
        MyHBox.pack_start(Icon)
        MyHBox.pack_start(label)
        self.add_button("Test upgraded database?\n(No changes are committed)",1)
        self.set_default_response(gtk.RESPONSE_OK)
        self.vbox.pack_start(MyHBox)
        self.show_all()
