# ClusterCardList.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Plugin to find clusters in the card lists."""

import gtk
import random
import math
from sutekh.core.SutekhObjects import PhysicalCard, \
                                      PhysicalCardSet, \
                                      IPhysicalCard
from sutekh.core.CardListTabulator import CardListTabulator
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error

class ClusterCardList(CardListPlugin):
    """Plugin that attempts to find clusters in the card list.

       Allows the user to choose various clustering parameters, such as
       attributes to to use and methods, and then to create card sets
       from the clustering results."""

    dTableVersions = {}
    aModelsSupported = [PhysicalCard, PhysicalCardSet]

    # pylint: disable-msg=W0142
    # ** magic OK
    def __init__(self, *aArgs, **kwargs):
        super(ClusterCardList, self).__init__(*aArgs, **kwargs)
        # pylint: disable-msg=C0103
        # fMakeCardFromCluster triggers on length, but we like the name
        if not self.model:
            self._fMakeCardSetFromCluster = None
        self._fMakeCardSetFromCluster = self.make_pcs_from_cluster
        self._dPropButtons = {}
        self._dGroups = {}
        self._oResultsVbox = None

    # pylint: enable-msg=W0142

    def get_menu_item(self):
        """Register on the 'Plugins' menu."""
        if not self.check_versions() or not self.check_model_type():
            return None
        oCluster = gtk.MenuItem("Cluster Cards")
        oCluster.connect("activate", self.activate)
        return ('Plugins', oCluster)

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def activate(self, oWidget):
        """In response to the menu, create the correct dialog."""
        oDlg = self.make_dialog()
        oDlg.run()

    def make_dialog(self):
        """Create the dialog for the clustering options."""
        sDlgName = "Cluster Cards in List"

        self.make_prop_groups()

        oDlg = SutekhDialog(sDlgName, self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT)
        oDlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        oDlg.add_button(gtk.STOCK_EXECUTE, gtk.RESPONSE_APPLY)

        oDlg.connect("response", self.handle_response)

        oNotebook = gtk.Notebook()

        oTableSection = self.make_table_section()
        # TODO: put algorithm parameters back in
        # oAlgorithmSection = self.make_algorithm_section()
        oResultsSection = self.make_results_section()

        oNotebook.append_page(oTableSection, gtk.Label('Select Columns'))
        # oNotebook.append_page(oAlgorithmSection, gtk.Label('Select Algorithm'))
        oNotebook.append_page(oResultsSection, gtk.Label('Results'))

        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oDlg.vbox.pack_start(oNotebook)
        oDlg.show_all()

        return oDlg

    def make_prop_groups(self):
        """Extract the list of possible properties to cluster on."""
        dPropFuncs = CardListTabulator.get_default_prop_funcs()
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

    def make_table_section(self):
        """Create a notebook, and populate the first tabe with a list of
           properties to cluster on."""
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

    def make_algorithm_section(self):
        """Populate a tab on the notebook with the different algorithm
           choices"""
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

        oIter = dDist.itervalues()
        for sName in oIter:
            oFirstBut = gtk.RadioButton(None, sName, False)
            oVbx.pack_start(oFirstBut)
            break

        for sName in oIter:
            oBut = gtk.RadioButton(oFirstBut, sName)
            oVbx.pack_start(oBut)

        return oVbx

    def make_results_section(self):
        """Create a widget in the notebook which can be used to display
           the clustering results."""
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
    def populate_results(self, aCards, aColNames, aMeans, aClusters):
        """Populate the results tab of the notebook with the results of
           clustering run."""
        self._aCards, self._aColNames, self._aMeans, self._aClusters = \
                aCards, aColNames, aMeans, aClusters

        # clean results box
        for oChild in self._oResultsVbox.get_children():
            self._oResultsVbox.remove(oChild)

        # Setup Table
        iNX = len(aMeans) # number of clusters
        iNY = len(aMeans[0]) # number of columns / properties
        iHeaderRows = 1
        iExtraCols = 4

        oTable = gtk.Table(rows=iNX * iNY, columns=len(aColNames) + 2)

        # Headings
        oLabel = gtk.Label()
        oLabel.set_markup('<b># Cards</b>')
        oTable.attach(oLabel, 3, 4, 0, 1, xpadding=3)

        for iColNum, sColName in enumerate(aColNames):
            oLabel = gtk.Label()
            oLabel.set_markup('<b>%s</b>' % sColName)
            oTable.attach(oLabel, iColNum + iExtraCols,
                    iColNum + iExtraCols + 1, 0, 1, xpadding=3)

        # Data
        self._dCardSetMakingButtons = {}
        for iId, oM in enumerate(self._aMeans):
            iRow = iId + iHeaderRows
            oBut = gtk.CheckButton('')
            self._dCardSetMakingButtons[iId] = oBut
            oTable.attach(oBut, 0, 1, iRow, iRow + 1)
            oTable.attach(gtk.Label(str(iId)), 1, 2, iRow, iRow + 1)
            # oTable.attach(gtk.Label(str(iId)), 2, 3, iRow, iRow + 1)
            oTable.attach(gtk.Label(str(len(oM))), 3, 4, iRow, iRow + 1)
            for iColNum, sText in enumerate(oM):
                oTable.attach(gtk.Label(str(sText)), iColNum + iExtraCols,
                        iColNum + iExtraCols + 1, iRow, iRow + 1)

        # top align, using viewport to scroll
        self._oResultsVbox.pack_start(AutoScrolledWindow(oTable, True))

        oMakeCardSetsButton = gtk.Button("Make Card Sets from Selected"
                " Clusters")
        oMakeCardSetsButton.connect("clicked", self.handle_make_card_sets)
        self._oResultsVbox.pack_end(oMakeCardSetsButton, False) # bottom align

        self._oResultsVbox.show_all()

    # pylint: enable-msg=W0201

    # Actions

    def handle_response(self, oDlg, oResponse):
        """Handle the user's response to the options dialog."""
        if oResponse == gtk.RESPONSE_CLOSE:
            oDlg.destroy()
        elif oResponse == gtk.RESPONSE_APPLY:
            self.do_clustering()

    # oSomeObj required by function signature
    def handle_make_card_sets(self, oSomeObj):
        """Create card a suitable card set from the chosen clusters"""
        for iId, oBut in self._dCardSetMakingButtons.iteritems():
            if oBut.get_active():
                self._fMakeCardSetFromCluster(iId)

    # pylint: enable-msg=W0613

    def k_means_plus_plus(self, aCards, iK):
        """Find a set of initial centers using the k-means++ algorithm.

           See http://www.stanford.edu/~darthur/kMeansPlusPlus.pdf.
           """
        aM = [ random.choice(aCards) ]

        while len(aM) < iK:
            aDists = []
            for oV in aCards:
                fMinD = min((oV.dist(oM) for oM in aM))**2
                aDists.append(fMinD)

            fSumSq = sum(aDists)
            fPick = random.uniform(0, fSumSq)

            for i, fMinD in enumerate(aDists):
                fPick -= fMinD
                if fPick <= 0:
                    break

            if i == len(aCards):
                # guard against slight possibility of being very close
                # to end of fSumSq.
                i -= 1

            aM.append(aCards[i])

        return aM

    def k_means(self, aCards, iK):
        """Perform k-means clustering on a list of cards using Lloyd's
           algorithm."""
        aCards = [Vector(x) for x in aCards]
        aM = self.k_means_plus_plus(aCards, iK)
        iN = len(aCards)
        fInvK = 1.0 / iK

        # just do 10 interations (no complex stopping condition)
        for j in range(10):
            # empty clusters
            aW = []
            for i in xrange(iK):
                aW.append([])

            # calculate membership in clusters
            for i in xrange(iN):
                fDist = aCards[i].dist
                iVmin = min(xrange(iK), key=lambda iV: fDist(aM[iV]))
                aW[iVmin].append(i)

            # recompute the centroids
            for i in xrange(iK):
                if aW[i]:
                    aM[i] = fInvK * sum((aCards[x] for x in aW[i]))

        return aM, aW

    def do_clustering(self):
        """Call the chosen clustering algorithm"""
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

        # aMeans -> list of vectors of cluster centroids
        # aClusters -> list of clusters, each cluster is a list of card indexes
        iK = max(4, len(aTable) / 80.0)
        aMeans, aClusters = self.k_means(aTable, iK)

        self.populate_results(aCards, aColNames, aMeans, aClusters)

    def make_pcs_from_cluster(self, iClusterId):
        """Create a Card Set from the chosen cluster"""
        sDeckName = '_cluster_deck_%d' % (iClusterId,)

        # Check Deck Doesn't Exist
        if PhysicalCardSet.selectBy(name=sDeckName).count() != 0:
            do_complaint_error("Card Set %s already exists." %
                    sDeckName)
            return

        # Create Deck
        oDeck = PhysicalCardSet(name=sDeckName)

        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        for iIndex in self._aClusters[iClusterId]:
            oC = IPhysicalCard(self._aCards[iIndex])
            oDeck.addPhysicalCard(oC)

        self.open_cs(sDeckName)


class Vector(object):
    """Really simple class representing a row of card table data."""

    def __init__(self, data):
        self._data = data

    def dist(self, other):
        """Distance between this vector and another."""
        assert len(self._data) == len(other._data)
        fS = sum(((x-y)**2 for (x, y) in zip(self._data, other._data)))
        return math.sqrt(fS)

    def __add__(self, other):
        """Sum this vector with another."""
        if other == 0:
            return self
        assert len(self._data) == len(other._data)
        return Vector([ x+y for (x, y) in zip(self._data, other._data)])

    def __radd__(self, other):
        """Sum this vector with another."""
        if other == 0:
            return self
        assert len(self._data) == len(other._data)
        return Vector([ x+y for (x, y) in zip(self._data, other._data)])

    def __mul__(self, fS):
        """Multiply this vector by a scalar."""
        fS = float(fS)
        return Vector([x*fS for x in self._data])

    def __rmul__(self, fS):
        """Multiply this vector by a scalar."""
        fS = float(fS)
        return Vector([x*fS for x in self._data])

    def __len__(self):
        """Length of this vector."""
        return len(self._data)

    def __str__(self):
        """String representation of this vector."""
        return str(self._data)

    def __iter__(self):
        """Iterator."""
        return iter(self._data)

# pylint: disable-msg=C0103
# accept plugin name
plugin = ClusterCardList
