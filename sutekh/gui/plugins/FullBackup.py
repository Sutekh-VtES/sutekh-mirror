# FullBackup.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""Plugin to wrap zipfile backup and restore methods"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhDialog import do_complaint_warning, \
        do_exception_complaint
from sutekh.gui.SutekhFileWidget import ZipFileDialog
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhCountLogHandler
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.SutekhUtility import get_cs_id_name_table
import gtk
import os


class FullBackup(SutekhPlugin):
    """Provide access to ZipFileWrapper's backup and restore methods.

       Handle GUI aspects associated with restoring (ensuring everything
       reloads, etc.)
       """

    dTableVersions = {}
    aModelsSupported = ("MainWindow",)

    # Dialog and Menu Item Creation

    def get_menu_item(self):
        """Register on the Plugins menu"""
        if not self.check_versions() or not self.check_model_type():
            return None

        oBackup = gtk.MenuItem("Save a Full Backup")
        oBackup.connect("activate", self.activate_backup)
        oRestore = gtk.MenuItem("Restore a Full Backup")
        oRestore.connect("activate", self.activate_restore)

        return [('Backup', oBackup), ('Backup', oRestore)]

    # Menu responses

    def activate_backup(self, _oWidget):
        """Handle backup request"""
        oDlg = self.make_backup_dialog()
        oDlg.run()
        sFilename = oDlg.get_name()
        if sFilename:
            self.handle_backup_response(sFilename)

    def activate_restore(self, _oWidget):
        """Handle restore request"""
        oDlg = self.make_restore_dialog()
        oDlg.run()
        sFilename = oDlg.get_name()
        if sFilename:
            self.handle_restore_response(sFilename)

    # Backup

    def make_backup_dialog(self):
        """Create file dialog for backup"""
        sName = "Choose a file to save the full backup to ..."

        oDlg = ZipFileDialog(self.parent, sName, gtk.FILE_CHOOSER_ACTION_SAVE)
        oDlg.set_do_overwrite_confirmation(True)
        oDlg.show_all()

        return oDlg

    # pylint: disable-msg=R0201
    # This could be a function, but that won't add any clarity to this code
    def handle_backup_response(self, sFilename):
        """Handle response from backup dialog"""
        # pylint: disable-msg=W0703
        # we really do want all the exceptions
        try:
            oLogHandler = SutekhCountLogHandler()
            oProgressDialog = ProgressDialog()
            oProgressDialog.set_description("Saving backup")
            oLogHandler.set_dialog(oProgressDialog)
            oProgressDialog.show()
            oFile = ZipFileWrapper(sFilename)
            oFile.do_dump_all_to_zip(oLogHandler)
            oProgressDialog.destroy()
        except Exception, oException:
            oProgressDialog.destroy()
            sMsg = "Failed to write backup.\n\n%s" % oException
            do_exception_complaint(sMsg)

    # pylint: enable-msg=R0201

    # Restore

    def make_restore_dialog(self):
        """Create file chooser dialog for restore"""
        sName = "Restore a Full Backup ...."

        oDlg = ZipFileDialog(self.parent, sName, gtk.FILE_CHOOSER_ACTION_OPEN)

        oWarning = gtk.Label()
        oWarning.set_markup("<b>This will delete all existing Card Sets</b>")
        # pylint: disable-msg=E1101
        # plint doesn't pick up vbox methods correctly
        oDlg.vbox.pack_start(oWarning, expand=False)
        oDlg.vbox.reorder_child(oWarning, 0)
        oDlg.show_all()

        return oDlg

    def handle_restore_response(self, sFilename):
        """Handle response from the restore dialog"""
        bContinue = True

        if not os.path.exists(sFilename):
            bContinue = do_complaint_warning(
                    "Backup file %s does not seem to exist."
                    % sFilename) != gtk.RESPONSE_CANCEL

        if bContinue:
            dOldMap = get_cs_id_name_table()
            try:
                aEditable = self.parent.get_editable_panes()
                oLogHandler = SutekhCountLogHandler()
                oProgressDialog = ProgressDialog()
                oProgressDialog.set_description("Restoring backup")
                oLogHandler.set_dialog(oProgressDialog)
                oProgressDialog.show()
                oFile = ZipFileWrapper(sFilename)
                oFile.do_restore_from_zip(self.cardlookup, oLogHandler)
                # restore successful, refresh display
                aMessages = oFile.get_warnings()
                if aMessages:
                    sMsg = "The following warnings were reported:\n%s" % \
                            "\n".join(aMessages)
                    do_complaint_warning(sMsg)
                # Id's will not be preserved
                dNewMap = get_cs_id_name_table()
                self.parent.config_file.fix_profile_mapping(dOldMap, dNewMap)
                self.parent.update_to_new_db()
                oProgressDialog.destroy()
                self.parent.restore_editable_panes(aEditable)
            # pylint: disable-msg=W0703
            # we really do want all the exceptions
            except Exception, oException:
                oProgressDialog.destroy()
                sMsg = "Failed to restore backup.\n\n%s" % oException
                do_exception_complaint(sMsg)


plugin = FullBackup
