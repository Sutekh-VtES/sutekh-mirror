# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""base plugin for controlling how cards are grouped in the CardListView"""

from ...core.BaseGroupings import (CardTypeGrouping, NullGrouping,
                                   ExpansionGrouping, RarityGrouping,
                                   MultiTypeGrouping, ArtistGrouping,
                                   KeywordGrouping)
from ...core.BaseTables import PhysicalCard, PhysicalCardSet
from ..BasePluginManager import BasePlugin


class BaseGroupBy(BasePlugin):
    """Plugin to allow the user to change how cards are grouped.

       Adds the list of groupings to the profile editor, and all the user
       to choose the groupings of the cards, and changes the setting
       in the CardListView.
       """

    GROUP_BY = "group by"
    dTableVersions = {}
    aModelsSupported = (PhysicalCard, PhysicalCardSet)

    dPerPaneConfig = {}
    dCardListConfig = dPerPaneConfig

    # GROUPINGS should be extended by subclasses
    GROUPINGS = {
        'Card Type': CardTypeGrouping,
        'Multi Card Type': MultiTypeGrouping,
        'Expansion': ExpansionGrouping,
        'Rarity': RarityGrouping,
        'Artist': ArtistGrouping,
        'Keyword': KeywordGrouping,
        'No Grouping': NullGrouping,
    }

    sHelpCategory = 'profile:groupby'

    sMenuName = 'Card Groupings'

    @classmethod
    def get_help_text(cls):
        """Construct the help text for the groupings."""
        aLines = [
            """By default, the cards are grouped into the seperate card \
               types. You can specify the grouping to use as part of the \
               pane profile.""",
            "", "The following groupings are available:", ""]
        for sName in sorted(cls.GROUPINGS):
            cGroup = cls.GROUPINGS[sName]
            aLines.append('* _%s_: %s' % (sName, cGroup.__doc__))
        aLines.append("")
        return '\n'.join(aLines)

    @classmethod
    def get_help_list_text(cls):
        """ToC entry."""
        return "Control how the cards are grouped in the pane."

    @classmethod
    def update_config(cls):
        """Add the correct list of options to the config"""
        sOptions = ", ".join('"%s"' % sKey for sKey in cls.GROUPINGS)
        cls.dPerPaneConfig[cls.GROUP_BY] = ('option(%s, default="Card Type")' %
                                            sOptions)

    def __init__(self, *aArgs, **kwargs):
        super().__init__(*aArgs, **kwargs)
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
