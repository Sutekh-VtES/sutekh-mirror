# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Various helpful functions that are generic enough to belong in base.gui"""

import logging
import os
import sys
import gtk
from .SutekhDialog import (do_complaint_error, do_exception_complaint,
                           do_complaint_warning)


def setup_logging(bVerbose, sErrFile):
    """Setup the log handling for this run"""
    # Only log critical messages by default
    oRootLogger = logging.getLogger()
    oRootLogger.setLevel(level=logging.CRITICAL)
    if bVerbose or sErrFile:
        # Change logging level to debug
        oRootLogger.setLevel(logging.DEBUG)
        bSkipVerbose = False
        if sErrFile:
            try:
                oLogHandler = logging.FileHandler(sErrFile)
                oRootLogger.addHandler(oLogHandler)
            except IOError:
                oLogHandler = logging.StreamHandler(sys.stderr)
                oRootLogger.addHandler(oLogHandler)
                bSkipVerbose = True  # Avoid doubled logging to stderr
                logging.error('Unable to open log file, logging to stderr',
                              exc_info=1)
        if bVerbose and not bSkipVerbose:
            # Add logging to stderr
            oLogHandler = logging.StreamHandler(sys.stderr)
            oRootLogger.addHandler(oLogHandler)
    else:
        # Setup fallback logger for critical messages
        oLogHandler = logging.StreamHandler(sys.stderr)
        oRootLogger.addHandler(oLogHandler)
    return oRootLogger


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
    except IOError, oExp:
        sMesg = ('Unable to write the configuration file\n'
                 'Error was: %s' % oExp)
        do_exception_complaint(sMesg)
