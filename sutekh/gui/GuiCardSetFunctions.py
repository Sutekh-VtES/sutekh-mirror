# GuiCardSetFunctions.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Useful utilities for managing card sets that need to access the gui"""

import gtk
import datetime
import logging
from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.gui.SutekhDialog import do_complaint_warning, do_complaint, \
        do_complaint_error, do_exception_complaint
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCardSet
from sutekh.core.CardLookup import LookupFailed
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.RenameDialog import RenameDialog, PROMPT, RENAME, REPLACE
from sutekh.core.CardSetUtilities import delete_physical_card_set, \
        find_children, has_children, detect_loop, get_loop_names, break_loop


def reparent_card_set(oCardSet, oNewParent):
    """Helper function to ensure that reparenting a card set doesn't
       cause loops"""
    if oNewParent:
        # Can only be a problem if the new parent is a card set
        oOldParent = oCardSet.parent
        oCardSet.parent = oNewParent
        oCardSet.syncUpdate()
        if detect_loop(oCardSet):
            oCardSet.parent = oOldParent
            oCardSet.syncUpdate()
            do_complaint('Changing parent of %s to %s introduces a'
                    ' loop. Leaving the parent unchanged.' % (
                        oCardSet.name, oNewParent.name),
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE)
        else:
            return True
    else:
        oCardSet.parent = oNewParent
        oCardSet.syncUpdate()
        return True
    return False


def reparent_all_children(sCardSetName, aChildren):
    """Handle reparenting a list of children gracefully"""
    if aChildren:
        oCardSet = IPhysicalCardSet(sCardSetName)
        for oChildCS in aChildren:
            reparent_card_set(oChildCS, oCardSet)


def check_ok_to_delete(oCardSet):
    """Check if the user is OK with deleting the card set."""
    bChildren = has_children(oCardSet)
    bCards = len(oCardSet.cards) > 0
    iResponse = gtk.RESPONSE_OK
    if bCards and bChildren:
        iResponse = do_complaint_warning("Card Set %s Not Empty and"
                " Has Children. Really Delete?" % oCardSet.name)
    elif bCards:
        iResponse = do_complaint_warning("Card Set %s Not Empty."
                " Really Delete?" % oCardSet.name)
    elif bChildren:
        iResponse = do_complaint_warning("Card Set %s"
                " Has Children. Really Delete?" % oCardSet.name)
    return iResponse == gtk.RESPONSE_OK


def create_card_set(oMainWindow):
    """Create a new card set from the edit dialog"""
    oDialog = CreateCardSetDialog(oMainWindow)
    oDialog.run()
    sName = oDialog.get_name()
    if sName:
        if PhysicalCardSet.selectBy(name=sName).count() != 0:
            do_complaint_error("Card Set %s already exists." % sName)
            return None
        sAuthor = oDialog.get_author()
        sComment = oDialog.get_comment()
        oParent = oDialog.get_parent()
        bInUse = oDialog.get_in_use()
        _oCS = PhysicalCardSet(name=sName, author=sAuthor,
                comment=sComment, parent=oParent, inuse=bInUse)
    return sName


# import helpers
def get_import_name(oHolder, iClashMode=PROMPT):
    """Helper for importing a card set holder.

       Deals with prompting the user for a new name if required, and properly
       dealing with child card sets if the user decides to replace an
       existing card set."""

    def setup_for_replace():
        """Little helper function to handle getting children and deleting
           the card set consistently"""
        oCS = IPhysicalCardSet(oHolder.name)
        aChildren = find_children(oCS)
        # Delete existing card set
        delete_physical_card_set(oHolder.name)
        return aChildren

    bRename = False
    if oHolder.name:
        # Check if we need to prompt for rename
        if PhysicalCardSet.selectBy(name=oHolder.name).count() != 0:
            bRename = True
    else:
        # No name, need to prompt
        bRename = True
    aChildren = []
    if bRename:
        if iClashMode == PROMPT:
            oDlg = RenameDialog(oHolder.name)
            iResponse = oDlg.run()
            if iResponse == RENAME:
                oHolder.name = oDlg.sNewName
            elif iResponse == REPLACE:
                # Get child card sets
                aChildren = setup_for_replace()
            else:
                # User cancelled, so bail
                oHolder.name = None
            oDlg.destroy()
        elif iClashMode == REPLACE:
            aChildren = setup_for_replace()
        elif iClashMode == RENAME:
             # Create a unique name based on our current name
            sTime = datetime.datetime.today().strftime('%Y-%m-%d %H:%M')
            sBaseName = '%s (imported %s)' % (oHolder.name, sTime)
            sNewName = sBaseName
            iCount = 0
            while PhysicalCardSet.selectBy(name=sNewName).count() != 0:
                iCount += 1
                sNewName = '%s (%d)' % (sBaseName, iCount)
            oHolder.name = sNewName

    return oHolder, aChildren


def update_open_card_sets(oMainWindow, sSetName):
    """Update open copies of the card set sSetName to database changes
       (from imports, etc.)"""
    for oFrame in oMainWindow.find_cs_pane_by_set_name(sSetName):
        oFrame.update_to_new_db()
    oMainWindow.reload_pcs_list()


def update_card_set(oCardSet, oMainWindow):
    """Update the details of the card set when the user edits them."""
    sOldName = oCardSet.name
    oEditDialog = CreateCardSetDialog(oMainWindow, oCardSet=oCardSet)
    oEditDialog.run()
    sName = oEditDialog.get_name()
    if not sName:
        return  # bail
    # To ensure we don't send unnecessary changed signals, only update
    # if things have changed
    if sName != oCardSet.name:
        oCardSet.name = sName
    sAuthor = oEditDialog.get_author()
    if sAuthor != oCardSet.author:
        oCardSet.author = sAuthor
    sComment = oEditDialog.get_comment()
    if sComment != oCardSet.comment:
        oCardSet.comment = sComment
    sAnnotations = oEditDialog.get_annotations()
    if sAnnotations != oCardSet.annotations:
        oCardSet.annotations = sAnnotations
    bInUse = oEditDialog.get_in_use()
    if bInUse != oCardSet.inuse:
        oCardSet.inuse = bInUse
    oParent = oEditDialog.get_parent()
    if oParent != oCardSet.parent:
        reparent_card_set(oCardSet, oParent)
    oCardSet.syncUpdate()
    # Update frame menu
    for oFrame in oMainWindow.find_cs_pane_by_set_name(sOldName):
        oFrame.menu.update_card_set_menu(oCardSet)
        # update_card_set_menu does the needed magic for us
    oMainWindow.reload_pcs_list()


# Common to MainMenu import code and plugins
def import_cs(fIn, oParser, oMainWindow, sSetName=None):
    """Create a card set from the given file object."""
    oHolder = CardSetHolder()

    # pylint: disable-msg=W0703
    # we really do want all the exceptions
    try:
        oParser.parse(fIn, oHolder)
    except Exception, oExp:
        sMsg = "Reading the card set failed with the following error:\n" \
               "%s\n The file is probably not in the format the Parser" \
               " expects.\nAborting" % oExp
        do_exception_complaint(sMsg)
        # Fail out
        return

    if oHolder.num_entries < 1:
        # No cards seen, so abort
        do_complaint_error("No cards found in the card set.\n"
                "The file may not be in the format the Parser expects.\n"
                "Aborting")
        return

    # Display any warnings
    aWarnings = oHolder.get_warnings()
    if aWarnings:
        sMsg = "The following warnings were reported:\n%s" % \
                "\n".join(aWarnings)
        logging.warn(sMsg)
        iResponse = do_complaint_warning("%s\nContinue with the import?"
                % sMsg)
        if iResponse != gtk.RESPONSE_OK:
            return  # bail out
        oHolder.clear_warnings()

    # Handle naming issues if needed
    if sSetName and not oHolder.name:
        # Use provided name if we don't have one from the set
        oHolder.name = sSetName
    oHolder, aChildren = get_import_name(oHolder)
    if not oHolder.name:
        return  # User bailed
    # Create CS
    try:
        oHolder.create_pcs(oCardLookup=oMainWindow.cardLookup)
        reparent_all_children(oHolder.name, aChildren)
        aWarnings = oHolder.get_warnings()
        if aWarnings:
            sMsg = "Card Set Created.\n" \
                    "The following warnings were reported during the final" \
                    " import:\n%s" % "\n".join(aWarnings)
            logging.warn(sMsg)
            do_complaint(sMsg, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE)
    except RuntimeError, oExp:
        sMsg = "Creating the card set failed with the following error:\n" \
               "%s\nAborting" % oExp
        do_exception_complaint(sMsg)
        return
    except LookupFailed, oExp:
        return

    if oMainWindow.find_cs_pane_by_set_name(oHolder.name):
        # Already open, so update to changes
        update_open_card_sets(oMainWindow, oHolder.name)
    else:
        # Not already open, so open a new copy
        oMainWindow.add_new_physical_card_set(oHolder.name)


def break_existing_loops():
    """Ensure there are no loops in the database"""
    for oCS in PhysicalCardSet.select():
        if detect_loop(oCS):
            sLoop = "->".join(get_loop_names(oCS))
            sBreakName = break_loop(oCS)
            do_complaint(
                    'Loop %s in the card sets relationships.\n'
                    'Breaking at %s' % (sLoop, sBreakName),
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE)
            # We break the loop, and let the user fix things,
            # rather than try and be too clever
