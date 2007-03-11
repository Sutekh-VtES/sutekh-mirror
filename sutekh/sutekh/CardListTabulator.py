# CardListTabulator.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from SutekhObjects import *

class CardListTabulator(object):
    """
    Creates a table of cards from a card list.
    Each row of the table corresponds to a card in the list.   
    Each column of the table represents a numerical property of the card (pool cost, blood cost, discipline levels etc).
    """

    def __init__(self,aColNames,dPropFuncs):
        """
        aColNames: Keys from dPropFuncs in the order in which you want the table columns to appear.
        dPropFuncs: Dictionary of functions for finding properties. Keys are strings suitable for use as column headings,
                    values are functions f(oAbstractCard) -> int which return the column value given an abstract card object.
        """
        self._aColNames = aColNames
        self._dPropFuncs = dPropFuncs

    @staticmethod
    def getDefaultPropFuncs():
        """
        Return a dictionary of card property creation functions.
        The keys are strings suitable for use as column names, the values are functions for calculating a column entry
        from an abstract card, i.e. f: AbstractCard -> Int.
        Since a new dictionary is created every time this function is called it's safe to edit it to include just
        the functions you want.

        Notes:        
         * For blood, pool and conviction costs, a cost of X is represented by a value of -1.
         * Boolean attributes (disciplines, rarities, expansions, clans and cardtypes) are represented by values of 0 or 1.
         * Group and capacity are set to 0 if the card doesn't have a group or capacity.
        """
        d = {}

        # properties from direct attributes of Abstract Cards
        d['group'] = lambda card: (card.group is not None and card.group) or 0
        d['capacity'] = lambda card: (card.capacity is not None and card.capacity) or 0
        d['pool cost'] = lambda card: (card.costtype == 'pool' and card.cost) or 0
        d['blood cost'] = lambda card: (card.costtype == 'blood' and card.cost) or 0
        d['conviction cost'] = lambda card: (card.costtype == 'conviction' and card.cost) or 0
        d['advanced'] = lambda card: (card.level == 'advanced' and 1) or 0
        d['physical card count'] = lambda card: len(card.physicalCards)

        # The little helper functions below are necessary for scoping reasons.

        # discipline properties
        def makeDisFunc(oTmpDis):
            return lambda card: ((oTmpDis in [oPair.discipline for oPair in card.discipline]) and 1) or 0

        for oDis in Discipline.select():
            sName = DisciplineAdapter.keys[oDis.name][-1]
            d['discipline: ' + sName] = makeDisFunc(oDis)

        # rarity properties
        def makeRarFunc(oTmpRar):
            return lambda card: ((oTmpRar in [oPair.rarity for oPair in card.rarity]) and 1) or 0

        for oRar in Rarity.select():
            d['rarity: ' + oRar.name] = makeRarFunc(oRar)

        # expansion properties
        def makeExpFunc(oTmpExp):
            return lambda card: ((oTmpExp in [oPair.expansion for oPair in card.rarity]) and 1) or 0

        for oExp in Expansion.select():
            d['expansion: ' + oExp.name] = makeExpFunc(oExp)

        # clan properties
        def makeClanFunc(oTmpClan):
            return lambda card: ((oTmpClan in card.clan) and 1) or 0

        for oClan in Clan.select():
            d['clan: ' + oClan.name] = makeClanFunc(oClan)

        # cardtype properties
        def makeCardTypeFunc(oTmpType):
            return lambda card: ((oTmpType in card.cardtype) and 1) or 0

        for oType in CardType.select():
            d['card type: ' + oType.name] = makeCardTypeFunc(oType)

        return d

    def tabulate(self,aCards):
        """
        Create a table from the list of (or iterator over) cards.
        Returns the table which is a nested list where each element is a row and each row consists of column values.
        The rows are in the same order as the cards in aCards.
        The columns are in the same order as in the aColNames list passed to __init__.
        """
        aColFuncs = [self._dPropFuncs[x] for x in self._aColNames]

        aTable = []

        for oC in aCards:
            oC = IAbstractCard(oC)
            aRow = []

            for fProp in aColFuncs:
                aRow.append(fProp(oC))

            aTable.append(aRow)

        return aTable

