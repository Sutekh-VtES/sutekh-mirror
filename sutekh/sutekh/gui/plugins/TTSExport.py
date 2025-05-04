# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2020 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for exporting to Table Top Simulator"""

import json
import logging
import os
import re
import string
import sys

from gi.repository import Gtk

from sutekh.base.core.BaseTables import PhysicalCardSet, AbstractCard
from sutekh.base.core.BaseAdapters import IKeyword
from sutekh.base.gui.SutekhFileWidget import ExportDialog, ImportDialog
from sutekh.base.gui.SutekhDialog import do_complaint_error
from sutekh.base.Utility import safe_filename, move_articles_to_back, to_ascii

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.Utility import to_ascii
from sutekh.SutekhUtility import is_crypt_card, strip_group_from_name, find_all_group_versions

# Not sure how stable this name is under module updates - guess we'll see
MODULE_NAME = "VtES_TTS_Module.json"

# File must be newer than this date
DATE_SUPPORTED = 1745563000

# Including this directly is a bit horrible, but it's also simple
DECK_TEMPLATE = """
{
  "SaveName": "",
  "GameMode": "",
  "Gravity": 0.5,
  "PlayArea": 0.5,
  "Date": "",
  "Table": "",
  "Sky": "",
  "Note": "",
  "Rules": "",
  "XmlUI": "",
  "LuaScript": "",
  "LuaScriptState": "",
  "ObjectStates": [
    {
      "Name": "Deck",
      "Transform": {
        "posX": -8.708832,
        "posY": 1.1591903,
        "posZ": -8.239059,
        "rotX": 5.22204255E-06,
        "rotY": 179.999985,
        "rotZ": 180.0,
        "scaleX": 1.0,
        "scaleY": 1.0,
        "scaleZ": 1.0
      },
      "Nickname": "",
      "Description": "",
      "GMNotes": "",
      "ColorDiffuse": {
        "r": 0.713235259,
        "g": 0.713235259,
        "b": 0.713235259
      },
      "Locked": false,
      "Grid": true,
      "Snap": true,
      "IgnoreFoW": false,
      "Autoraise": true,
      "Sticky": true,
      "Tooltip": true,
      "GridProjection": false,
      "HideWhenFaceDown": true,
      "Hands": false,
      "SidewaysCard": false,
      "DeckIDs": [
      ],
      "CustomDeck": {
      },
      "XmlUI": "",
      "LuaScript": "",
      "LuaScriptState": "",
      "ContainedObjects": [
      ],
      "GUID": "28d019"
    },
    {
      "Name": "Deck",
      "Transform": {
        "posX": 2.75010633,
        "posY": -0.003134966,
        "posZ": 0.0665216446,
        "rotX": 6.383264E-06,
        "rotY": 180.0007,
        "rotZ": 180.0,
        "scaleX": 1.0,
        "scaleY": 1.0,
        "scaleZ": 1.0
      },
      "Nickname": "",
      "Description": "",
      "GMNotes": "",
      "ColorDiffuse": {
        "r": 0.713235259,
        "g": 0.713235259,
        "b": 0.713235259
      },
      "Locked": false,
      "Grid": true,
      "Snap": true,
      "IgnoreFoW": false,
      "Autoraise": true,
      "Sticky": true,
      "Tooltip": true,
      "GridProjection": false,
      "HideWhenFaceDown": true,
      "Hands": false,
      "SidewaysCard": false,
      "DeckIDs": [
      ],
      "CustomDeck": {
      },
      "XmlUI": "",
      "LuaScript": "",
      "LuaScriptState": "",
      "ContainedObjects": [
      ],
      "GUID": "233766"
    }
  ],
  "TabStates": {},
  "VersionNumber": ""
}
"""

# Default card transforms
CRYPT_TRANSFORM = {
    "posX": 0.03614205,
    "posY": 1.3037678,
    "posZ": -0.14448297,
    "rotX": 0.00705644675,
    "rotY": 180.0,
    "rotZ": 179.997849,
    "scaleX": 1.0,
    "scaleY": 1.0,
    "scaleZ": 1.0,
}

LIB_TRANSFORM = {
    "posX": -4.97454071,
    "posY": 1.30109692,
    "posZ": 6.69189024,
    "rotX": 4.56903763E-05,
    "rotY": 180.000839,
    "rotZ": 179.999786,
    "scaleX": 1.0,
    "scaleY": 1.0,
    "scaleZ": 1.0,
}

# We handle cases where our simple normalisation fails
SPECIAL_CASES = {
    'bolesaw gutowski': 'boleslaw gutowski',
    'lodin (olaf holte)': 'lodin olaf holte',
    'bang nakh  tigers claws': 'bang nakh - tigers claws',
    'khazars diary (endless night)': 'khazars diary endless night',
    'ohoyo hopoksia (bastet)' : 'ohoyo hopoksia bastet',
    'sacre-cur cathedral, france': 'sacre-coeur cathedral, france',
    'kpist m/45': 'kpist m45'
}


NONNAME = re.compile(r'\W')


def fix_nickname(sName):
    """Fix unexpected issues with the nickname"""
    # We lowercase stuff as the JSON file sometimes has weird capitalisation
    sName = sName.lower()
    sName = to_ascii(sName)
    # Quotes are a bit inconsistent, so we strip them
    sName = sName.replace("'", "").replace('"', '').replace('`', '')
    # Pentex can be weird
    sName = sName.replace('pentextm', 'pentex(tm)')
    return sName


def add_group_and_advanced(oCard, sName):
    """KRCG names cards as 'Card Name (GX)', so we need to match that"""
    if oCard.group:
        if oCard.level:
            sName = f'{sName} (g{oCard.group} adv)'
        else:
            if oCard.group == -1:
                sName = f'{sName} (any)'
            else:
                sName = f'{sName} (g{oCard.group})'
    return sName


def make_json_name(oCard):
    """Create the corresponding TTS json name for the given card"""
    sJSONName = strip_group_from_name(oCard.name)
    sJSONName = to_ascii(sJSONName.lower())
    # Advanced is handled in the group name
    sJSONName = sJSONName.replace(' (advanced)', '')
    sJSONName = add_group_and_advanced(oCard, sJSONName)
    # strip quotes to simplify matching
    sJSONName = sJSONName.replace("'", "").replace('"', '').replace('`', '')
    #sJSONName = NONNAME.sub('', sJSONName)
    #if sJSONName in SPECIAL_CASES:
    #    sJSONName = SPECIAL_CASES[sJSONName]
    return sJSONName


def make_alternative_json_name(oCard):
    """Alternative formatting for those cards that use a different
       convention"""
    sJSONName = move_articles_to_back(strip_group_from_name(oCard.name))
    sJSONName = add_group_and_advanced(oCard, sJSONName)
    sJSONName = to_ascii(sJSONName)
    return sJSONName.lower()


def is_card_bag(oData):
    """Does this look like a bag to search for cards?"""
    if oData['Name'] != 'Bag':
        return False
    if oData['Nickname'].startswith('Cards: '):
        return True
    # Custom bags
    if oData['Nickname'].startswith('Other: New '):
        return True
    return False


def fix_deck_ids(dCards):
    """Fix incorrect "CustomDeck" ids in the list.

       Sometimes cards in the json file have the wrong value specified
       for the deck id in the "CustomDeck" section. This appears to
       be because of copy-n-paste errors in the TTS json file. Since
       TTS appears to use this as a cache key, it results in it using
       the wrong images, even though the actual urls in the section
       are correct.
       """
    for _sName, dCardData in dCards.items():
        sTrueID = "%d" % (dCardData["CardID"] // 100)
        if sTrueID not in dCardData["CustomDeck"]:
            # they lied to us
            # CustomDeck is a dict with a single entry
            _sKey, dContent = dCardData["CustomDeck"].popitem()
            # The values are correct enough, but the key is wrong
            # logging.info(f"Fixing {sTrueID} in {_sName} - saw {_sKey}")
            dCardData["CustomDeck"][sTrueID] = dContent


def parse_tts_file(sFileName):
    """Internal function to parse the TTS file and create the
       dictionary of cards."""
    try:
        with open(sFileName, 'r') as oFile:
            dJsonData = json.load(oFile)
            # Check if the file is new enough
            if 'EpochTime' not in dJsonData:
                logging.warning(
                        "Unable to determine date for: %s", sFileName)
                logging.warning("Skipping file")
                return False
            iEpoch = int(dJsonData['EpochTime'])
            if iEpoch < DATE_SUPPORTED:
                logging.warning(
                        "TSS Module: %s is outdated", sFileName)
                logging.warning("Skipping file")
                return False
            # Extract the relevant chunks from the file
            try:
                dCards = {}
                for oCandidate in dJsonData['ObjectStates']:
                    if not is_card_bag(oCandidate):
                        continue
                    # Extract cards
                    if 'ContainedObjects' not in oCandidate:
                        # Some bags may be empty. Bleh.
                        continue
                    for oObj in oCandidate['ContainedObjects']:
                        sKey = fix_nickname(oObj['Nickname'])
                        if sKey in dCards:
                            iIDNum1 = int(dCards[sKey]["CardID"])
                            iIDNum2 = int(oObj["CardID"])
                            if iIDNum2 > iIDNum1:
                                dCards[sKey] = oObj
                        else:
                            dCards[sKey] = oObj
                #fix_deck_ids(dCards)
                return dCards
            except (KeyError, IndexError) as oErr:
                logging.warning(
                    "Failed to extract data from TTS Module file: %s", sFileName)
                logging.warning("Error in bag: %s (GUID: %s)",
                                 oCandidate['Nickname'], oCandidate['GUID'])
                logging.warning("Error in bag: %s", oCandidate['Nickname'])
                logging.warning("Exception: %s", oErr)
    except json.JSONDecodeError as oErr:
        # Log error for verbose out
        logging.warning("Failed to parse TTS Module file: %s", sFileName)
        logging.warning("Exception: %s", oErr)


class TTSExportDialog(ExportDialog):
    """Override the base Export Dialog so we can add Gtk.Entry fields
       for the crypt and library nicknames"""

    def __init__(self, parent, oCardSet):
        super().__init__("Filename to save as", parent,
                            '%s.json' % safe_filename(oCardSet.name))
        self.add_filter_with_pattern('JSON Files', ['*.json'])

        oEntryGrid = Gtk.Grid()
        oEntryGrid.attach(Gtk.Label(label="Crypt TTS Name"), 0, 0, 1, 1)
        self._oCryptNickName = Gtk.Entry()
        self._oCryptNickName.set_text(f"{oCardSet.name} crypt")
        oEntryGrid.attach(self._oCryptNickName, 1, 0, 5, 1)
        oEntryGrid.attach(Gtk.Label(label="Library TTS Name"), 0, 1, 1, 1)
        self._oLibNickName = Gtk.Entry()
        self._oLibNickName.set_text(f"{oCardSet.name} library")
        oEntryGrid.attach(self._oLibNickName, 1, 1, 5, 1)

        oEntryGrid.set_column_homogeneous(True)
        oEntryGrid.set_row_homogeneous(True)

        self.vbox.pack_start(oEntryGrid, False, True, 0)

        self._sCryptName = None
        self._sLibName = None

    def button_response(self, _oWidget, iResponse):
        """Handle button press events"""
        if iResponse == Gtk.ResponseType.OK:
            self.sName = self.get_filename()
            self._sCryptName = self._oCryptNickName.get_text().strip()
            self._sLibName = self._oLibNickName.get_text().strip()
        self.destroy()

    def get_crypt_nickname(self):
        return self._sCryptName

    def get_lib_nickname(self):
        return self._sLibName


class TTSExport(SutekhPlugin):
    """Provides a dialog for selecting a filename, then generates
       a TTS readable json file"""

    dTableVersions = {PhysicalCardSet: (7,)}
    aModelsSupported = (PhysicalCardSet, 'MainWindow')

    dGlobalConfig = {
        'tts module file': 'string(default=None)',
    }

    sMenuName = "Export to a TTS json file"

    sHelpCategory = "card_sets:actions"

    sHelpText = """Export to a Table Top Simulator JSON file.

                   This exports the current card set to a JSON file that
                   can be loaded into Table Top Simulator using the
                   'Saved Objects' menu.

                   You can set the names TTS will display for the crypt
                   and library decks.

                   This plugin needs to read data from the TTS VtES module.


                   Due to slow updates with the steam workshop module,
                   this requires the custom module hosted at
                   https://github.com/drnlm/VtES_TTS_Module_Generator

                   It will not work unless that module has been
                   installed.
                   """

    sConfigKey = 'tts module file'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dTTSData = {}
        self.load_tts_json_file()

    def setup(self):
        """1st time setup tasks"""
        sPrefsValue = self.get_config_item(self.sConfigKey)
        if sPrefsValue is None:
            # Try to find the TTS VtES module
            self.find_tts_file(None)
            self.load_tts_json_file()

    def load_tts_json_file(self):
        """Load the info from the TTS module"""
        sTTSModulePath = self.get_config_item(self.sConfigKey)
        if not sTTSModulePath:
            logging.warning("No config item")
            return
        if not os.path.exists(sTTSModulePath):
            logging.warning("Path not found: %s", sTTSModulePath)
            return
        self._dTTSData = parse_tts_file(sTTSModulePath)

    def check_enabled(self):
        """Only enable the export menu if we successfully loaded the TTS
           module data"""
        if not self._dTTSData:
            return False
        return True

    def find_tts_file(self, _oWidget):
        """Try find the TTS json file in the most likely location"""
        sCand = ''
        if sys.platform.startswith("win"):
            if "APPDATA" in os.environ:
                sCand = os.path.join(os.environ["APPDATA"],
                                     "Tabletop Simulator", "Mods",
                                     "Workshop", MODULE_NAME)
        else:
            sCand = os.path.join(os.path.expanduser("~"), ".local", "share",
                                 "Tabletop Simulator", "Mods",
                                 "Workshop", MODULE_NAME)
        oDlg = ImportDialog("Select TTS VtES plugin file", self.parent)
        if os.path.exists(sCand):
            # If the module is where we expect, set it as the default choice
            oDlg.set_filename(sCand)
        oDlg.run()
        sResult = oDlg.get_name()
        if sResult:
            self.set_config_item(self.sConfigKey, sResult)
        else:
            # Set this to the empty string, so we don't ask every time
            self.set_config_item(self.sConfigKey, "")

    def get_menu_item(self):
        """Register with the 'Export Card Set' Menu"""
        if self.model is None:
            # Main window, so add a config entry
            oConfig = Gtk.MenuItem(label="Configure TTS Export Plugin")
            oConfig.connect('activate', self.find_tts_file)
            return ('File Preferences', oConfig)
        if not self.check_enabled():
            # Don't enable export if we don't have the TTS module installed
            logging.debug('TTS export menu disabled')
            return None
        oExport = Gtk.MenuItem(label=self.sMenuName)
        oExport.connect("activate", self.do_export)
        return ('Export Card Set', oExport)

    def do_export(self, _oWidget):
        """Display the export dialog and hand off the response"""
        oCardSet = self._get_card_set()
        if not oCardSet:
            return
        oDlg = self.make_dialog(oCardSet)
        oDlg.run()
        self.handle_response(oCardSet, oDlg.get_name(),
                             oDlg.get_crypt_nickname(),
                             oDlg.get_lib_nickname())

    def make_dialog(self, oCardSet):
        """Create the dialog"""
        oDlg = TTSExportDialog(self.parent, oCardSet)
        oDlg.show_all()
        return oDlg

    def handle_response(self, oCardSet, sFilename, sCryptName, sLibName):
        """Actually do the export"""
        if sFilename is None:
            return
        dDeck = json.loads(DECK_TEMPLATE)
        aCrypt = []
        aLibrary = []
        aMissing = set()
        for oCard in oCardSet.cards:
            # Need to turn name into the JSON file version
            sJSONName = make_json_name(oCard.abstractCard)
            sAltName = make_alternative_json_name(oCard.abstractCard)
            if sJSONName not in self._dTTSData:
                # Check if it's just using the card name instead
                if sAltName not in self._dTTSData:
                    aMissing.add((oCard.abstractCard.name, sJSONName))
                    logging.warning("Unable to find an entry for %s (%s)",
                                    oCard.abstractCard.name, sJSONName)
                    continue
                else:
                    sJSONName = sAltName
            if is_crypt_card(oCard.abstractCard):
                aCrypt.append(sJSONName)
            else:
                aLibrary.append(sJSONName)
        if aMissing:
            aText = []
            for tDetails in aMissing:
                aText.append("Unable to find an entry for %s (%s)" % tDetails)
            do_complaint_error('\n'.join(aText))
            return
        dCrypt = dDeck['ObjectStates'][0]
        dCrypt['Nickname'] = sCryptName
        dLibrary = dDeck['ObjectStates'][1]
        dLibrary['Nickname'] = sLibName
        for sName in sorted(aCrypt):
            oObj = self._dTTSData[sName]
            dTTSCard = oObj.copy()
            dTTSCard['Transform'] = CRYPT_TRANSFORM
            dCrypt['DeckIDs'].append(dTTSCard['CardID'])
            dCrypt['CustomDeck'].update(dTTSCard['CustomDeck'])
            dCrypt['ContainedObjects'].append(dTTSCard)
        for sName in sorted(aLibrary):
            oObj = self._dTTSData[sName]
            dTTSCard = oObj.copy()
            dTTSCard['Transform'] = LIB_TRANSFORM
            dLibrary['DeckIDs'].append(dTTSCard['CardID'])
            dLibrary['CustomDeck'].update(dTTSCard['CustomDeck'])
            dLibrary['ContainedObjects'].append(dTTSCard)
        with open(sFilename, 'w') as oFile:
            json.dump(dDeck, oFile, indent=2)

    def list_unmatched_cards(self):
        """List any unmatched cards in the full cardlist"""
        # This is mainly a debugging / testing helper and not intended to
        # be called by the actual gui
        oIIegal = IKeyword('not for legal play')
        dAllCards = {}
        aFound = set()
        for oCard in AbstractCard.select():
            # We want this so we can identify missed storyline cards as such
            dAllCards[make_json_name(oCard)] = oCard
        aLegalMissed = []
        aNotLegalMissed = []
        aTTSMissed = []
        for sName, oCard in dAllCards.items():
            if sName not in self._dTTSData:
                sAltName = make_alternative_json_name(oCard)
                # Some cards just use the card name, not the nickname
                if sAltName not in self._dTTSData:
                    if oIIegal in oCard.keywords:
                        aNotLegalMissed.append((sName, oCard))
                    else:
                        aLegalMissed.append((sName, oCard))
                else:
                    aFound.add(sAltName)
            else:
                aFound.add(sName)
        # Check TTS file for entries we haven't matched to a card
        for sName in self._dTTSData:
            if sName not in aFound:
                aTTSMissed.append(sName)
        # We print these, because this is testing related
        print('Legal Cards Missed')
        print('------------------')
        print()
        for sNickName, oCard in aLegalMissed:
            aExpansions = sorted(set([x.expansion.name for x in oCard.rarity]))
            print("%s (%s) - (from %s)" % (oCard.name, sNickName, " , ".join(aExpansions)))
        print()
        print('Not Legal Cards Missed')
        print('----------------------')
        print()
        for sNickName, oCard in aNotLegalMissed:
            aExpansions = sorted(set([x.expansion.name for x in oCard.rarity]))
            print("%s (%s) - (from %s)" % (oCard.name, sNickName, " , ".join(aExpansions)))
        print()
        print('TTS Entries with no matching card')
        print('---------------------------------')
        for sName in aTTSMissed:
            print("%s" % sName)
        print()

    def run_checks(self):
        """Print missed cards."""
        self.list_unmatched_cards()


plugin = TTSExport
