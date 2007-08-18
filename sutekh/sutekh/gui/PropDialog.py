# Dialog for handling Card Set Properties
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>

import gtk

class PropDialog(gtk.Dialog):
    def __init__(self,sTitle,oParent,curName,curAuthor,curComment):
        super(PropDialog,self).__init__(sTitle,oParent,\
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK, \
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response",self.buttonResponse)
        nameLabel = gtk.Label("Card Set Name : ")
        authLabel = gtk.Label("Author : ")
        commLabel = gtk.Label("Description : ")
        self.oName = gtk.Entry(50)
        self.oAuthor = gtk.Entry(50)
        self.oComment = gtk.Entry()
        self.oName.set_text(curName)
        self.oAuthor.set_text(curAuthor)
        self.oComment.set_text(curComment)
        self.vbox.pack_start(nameLabel)
        self.vbox.pack_start(self.oName)
        self.vbox.pack_start(authLabel)
        self.vbox.pack_start(self.oAuthor)
        self.vbox.pack_start(commLabel)
        self.vbox.pack_start(self.oComment)
        self.show_all()
        self.sName = None
        self.sAuthor = None
        self.sComment = None

    def buttonResponse(self,widget,response):
        if response == gtk.RESPONSE_OK:
            self.sName = self.oName.get_text()
            self.sAuthor = self.oAuthor.get_text()
            self.sComment = self.oComment.get_text()
        self.destroy()

    def getData(self):
        return (self.sName,self.sAuthor,self.sComment)
