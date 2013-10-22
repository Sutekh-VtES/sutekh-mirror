# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Generic message bus
# Copyright 2012 Neil Muller <drnlmuller+sutekh@gmail.com>
# Inspired by PyBus by Bernardo Heynemann (http://pypi.python.org/pypi/PyBus/)
#
# GPL - see COPYING for details

"""Message Bus for Sutekh"""


# Useful constants to avoid typoes

CONFIG_MSG, CARD_TEXT_MSG, DATABASE_MSG = range(3)


class MessageBus(object):
    """The actual message bus"""

    _dSubscriptions = {}

    @classmethod
    def subscribe(cls, oObject, sSignalName, fCallback):
        """Subscribe to a given signal on an object"""
        if oObject not in cls._dSubscriptions:
            cls._dSubscriptions[oObject] = {}
        dCallbacks = cls._dSubscriptions[oObject]
        if sSignalName not in dCallbacks:
            dCallbacks[sSignalName] = []
        dCallbacks[sSignalName].append(fCallback)

    @classmethod
    def publish(cls, oObject, sSignalName, *args, **kwargs):
        """Publish the signal to any subscribers"""
        if oObject not in cls._dSubscriptions:
            return
        dCallbacks = cls._dSubscriptions[oObject]
        if sSignalName not in dCallbacks:
            return
        for fCallback in dCallbacks[sSignalName]:
            fCallback(*args, **kwargs)

    @classmethod
    def unsubscribe(cls, oObject, sSignalName, fCallback):
        """Remove a callback from the list"""
        if oObject not in cls._dSubscriptions:
            return
        dCallbacks = cls._dSubscriptions[oObject]
        if sSignalName not in dCallbacks:
            return
        if fCallback not in dCallbacks[sSignalName]:
            return
        dCallbacks[sSignalName].remove(fCallback)

    @classmethod
    def clear(cls, oObject):
        """Clear all callbacks associated with the given object"""
        if oObject in cls._dSubscriptions:
            del cls._dSubscriptions[oObject]
