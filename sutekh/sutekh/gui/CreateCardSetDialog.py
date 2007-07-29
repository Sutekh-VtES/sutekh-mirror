# CreateCardSetDialog.py
# Dialog to create a new PhysicalCardSet or AbstrctCardSet
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class CreateCardSetDialog(gtk.Dialog):
    def __init__(self,parent,sType,sAuthor=None,sDesc=None):
        super(CreateCardSetDialog,self).__init__(sType+" Card Set Details",
            parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oNameLabel = gtk.Label("Card Set Name : ")
        self.oName = gtk.Entry(50)
        oAuthorLabel = gtk.Label("Author : ")
        self.oAuthor = gtk.Entry(50)
        oDescriptionLabel = gtk.Label("Description : ")
        self.oDesc = gtk.Entry(50)

        self.vbox.pack_start(oNameLabel)
        self.vbox.pack_start(self.oName)
        self.vbox.pack_start(oAuthorLabel)
        self.vbox.pack_start(self.oAuthor)
        self.vbox.pack_start(oDescriptionLabel)
        self.vbox.pack_start(self.oDesc)

        self.connect("response", self.buttonResponse)
        self.oName.connect("activate", self.buttonResponse, gtk.RESPONSE_OK)

        if sAuthor is not None:
	        self.oAuthor.set_text(sAuthor)

        if sDesc is not None:
	        self.oDesc.set_text(sDesc)

        self.sName = None
        self.sAuthor = None
        self.sDesc = None
        self.sType = sType

        self.show_all()

    def getName(self):
        return (self.sName, self.sAuthor, self.sDesc)

    def buttonResponse(self,oWidget,oResponse):
        if oResponse == gtk.RESPONSE_OK:
            self.sName = self.oName.get_text()
            if len(self.sName) > 0:
                self.sAuthor = self.oAuthor.get_text()
                self.sDesc = self.oDesc.get_text()
                # We use _ as a deliminator for dragging (see CardSetView)
                # so change any _'s to spaces
                self.sName = self.sName.replace("_"," ")
            else:
                # We don't allow empty names
                self.sName = None

                Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_CLOSE,
                    "You did not specify a name for the %s." % self.sType)
                Complaint.run()
                Complaint.destroy()

        self.destroy()
