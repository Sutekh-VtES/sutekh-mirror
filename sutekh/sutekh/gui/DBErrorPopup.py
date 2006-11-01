# MainController.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class DBErrorPopup(object):
    def __init__(self):
        # Create PluginManager
        self.window=gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.box=gtk.VBox()
        label=gtk.Label("Database version error. Unable to continue")
        self.window.connect("destroy",self.destroy)
        self.button=gtk.Button("OK")
        self.button.connect("clicked",self.destroy)
        self.box.pack_start(label)
        self.box.pack_end(self.button)
        self.window.add(self.box)
        self.window.show_all()

    def destroy(self,widget, data=None):
        self.actionQuit()

    def run(self):
        gtk.main()

    def actionQuit(self):
        gtk.main_quit()
