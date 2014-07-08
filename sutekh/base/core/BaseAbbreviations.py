# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Base classes for handling the abbrevations."""

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
