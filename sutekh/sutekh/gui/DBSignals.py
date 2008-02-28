# DBSignals.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Define the reload singal we need
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
#                Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sqlobject.events import Signal, listen, RowUpdateSignal, RowDestroySignal
from sutekh.core.SutekhObjects import PhysicalCard

class ReloadSignal(Signal):
    """
    Syncronisation signal for card sets. Needs to be sent after
    changes are commited to the database, so card sets can reload
    properly
    """

# Senders

def send_reload_signal(oAbstractCard, cClass=PhysicalCard):
    cClass.sqlmeta.send(ReloadSignal, oAbstractCard)

# Listeners

def listen_reload(fListener, cClass):
    listen(fListener, cClass, ReloadSignal)

def listen_row_destroy(fListener, cClass):
    listen(fListener, cClass, RowDestroySignal)

def listen_row_update(fListener, cClass):
    listen(fListener, cClass, RowUpdateSignal)

