# ChangeGroupBy.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Allow the use to change how the cards are grouped in the CardListView"""

from sutekh.core.SutekhObjects import PhysicalCard, PhysicalCardSet
from sutekh.core.Groupings import CardTypeGrouping, ClanGrouping, \
        DisciplineGrouping, ExpansionGrouping, RarityGrouping, \
        CryptLibraryGrouping, NullGrouping, MultiTypeGrouping, \
        SectGrouping, TitleGrouping, CostGrouping, GroupGrouping, \
        ArtistGrouping, KeywordGrouping, GroupPairGrouping, \
        DisciplineLevelGrouping
from sutekh.gui.PluginManager import SutekhPlugin


class GroupCardList(SutekhPlugin):
    """Plugin to allow the user to change how cards are grouped.

       Show a dialog which allows the user to select from the avail
       groupings of the cards, and changes the setting in the CardListView.
       """

    GROUPINGS = {
        'Card Type': CardTypeGrouping,
        'Multi Card Type': MultiTypeGrouping,
        'Crypt or Library': CryptLibraryGrouping,
        'Clans and Creeds': ClanGrouping,
        'Disciplines and Virtues': DisciplineGrouping,
        'Disciplines (by level) and Virtues': DisciplineLevelGrouping,
        'Expansion': ExpansionGrouping,
        'Rarity': RarityGrouping,
        'Sect': SectGrouping,
        'Title': TitleGrouping,
        'Cost': CostGrouping,
        'Group': GroupGrouping,
        'Group pairs': GroupPairGrouping,
        'Artist': ArtistGrouping,
        'Keyword': KeywordGrouping,
        'No Grouping': NullGrouping,
    }

    OPTION_STR = ", ".join('"%s"' % sKey for sKey in GROUPINGS.keys())
    GROUP_BY = "group by"

    dTableVersions = {}
    aModelsSupported = (PhysicalCard, PhysicalCardSet)
    dPerPaneConfig = {
        GROUP_BY: 'option(%s, default="Card Type")' % OPTION_STR,
    }

    dCardListConfig = dPerPaneConfig

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(GroupCardList, self).__init__(*aArgs, **kwargs)
        self._oFirstBut = None  # placeholder for the radio group
        # We don't reload on init, to avoid double loads.
        self.perpane_config_updated(False)

    # Config Update

    def perpane_config_updated(self, bDoReload=True):
        """Called by base class on config updates."""
        # bReload flag so we can call this during __init__
        sGrping = self.get_perpane_item(self.GROUP_BY)
        cGrping = self.GROUPINGS.get(sGrping)
        if cGrping is not None:
            self.set_grouping(cGrping, bDoReload)

    # Actions

    def set_grouping(self, cGrping, bReload=True):
        """Set the grouping to that specified by cGrping."""
        if self.model.groupby != cGrping:
            self.model.groupby = cGrping
            if bReload:
                # Use view.load so we get busy cursor, etc.
                self.view.frame.queue_reload()

plugin = GroupCardList
