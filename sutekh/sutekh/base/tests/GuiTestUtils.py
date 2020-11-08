# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# Copyright 2008, 2018 Neil Muller <drnlmuller+sutekh@gmail.com>

"""Utilities and support classes that are useful for testing bits of the
   gui."""

from ..core.BaseAdapters import IAbstractCard
from ..gui.MessageBus import MessageBus
from ..gui.CardSetListModel import ParentCountMode, ExtraLevels, ShowMode

# Useful mock classes


class LocalTestListener:
    """Listener used in the test cases.

       Pass bKeepCards to keep a copy of the all the cards passed to the
       listener for validation checks."""

    def __init__(self, oModel, bKeepCards):
        self.bLoadCalled = False
        self.iCnt = 0
        self.aCards = []
        self._bKeepCards = bKeepCards
        MessageBus.subscribe(oModel, 'load', self.load)
        MessageBus.subscribe(oModel, 'alter_card_count', self.alter_count)
        MessageBus.subscribe(oModel, 'add_new_card', self.alter_count)

    def load(self, aCards):
        """Called when the model is loaded."""
        self.bLoadCalled = True
        self.iCnt = len(aCards)
        if self._bKeepCards:
            self.aCards = [IAbstractCard(oCard) for oCard in aCards]

    def alter_count(self, _oCard, iChg):
        """Called when the model alters the card count or adds cards"""
        self.iCnt += iChg


class DummyCardSetController:
    """Dummy controller object for config tests"""

    def __init__(self):
        self.bReload = False

    # pylint: disable=protected-access
    # We allow access via these properties

    view = property(fget=lambda self: self)
    frame = property(fget=lambda self: self)
    pane_id = property(fget=lambda self: 10)
    config_frame_id = property(fget=lambda self: 'pane10')

    # pylint: enable=protected-access

    # pylint: disable=no-self-use, missing-docstring
    # dummy functions, so they're empty

    def set_parent_count_col_vis(self, _bVal):
        return

    def reload_keep_expanded(self):
        return

    def queue_reload(self):
        self.bReload = True  # For use in listener test cases

# Utility functions to inspect various models


def count_all_cards(oModel):
    """Count all the entries in the model."""
    iTotal = 0
    oIter = oModel.get_iter_first()
    while oIter:
        iTotal += oModel.iter_n_children(oIter)
        oIter = oModel.iter_next(oIter)
    return iTotal


def count_second_level(oModel):
    """Count all the second level entries in the model."""
    iTotal = 0
    oIter = oModel.get_iter_first()
    while oIter:
        oChildIter = oModel.iter_children(oIter)
        while oChildIter:
            iTotal += oModel.iter_n_children(oChildIter)
            oChildIter = oModel.iter_next(oChildIter)
        oIter = oModel.iter_next(oIter)
    return iTotal


def _get_all_child_counts(oModel, oIter, sName=''):
    """Recursively descend the children of oIter, getting all the
       relevant info."""
    # We use get_value rather than get_name_from_iter, as we're
    # not worried about the encoding issues here, and it saves time.
    aList = []
    oChildIter = oModel.iter_children(oIter)
    while oChildIter:
        if sName:
            sListName = sName + ':' + oModel.get_value(oChildIter, 0)
        else:
            sListName = oModel.get_value(oChildIter, 0)
        # similiarly, we use get_value rather than the count functions
        # for speed as well
        aList.append((oModel.get_value(oChildIter, 1),
                      oModel.get_value(oChildIter, 2), sListName))
        if oModel.iter_n_children(oChildIter) > 0:
            oGCIter = oModel.iter_children(oChildIter)
            # We unroll a level for speed reasons
            # This is messy - we could easily do this as a recursive call
            # in all cases, but we hit this function 4 times for almost
            # every iteration of the test, so sacrificing some readablity
            # for speed is worthwhile
            while oGCIter:
                sGCName = sListName + ':' + \
                    oModel.get_value(oGCIter, 0)
                if oModel.iter_n_children(oGCIter) > 0:
                    aList.extend(_get_all_child_counts(oModel,
                                                       oGCIter,
                                                       sGCName))
                else:
                    aList.append((oModel.get_value(oGCIter, 1),
                                  oModel.get_value(oGCIter, 2), sGCName))
                oGCIter = oModel.iter_next(oGCIter)
        oChildIter = oModel.iter_next(oChildIter)
    return aList


def get_all_counts(oModel):
    """Return a list of iCnt, iParCnt, sCardName tuples from the Model"""
    return _get_all_child_counts(oModel, None)


def count_top_level(oModel):
    """Count all the top level entries in the model."""
    iTotal = oModel.iter_n_children(None)
    return iTotal


def get_card_names(oModel):
    """Return a set of all the cards listed in the model"""
    oIter = oModel.get_iter_first()
    aResults = set()
    while oIter:
        oChildIter = oModel.iter_children(oIter)
        while oChildIter:
            aResults.add(oModel.get_value(oChildIter, 0))
            oChildIter = oModel.iter_next(oChildIter)
        oIter = oModel.iter_next(oIter)
    return aResults

# Helper functions for managing model test cases


def reset_modes(oModel):
    """Set the model to the minimal state."""
    # pylint: disable=protected-access
    # we need to access protected methods
    # The database signal handling means that all CardSetListModels
    # associated with a card set will update when send_changed_signal is
    # called, so we reset the model state so these calls will be cheap if
    # this models is affected when we're not explicitly testing it.
    oModel._change_parent_count_mode(ParentCountMode.IGNORE_PARENT)
    oModel._change_level_mode(ExtraLevels.NO_SECOND_LEVEL)
    oModel.bEditable = False
    oModel._change_count_mode(ShowMode.THIS_SET_ONLY)


def cleanup_models(aModels):
    """Utility function to cleanup models signals, etc."""
    for oModel in aModels:
        oModel.cleanup()
