# Abbreviations.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""A catalog of common abbreviations for VtES terms.
   """

# Fullname: Discipline, Virtue
# Shortname: Expansion, Creed, Clan


# Base Classes
class AbbrevMeta(type):
    """Meta class for the abbreviation classes"""
    # pylint: disable-msg=W0231, C0203
    # W0231 - no point in calling type's init
    # C0203 - pylint's buggy here, see
    # http://lists.logilab.org/pipermail/python-projects/2007-July/001249.html
    def __init__(cls, _sName, _aBases, _dDict):
        if cls.dKeys:
            cls.make_lookup()

    # pylint: disable-msg=W0201
    # W0201 - make_lookup called from init
    def make_lookup(cls):
        """Create a lookup table for the class."""
        cls._dLook = {}
        for sKey, aAlts in cls.dKeys.iteritems():
            cls._dLook[sKey] = sKey
            for sAlt in aAlts:
                cls._dLook[sAlt] = sKey


# pylint: disable-msg=E1101
# meta-class magic with _dLook confuses pylint
class AbbreviationLookup(object):
    """Base class for specific abbreviation tables."""
    __metaclass__ = AbbrevMeta

    # Subclass should define a dictionary of keys:
    #   Canonical Name -> [ other names ... ]
    dKeys = None

    @classmethod
    def canonical(cls, sName):
        """Translate a possibly abbreviated name into a canonical one.
           """
        return cls._dLook[sName]

    @classmethod
    def fullname(cls, sCanonical):
        """Translate a canonical name into a full name.
           """
        raise NotImplementedError

    @classmethod
    def shortname(cls, sCanonical):
        """Translate a canonical name into a short name.
           """
        raise NotImplementedError

# Abbreviation Lookups


# pylint: disable-msg=W0223
# We don't override all the abstract methods in all the classes
# this is OK, since we control the use cases
class CardTypes(AbbreviationLookup):
    """The standard VtES card types."""
    dKeys = {
        'Action': [], 'Action Modifier': [], 'Ally': [],
        'Combat': [], 'Conviction': [], 'Equipment': [],
        'Event': [], 'Imbued': [], 'Master': [],
        'Political Action': [], 'Power': [], 'Reaction': [],
        'Reflex': [], 'Retainer': [], 'Vampire': [],
    }


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


class Expansions(AbbreviationLookup):
    """Common names and abbreviations for the different expansions."""
    dKeys = {
        # Ordinary expansions
        'Anarchs': [],
        'Ancient Hearts': ['AH'],
        # Blackhand is an abbreviation so reading card sets from old versions
        # work
        'Black Hand': ['BH', 'Blackhand'],
        'Bloodlines': ['BL'],
        'Blood Shadowed Court': ['BSC'],
        'Camarilla Edition': ['CE'],
        'Dark Sovereigns': ['DS'],
        'Ebony Kingdom': ['EK'],
        'Final Nights': ['FN'],
        'Gehenna': [],
        'Heirs to the Blood': ['HttB'],
        'Jyhad': [],
        'Kindred Most Wanted': ['KMW'],
        'Keepers of Tradition': ['KoT'],
        'Legacy of Blood': ['LoB'],
        'Lords of the Night': ['LotN'],
        'Nights of Reckoning': ['NoR'],
        'Sabbat': [],
        'Sabbat Wars': ['SW'],
        'Sword of Caine': ['SoC'],
        'Tenth Anniversary': ['Tenth'],
        'Third Edition': ['Third'],
        'Twilight Rebellion': ['TR'],
        'VTES': [],
        # Special cases
        # The Promo entry is to special-case the AaA cards which
        # appear with promo entries in the card list
        'Anarchs and Alastors Storyline': ['Promo-20080810'],
    }

    @classmethod
    def canonical(cls, sName):
        """Return the canonical name of the expansion.

           Treats promo's somewhat specially, since each promo release
           is essentially it's own unique expansion.

           Unknown expansions are also allowed in order to make it
           possible to update to a card list that includes expansions
           not in the list known to the Expansion class."""
        if sName in cls._dLook:
            return cls._dLook[sName]
        if sName.startswith('Promo-'):
            return sName
        return sName

    @classmethod
    def shortname(cls, sCanonical):
        """Return the short name for the given expansion."""
        if sCanonical.startswith('Promo-'):
            return 'Promo'
        if sCanonical in cls.dKeys and cls.dKeys[sCanonical]:
            return cls.dKeys[sCanonical][0]
        return sCanonical


class Rarities(AbbreviationLookup):
    """Common strings and abbreviations for the different card rarities."""
    dKeys = {
        # EK uses C1/2 for Aye & Orun
        'Common': ['C', 'C1', 'C2', 'C3', u'C\xbd'],
        'Uncommon': ['U', 'U1', 'U2', 'U3', 'U5'],
        'Rare': ['R', 'R1', 'R2', 'R3'],
        'Vampire': ['V', 'V1', 'V2', 'V3'],
        'Tenth': ['A', 'B'],
        'BSC': ['X'],
        'Precon': ['P', 'PB', 'PA', 'PTo3', 'PTr', 'PG', 'PB2', 'PTo4', 'PAl2',
            'PO3'],
        'Not Applicable': ['NA'],
        'Rules': ['Rules'],
        'Demo': ['Demo'],
        'Storyline': ['Storyline'],
    }

    @classmethod
    def canonical(cls, sName):
        """Return the canonical name of the rarity."""
        if sName.startswith('P'):
            return 'Precon'
        if sName in cls._dLook:
            return cls._dLook[sName]
        return 'Unknown'

    @classmethod
    def shortname(cls, sCanonical):
        """Return the corresponding short name for the rarity."""
        if sCanonical in cls.dKeys and cls.dKeys[sCanonical]:
            return cls.dKeys[sCanonical][0]
        return sCanonical


class Sects(AbbreviationLookup):
    """Common strings for the different sects."""
    dKeys = {
        'Camarilla': [], 'Sabbat': [], 'Independent': [],
        'Laibon': [],
        # For if we ever start handling merged vampires somehow
        'Anarch': [],
    }


class Titles(AbbreviationLookup):
    """Common strings used to refer to the different titles."""
    dKeys = {
        # Camarilla Titles
        'Primogen': [], 'Prince':  [], 'Justicar': [],
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
