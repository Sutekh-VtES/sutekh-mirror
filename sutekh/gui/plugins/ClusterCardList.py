# ClusterCardList.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.SutekhObjects import PhysicalCardSet, IAbstractCard
from sutekh.CardListTabulator import CardListTabulator
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

# find a cluster module
for module in ['Pycluster','Bio.Cluster']:
    try:
        Cluster = __import__(module)
        break
    except ImportError:
        pass
else:
    raise ImportError("Could not find PyCluster or Bio.Cluster. Not loading clustering plugin.")

class ClusterCardList(CardListPlugin):
    dTableVersions = {}
    aModelsSupported = ["PhysicalCard"]
    def __init__(self,*args,**kws):
        super(ClusterCardList,self).__init__(*args,**kws)

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iCluster = gtk.MenuItem("Cluster Cards")
        iCluster.connect("activate", self.activate)
        return iCluster

    def getDesiredMenu(self):
        return "Plugins"

    def activate(self,oWidget):
        dlg = self.makeDialog()
        dlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()
        name = "Cluster Cards in List"

        self.makePropGroups()

        oDlg = gtk.Dialog(name,parent,
                          gtk.DIALOG_DESTROY_WITH_PARENT)
        oDlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        oDlg.add_button(gtk.STOCK_EXECUTE, gtk.RESPONSE_APPLY)

        oDlg.connect("response", self.handleResponse)

        oNotebook = gtk.Notebook()

        oTableSection = self.makeTableSection()
        oAlgorithmSection = self.makeAlgorithmSection()
        oResultsSection = self.makeResultsSection()

        oNotebook.append_page(oTableSection,gtk.Label('Select Columns'));
        oNotebook.append_page(oAlgorithmSection,gtk.Label('Select Algorithm'));
        oNotebook.append_page(oResultsSection,gtk.Label('Results'));

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

        self._dPropButtons = {}

        for sGroup in aGroups:
            self._dPropButtons[sGroup] = {}
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
                oVbx.pack_start(oBut,False) # pack at top, don't fill space

                self._dPropButtons[sGroup][sName] = oBut

            oNotebook.append_page(oHbx,gtk.Label(sGroup))

        return oNotebook

    def makeAlgorithmSection(self):
        oVbx = gtk.VBox(False,0)

        # Hard coded to SOM for now
        oHeading = gtk.Label()
        oHeading.set_markup("<b>Parameters for SOM Clustering</b>")
        oVbx.pack_start(oHeading,False) # top align

        # Tau
        oTauLabel = gtk.Label("Initial Value of Tau (Neighbourhood function):")
        oTauEntry = gtk.Entry(0)
        oTauHbox = gtk.HBox(False,0)
        oTauHbox.pack_start(oTauLabel,False) # left align
        oTauHbox.pack_end(oTauEntry,False) # right align
        oVbx.pack_start(oTauHbox)

        # Number of iterations
        oNumIterLabel = gtk.Label("Number of Iterations:")
        oNumIterEntry = gtk.Entry(0)
        oNumIterHbox = gtk.HBox(False,0)
        oNumIterHbox.pack_start(oNumIterLabel,False) # left align
        oNumIterHbox.pack_end(oNumIterEntry,False) # right align
        oVbx.pack_start(oNumIterHbox)

        # Distance Measure
        oDistLabel = gtk.Label()
        oDistLabel.set_markup("<b>Distance Measure for SOM Clustering</b>")
        oVbx.pack_start(oDistLabel)

        dDist = { 'e' : 'Euclidean Distance', 'b' : 'City Block Distance',
                  'c' : 'Correlation', 'a' : 'Absolute Value of the Correlation',
                  'u' : 'Uncentered Correlation', 'x' : 'Absolute Value of the Uncentered Correlation',
                  's' : "Spearman's Rank Correlation", 'k' : "Kendall's Tau" }

        oIter = dDist.iteritems()
        for sChr, sName in oIter:
            oFirstBut = gtk.RadioButton(None,sName,False)
            oVbx.pack_start(oFirstBut)
            break

        for sChr, sName in oIter:
            oBut = gtk.RadioButton(oFirstBut,sName)
            oVbx.pack_start(oBut)

        return oVbx

    def makeResultsSection(self):
        oVbx = gtk.VBox(False,0)
        self._oResultsVbox = gtk.VBox(False,0)

        # Results Heading
        oHeading = gtk.Label()
        oHeading.set_markup("<b>Results</b>")
        oVbx.pack_start(oHeading,False) # top align

        # No Results Yet
        oLabel = gtk.Label("No results yet.")
        self._oResultsVbox.pack_start(oLabel)
        oVbx.pack_start(self._oResultsVbox)

        return oVbx

    def populateResults(self,aCards,aColNames,aClusterIds,aCellData):
        self._aCards, self._aColNames, self._aClusterIds, self._aCellData = aCards,aColNames,aClusterIds,aCellData

        # clean results box
        for oChild in self._oResultsVbox.get_children():
            self._oResultsVbox.remove(oChild)

        # Count cards in each cluster
        dClusterCounts = {}
        for i,j in self._aClusterIds:
            dClusterCounts[(i,j)] = dClusterCounts.get((i,j),0) + 1

        # Setup Table
        iNX = len(aCellData)
        iNY = len(aCellData[0])
        iHeaderRows = 1
        iExtraCols = 4

        oTable = gtk.Table(rows=iNX*iNY,columns=len(aColNames)+2)

        # Headings
        oLabel = gtk.Label()
        oLabel.set_markup('<b># Cards</b>')
        oTable.attach(oLabel,3,4,0,1,xpadding=3)

        for k, sColName in enumerate(aColNames):
            oLabel = gtk.Label()
            oLabel.set_markup('<b>%s</b>' % sColName)
            oTable.attach(oLabel,k+iExtraCols,k+iExtraCols+1,0,1,xpadding=3)

        # Data
        self._dDeckMakingButtons = {}
        for i in range(iNX):
            for j in range(iNY):
                iRow = i*iNY+j+iHeaderRows
                oBut = gtk.CheckButton('')
                self._dDeckMakingButtons[(i,j)] = oBut
                oTable.attach(oBut,0,1,iRow,iRow+1)
                oTable.attach(gtk.Label(str(i)),1,2,iRow,iRow+1)
                oTable.attach(gtk.Label(str(j)),2,3,iRow,iRow+1)
                oTable.attach(gtk.Label(str(dClusterCounts.get((i,j),0))),3,4,iRow,iRow+1)
                for k, x in enumerate(aCellData[i][j]):
                    oTable.attach(gtk.Label(str(x)),k+iExtraCols,k+iExtraCols+1,iRow,iRow+1)

        self._oResultsVbox.pack_start(AutoScrolledWindow(oTable,True)) # top align, using viewport to scroll

        oMakeDeckButton = gtk.Button("Make Decks from Selected Clusters")
        oMakeDeckButton.connect("clicked",self.handleMakeDecks)
        self._oResultsVbox.pack_end(oMakeDeckButton,False) # bottom align

        self._oResultsVbox.show_all()

    # Actions

    def handleResponse(self,oDlg,oResponse):
        if oResponse == gtk.RESPONSE_CLOSE:
            oDlg.destroy()
        elif oResponse == gtk.RESPONSE_APPLY:
            self.doClustering()

    def handleMakeDecks(self,oSomeObj):
        for tId, oBut in self._dDeckMakingButtons.iteritems():
            if oBut.get_active():
                self.makeDeckFromCluster(tId)

    def doClustering(self):
        # gather cards
        aCards = list(self.model.getCardIterator(None))

        # gather property functions
        dPropFuncs = {}
        for sGroup, dButtons in self._dPropButtons.iteritems():
            for sName, oBut in dButtons.iteritems():
                if oBut.get_active():
                    dPropFuncs[sGroup + ": " + sName] = self._dGroups[sGroup][sName]

        # sort column names
        aColNames = dPropFuncs.keys()
        aColNames.sort()

        # make tabulator and get table
        oTab = CardListTabulator(aColNames,dPropFuncs)
        aTable = oTab.tabulate(aCards)

        # make date file
        oDatFile = Cluster.DataFile()
        oDatFile.geneid = [oC.id for oC in aCards]
        oDatFile.genename = [IAbstractCard(oC).name.encode('ascii','replace') for oC in aCards]
        oDatFile.expid = [s.encode('ascii','replace') for s in aColNames]
        oDatFile.data = aTable
        oDatFile.mask = None # no data missing
        oDatFile.uniqid = "UNIQID"

        # run SOM clustering on table
        (aClusterIds, aCellData) = oDatFile.somcluster(transpose=0, nxgrid=3, nygrid=3, inittau=0.02, niter=10, dist='e')
        # (aPropClusterIds, aPropCelldata) = oDatFile.somcluster(transpose=1, nxgrid=2, nygrid=1, inittau=0.02, niter=10, dist='e')

        # run K-Means clustering on table
        # (aKmeansClusters, fError, iFound) = oDatFile.kcluster(nclusters=20,npass=10,transpose=0)
        # (aKmeansPropClusters, fError, iFound) = oDatFile.kcluster(nclusters=20,npass=10,transpose=1)

        # write to file (for now)
        # tmp = file("cluster.data","w")
        # for i, cardname in enumerate(oDatFile.genename):
        #     tmp.write("%s | %s %s\n" % (cardname, aClusterIds[i][0], aClusterIds[i][1]))
        # tmp.close()

        # tmp = file("table.data","w")
        # for sCardName, aRow in zip(oDatFile.genename,aTable):
        #    tmp.write(sCardName + " | ")
        #    tmp.write(",".join([str(x) for x in aRow]))
        #    tmp.write("\n")
        # tmp.close()

        self.populateResults(aCards,aColNames,aClusterIds,aCellData)

    def makeDeckFromCluster(self,aClusterId):
        sDeckName = '_cluster_deck_%d_%d' % (aClusterId[0],aClusterId[1])

        # Check Deck Doesn't Exist
        if PhysicalCardSet.selectBy(name=sDeckName).count() != 0:
            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                          gtk.BUTTONS_CLOSE,"Deck %s already exists." % sDeckName)
            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return

        # Create Deck
        oDeck = PhysicalCardSet(name=sDeckName)

        for oCard, aCardCluster in zip(self._aCards,self._aClusterIds):
            if aClusterId[0] == aCardCluster[0] and aClusterId[1] == aCardCluster[1]:
                oDeck.addPhysicalCard(oCard)

plugin = ClusterCardList
