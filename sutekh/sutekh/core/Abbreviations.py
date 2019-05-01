# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""A catalog of common abbreviations for VtES terms.
   """

# Fullname: Discipline, Virtue
# Shortname: Expansion, Creed, Clan

from sutekh.base.core.BaseAbbreviations import AbbreviationLookup, DatabaseAbbreviation

# Abbreviation Lookups


# pylint: disable=W0223
# We don't override all the abstract methods in all the classes
# this is OK, since we control the use cases
class Clans(DatabaseAbbreviation):
    """Standard names and common abbreviations for the VtES clans."""
    sLookupDomain = 'Clans'


class Creeds(DatabaseAbbreviation):
    """The Imbued creeds."""
    sLookupDomain = 'Creeds'


class Disciplines(AbbreviationLookup):
    """Standard abbreviations and names for the VtES disciplines."""
    dKeys = {
        'abo': ['ABO', 'Abombwe'],
        'ani': ['ANI', 'Animalism'],
        'aus': ['AUS', 'Auspex'],
        'cel': ['CEL', 'Celerity'],
        'chi': ['CHI', 'Chimerstry'],
        'dai': ['DAI', 'Daimoinon'],
        'dem': ['DEM', 'Dementation'],
        'dom': ['DOM', 'Dominate'],
        'fli': ['FLI', 'Flight'],
        'for': ['FOR', 'Fortitude'],
        'mal': ['MAL', 'Maleficia'],
        'mel': ['MEL', 'Melpominee'],
        'myt': ['MYT', 'Mytherceria'],
        'nec': ['NEC', 'Necromancy'],
        'obe': ['OBE', 'Obeah'],
        'obf': ['OBF', 'Obfuscate'],
        'obt': ['OBT', 'Obtenebration'],
        'pot': ['POT', 'Potence'],
        'pre': ['PRE', 'Presence'],
        'pro': ['PRO', 'Protean'],
        'qui': ['QUI', 'Quietus'],
        'san': ['SAN', 'Sanguinus'],
        'ser': ['SER', 'Serpentis'],
        'spi': ['SPI', 'Spiritus'],
        'str': ['STR', 'Striga'],
        'tem': ['TEM', 'Temporis'],
        'thn': ['THN', 'Thanatosis'],
        'tha': ['THA', 'Thaumaturgy'],
        'val': ['VAL', 'Valeren'],
        'vic': ['VIC', 'Vicissitude'],
        'vis': ['VIS', 'Visceratika'],
    }

    @classmethod
    def fullname(cls, sCanonical):
        """Return the full name for the given abbreviation."""
        return cls.dKeys[sCanonical][1]


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


class Virtues(AbbreviationLookup):
    """Common abbreviations for Imbued Virtues"""
    dKeys = {
        # Virtues (last key is full name)
        'def': ['Defense'],
        'inn': ['Innocence'],
        'jud': ['Judgment', 'Judgement'],
        'mar': ['Martyrdom'],
        'red': ['Redemption'],
        'ven': ['Vengeance'],
        'vis': ['Vision'],
    }

    @classmethod
    def fullname(cls, sCanonical):
        """Return the canonical long name of the Virtue"""
        return cls.dKeys[sCanonical][0]
