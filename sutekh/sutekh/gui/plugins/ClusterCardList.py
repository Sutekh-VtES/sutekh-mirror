# ClusterCardList.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from CardListTabulator import CardListTabulator
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
    
        self.makePropGroups()
    
        oDlg = gtk.Dialog(name,parent,
                         gtk.DIALOG_DESTROY_WITH_PARENT,
                         (gtk.STOCK_OK, gtk.RESPONSE_OK))
                         
        oDlg.connect("response", lambda dlg, resp: dlg.destroy())

        oNotebook = gtk.Notebook()

        oTableSection = self.makeTableSection()
        oAlgorithmSection = self.makeAlgorithmSection()
        oClusterSection = self.makeClusterSection()
        
        oNotebook.append_page(oTableSection,gtk.Label('Select Columns'));
        oNotebook.append_page(oAlgorithmSection,gtk.Label('Select Algorithm'));
        oNotebook.append_page(oClusterSection,gtk.Label('Run Clustering'));

        oDlg.vbox.pack_start(oNotebook)
        oDlg.show_all()

        return oDlg

    def makePropGroups(self):
        dPropFuncs = CardListTabulator.getDefaultPropFuncs()
        self._dGroups = {}
        
        for sName, fProp in dPropFuncs.iteritems():
            aParts = sName.split(":")
            if len(aParts) == 1:
                self._dGroups.setdefault("Miscellaneous",{})[sName.capitalize()] = fProp
            else:
                sGroup, sRest = aParts[0].strip().capitalize(), ":".join(aParts[1:]).strip().capitalize()
                self._dGroups.setdefault(sGroup,{})[sRest] = fProp

    def makeTableSection(self):
        oNotebook = gtk.Notebook()
        aGroups = self._dGroups.keys()
        aGroups.sort()

        for sGroup in aGroups:
            dPropFuncs = self._dGroups[sGroup]
            
            oHbx = gtk.HBox(False,0)
            
            iCols = 3
            iPropsPerCol = len(dPropFuncs) / iCols
            if len(dPropFuncs) % iCols != 0:
                iPropsPerCol += 1

            aPropNames = dPropFuncs.keys()
            aPropNames.sort()
                
            for iProp, sName in enumerate(aPropNames):
                if iProp % iPropsPerCol == 0:
                    oVbx = gtk.VBox(False,0)
                    oHbx.pack_start(oVbx)
                
                oBut = gtk.CheckButton(sName)
                oVbx.pack_start(oBut)

            oNotebook.append_page(oHbx,gtk.Label(sGroup))

        return oNotebook
        
    def makeAlgorithmSection(self):
        oHbx = gtk.VBox(False,0)

        # Hard coded to SOM for now
        
        # Tau
        oTauLabel = gtk.Label("Initial Value of Tau (Neighbourhood function):")
        oHbx.pack_start(oTauLabel)

        # Number of iterations
        oNumIterLabel = gtk.Label("Number of Iterations:")
        oHbx.pack_start(oNumIterLabel)
        
        # Distance Measure
        oDistLabel = gtk.Label("Distance Measure:")
        oHbx.pack_start(oDistLabel)
        
        dDist = { 'e' : 'Euclidean Distance', 'b' : 'City Block Distance',
                  'c' : 'Correlation', 'a' : 'Absolute Value of the Correlation',
                  'u' : 'Uncentered Correlation', 'x' : 'Absolute Value of the Uncentered Correlation',
                  's' : "Spearman's Rank Correlation", 'k' : "Kendall's Tau" }

        oIter = dDist.iteritems()
        for sChr, sName in oIter:
            oFirstBut = gtk.RadioButton(None,sName,False)
            oHbx.pack_start(oFirstBut)
            break
                          
        for sChr, sName in oIter:
            oBut = gtk.RadioButton(oFirstBut,sName)
            oHbx.pack_start(oBut)
    
        return oHbx
        
    def makeClusterSection(self):
        return gtk.Label()
        
plugin = ClusterCardList
