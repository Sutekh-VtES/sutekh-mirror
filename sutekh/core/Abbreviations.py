# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""A catalog of common abbreviations for VtES terms.
   """

# Fullname: Discipline, Virtue
# Shortname: Expansion, Creed, Clan

from sutekh.base.core.BaseAbbreviations import (AbbreviationLookup,
                                                DatabaseAbbreviation)
from sutekh.base.core.BaseTables import LookupHints

# Abbreviation Lookups


# pylint: disable=abstract-method
# We don't override all the abstract methods in all the classes
# this is OK, since we control the use cases
class Clans(DatabaseAbbreviation):
    """Standard names and common abbreviations for the VtES clans."""
    sLookupDomain = 'Clans'


class Creeds(DatabaseAbbreviation):
    """The Imbued creeds."""
    sLookupDomain = 'Creeds'


class Disciplines(DatabaseAbbreviation):
    """Standard abbreviations and names for the VtES disciplines."""
    sLookupDomain = "Disciplines"

    @classmethod
    def fullname(cls, sShortName):
        """Return the full name for the given abbreviation."""
        sFullName = None
        sCanonical = cls.canonical(sShortName)
        # We need to look up the longest reverse version of the canonical
        # lookup.  We assume the 3 letter entries are all abbrevations
        for oLookup in LookupHints.selectBy(domain=cls.sLookupDomain):
            if oLookup.value == sCanonical and len(oLookup.lookup) > 3:
                sFullName = oLookup.lookup
                break
        return sFullName


class Sects(DatabaseAbbreviation):
    """Common strings for the different sects."""
    sLookupDomain = 'Sects'


class Titles(AbbreviationLookup):
    """Common strings used to refer to the different titles."""
    dKeys = {
        # Camarilla Titles
        'Primogen': [], 'Prince': [], 'Justicar': [],
        'Inner Circle': [],
        # Sabbat Titles
        'Bishop': [], 'Archbishop': [], 'Priscus': [],
        'Cardinal': [], 'Regent': [],
        # Independant Titles
        'Independent with 1 vote': [],
        'Independent with 2 votes': [],
        'Independent with 3 votes': [],
        # Laibon Titles
        'Magaji': [],
        # Anarch Titles
        'Baron': [],
    }

    dVoteValues = {
        # Camarilla Titles
        'Primogen': 1, 'Prince': 2, 'Justicar': 3,
        'Inner Circle': 4,
        # Sabbat Titles
        'Bishop': 1, 'Archbishop': 2, 'Priscus': 3,
        'Cardinal': 3, 'Regent': 4,
        # Independent Titles
        'Independent with 1 vote': 1,
        'Independent with 2 votes': 2,
        'Independent with 3 votes': 3,
        # Laibon Titles
        'Magaji': 2,
        # Anarch Titles
        'Baron': 2,
    }

    @classmethod
    def vote_value(cls, sTitle):
        """Get the vote value for the title"""
        return cls.dVoteValues[sTitle]


class Virtues(DatabaseAbbreviation):
    """Common abbreviations for Imbued Virtues"""
    sLookupDomain = 'Virtues'

    @classmethod
    def fullname(cls, sCanonical):
        """Return the canonical long name of the Virtue"""
        sFullName = None
        sCanonical = cls.canonical(sCanonical)
        # We need to look reverse version of the canonical lookup
        for oLookup in LookupHints.selectBy(domain=cls.sLookupDomain):
            # We skip the identity lookup and grab the next one
            # We assume the ordering in the lookup file is correct
            # so we handle the 'Judgement/Judgment' case
            if oLookup.value == sCanonical and oLookup.lookup != sCanonical:
                sFullName = oLookup.lookup
                break
        return sFullName
