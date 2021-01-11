# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""The base card and related objects creation helper"""

from sqlobject import SQLObjectNotFound

from .BaseTables import (CardType, Expansion, Rarity, RarityPair,
                         PhysicalCard, Ruling, Keyword, Artist, Printing,
                         PrintingProperty, LookupHints)
from .BaseAdapters import (ICardType, IExpansion, IRarity, IRarityPair,
                           IPhysicalCard, IRuling, IKeyword, IArtist,
                           IPrinting, IPrintingProperty, ILookupHint)
from .BaseAbbreviations import CardTypes, Expansions, Rarities


# Object Maker API
# pylint: disable=missing-docstring
# No point in docstrings for these methods, really
class BaseObjectMaker:
    """Creates all kinds of program Objects from simple strings.

       All the methods will return either a copy of an existing object
       or a new object.
       """
    # pylint: disable=no-self-use, too-many-arguments
    # we want ObjectMakers to be self-contained, so these are all methods.
    # This needs all these arguments
    def _make_object(self, cObjClass, fAdapter, cAbbreviation, sObj,
                     bShortname=False, bFullname=False):
        try:
            return fAdapter(sObj)
        except SQLObjectNotFound:
            sObj = cAbbreviation.canonical(sObj)
            dKw = {'name': sObj}
            if bShortname:
                dKw['shortname'] = cAbbreviation.shortname(sObj)
            if bFullname:
                dKw['fullname'] = cAbbreviation.fullname(sObj)
            return cObjClass(**dKw)

    def make_card_type(self, sType):
        return self._make_object(CardType, ICardType, CardTypes, sType)

    def make_expansion(self, sExpansion):
        return self._make_object(Expansion, IExpansion, Expansions, sExpansion,
                                 bShortname=True)

    def make_rarity(self, sRarity):
        return self._make_object(Rarity, IRarity, Rarities, sRarity,
                                 bShortname=True)

    def make_abstract_card(self, sCard):
        # Subclasses should implement this
        # XXX: Should we define some of the common logic here
        # and just provide a hook for creating the object if it
        # doesn't exist?
        raise NotImplementedError  # pragma: no cover

    def make_physical_card(self, oCard, oPrinting):
        try:
            return IPhysicalCard((oCard, oPrinting))
        except SQLObjectNotFound:
            return PhysicalCard(abstractCard=oCard, printing=oPrinting)

    def make_default_printing(self, oExp):
        return self.make_printing(oExp, None)

    def make_printing(self, oExp, sPrinting):
        try:
            return IPrinting((oExp, sPrinting))
        except SQLObjectNotFound:
            return Printing(name=sPrinting, expansion=oExp)

    def make_lookup_hint(self, sLookupDomain, sKey, sValue):
        try:
            return ILookupHint((sLookupDomain, sKey))
        except SQLObjectNotFound:
            return LookupHints(domain=sLookupDomain,
                               lookup=sKey, value=sValue)

    def make_rarity_pair(self, sExp, sRarity):
        try:
            return IRarityPair((sExp, sRarity))
        except SQLObjectNotFound:
            oExp = self.make_expansion(sExp)
            oRarity = self.make_rarity(sRarity)
            return RarityPair(expansion=oExp, rarity=oRarity)

    def make_ruling(self, sText, sCode):
        try:
            return IRuling((sText, sCode))
        except SQLObjectNotFound:
            return Ruling(text=sText, code=sCode)

    def make_keyword(self, sKeyword):
        try:
            return IKeyword(sKeyword)
        except SQLObjectNotFound:
            return Keyword(keyword=sKeyword)

    def make_artist(self, sArtist):
        try:
            return IArtist(sArtist)
        except SQLObjectNotFound:
            return Artist(canonicalName=sArtist.lower(), name=sArtist)

    def make_printing_property(self, sValue):
        try:
            return IPrintingProperty(sValue)
        except SQLObjectNotFound:
            return PrintingProperty(value=sValue,
                                    canonicalValue=sValue.lower())
