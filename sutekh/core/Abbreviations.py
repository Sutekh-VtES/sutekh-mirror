# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""A catalog of common abbreviations for VtES terms.
   """

# Fullname: Discipline, Virtue
# Shortname: Expansion, Creed, Clan

from sutekh.base.core.BaseAbbreviations import AbbreviationLookup

# Abbreviation Lookups


# pylint: disable=W0223
# We don't override all the abstract methods in all the classes
# this is OK, since we control the use cases
class Clans(AbbreviationLookup):
    """Standard names and common abbreviations for the VtES clans."""
    dKeys = {
        # Camarilla
        'Brujah': ['Brujah'], 'Malkavian': ['Malk'],
        'Nosferatu': ['Nos'], 'Toreador': ['Tor'],
        'Tremere': ['Tre'], 'Ventrue': ['Ven'],
        'Caitiff': ['Caitiff'],
        # Independents
        'Abomination': ['Abom'], 'Gangrel': ['Gangrel'],
        'Assamite': ['Assa'], 'Follower of Set': ['Set'],
        'Giovanni': ['Giov'], 'Ravnos': ['Ravnos'],
        'Baali': ['Baali'], 'Daughter of Cacophony': ['DoC'],
        'Gargoyle': ['Garg'], 'Nagaraja': ['Naga'],
        'Salubri': ['Salu'], 'Samedi': ['Sam'],
        'True Brujah': ['TBruj'],
        # Sabbat
        'Lasombra': ['Lasom'], 'Tzimisce': ['Tz'],
        'Brujah antitribu': ['!Brujah'], 'Gangrel antitribu': ['!Gangrel'],
        'Malkavian antitribu': ['!Malk'], 'Nosferatu antitribu': ['!Nos'],
        'Toreador antitribu': ['!Tor'], 'Tremere antitribu': ['!Tre'],
        'Ventrue antitribu': ['!Ven'], 'Pander': ['Pan'],
        'Ahrimane': ['Ahrimanes'],
        'Blood Brother': ['BB', 'Blood Brothers'],
        'Harbinger of Skulls': ['HoS'],
        'Kiasyd': ['Kias'], 'Salubri antitribu': ['!Salu'],
        # Laibon
        'Akunanse': ['Aku'], 'Guruhi': ['Guru'], 'Ishtarri': ['Ish'],
        'Osebo': ['Ose'],
        # Other
    }

    @classmethod
    def shortname(cls, sCanonical):
        """Return the abbreviation for the canonical clan name."""
        return cls.dKeys[sCanonical][0]


class Creeds(AbbreviationLookup):
    """The Imbued creeds."""
    dKeys = {
        # Imbued
        'Avenger': [], 'Defender': [], 'Innocent': [],
        'Judge': [], 'Martyr': [], 'Redeemer': [],
        'Visionary': [],
    }

    @classmethod
    def shortname(cls, sCanonical):
        """Return the defined shortname."""
        return sCanonical


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


class Sects(AbbreviationLookup):
    """Common strings for the different sects."""
    dKeys = {
        'Camarilla': [], 'Sabbat': [], 'Independent': [],
        'Laibon': [], 'Anarch': [],
    }


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
