# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Various helpful functions that are generic enough to belong in base.gui"""

import os
import gtk
from .SutekhDialog import (do_complaint_error, do_exception_complaint,
                           do_complaint_warning)


def prepare_gui(sName):
    """Handle all the checks needed to ensure we can run the gui."""
    # Print nice complaint if not under a windowing system
    if gtk.gdk.screen_get_default() is None:
        print "Unable to find windowing system. Aborting"
        return False

    # check minimum pygtk version
    sMessage = gtk.check_version(2, 16, 0)
    if sMessage is not None:
        do_complaint_error('Incorrect gtk version. %s requires at least'
                           ' gtk 2.16.0.\nError reported %s' % (sName,
                                                                sMessage))
        return False

    # Disable Unity's moving of menubars to the appmenu at
    # the top of the screen since this moves the panel menus
    # into limbo.
    # TODO: we should only disable this on the panel menus
    os.environ["UBUNTU_MENUPROXY"] = "0"

    return True


def load_config(cConfigFile, sRCFile):
    """Load the config and handle the checks needed before we
       start using it."""
    # Init
    oConfig = cConfigFile(sRCFile)
    # initial config validation to set sane defaults
    # (re-validated later after plugins are loaded)
    oConfig.validate()

    if not oConfig.check_writeable():
        # Warn the user
        iRes = do_complaint_warning('Unable to write to the config file %s.\n'
                                    'Config changes will NOT be saved.\n'
                                    'Do you wish to continue?' % sRCFile)
        if iRes == gtk.RESPONSE_CANCEL:
            return None
    return oConfig


def save_config(oConfig):
    """Handle writing the config file and complaining if it fails."""
    try:
        oConfig.write()
    except IOError as oExp:
        sMesg = ('Unable to write the configuration file\n'
                 'Error was: %s' % oExp)
        do_exception_complaint(sMesg)


def make_markup_button(sMarkup):
    """Create a gtk.Button using the given markup string for the label."""
    oBut = gtk.Button()
    oLabel = gtk.Label()
    oLabel.set_markup(sMarkup)
    oBut.add(oLabel)
    oBut.show_all()
    return oBut


def wrap(sText):
    """Return a gtk.Label which wraps the given text"""
    oLabel = gtk.Label()
    oLabel.set_line_wrap(True)
    oLabel.set_width_chars(80)
    oLabel.set_alignment(0, 0)  # Align top-left
    oLabel.set_markup(sText)
    return oLabel
