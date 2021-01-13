# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Plugin to find clusters in the card lists."""

import random
import math

from gi.repository import Gtk

from sutekh.base.core.BaseTables import PhysicalCard, PhysicalCardSet
from sutekh.base.core.BaseAdapters import IPhysicalCard
from sutekh.base.core.CardSetUtilities import check_cs_exists
from sutekh.base.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.base.gui.SutekhDialog import NotebookDialog, do_complaint_error

from sutekh.core.CardListTabulator import CardListTabulator
from sutekh.gui.PluginManager import SutekhPlugin


class ClusterCardList(SutekhPlugin):
    """Plugin that attempts to find clusters in the card list.

       Allows the user to choose various clustering parameters, such as
       attributes to to use and methods, and then to create card sets
       from the clustering results."""
    # pylint: disable=too-many-instance-attributes
    # we use a lot of attributes to keep track of data & gui aspects

    dTableVersions = {}
    aModelsSupported = (PhysicalCard, PhysicalCardSet)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pylint: disable=invalid-name
        # fMakeCardFromCluster triggers on length, but we like the name
        if not self.model:
            self._fMakeCardSetFromCluster = None
        self._fMakeCardSetFromCluster = self._make_pcs_from_cluster
        self._dPropButtons = {}
        self._dGroups = {}
        self._oResultsVbox = None
        self._aDistanceMeasureGroup = None

        # cluster parameter widgets
        self._oAutoNumClusters = None
        self._oNumClustersSpin = None
        self._oNumIterSpin = None

    def get_menu_item(self):
        """Register on the 'Analyze' menu."""
        oCluster = Gtk.MenuItem(label="Cluster Cards")
        oCluster.connect("activate", self.activate)
        return ('Analyze', oCluster)

    def activate(self, _oWidget):
        """In response to the menu, create the correct dialog."""
        oDlg = self.make_dialog()
        oDlg.run()

    def make_dialog(self):
        """Create the dialog for the clustering options."""
        sDlgName = "Cluster Cards in List"

        self._make_prop_groups()

        oDlg = NotebookDialog(sDlgName, self.parent,
                              Gtk.DialogFlags.DESTROY_WITH_PARENT)
        oDlg.add_button("_Close", Gtk.ResponseType.CLOSE)
        oBut = oDlg.add_button("Execute", Gtk.ResponseType.APPLY)
        oImage = Gtk.Image.new_from_icon_name('system-run',
                                              Gtk.IconSize.BUTTON)
        oBut.set_image(oImage)
        oBut.set_always_show_image(True)

        oDlg.connect("response", self.handle_response)

        oTableSection = self._make_table_section()
        oAlgorithmSection = self._make_algorithm_section()
        oResultsSection = self._make_results_section()

        oDlg.add_widget_page(oTableSection, 'Select Columns')
        oDlg.add_widget_page(oAlgorithmSection, 'Settings')
        oDlg.add_widget_page(oResultsSection, 'Results')

        oDlg.show_all()

        return oDlg

    def _make_prop_groups(self):
        """Extract the list of possible properties to cluster on."""
        dPropFuncs = CardListTabulator.get_default_prop_funcs()
        self._dGroups = {}

        for sName, fProp in dPropFuncs.items():
            aParts = sName.split(":")
            if len(aParts) == 1:
                self._dGroups.setdefault("Miscellaneous",
                                         {})[sName.capitalize()] = fProp
            else:
                sGroup, sRest = (aParts[0].strip().capitalize(),
                                 ":".join(aParts[1:]).strip().capitalize())
                self._dGroups.setdefault(sGroup, {})[sRest] = fProp

    def _make_table_section(self):
        """Create a notebook, and populate the first tabe with a list of
           properties to cluster on."""
        oNotebook = Gtk.Notebook()
        aGroups = sorted(self._dGroups.keys())

        self._dPropButtons = {}

        for sGroup in aGroups:
            self._dPropButtons[sGroup] = {}
            dPropFuncs = self._dGroups[sGroup]

            oHbx = Gtk.HBox(False, 0)

            iCols = 3
            iPropsPerCol = len(dPropFuncs) // iCols
            if len(dPropFuncs) % iCols != 0:
                iPropsPerCol += 1

            aPropNames = sorted(dPropFuncs.keys())

            for iProp, sName in enumerate(aPropNames):
                if iProp % iPropsPerCol == 0:
                    oVbx = Gtk.VBox(homogeneous=False, spacing=0)
                    oHbx.pack_start(oVbx, False, True, 0)

                oBut = Gtk.CheckButton(sName)
                # pack at top, don't expand
                oVbx.pack_start(oBut, False, True, 0)

                self._dPropButtons[sGroup][sName] = oBut

            oNotebook.append_page(oHbx, Gtk.Label(sGroup))

        return oNotebook

    def _make_algorithm_section(self):
        """Populate a tab on the notebook with the parameters and options for
           the clustering algorithm.
           """
        oVbx = Gtk.VBox(homogeneous=False, spacing=0)

        # K-Means is the only clustering solution for the moment
        oHeading = Gtk.Label()
        oHeading.set_markup("<b>Parameters for K-Means Clustering</b>")
        oVbx.pack_start(oHeading, False, False, 5)  # top align

        # Number of iterations
        oNumIterLabel = Gtk.Label(label="Number of Iterations:")
        self._oNumIterSpin = Gtk.SpinButton()
        self._oNumIterSpin.set_range(1, 50)
        self._oNumIterSpin.set_increments(1, 10)
        self._oNumIterSpin.set_value(10)
        oHbox = Gtk.HBox(False, 0)
        oHbox.pack_start(oNumIterLabel, False, True, 0)  # left align
        oHbox.pack_end(self._oNumIterSpin, False, True, 0)  # right align
        oVbx.pack_start(oHbox, False, True, 0)

        # Autoset Num clusters
        self._oAutoNumClusters = Gtk.CheckButton("One cluster per 80 cards")
        oHbox = Gtk.HBox(False, 0)
        oHbox.pack_start(self._oAutoNumClusters, False, True, 0)  # right align
        oVbx.pack_start(oHbox, False, True, 0)

        # Number of clusters
        oNumClustersLabel = Gtk.Label(label="Number of Clusters:")
        self._oNumClustersSpin = Gtk.SpinButton()
        self._oNumClustersSpin.set_range(2, 50)
        self._oNumClustersSpin.set_increments(1, 10)
        self._oNumClustersSpin.set_value(10)
        oHbox = Gtk.HBox(False, 0)
        oHbox.pack_start(oNumClustersLabel, False, True, 0)  # left align
        oHbox.pack_end(self._oNumClustersSpin, False, True, 0)  # right align
        oVbx.pack_start(oHbox, False, True, 0)

        # Connect Autoset and Number of clusters
        self._oAutoNumClusters.set_active(True)
        self._oNumClustersSpin.set_sensitive(False)

        def auto_toggled(oAutoNumClusters):
            """Called when oAutoNumClusters is toggled."""
            if oAutoNumClusters.get_active():
                self._oNumClustersSpin.set_sensitive(False)
            else:
                self._oNumClustersSpin.set_sensitive(True)

        self._oAutoNumClusters.connect("toggled", auto_toggled)

        # Separator
        oVbx.pack_start(Gtk.HSeparator(), False, False, 10)

        # Distance Measure
        oDistLabel = Gtk.Label()
        oDistLabel.set_markup("<b>Distance Measure for Clustering</b>")
        oVbx.pack_start(oDistLabel, False, False, 5)

        oIter = Vector.METRICS.keys()
        for sName in oIter:
            oFirstBut = Gtk.RadioButton(group=None, label=sName)
            oVbx.pack_start(oFirstBut, False, True, 0)
            break

        for sName in oIter:
            oBut = Gtk.RadioButton(group=oFirstBut, label=sName)
            oVbx.pack_start(oBut, False, True, 0)

        self._aDistanceMeasureGroup = oFirstBut.get_group()

        return oVbx

    def _make_results_section(self):
        """Create a widget in the notebook which can be used to display
           the clustering results."""
        oVbx = Gtk.VBox(homogeneous=False, spacing=0)
        self._oResultsVbox = Gtk.VBox(homogeneous=False, spacing=0)

        # Results Heading
        oHeading = Gtk.Label()
        oHeading.set_markup("<b>Results</b>")
        oVbx.pack_start(oHeading, False, True, 0)  # top align

        # No Results Yet
        oLabel = Gtk.Label(label="No results yet.")
        self._oResultsVbox.pack_start(oLabel, False, False, 0)
        oVbx.pack_start(self._oResultsVbox, True, True, 0)

        return oVbx

    # pylint: disable=attribute-defined-outside-init, too-many-locals
    # We create a lot of attributes here, which is OK, because of
    # plugin structure
    # We use lots of local variables for clarity
    def _populate_results(self, aCards, aColNames, aMeans, aClusters):
        """Populate the results tab of the notebook with the results of
           clustering run."""
        self._aCards, self._aColNames, self._aMeans, self._aClusters = \
                aCards, aColNames, aMeans, aClusters

        # clean results box
        for oChild in self._oResultsVbox.get_children():
            self._oResultsVbox.remove(oChild)

        # Setup Table
        iHeaderRows = 1
        iExtraCols = 4

        oTable = Gtk.Table(rows=len(aMeans) + iHeaderRows,
                           columns=iExtraCols)
        oTable.set_row_spacings(0)

        # Headings
        oLabel = Gtk.Label()
        oLabel.set_markup('<b>Save Deck</b>')
        oTable.attach(oLabel, 0, 1, 0, 1, xpadding=3)

        oLabel = Gtk.Label()
        oLabel.set_markup('<b>Cluster Id</b>')
        oTable.attach(oLabel, 1, 2, 0, 1, xpadding=3)

        oLabel = Gtk.Label()
        oLabel.set_markup('<b>No. Cards</b>')
        oTable.attach(oLabel, 2, 3, 0, 1, xpadding=3)

        oLabel = Gtk.Label()
        oLabel.set_markup('<b>Cluster Center</b>')
        oTable.attach(oLabel, 3, 4, 0, 1, xpadding=3)

        # Data
        self._dCardSetMakingButtons = {}
        for iId, oMean in enumerate(self._aMeans):
            iRow = iId + iHeaderRows
            oBut = Gtk.CheckButton()
            self._dCardSetMakingButtons[iId] = oBut
            sCenterText = "\n".join([
                "%s: %.2f" % (sColName, fColVal) for sColName, fColVal
                in zip(aColNames, oMean)
                if abs(fColVal) > 0.01
            ])
            oCenterLabel = Gtk.Label(sCenterText)
            oCenterLabel.set_alignment(0.0, 0.5)

            oTable.attach(oBut, 0, 1, iRow, iRow + 1)
            oTable.attach(Gtk.Label(str(iId)), 1, 2, iRow, iRow + 1)
            oTable.attach(Gtk.Label(str(len(aClusters[iId]))),
                          2, 3, iRow, iRow + 1)
            oTable.attach(oCenterLabel, 3, 4, iRow, iRow + 1)

        # top align, using viewport to scroll
        self._oResultsVbox.pack_start(AutoScrolledWindow(oTable),
                                      True, True, 0)

        oMakeCardSetsButton = Gtk.Button("Make Card Sets from Selected"
                                         " Clusters")
        oMakeCardSetsButton.connect("clicked", self.handle_make_card_sets)
        # bottom align
        self._oResultsVbox.pack_end(oMakeCardSetsButton, False, False, 0)

        self._oResultsVbox.show_all()

    # pylint: enable=attribute-defined-outside-init, too-many-locals

    # Actions

    def handle_response(self, oDlg, oResponse):
        """Handle the user's response to the options dialog."""
        if oResponse == Gtk.ResponseType.CLOSE:
            oDlg.destroy()
        elif oResponse == Gtk.ResponseType.APPLY:
            self.do_clustering()
            # change to results section
            oDlg.notebook.set_current_page(2)

    def handle_make_card_sets(self, _oSomeObj):
        """Create card a suitable card set from the chosen clusters"""
        for iId, oBut in self._dCardSetMakingButtons.items():
            if oBut.get_active():
                self._fMakeCardSetFromCluster(iId)

    @staticmethod
    def k_means_plus_plus(aCards, iNumClust, fDist):
        """Find a set of initial centers using the k-means++ algorithm.

           See http://www.stanford.edu/~darthur/kMeansPlusPlus.pdf.
           """
        aMeans = [random.choice(aCards)]

        while len(aMeans) < iNumClust:
            aDists = []
            for oVec in aCards:
                fMinD = min((fDist(oVec, oMean) for oMean in aMeans)) ** 2
                aDists.append(fMinD)

            fSumSq = sum(aDists)
            fPick = random.uniform(0, fSumSq)

            for iCard, fMinD in enumerate(aDists):
                fPick -= fMinD
                if fPick <= 0:
                    break

            # iCard is defined because k_means doesn't call
            # this unless aCards is non-empty
            # pylint: disable=undefined-loop-variable

            if iCard == len(aCards):
                # guard against slight possibility of being very close
                # to end of fSumSq.
                iCard -= 1

            aMeans.append(aCards[iCard])

        return aMeans

    def k_means(self, aCards, iNumClust, iIterations, fDist):
        """Perform k-means clustering on a list of cards using Lloyd's
           algorithm."""
        if (not aCards) or (not aCards[0]):
            # empty card set or zero-length vectors
            return [], []

        aCards = [Vector(x) for x in aCards]
        aMeans = self.k_means_plus_plus(aCards, iNumClust, fDist)
        iCards = len(aCards)

        # just do a fixed number of interations (no complex stopping condition)
        for _iIter in range(iIterations):
            # empty clusters
            aClusters = []
            for iClust in range(iNumClust):
                aClusters.append([])

            # calculate membership in clusters
            for iCard in range(iCards):
                oVec = aCards[iCard]
                # pylint: disable=cell-var-from-loop
                # Since we use key immediately, this warning isn't
                # an issue
                iVmin = min(range(iNumClust),
                            key=lambda iV: fDist(oVec, aMeans[iV]))
                # pylint: enable=cell-var-from-loop
                aClusters[iVmin].append(iCard)

            # recompute the centroids
            for iClust in range(iNumClust):
                if aClusters[iClust]:
                    aMeans[iClust] = (1.0 / len(aClusters[iClust])) * sum(
                        (aCards[x] for x in aClusters[iClust])
                    )

        return aMeans, aClusters

    def do_clustering(self):
        """Call the chosen clustering algorithm"""
        # gather cards
        aCards = list(self.model.get_card_iterator(None))

        # gather property functions
        dPropFuncs = {}
        for sGroup, dButtons in self._dPropButtons.items():
            for sName, oBut in dButtons.items():
                if oBut.get_active():
                    dPropFuncs[sGroup + ": " + sName] = \
                        self._dGroups[sGroup][sName]

        # sort column names
        aColNames = sorted(dPropFuncs.keys())

        # make tabulator and get table
        oTab = CardListTabulator(aColNames, dPropFuncs)
        aTable = oTab.tabulate(aCards)

        # set k-means parameters
        if self._oAutoNumClusters.get_active():
            iNumClusts = max(4, int(len(aTable) / 80.0) + 1)
        else:
            iNumClusts = max(2, int(self._oNumClustersSpin.get_value()))
        iIterations = max(2, int(self._oNumIterSpin.get_value()))
        for oBut in self._aDistanceMeasureGroup:
            if oBut.get_active():
                sName = oBut.get_label()
                fDist = Vector.METRICS[sName]
                break
        else:
            fDist = Vector.METRICS['Euclidean Distance']

        # aMeans -> list of vectors of cluster centroids
        # aClusters -> list of clusters, each cluster is a list of card indexes

        aMeans, aClusters = self.k_means(aTable, iNumClusts, iIterations,
                                         fDist)

        self._populate_results(aCards, aColNames, aMeans, aClusters)

    def _make_pcs_from_cluster(self, iClusterId):
        """Create a Card Set from the chosen cluster"""
        sDeckName = '_cluster_deck_%d' % (iClusterId,)

        # Check Deck Doesn't Exist
        if check_cs_exists(sDeckName):
            do_complaint_error("Card Set %s already exists." %
                               sDeckName)
            return

        # Create Deck
        oDeck = PhysicalCardSet(name=sDeckName)

        # pylint: disable=no-member
        # SQLObject confuses pylint
        aCards = [IPhysicalCard(self._aCards[x]) for x in
                  self._aClusters[iClusterId]]
        self._commit_cards(oDeck, aCards)
        self._open_cs(sDeckName, True)


class Vector:
    """Really simple class representing a row of card table data."""

    METRICS = {}

    def __init__(self, aData):
        self._aData = aData

    # We do want to access _aData on other Vectors.
    # pylint: disable=protected-access

    def euclidian_distance(self, oVec2):
        """Euclidean distance between two vectors."""
        assert len(self._aData) == len(oVec2._aData)
        fSum = sum(((x - y) ** 2 for (x, y) in zip(self._aData, oVec2._aData)))
        return math.sqrt(fSum)

    METRICS['Euclidean Distance'] = euclidian_distance

    def sutekh_distance(self, oVec2):
        """Like Euclidean distance, but -1 is distance 0.25 to anything
           (including 0 and -1) and 0 is distance 4.0 from anything other
           than 0.
           """
        assert len(self._aData) == len(oVec2._aData)
        fSum = sum((
            ((x == -1 or y == -1) and 0.25) or
            (((x == 0) ^ (y == 0) and 4.0)) or
            (x - y) ** 2 for (x, y) in zip(self._aData, oVec2._aData)
        ))
        return math.sqrt(fSum)

    METRICS['Sutekh Distance'] = sutekh_distance

    # Other possibile metrics:
    #  'City Block Distance',
    #  'Correlation',
    #  'Absolute Value of the Correlation',
    #  'Uncentered Correlation',
    #  'Absolute Value of the Uncentered Correlation',
    #  "Spearman's Rank Correlation"
    #  "Kendall's Tau"

    def __add__(self, oOther):
        """Sum this vector with another."""
        if oOther == 0:
            return self
        assert len(self._aData) == len(oOther._aData)
        return Vector([x + y for (x, y) in zip(self._aData, oOther._aData)])

    def __radd__(self, oOther):
        """Sum this vector with another."""
        if oOther == 0:
            return self
        assert len(self._aData) == len(oOther._aData)
        return Vector([x + y for (x, y) in zip(self._aData, oOther._aData)])

    def __mul__(self, fScale):
        """Multiply this vector by a scalar."""
        fScale = float(fScale)
        return Vector([x * fScale for x in self._aData])

    def __rmul__(self, fScale):
        """Multiply this vector by a scalar."""
        fScale = float(fScale)
        return Vector([x * fScale for x in self._aData])

    def __len__(self):
        """Length of this vector."""
        return len(self._aData)

    def __str__(self):
        """String representation of this vector."""
        return str(self._aData)

    def __iter__(self):
        """Iterator."""
        return iter(self._aData)

plugin = ClusterCardList
