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
    def __init__(self, sName, aBases, dDict):
        if self.dKeys:
            self.makeLookup()

    def makeLookup(self):
        self._dLook = {}
        for sKey, aAlts in self.dKeys.iteritems():
            self._dLook[sKey] = sKey
            for sAlt in aAlts:
                self._dLook[sAlt] = sKey

class AbbreviationLookup(object):
    __metaclass__ = AbbrevMeta

    # Subclass should define a dictionary of keys:
    #   Canonical Name -> [ other names ... ]
    dKeys = None

    @classmethod
    def canonical(cls,sName):
        """Translate a possibly abbreviated name into a canonical one.
           """
        return cls._dLook[sName]

    @classmethod
    def fullname(cls,sCanonical):
        """Translate a canonical name into a full name.
           """
        raise NotImplementedError

    @classmethod
    def shortname(cls,sCanonical):
        """Translate a canonical name into a short name.
           """
        raise NotImplementedError

# Abbreviation Lookups

class CardTypes(AbbreviationLookup):
    dKeys = {
        'Action' : [], 'Action Modifier' : [], 'Ally' : [],
        'Combat' : [], 'Conviction' : [], 'Equipment' : [],
        'Event' : [], 'Imbued' : [], 'Master' : [],
        'Political Action' : [], 'Power' : [], 'Reaction' : [],
        'Reflex' : [], 'Retainer' : [], 'Vampire' : [],
    }

class Clans(AbbreviationLookup):
    dKeys = {
        # Camarilla
        'Brujah' : ['Brujah'], 'Malkavian' : ['Malk'],
        'Nosferatu' : ['Nos'], 'Toreador' : ['Tor'],
        'Tremere' : ['Tre'], 'Ventrue' : ['Ven'],
        'Caitiff' : ['Caitiff'],
        # Independents
        'Abomination' : ['Abom'], 'Gangrel' : ['Gangrel'],
        'Assamite' : ['Assa'], 'Follower of Set' : ['Set'],
        'Giovanni' : ['Giov'], 'Ravnos' : ['Ravnos'],
        'Baali' : ['Baali'], 'Daughter of Cacophony' : ['DoC'],
        'Gargoyle' : ['Garg'], 'Nagaraja' : ['Naga'],
        'Salubri' :['Salu'], 'Samedi' : ['Sam'],
        'True Brujah' : ['TBruj'],
        # Sabbat
        'Lasombra' : ['Lasom'], 'Tzimisce' : ['Tz'],
        'Brujah antitribu' : ['!Brujah'], 'Gangrel antitribu' : ['!Gangrel'],
        'Malkavian antitribu' : ['!Malk'], 'Nosferatu antitribu' : ['!Nos'],
        'Toreador antitribu' : ['!Tor'], 'Tremere antitribu' : ['!Tre'],
        'Ventrue antitribu' : ['!Ven'], 'Pander' : ['Pan'],
        'Ahrimanes' : ['Ahrimanes'], 'Blood Brother' : ['BB'],
        'Harbinger of Skulls' : ['HoS'],
        'Kiasyd' : ['Kias'], 'Salubri antitribu' : ['!Salu'],
        # Laibon
        'Akunanse' : ['Aku'], 'Guruhi' : ['Guru'], 'Ishtarri' : ['Ish'],
        'Osebo' : ['Ose'],
        # Other
        'Ahrimane' : ['Ahrimane'],
    }

    @classmethod
    def shortname(cls,sCanonical):
        return cls.dKeys[sCanonical][0]

class Creeds(AbbreviationLookup):
    dKeys = {
        # Imbued
        'Avenger' : [], 'Defender' : [], 'Innocent' : [],
        'Judge' : [], 'Martyr' : [], 'Redeemer' : [],
        'Visionary' : []
    }

    @classmethod
    def shortname(cls,sCanonical):
        return sCanonical

class Disciplines(AbbreviationLookup):
    dKeys = {
        'abo' : ['ABO','Abombwe'],
        'ani' : ['ANI','Animalism'],
        'aus' : ['AUS','Auspex'],
        'cel' : ['CEL','Celerity'],
        'chi' : ['CHI','Chimerstry'],
        'dai' : ['DAI','Daimoinon'],
        'dem' : ['DEM','Dementation'],
        'dom' : ['DOM','Dominate'],
        'fli' : ['FLI','Flight'],
        'for' : ['FOR','Fortitude'],
        'mel' : ['MEL','Melpominee'],
        'myt' : ['MYT','Mytherceria'],
        'nec' : ['NEC','Necromancy'],
        'obe' : ['OBE','Obeah'],
        'obf' : ['OBF','Obfuscate'],
        'obt' : ['OBT','Obtenebration'],
        'pot' : ['POT','Potence'],
        'pre' : ['PRE','Presence'],
        'pro' : ['PRO','Protean'],
        'qui' : ['QUI','Quietus'],
        'san' : ['SAN','Sanguinus'],
        'ser' : ['SER','Serpentis'],
        'spi' : ['SPI','Spiritus'],
        'tem' : ['TEM','Temporis'],
        'thn' : ['THN','Thanatosis'],
        'tha' : ['THA','Thaumaturgy'],
        'val' : ['VAL','Valeren'],
        'vic' : ['VIC','Vicissitude'],
        'vis' : ['VIS','Visceratika'],
    }

    @classmethod
    def fullname(cls,sCanonical):
        return cls.dKeys[sCanonical][1]

class Expansions(AbbreviationLookup):
    dKeys = {
        'Anarchs' : [],
        'Ancient Hearts' : ['AH'],
        'Blackhand' : ['BH'],
        'Bloodlines' : ['BL'],
        'Camarilla Edition' : ['CE'],
        'Dark Sovereigns' : ['DS'],
        'Final Nights' : ['FN'],
        'Gehenna' : [],
        'Jyhad' : [],
        'Kindred Most Wanted' : ['KMW'],
        'Legacy of Blood' : ['LoB'],
        'Lords of the Night' : ['LotN'],
        'Nights of Reckoning' : ['NoR'],
        'Sabbat' : [],
        'Sabbat Wars' : ['SW'],
        'Sword of Caine' : ['SoC'],
        'Tenth Anniversary' : ['Tenth'],
        'Third Edition' : ['Third'],
        'VTES' : [],
    }

    @classmethod
    def canonical(cls,sName):
        if sName.startswith('Promo-'):
            return sName
        return cls._dLook[sName]

    @classmethod
    def shortname(cls,sCanonical):
        if sCanonical.startswith('Promo-'):
            return 'Promo'
        if cls.dKeys[sCanonical]:
            return cls.dKeys[sCanonical][0]
        return sCanonical

class Rarities(AbbreviationLookup):
    dKeys = {
        'Common' : ['C','C1','C2','C3'],
        'Uncommon' : ['U','U1','U2','U3','U5'],
        'Rare' : ['R','R1','R2','R3'],
        'Vampire' : ['V','V1','V2','V3'],
        'Tenth': ['A','B'],
        'Precon' : ['PB','PA','PTo3','PTr','PG','PB2','PTo4','PAl2','PO3'],
        'Not Applicable' : ['NA'],
    }

    @classmethod
    def canonical(cls,sName):
        if sName.startswith('P'):
            return 'Precon'
        return cls._dLook[sName]

    @classmethod
    def shortname(cls,sCanonical):
        return cls.dKeys[sCanonical][0]

class Sects(AbbreviationLookup):
    dKeys = {
        'Camarilla' : [], 'Sabbat' : [], 'Independent' : [],
        'Laibon' : [],
        # For if we ever start handling merged vampires somehow
        'Anarch' : [],
    }

class Titles(AbbreviationLookup):
    dKeys = {
        # Camarilla Titles
        'Primogen' : [], 'Prince' :  [], 'Justicar' : [],
        'Inner Circle' : [],
        # Sabbat Titles
        'Bishop' : [], 'Archbishop' : [], 'Priscus':[],
        'Cardinal' : [], 'Regent' : [],
        # Independant Titles
        'Independent with 1 vote' : [],
        'Independent with 2 votes' : [],
        'Independent with 3 votes' : [],
        # Laibon Titles
        'Magaji' : [],
    }

class Virtues(AbbreviationLookup):
    dKeys = {
        # Virtues (last key is full name)
        'def' : ['Defense'],
        'inn' : ['Innocence'],
        'jud' : ['Judgment','Judgement'],
        'mar' : ['Martyrdom'],
        'red' : ['Redemption'],
        'ven' : ['Vengeance'],
        'vis' : ['Vision'],
    }

    @classmethod
    def fullname(cls,sCanonical):
        return cls.dKeys[sCanonical][0]
