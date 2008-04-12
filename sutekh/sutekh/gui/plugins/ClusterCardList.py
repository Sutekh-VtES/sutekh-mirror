# ClusterCardList.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Plugin to find clusters in the card lists."""

import gtk
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCard, \
                                      AbstractCardSet, PhysicalCardSet, \
                                      IAbstractCard
from sutekh.core.CardListTabulator import CardListTabulator
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error

# find a cluster module
# Bio.Cluster needs a fromlist to do the right thing
for module, aFromlist in [('Pycluster', None), ('Bio.Cluster', ['Cluster'])]:
    # pylint: disable-msg=W0704
    # we loop over options, so ignoring error is correct
    try:
        Cluster = __import__(module, None, None, aFromlist)
        break
    except ImportError:
        pass
else:
    raise ImportError("Could not find PyCluster or Bio.Cluster. Not loading"
            " clustering plugin.")

class ClusterCardList(CardListPlugin):
    dTableVersions = {}
    aModelsSupported = [AbstractCard, PhysicalCard, PhysicalCardSet,
            AbstractCardSet]

    # pylint: disable-msg=W0142
    # ** magic OK
    def __init__(self, *aArgs, **kwargs):
        super(ClusterCardList, self).__init__(*aArgs, **kwargs)
        if not self.model:
            self._fMakeCardSetFromClusterCluster = None
        elif self.model.cardclass is PhysicalCard:
            self._fMakeCardSetFromClusterCluster = self.make_pcs_from_cluster
        else:
            self._fMakeCardSetFromClusterCluster = self.make_acs_from_cluster

    # pylint: enable-msg=W0142

    def get_menu_item(self):
        """Register on the 'Plugins' menu."""
        if not self.check_versions() or not self.check_model_type():
            return None
        oCluster = gtk.MenuItem("Cluster Cards")
        oCluster.connect("activate", self.activate)
        return ('Plugins', oCluster)

    def activate(self, oWidget):
        """In response to the menu, create the correct dialog."""
        oDlg = self.make_dialog()
        oDlg.run()

    def make_dialog(self):
        """Create the dialog for the clustering options."""
        sDlgName = "Cluster Cards in List"

        self.makePropGroups()

        oDlg = SutekhDialog(sDlgName, self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT)
        oDlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        oDlg.add_button(gtk.STOCK_EXECUTE, gtk.RESPONSE_APPLY)

        oDlg.connect("response", self.handle_response)

        oNotebook = gtk.Notebook()

        oTableSection = self.makeTableSection()
        oAlgorithmSection = self.makeAlgorithmSection()
        oResultsSection = self.makeResultsSection()

        oNotebook.append_page(oTableSection, gtk.Label('Select Columns'))
        oNotebook.append_page(oAlgorithmSection, gtk.Label('Select Algorithm'))
        oNotebook.append_page(oResultsSection, gtk.Label('Results'))

        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oDlg.vbox.pack_start(oNotebook)
        oDlg.show_all()

        return oDlg

    def makePropGroups(self):
        dPropFuncs = CardListTabulator.getDefaultPropFuncs()
        self._dGroups = {}

        for sName, fProp in dPropFuncs.iteritems():
            aParts = sName.split(":")
            if len(aParts) == 1:
                self._dGroups.setdefault("Miscellaneous",
                        {})[sName.capitalize()] = fProp
            else:
                sGroup, sRest = aParts[0].strip().capitalize(), \
                        ":".join(aParts[1:]).strip().capitalize()
                self._dGroups.setdefault(sGroup, {})[sRest] = fProp

    def makeTableSection(self):
        oNotebook = gtk.Notebook()
        aGroups = self._dGroups.keys()
        aGroups.sort()

        self._dPropButtons = {}

        for sGroup in aGroups:
            self._dPropButtons[sGroup] = {}
            dPropFuncs = self._dGroups[sGroup]

            oHbx = gtk.HBox(False, 0)

            iCols = 3
            iPropsPerCol = len(dPropFuncs) / iCols
            if len(dPropFuncs) % iCols != 0:
                iPropsPerCol += 1

            aPropNames = dPropFuncs.keys()
            aPropNames.sort()

            for iProp, sName in enumerate(aPropNames):
                if iProp % iPropsPerCol == 0:
                    oVbx = gtk.VBox(False, 0)
                    oHbx.pack_start(oVbx)

                oBut = gtk.CheckButton(sName)
                oVbx.pack_start(oBut, False) # pack at top, don't fill space

                self._dPropButtons[sGroup][sName] = oBut

            oNotebook.append_page(oHbx, gtk.Label(sGroup))

        return oNotebook

    def makeAlgorithmSection(self):
        oVbx = gtk.VBox(False, 0)

        # Hard coded to SOM for now
        oHeading = gtk.Label()
        oHeading.set_markup("<b>Parameters for SOM Clustering</b>")
        oVbx.pack_start(oHeading, False) # top align

        # Tau
        oTauLabel = gtk.Label("Initial Value of Tau (Neighbourhood function):")
        oTauEntry = gtk.Entry(0)
        oTauHbox = gtk.HBox(False, 0)
        oTauHbox.pack_start(oTauLabel, False) # left align
        oTauHbox.pack_end(oTauEntry, False) # right align
        oVbx.pack_start(oTauHbox)

        # Number of iterations
        oNumIterLabel = gtk.Label("Number of Iterations:")
        oNumIterEntry = gtk.Entry(0)
        oNumIterHbox = gtk.HBox(False, 0)
        oNumIterHbox.pack_start(oNumIterLabel, False) # left align
        oNumIterHbox.pack_end(oNumIterEntry, False) # right align
        oVbx.pack_start(oNumIterHbox)

        # Distance Measure
        oDistLabel = gtk.Label()
        oDistLabel.set_markup("<b>Distance Measure for SOM Clustering</b>")
        oVbx.pack_start(oDistLabel)

        dDist = { 'e' : 'Euclidean Distance', 'b' : 'City Block Distance',
                  'c' : 'Correlation',
                  'a' : 'Absolute Value of the Correlation',
                  'u' : 'Uncentered Correlation',
                  'x' : 'Absolute Value of the Uncentered Correlation',
                  's' : "Spearman's Rank Correlation", 'k' : "Kendall's Tau" }

        oIter = dDist.iteritems()
        for sChr, sName in oIter:
            oFirstBut = gtk.RadioButton(None, sName, False)
            oVbx.pack_start(oFirstBut)
            break

        for sChr, sName in oIter:
            oBut = gtk.RadioButton(oFirstBut, sName)
            oVbx.pack_start(oBut)

        return oVbx

    def makeResultsSection(self):
        oVbx = gtk.VBox(False, 0)
        self._oResultsVbox = gtk.VBox(False, 0)

        # Results Heading
        oHeading = gtk.Label()
        oHeading.set_markup("<b>Results</b>")
        oVbx.pack_start(oHeading, False) # top align

        # No Results Yet
        oLabel = gtk.Label("No results yet.")
        self._oResultsVbox.pack_start(oLabel)
        oVbx.pack_start(self._oResultsVbox)

        return oVbx

    # pylint: disable-msg=W0201
    # We create a lot of attributes here, which is OK, because of plugin
    # structure
    def populateResults(self, aCards, aColNames, aClusterIds, aCellData):
        self._aCards, self._aColNames, self._aClusterIds, self._aCellData = \
                aCards, aColNames, aClusterIds, aCellData

        # clean results box
        for oChild in self._oResultsVbox.get_children():
            self._oResultsVbox.remove(oChild)

        # Count cards in each cluster
        dClusterCounts = {}
        for i, j in self._aClusterIds:
            dClusterCounts[(i, j)] = dClusterCounts.get((i, j), 0) + 1

        # Setup Table
        iNX = len(aCellData)
        iNY = len(aCellData[0])
        iHeaderRows = 1
        iExtraCols = 4

        oTable = gtk.Table(rows=iNX * iNY, columns=len(aColNames) + 2)

        # Headings
        oLabel = gtk.Label()
        oLabel.set_markup('<b># Cards</b>')
        oTable.attach(oLabel, 3, 4, 0, 1, xpadding=3)

        for k, sColName in enumerate(aColNames):
            oLabel = gtk.Label()
            oLabel.set_markup('<b>%s</b>' % sColName)
            oTable.attach(oLabel, k + iExtraCols, k + iExtraCols + 1, 0, 1,
                    xpadding=3)

        # Data
        self._dCardSetMakingButtons = {}
        for i in range(iNX):
            for j in range(iNY):
                iRow = i * iNY + j + iHeaderRows
                oBut = gtk.CheckButton('')
                self._dCardSetMakingButtons[(i, j)] = oBut
                oTable.attach(oBut, 0, 1, iRow, iRow + 1)
                oTable.attach(gtk.Label(str(i)), 1, 2, iRow, iRow + 1)
                oTable.attach(gtk.Label(str(j)), 2, 3, iRow, iRow + 1)
                oTable.attach(gtk.Label(str(dClusterCounts.get((i, j), 0))), 3,
                        4, iRow, iRow + 1)
                for k, x in enumerate(aCellData[i][j]):
                    oTable.attach(gtk.Label(str(x)), k + iExtraCols,
                            k + iExtraCols + 1, iRow, iRow + 1)

        # top align, using viewport to scroll
        self._oResultsVbox.pack_start(AutoScrolledWindow(oTable, True))

        oMakeCardSetsButton = gtk.Button("Make Card Sets from Selected"
                " Clusters")
        oMakeCardSetsButton.connect("clicked", self.handleMakeCardSets)
        self._oResultsVbox.pack_end(oMakeCardSetsButton, False) # bottom align

        self._oResultsVbox.show_all()

    # pylint: enable-msg=W0201

    # Actions

    def handle_response(self, oDlg, oResponse):
        """Handle the user's response to the options dialog."""
        if oResponse == gtk.RESPONSE_CLOSE:
            oDlg.destroy()
        elif oResponse == gtk.RESPONSE_APPLY:
            self.doClustering()

    def handleMakeCardSets(self, oSomeObj):
        for tId, oBut in self._dCardSetMakingButtons.iteritems():
            if oBut.get_active():
                self._fMakeCardSetFromClusterCluster(tId)

    def doClustering(self):
        # gather cards
        aCards = list(self.model.get_card_iterator(None))

        # gather property functions
        dPropFuncs = {}
        for sGroup, dButtons in self._dPropButtons.iteritems():
            for sName, oBut in dButtons.iteritems():
                if oBut.get_active():
                    dPropFuncs[sGroup + ": " + sName] = \
                            self._dGroups[sGroup][sName]

        # sort column names
        aColNames = dPropFuncs.keys()
        aColNames.sort()

        # make tabulator and get table
        oTab = CardListTabulator(aColNames, dPropFuncs)
        aTable = oTab.tabulate(aCards)

        # make data file
        # pylint: disable-msg=E1101
        # IAbstractCard confuses pylint
        oDatFile = Cluster.DataFile()
        oDatFile.geneid = [oC.id for oC in aCards]
        oDatFile.genename = [IAbstractCard(oC).name.encode('ascii', 'replace')
                for oC in aCards]
        oDatFile.expid = [s.encode('ascii', 'replace') for s in aColNames]
        oDatFile.data = aTable
        oDatFile.mask = None # no data missing
        oDatFile.uniqid = "UNIQID"

        # run SOM clustering on table
        (aClusterIds, aCellData) = oDatFile.somcluster(transpose=0, nxgrid=3,
                nygrid=3, inittau=0.02, niter=10, dist='e')
        # (aPropClusterIds, aPropCelldata) = oDatFile.somcluster(transpose=1,
        #         nxgrid=2, nygrid=1, inittau=0.02, niter=10, dist='e')
        #
        # run K-Means clustering on table
        # (aKmeansClusters, fError, iFound) = oDatFile.kcluster(nclusters=20,
        #         npass=10, transpose=0)
        # (aKmeansPropClusters, fError, iFound) = oDatFile.kcluster(
        #         nclusters=20, npass=10, transpose=1)
        #
        # write to file (for now)
        # tmp = file("cluster.data", "w")
        # for i, cardname in enumerate(oDatFile.genename):
        #     tmp.write("%s | %s %s\n" % (cardname, aClusterIds[i][0],
        #             aClusterIds[i][1]))
        # tmp.close()

        # tmp = file("table.data", "w")
        # for sCardName, aRow in zip(oDatFile.genename, aTable):
        #    tmp.write(sCardName + " | ")
        #    tmp.write(",".join([str(x) for x in aRow]))
        #    tmp.write("\n")
        # tmp.close()

        self.populateResults(aCards, aColNames, aClusterIds, aCellData)

    def make_pcs_from_cluster(self, aClusterId):
        """Create a Physical Card Set from the chosen cluster"""
        sDeckName = '_cluster_deck_%d_%d' % (aClusterId[0], aClusterId[1])

        # Check Deck Doesn't Exist
        if PhysicalCardSet.selectBy(name=sDeckName).count() != 0:
            do_complaint_error("Physical Card Set %s already exists." %
                    sDeckName)
            return

        # Create Deck
        oDeck = PhysicalCardSet(name=sDeckName)

        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        for oCard, aCardCluster in zip(self._aCards, self._aClusterIds):
            if aClusterId[0] == aCardCluster[0] and \
                    aClusterId[1] == aCardCluster[1]:
                oDeck.addPhysicalCard(oCard)

        self.open_pcs(sDeckName)

    def make_acs_from_cluster(self, aClusterId):
        """Create a Abstract Card Set from the chosen cluster"""
        sACSName = '_cluster_acs_%d_%d' % (aClusterId[0], aClusterId[1])

        # Check ACS Doesn't Exist
        if AbstractCardSet.selectBy(name=sACSName).count() != 0:
            do_complaint_error("Abstract Card Set %s already exists." %
                    sACSName)
            return

        # Create ACS
        oACS = AbstractCardSet(name=sACSName)

        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        for oCard, aCardCluster in zip(self._aCards, self._aClusterIds):
            oCard = IAbstractCard(oCard)
            if aClusterId[0] == aCardCluster[0] and \
                    aClusterId[1] == aCardCluster[1]:
                oACS.addAbstractCard(oCard)

        self.open_acs(sACSName)

# pylint: disable-msg=C0103
# accept plugin name
plugin = ClusterCardList
