# ClusterCardList.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from gui.PluginManager import CardListPlugin

# find a cluster module
for module in ['Pycluster','Bio.Cluster']:
    try:
        cluster = __import__(module)
        break
    except ImportError:
        pass
else:
    raise ImportError("Could not find PyCluster or Bio.Cluster. Not loading clustering plugin.")

class ClusterCardList(CardListPlugin):
    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        iCluster = gtk.MenuItem("Cluster Cards")
        iCluster.connect("activate", self.activate)
        return iCluster
        
    def activate(self,oWidget):
        dlg = self.makeDialog()
        dlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()
        name = "Cluster Cards in List"
    
        dlg = gtk.Dialog(name,parent,
                         gtk.DIALOG_DESTROY_WITH_PARENT,
                         (gtk.STOCK_OK, gtk.RESPONSE_OK))
                         
        dlg.connect("response", lambda dlg, resp: dlg.destroy())

        oNotebook = gtk.Notebook()

        # TODO: Replace with appropriate objects        
        oTableSection = gtk.Label()
        oAlgorithmSection = gtk.Label()
        oClusterSection = gtk.Label()
        
        oNotebook.append_page(oTableSection,gtk.Label('Select Columns'));
        oNotebook.append_page(oAlgorithmSection,gtk.Label('Select Algorithm'));
        oNotebook.append_page(oClusterSection,gtk.Label('Run Clustering'));

        return dlg
        
plugin = ClusterCardList
