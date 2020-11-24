# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""Display extra columns in the tree view"""

from sqlobject import SQLObjectNotFound

from ...core.BaseTables import PhysicalCard, PhysicalCardSet
from ..CellRendererIcons import DisplayOption
from .BaseExtraColumns import BaseExtraColumns


class BaseExtraCardViewColumns(BaseExtraColumns):
    """Add extra columns to the card list view.

       This handles the very generic cases
       """

    POS_COLUMN_OFFSET = 3  # After count, parent count & card name

    COLUMNS = {
        'Card Type': (100, '_render_card_type', '_get_data_card_type'),
        'Expansions': (600, '_render_expansions', '_get_data_expansions'),
        'Card Text': (100, '_render_card_text', '_get_data_card_text'),
    }

    dTableVersions = {}
    aModelsSupported = (PhysicalCardSet, PhysicalCard)
    dPerPaneConfig = {}

    dCardListConfig = dPerPaneConfig

    @classmethod
    def update_config(cls):
        """Fix the config to use the right keys."""
        cls.fix_config(cls.dPerPaneConfig)
        cls.dCardListConfig = cls.dPerPaneConfig

    def _get_iter_data(self, oIter):
        """For the given iterator, get the associated abstract card"""
        if self.model.iter_depth(oIter) == 1:
            # Only try and lookup things that look like they should be cards
            try:
                oAbsCard = self.model.get_abstract_card_from_iter(oIter)
                return oAbsCard
            except SQLObjectNotFound:
                return None
        else:
            return None

    # pylint: disable=no-self-use
    # Making these functions for clarity
    # several unused paramaters due to function signatures
    # The bGetIcons parameter is needed to avoid icon lookups, etc when
    # sorting
    def _get_data_card_type(self, oCard, bGetIcons=True):
        """Return the card type"""
        if oCard is not None:
            aTypes = [x.name for x in oCard.cardtype]
            aTypes.sort()
            aIcons = []
            if bGetIcons:
                dIcons = self.icon_manager.get_icon_list(oCard.cardtype)
                if dIcons:
                    aIcons = [dIcons[x] for x in aTypes]
                else:
                    aIcons = [None] * len(aTypes)
            return " /|".join(aTypes).split("|"), aIcons
        return [], []

    def _render_card_type(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """display the card type(s)"""
        oCard = self._get_iter_data(oIter)
        aText, aIcons = self._get_data_card_type(oCard, True)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_expansions(self, oCard, bGetIcons=True):
        """get expansion info"""
        if oCard is not None:
            aExp = [oP.expansion.shortname + "(" + oP.rarity.name + ")" for
                    oP in oCard.rarity]
            aExp.sort()
            aIcons = []
            if bGetIcons:
                aIcons = [None] * len(aExp)
            return aExp, aIcons
        return [], []

    def _render_expansions(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """Display expansion info"""
        oCard = self._get_iter_data(oIter)
        aText, aIcons = self._get_data_expansions(oCard)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_card_text(self, oCard, bGetIcons=True):
        """Get the card's card text."""
        if oCard is not None:
            aTexts = [oCard.text.replace("\n", " ")]
            aIcons = []
            if bGetIcons:
                aIcons = [None] * len(aTexts)
            return aTexts, aIcons
        return [], []

    def _render_card_text(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """Display card text in the column"""
        oCard = self._get_iter_data(oIter)
        aTexts, aIcons = self._get_data_card_text(oCard)
        oCell.set_data(aTexts, aIcons, DisplayOption.SHOW_TEXT_ONLY)
