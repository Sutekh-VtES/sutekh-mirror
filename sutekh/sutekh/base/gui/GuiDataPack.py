# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2013 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Wrap various functions from base.io.UrlOps with timeout handling"""

from urllib.error import URLError
import socket
from ..io.UrlOps import fetch_data
from .SutekhDialog import do_exception_complaint
from .ProgressDialog import ProgressDialog, SutekhCountLogHandler


def gui_error_handler(oExp):
    """Default error handler for url fetching operations."""
    if isinstance(oExp, socket.timeout):
        do_exception_complaint('Connection Timeout')
    elif isinstance(oExp, URLError) and \
            isinstance(oExp.reason, socket.timeout):
        do_exception_complaint('Connection Timeout')
    else:
        do_exception_complaint('Connection Error')


def progress_fetch_data(oFile, oOutFile=None, sHash=None, sDesc=None):
    """Wrap a Progress Dialog around fetch_data"""
    oProgress = ProgressDialog()
    if sDesc:
        oProgress.set_description(sDesc)
    else:
        oProgress.set_description('Download progress')
    oLogHandler = SutekhCountLogHandler()
    oLogHandler.set_dialog(oProgress)
    try:
        return fetch_data(oFile, oOutFile, sHash, oLogHandler,
                          gui_error_handler)
    finally:
        oProgress.destroy()
    return None
