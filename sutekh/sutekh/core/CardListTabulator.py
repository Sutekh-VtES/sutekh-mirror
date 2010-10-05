# CardListTabulator.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Create a table (as a list of list) from a list of cards"""

from sutekh.core.SutekhObjects import Discipline, Clan, Rarity, Expansion, \
        CardType, IAbstractCard


class CardListTabulator(object):
    """Creates a table of cards from a card list.

       Each row of the table corresponds to a card in the list.
       Each column of the table represents a numerical property of the card
       (pool cost, blood cost, discipline levels etc).
       """

    def __init__(self, aColNames, dPropFuncs):
        """Create the Table

           aColNames: Keys from dPropFuncs in the order in which you want the
                      table columns to appear.
           dPropFuncs: Dictionary of functions for finding properties. Keys are
                       strings suitable for use as column headings,
                       values are functions f(oAbstractCard) -> int which
                       return the column value given an abstract card object.
           """
        self._aColNames = aColNames
        self._dPropFuncs = dPropFuncs

    @staticmethod
    def get_default_prop_funcs():
        """Return a dictionary of card property creation functions.

           The keys are strings suitable for use as column names, the values
           are functions for calculating a column entry from an abstract card,
           i.e. f: AbstractCard -> Int.  Since a new dictionary is created
           every time this function is called it's safe to edit it to include
           just the functions you want.

           Notes:
             * For blood, pool and conviction costs, a cost of X is represented
               by a value of -1.
             * Boolean attributes (disciplines, rarities, expansions, clans and
               cardtypes) are represented by values of 0 or 1.
             * Group and capacity are set to 0 if the card doesn't have a group
               or capacity.
           """
        dProps = {}

        # properties from direct attributes of Abstract Cards
        dProps['group'] = lambda card: (card.group is not None and
                card.group) or 0
        dProps['capacity'] = lambda card: (card.capacity is not None and
                card.capacity) or 0
        dProps['pool cost'] = lambda card: (card.costtype == 'pool' and
                card.cost) or 0
        dProps['blood cost'] = lambda card: (card.costtype == 'blood' and
                card.cost) or 0
        dProps['conviction cost'] = lambda card: (card.costtype == 'conviction'
                and card.cost) or 0
        dProps['advanced'] = lambda card: (card.level == 'advanced' and
                1) or 0
        dProps['physical card count'] = lambda card: len(card.physicalCards)

        # The little helper functions below are necessary for scoping reasons.

        # discipline properties
        def make_dis_func(oTmpDis):
            """Create a function that tests for the given discipline."""
            return lambda card: ((oTmpDis in [oPair.discipline for oPair in
                card.discipline]) and 1) or 0

        for oDis in Discipline.select():
            dProps['discipline: ' + oDis.fullname] = make_dis_func(oDis)

        # rarity properties
        def make_rar_func(oTmpRar):
            """Create a function that tests for the given rarity."""
            return lambda card: ((oTmpRar in [oPair.rarity for oPair in
                card.rarity]) and 1) or 0

        for oRar in Rarity.select():
            dProps['rarity: ' + oRar.name] = make_rar_func(oRar)

        # expansion properties
        def make_exp_func(oTmpExp):
            """Create a function that tests for the given expansion."""
            return lambda card: ((oTmpExp in [oPair.expansion for oPair in
                card.rarity]) and 1) or 0

        for oExp in Expansion.select():
            dProps['expansion: ' + oExp.name] = make_exp_func(oExp)

        # clan properties
        def make_clan_func(oTmpClan):
            """Create a function that tests for the given clan"""
            return lambda card: ((oTmpClan in card.clan) and 1) or 0

        for oClan in Clan.select():
            dProps['clan: ' + oClan.name] = make_clan_func(oClan)

        # cardtype properties
        def make_card_type_func(oTmpType):
            """Create a function that tests for the given card type."""
            return lambda card: ((oTmpType in card.cardtype) and 1) or 0

        for oType in CardType.select():
            dProps['card type: ' + oType.name] = make_card_type_func(oType)

        return dProps

    def tabulate(self, aCards):
        """Create a table from the list of (or iterator over) cards.

           Returns the table which is a nested list where each element is a row
           and each row consists of column values.
           The rows are in the same order as the cards in aCards.
           The columns are in the same order as in the aColNames list passed to
           __init__.
           """
        aColFuncs = [self._dPropFuncs[x] for x in self._aColNames]

        aTable = []

        for oCard in aCards:
            oCard = IAbstractCard(oCard)
            aRow = []

            for fProp in aColFuncs:
                aRow.append(fProp(oCard))

            aTable.append(aRow)

        return aTable
