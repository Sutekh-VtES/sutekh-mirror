# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for analysing all expansions and reporting the number of cards
   of each rarity."""

from gi.repository import GObject, Gtk, Pango

from ...core.BaseTables import PhysicalCard, AbstractCard, Expansion
from ...core.BaseAdapters import IExpansion
from ...core.BaseFilters import NullFilter, make_illegal_filter
from ..BasePluginManager import BasePlugin
from ..SutekhDialog import SutekhDialog
from ..AutoScrolledWindow import AutoScrolledWindow
from ...Utility import get_expansion_date


class BaseExpansionStats(BasePlugin):
    """Display card counts and stats for each expansion, rarity grouping.

       A dialog listing cards for each expansion, split by the rarity,
       with a special category for cards only included in the precon decks.
       The cards are grouped by the current grouping used by the WW card
       list view.
       """

    dTableVersions = {Expansion: (4, 5, )}
    aModelsSupported = (PhysicalCard,)

    sMenuName = "Expansion Stats"

    sHelpCategory = "card_list:analysis"

    sHelpText = """This lists some statistics about the different
                   expansions and rarities.

                   For each expansion, this lists the number of cards of each
                   rarity. It also notes which cards are found only in the
                   preconstructed decks for that expansion if needed. For each
                   rarity, the individual cards are list, grouped according
                   to the current grouping of the full card list.

                   Note that this will only include cards not legal for
                   tournament play (such as banned cards or storyline only
                   cards) if the current profile for the full card list shows
                   those cards."""

    # Subclasses should specify this
    GROUPING = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._oStatsVbox = None

    def get_menu_item(self):
        """Register on the 'Analyze' menu"""
        oExpStats = Gtk.MenuItem(label=self.sMenuName)
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
                            Gtk.DialogFlags.DESTROY_WITH_PARENT)

        oDlg.add_button("_Close", Gtk.ResponseType.CLOSE)
        oDlg.connect("response", lambda oW, oR: oDlg.destroy())

        self._oStatsVbox = Gtk.VBox(homogeneous=False, spacing=0)

        oDlg.vbox.pack_start(self._oStatsVbox, True, True, 0)
        oDlg.set_size_request(600, 400)
        oDlg.show_all()

        self.populate_stats_box()

        return oDlg

    def populate_stats_box(self):
        """Create a tree view of stats in self._oStatsVbox."""
        # clean box
        for oChild in self._oStatsVbox.get_children():
            self._oStatsVbox.remove(oChild)

        oView = StatsView(self.model.groupby, self.GROUPING,
                          self.model.hideillegal)

        # top align, using viewport to scroll
        self._oStatsVbox.pack_start(AutoScrolledWindow(oView), True, True, 0)
        self._oStatsVbox.show_all()


class StatsView(Gtk.TreeView):
    # pylint: disable=too-many-public-methods
    # Gtk classes, so we have lots of public methods
    """TreeView used to display expansion stats"""

    def __init__(self, cGrping, cExpRarityGrping, bHideIllegal):
        self._oModel = StatsModel(cGrping, cExpRarityGrping, bHideIllegal)
        self._aLabels = ["Expansion", "Date", "Count"]

        super().__init__(self._oModel)

        oCell = Gtk.CellRendererText()
        oCell.set_property('style', Pango.Style.ITALIC)

        for iCol, sLabel in enumerate(self._aLabels):
            oColumn = Gtk.TreeViewColumn(sLabel, oCell, text=iCol)
            oColumn.set_sort_column_id(iCol)
            self.append_column(oColumn)

        self.set_grid_lines(Gtk.TreeViewGridLine._BOTH)


class StatsModel(Gtk.TreeStore):
    # pylint: disable=too-many-public-methods
    # Gtk classes, so we have lots of public methods
    """TreeStore to hold the data about the expansion statistics"""

    def __init__(self, cGrping, cExpRarityGrping, bHideIllegal):
        super().__init__(GObject.TYPE_STRING, GObject.TYPE_STRING,
                         GObject.TYPE_INT)
        self.cExpRarityGrping = cExpRarityGrping
        self.oLegalFilter = NullFilter()
        if bHideIllegal:
            self.oLegalFilter = make_illegal_filter()
        self.load(cGrping)

    # pylint: disable=too-many-locals, too-many-branches
    # Lots of different cases and loops, so a lot of branches
    # We use lots of local variables for clarity
    # pylint: disable=too-many-nested-blocks, too-many-statements
    # Splitting logic into separate functions doesn't gain us much here
    def load(self, cSubGrping):
        """Populate the contents of the TreeStore"""
        self.clear()

        aCards = self.oLegalFilter.select(AbstractCard)
        oGrouping = self.cExpRarityGrping(aCards)
        aTopLevel = []
        oExpIter = None
        iTotal = 0
        dSeenCards = {}
        for sGroup, oGroupIter in sorted(oGrouping):
            oExp = None
            sDate = 'Unknown Date'
            if sGroup != 'Promo':
                sExp, sRarity = sGroup.split(':')
                oExp = IExpansion(sExp.strip())
                oRelDate = get_expansion_date(oExp)
                if oRelDate:
                    sDate = oRelDate.strftime('%Y-%m-%d')
            else:
                sExp, sRarity = 'Promo', None
                sDate = ''
            if sExp not in aTopLevel:
                dSeenCards[sExp] = set()
                oExpIter = self.append(None)
                self.set(oExpIter, 0, sExp.strip(), 1, sDate)
                aTopLevel.append(sExp)
                iTotal = 0
            aSubCards = list(oGroupIter)
            if sRarity:
                oIter = self.append(oExpIter)
                self.set(oIter, 0, sRarity.strip(), 1, sDate)
                # We don't want to double count cards with multiple
                # rarities in the total
                for oCard in aSubCards:
                    if oCard in dSeenCards[sExp]:
                        continue
                    dSeenCards[sExp].add(oCard)
                    iTotal += 1
                self.set(oExpIter, 2, iTotal)
            else:
                oIter = oExpIter
            self.set(oIter, 2, len(aSubCards))
            oSubGroup = cSubGrping(aSubCards)
            for sInfo, oSubGrpIter in sorted(oSubGroup):
                oChildIter = self.append(oIter)
                if not sInfo:
                    sInfo = "<< None >>"
                self.set(oChildIter, 0, sInfo, 1, sDate,
                         2, len(list(oSubGrpIter)))
                for oCard in sorted(oSubGrpIter, key=lambda x: x.name):
                    oCardIter = self.append(oChildIter)
                    sCard = oCard.name
                    self.set(oCardIter, 0, sCard, 1, sDate, 2, 1)
                    if sGroup == 'Promo':
                        for oPair in oCard.rarity:
                            if not oPair.expansion.name.startswith('Promo-'):
                                continue
                            oExp = oPair.expansion
                            oRelDate = get_expansion_date(oExp)
                            if oRelDate:
                                sDate = oRelDate.strftime('%Y-%m-%d')
                                self.set(oCardIter, 1, sDate)
