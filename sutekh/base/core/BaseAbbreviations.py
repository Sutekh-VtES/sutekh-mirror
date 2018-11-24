# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Base classes for handling the abbrevations."""

# Fullname: Discipline, Virtue
# Shortname: Expansion, Creed, Clan

from .BaseTables import LookupHints


# Base Classes
class AbbrevMeta(type):
    """Meta class for the abbreviation classes"""
    # pylint: disable=W0231
    # W0231 - no point in calling type's init
    def __init__(cls, _sName, _aBases, _dDict):
        if cls.dKeys:
            cls.make_lookup()

    # pylint: disable=W0201
    # W0201 - make_lookup called from init
    def make_lookup(cls):
        """Create a lookup table for the class."""
        cls._dLook = {}
        for sKey, aAlts in cls.dKeys.iteritems():
            cls._dLook[sKey] = sKey
            for sAlt in aAlts:
                cls._dLook[sAlt] = sKey


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
        # pylint: disable=no-member
        # meta-class magic with _dLook confuses pylint
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


class DatabaseAbbreviation(object):
    """Base class for database backed abbrevations"""

    _dLook = {}
    _dLookupPrefix = {}
    _dReversePrefix = {}
    _dReverse = {}

    sLookupDomain = None

    # pylint: disable=W0201
    # W0201 - make_lookup called from cache handling code
    @classmethod
    def make_lookup(cls):
        """Create a lookup table for the class."""
        cls._dLook = {}
        cls._dPrefix = {}
        cls._dReversePrefix = {}
        cls._dReverse = {}
        for oLookup in LookupHints.selectBy(domain=cls.sLookupDomain):
            cls._dLook[oLookup.value] = oLookup.value
            if oLookup.lookup.startswith('Prefix:'):
                sPrefix = oLookup.lookup.replace('Prefix:', '')
                cls._dPrefix[sPrefix] = oLookup.value
            elif oLookup.lookup.startswith('ReversePrefix:'):
                sPrefix = oLookup.lookup.replace('ReversePrefix:', '')
                cls._dReversePrefix[sPrefix] = oLookup.value
            else:
                cls._dLook[oLookup.lookup] = oLookup.value
                if oLookup.lookup != oLookup.value:
                    cls._dReverse.setdefault(oLookup.value, oLookup.lookup)

    @classmethod
    def canonical(cls, sName):
        """Translate a possibly abbreviated name into a canonical one.
           """
        for sPrefix, sLookup in cls._dPrefix.items():
            if sName.startswith(sPrefix):
                return sLookup
        return cls._dLook[sName]

    @classmethod
    def shortname(cls, sCanonical):
        """Translate a canonical name into a short name.
           """
        for sPrefix, sLookup in cls._dReversePrefix.items():
            if sCanonical.startswith(sPrefix):
                return sLookup
        if sCanonical in cls._dReverse and cls._dReverse[sCanonical]:
            return cls._dReverse[sCanonical]
        return sCanonical


class CardTypes(DatabaseAbbreviation):
    """Card Types Abbrevations"""
    sLookupDomain = 'CardTypes'


class Expansions(DatabaseAbbreviation):
    """Expansion Abbrevations"""
    sLookupDomain = 'Expansions'

    @classmethod
    def canonical(cls, sName):
        """Translate, using prefixes if specified"""
        # We passthrough expansions we don't recognise, so we don't fall
        # over completely in the face of new expansions while still creating
        # unique DB objects for each new expansion.
        try:
            sResult = super(Expansions, cls).canonical(sName)
        except KeyError:
            sResult = cls._dLook[sName] = sName
        return sResult


class Rarities(DatabaseAbbreviation):
    """Card rarity abbrevations"""
    sLookupDomain = 'Rarities'

    @classmethod
    def canonical(cls, sName):
        """Lookup rarity"""
        # We return 'Unknown', so we don't fall over on unrecognised
        # rarities.
        try:
            sResult = super(Rarities, cls).canonical(sName)
        except KeyError:
            sResult = cls._dLook[sName] = 'Unknown'
        return sResult
