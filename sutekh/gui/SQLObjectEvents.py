# SQLObjectEvents.py
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING file for details

from sqlobject.events import Signal, RowDestroySignal, RowCreatedSignal,\
        RowUpdateSignal

# We need a bunch of extra signals to handle all the database changes we 
# want to track

class IncCardSignal(Signal):
    """
    Called when a card is incremented - called with (sCardName)
    """

class DecCardSignal(Signal):
    """
    Called when a card is decremented - called with (sCardName)
    """

class CardSetOpenedSignal(Signal):
    """
    Called when a card set is opened - called with (sSetName)
    """

class CardSetClosedSignal(Signal):
    """
    Called when a card set is closed - called with (sSetName)
    """
