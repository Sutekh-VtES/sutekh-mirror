# ExpansionStats.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for analysing all expansions and reporting the number of cards
   of each rarity."""

import gtk
import pango
import gobject
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCard
from sutekh.core.Groupings import ExpansionRarityGrouping
from sutekh.core.Filters import make_illegal_filter, NullFilter
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow


class ExpansionStats(SutekhPlugin):
    """Display card counts and stats for each expansion, rarity grouping.

       A dialog listing cards for each expansion, split by the rarity,
       with a special category for cards only included in the precon decks.
       The cards are grouped by the current grouping used by the WW card
       list view.
       """

    dTableVersions = {}
    aModelsSupported = (PhysicalCard,)

    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *args, **kwargs):
        super(ExpansionStats, self).__init__(*args, **kwargs)
        self._oStatsVbox = None

    def get_menu_item(self):
        """Register on the 'Analyze' menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oExpStats = gtk.MenuItem("Expansion Stats")
        oExpStats.connect("activate", self.activate)
        return ('Analyze', oExpStats)

    def activate(self, _oWidget):
        """Handle response from menu"""
        oDlg = self.make_dialog()
        oDlg.run()
        self._oStatsVbox = None

    def make_dialog(self):
        """Create the dialog to display the statistics"""
        oDlg = SutekhDialog("Expansion Statistics", self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT)

        oDlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        oDlg.connect("response", lambda oW, oR: oDlg.destroy())

        self._oStatsVbox = gtk.VBox(False, 0)

        # pylint: disable-msg=E1101
        # vbox methods not seen
        oDlg.vbox.pack_start(self._oStatsVbox)
        oDlg.set_size_request(600, 400)
        oDlg.show_all()

        self.populate_stats_box()

        return oDlg

    def populate_stats_box(self):
        """Create a tree view of stats in self._oStatsVbox."""
        # clean box
        for oChild in self._oStatsVbox.get_children():
            self._oStatsVbox.remove(oChild)

        oView = StatsView(self.model.groupby, self.model.hideillegal)

        # top align, using viewport to scroll
        self._oStatsVbox.pack_start(AutoScrolledWindow(oView, True))
        self._oStatsVbox.show_all()


class StatsView(gtk.TreeView):
    # pylint: disable-msg=R0904
    # gtk classes, so we have lots of public methods
    """TreeView used to display expansion stats"""

    def __init__(self, cGrping, bHideIllegal):
        self._oModel = StatsModel(cGrping, bHideIllegal)
        self._aLabels = ["Expansion", "Count"]

        super(StatsView, self).__init__(self._oModel)

        oCell = gtk.CellRendererText()
        oCell.set_property('style', pango.STYLE_ITALIC)

        for iCol, sLabel in enumerate(self._aLabels):
            oColumn = gtk.TreeViewColumn(sLabel, oCell, text=iCol)
            oColumn.set_sort_column_id(iCol)
            self.append_column(oColumn)

        self.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)


class StatsModel(gtk.TreeStore):
    # pylint: disable-msg=R0904
    # gtk classes, so we have lots of public methods
    """TreeStore to hold the data about the expansion statistics"""

    def __init__(self, cGrping, bHideIllegal):
        # pylint: disable-msg=W0142
        # We need the * magic here
        super(StatsModel, self).__init__(gobject.TYPE_STRING,
                gobject.TYPE_INT)
        self.oLegalFilter = NullFilter()
        if bHideIllegal:
            self.oLegalFilter = make_illegal_filter()
        self.load(cGrping)

    # pylint: disable-msg=R0914
    # R0914: We use lots of local variables for clarity
    def load(self, cSubGrping):
        """Populate the contents of the TreeStore"""
        self.clear()

        aCards = self.oLegalFilter.select(AbstractCard)
        oGrouping = ExpansionRarityGrouping(aCards)
        aTopLevel = []
        oExpIter = None
        iTotal = 0
        for sGroup, oGroupIter in sorted(oGrouping):
            if sGroup != 'Promo':
                sExp, sRarity = sGroup.split(':')
            else:
                sExp, sRarity = 'Promo', None
            if sExp not in aTopLevel:
                oExpIter = self.append(None)
                self.set(oExpIter, 0, sExp.strip())
                aTopLevel.append(sExp)
                iTotal = 0
            aSubCards = list(oGroupIter)
            if sRarity:
                oIter = self.append(oExpIter)
                self.set(oIter, 0, sRarity.strip())
                if sRarity.strip() != 'Precon Only':
                    iTotal += len(aSubCards)
                    self.set(oExpIter, 1, iTotal)
            else:
                oIter = oExpIter
            self.set(oIter, 1, len(aSubCards))
            oSubGroup = cSubGrping(aSubCards)
            for sInfo, oSubGrpIter in sorted(oSubGroup):
                oChildIter = self.append(oIter)
                if not sInfo:
                    sInfo = "<< None >>"
                self.set(oChildIter, 0, sInfo, 1, len(list(oSubGrpIter)))
                for sCard in sorted([x.name for x in oSubGrpIter]):
                    oCardIter = self.append(oChildIter)
                    self.set(oCardIter, 0, sCard, 1, 1)

plugin = ExpansionStats
