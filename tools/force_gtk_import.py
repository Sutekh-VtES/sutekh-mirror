# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based on custom_raw.py from pylint, so the license is
# GPL v2 or later - see the COPYRIGHT file for details

"""This forces gtk to be imported. astroid disabled importing c modules
   by default because of
   https://bitbucket.org/logilab/pylint/issue/347/please-either-disable-or-document-dynamic
   but this completely breaks it's ability to introspect gtk. We hack around that
   by monkey-patching astroid to consider gtk and gobject system modules."""

# Add this pylintrc using load-plugins
# The path to this file needs to be in PYTHONPATH as pylint must be able
# to import this

from pylint.interfaces import IRawChecker
from compat_helper import Base, compat_register
from astroid import modutils

OVERRIDES = ['gtk', 'gobject', 'pango']

# FIXME: Find a better solution than this
# pylint: disable=C0301, C0103
# Using astroid naming conventions for clarity
old_is_standard_module = modutils.is_standard_module


def my_is_standard_module(mod_name, std_path=None):
    """Fake out astroid.modutils."""
    for sPrefix in OVERRIDES:
        if mod_name.startswith(sPrefix):
            return True
    return old_is_standard_module(mod_name, std_path)


modutils.is_standard_module = my_is_standard_module

# pylint: enable=C0301, C0103


class GtkImporter(Base):
    """Check for whitespace at the end of a line."""

    __implements__ = IRawChecker

    name = 'gtk_importer'
    msgs = {}
    options = ()

    def process_module(self, aStream):
        """Dummy method."""
        pass

    def process_tokens(self, _aTokens):
        """Dummy method."""
        pass


def register(oLinter):
    """required method to auto register this checker."""
    compat_register(GtkImporter, oLinter)
