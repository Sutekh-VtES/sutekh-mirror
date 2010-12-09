# DBSignals.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Define the reload singal we need
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Wrappers around SQLObject signals needed to keep card sets and the card
collection in sync."""

from sqlobject.events import Signal, listen, RowUpdateSignal, \
        RowDestroySignal, RowCreatedSignal
from sqlobject.include.pydispatch import dispatcher
from sutekh.core.SutekhObjects import PhysicalCardSet


class ChangedSignal(Signal):
    """Syncronisation signal for card sets.

       Needs to be sent after changes are commited to the database, so card
       sets can reload properly.
       Used so card sets always reflect correct available counts.
       """


# Senders
def send_changed_signal(oCardSet, oPhysCard, iChange, cClass=PhysicalCardSet):
    """Sent when card counts change, as card sets may need to update."""
    cClass.sqlmeta.send(ChangedSignal, oCardSet, oPhysCard, iChange)


# Listeners
def listen_changed(fListener, cClass):
    """Listens for the changed_signal."""
    listen(fListener, cClass, ChangedSignal)


def listen_row_destroy(fListener, cClass):
    """listen for the row destroyed signal sent when a card set is deleted."""
    listen(fListener, cClass, RowDestroySignal)


def listen_row_update(fListener, cClass):
    """listen for the row updated signal sent when a card set is modified."""
    listen(fListener, cClass, RowUpdateSignal)


def listen_row_created(fListener, cClass):
    """listen for the row updated signal sent when a card set is modified."""
    listen(fListener, cClass, RowCreatedSignal)


def disconnect_changed(fListener, cClass):
    """Disconnects from the changed_signal."""
    dispatcher.disconnect(fListener, signal=ChangedSignal, sender=cClass)


def disconnect_row_destroy(fListener, cClass):
    """Disconnect from the row destroyed signal."""
    dispatcher.disconnect(fListener, signal=RowDestroySignal, sender=cClass)


def disconnect_row_created(fListener, cClass):
    """Disconnect from the row destroyed signal."""
    dispatcher.disconnect(fListener, signal=RowCreatedSignal, sender=cClass)


def disconnect_row_update(fListener, cClass):
    """Disconnect the row updated signal."""
    dispatcher.disconnect(fListener, signal=RowUpdateSignal, sender=cClass)
