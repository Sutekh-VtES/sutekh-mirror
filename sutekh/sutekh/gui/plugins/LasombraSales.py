# LasombraSales.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""Display Lasombra single card prices in extra columns in the tree view"""

import gtk
import xlrd
import zipfile
import os
import cPickle
from cStringIO import StringIO
from sqlobject import SQLObjectNotFound
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.CellRendererIcons import CellRendererIcons, SHOW_TEXT_ONLY
from sutekh.gui.CardListModel import CardListModel
from sutekh.gui.FileOrUrlWidget import FileOrUrlWidget
from sutekh.core.SutekhObjects import PhysicalCard, PhysicalCardSet, IExpansion, IAbstractCard
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists

# pylint: disable-msg=R0904
# R0904 - gtk Widget, so has many public methods
class LasombraConfigDialog(SutekhDialog):
    """Dialog for configuring the LasombraSales plugin."""

    INVENTORY_URL = "http://www.thelasombra.com/inventory.zip"

    def __init__(self, oParent, bFirstTime=False):
        super(LasombraConfigDialog, self).__init__('Configure Lasombra Sales'
                ' Plugin', oParent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))

        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.set_spacing(10)

        oDescLabel = gtk.Label()
        if not bFirstTime:
            oDescLabel.set_markup('<b>Load the Lasombra '
                'sales inventory</b>')
        else:
            oDescLabel.set_markup('<b>Load the Lasombra '
                'sales inventory</b>\nChoose cancel to skip configuring the '
                'Lasombra sales plugin\nYou will not be prompted again')

        self._oFileSelector = FileOrUrlWidget(oParent,
            dUrls = {
                'www.thelasombra.com': self.INVENTORY_URL,
            },
            sTitle="Select inventory file ...",
        )

        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False)
        self.vbox.pack_start(self._oFileSelector, False, False)

        self.show_all()

    def get_binary_data(self):
        """Return the data for the inventory file."""
        return self._oFileSelector.get_binary_data()


class LasombraSales(CardListPlugin):
    """Add singles card sales information as extra columns to the card list
       view and allow sorting on these columns.
       """
    dTableVersions = {}
    aModelsSupported = [PhysicalCardSet, PhysicalCard, "MainWindow"]

    INVENTORY_XLS = "inventory.xls"

    _dWidths = {
            'Price' : 50,
            'Stock' : 50,
            }

    # Lasombra Expansion Name -> WW Expansion Name
    # (used to look up expansions on normal sheets)
    _dExpansionLookup = {
        '3rd Edition Sabbat': 'Third Edition',
        '10th Anniversary Set, broken up.': 'Tenth Anniversary',
        'Anarchs Set': 'Anarchs',
        'Black Hand Set': 'Blackhand',
        'Bloodlines Set': 'Bloodlines',
        'Camarilla Set': 'Camarilla Edition',
        'Gehenna Set, Rares and Commons': 'Gehenna',
        'Kindred Most Wanted Set': 'Kindred Most Wanted',
        'Keepers of Tradition': 'Keepers of Tradition',
        'Legacies of Blood Set': 'Legacy of Blood',
        'Lords of the Night Set': 'Lords of the Night',
        'Nights of Reckoning Set': 'Nights of Reckoning',
        'Sword of Caine set': 'Sword of Caine',
        'Twilight Rebellion': 'Twilight Rebellion',
    }

    # Lasombra Short Expansion Name -> Preferred Short Name
    # (used for crypt sheet expansion lookup)
    _dShortExpLookup = {
        '3rd': 'Third',
        'S': 'Sabbat',
        'W': 'SW',
        'B': 'BL',
        'V': 'VTES',
        'Camarilla': 'CE',
        'Black Hand': 'BH',
        'F': 'FN',
        'D': 'DS',
        'A': 'AH',
    }


    # (sCardName, sExpansionName) -> (fPrive, iStock)
    # Initialized when module first loaded
    _dPriceCache = None

    # List of warnings generated while populating the cache
    # Initialized when module first loaded
    _aWarnings = None

    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(LasombraSales, self).__init__(*aArgs, **kwargs)

        self._dCols = {}
        self._dCols['Price'] = self._render_price
        self._dCols['Stock'] = self._render_stock

        self._dSortDataFuncs = {}
        self._dSortDataFuncs['Price'] = self._get_data_price
        self._dSortDataFuncs['Stock'] = self._get_data_stock

        self._sPrefsPath = os.path.join(prefs_dir('Sutekh'), 'lasombra')
        self._sCacheFile = os.path.join(self._sPrefsPath, 'cache.dat')
        self._load_cache()

        if hasattr(self.model, "get_all_names_from_path"):
            self._get_key = self._get_key_for_card_set_list
        elif hasattr(self.model, "get_all_from_path"):
            self._get_key = self._get_key_for_card_list
        else:
            # This plugin is also registered on the main window
            self._get_key = None

    def _load_cache(self):
        """Attempt to load the cache from a pickle."""
        if self._dPriceCache is not None:
            return

        if not os.path.exists(self._sCacheFile):
            return

        fIn = file(self._sCacheFile, "rb")
        try:
            self.__class__._dPriceCache, self.__class__._aWarnings = \
                cPickle.load(fIn)
        except Exception, oExp:
            if self._aWarnings is None:
                # first time encountering error
                sMsg = "Lasombra Sales plugin cache can't be loaded" \
                    " -- ignoring it. Re-configure the plugin to attempt to" \
                    " correct the problem."
                self.__class__._aWarnings = [sMsg]
                do_complaint_error(sMsg)
        finally:
            fIn.close()

    def _initialize_cache(self, fInventory):
        """Initialize the price information from the Lasombra inventory."""
        # might be a zip file, check
        try:
            fZip = zipfile.ZipFile(fInventory, "r")
            aNames = fZip.namelist()
            if self.INVENTORY_XLS in aNames:
                sName = self.INVENTORY_XLS
            elif len(aNames) == 1:
                sName = aNames[0]
            else:
                raise ValueError("Unable to locate inventory spreadsheet"
                            " inside zip file.")
            sData = fZip.read(sName)
        except zipfile.BadZipfile, oE:
            # not a zip file, proceed as if it's a spreadsheet
            sData = fInventory.read()

        self.__class__._dPriceCache = {}
        self.__class__._aWarnings = []

        oBook = xlrd.open_workbook(self.INVENTORY_XLS, file_contents=sData)
        for oSheet in oBook.sheets():
            if oSheet.name == 'Specialty+Boxes':
                # Promos are a very special case, so we handle them seperately
                self._extract_promos(oSheet)
            elif oSheet.name == 'Crypt':
                # The crypt sheet also has its own special format
                self._extract_crypt(oSheet)
            else:
                # Try the default format
                self._extract_default(oSheet)

        fOut = file(self._sCacheFile, "wb")
        try:
            cPickle.dump((self._dPriceCache, self._aWarnings), fOut)
        finally:
            fOut.close()

    def _extract_promos(self, oSheet):
        """Find the start of the promo cards"""
        iStart = 0
        iEnd = 0
        for n in range(2, oSheet.nrows):
            oRow = oSheet.row(n)
            sVal = oRow[1].value
            sVal.strip()
            if sVal.endswith('Promos'):
                # Success
                iStart = n + 2
            elif sVal == 'Description' and iStart > 0 and n > iStart:
                # End found
                iEnd = n - 2
                break # No need to continue the loop

        if iStart <= 0:
            return

        if iEnd == 0:
            # If we missed the end for some reason
            iEnd = oSheet.nrows

        def get_exp(oAbsCard, oRow):
            """Retrieve the expansion object for the given card."""
            aCards = PhysicalCard.selectBy(abstractCardID=oAbsCard.id)
            for oCard in aCards:
                if oCard.expansion and oCard.expansion.name.startswith('Promo'):
                    return oCard.expansion
            # None means no expansion found.
            return None

        self._extract_cards(oSheet, iStart, iEnd, fExp=get_exp)

    def _extract_crypt(self, oSheet):
        """Extract prices from the crypt sheet."""
        oUnknownExpansions = set()

        def get_exp(oAbsCard, oRow):
            """Return the expansion for the given row."""
            sShort = str(oRow[5].value).strip()
            sShort = self._dShortExpLookup.get(sShort, sShort)
            try:
                oExp = IExpansion(sShort)
            except Exception, e:
                if sShort not in oUnknownExpansions:
                    sMsg = "Could not map expansion code '%s' found in Crypt" \
                           " sheet to unique expansion (setting expansion to" \
                           " unknown)." % (sShort,)
                    self._aWarnings.append(sMsg)
                    oUnknownExpansions.add(sShort)
                oExp = None
            return oExp

        tCols = (0, 3, 4) # quantity, name, price
        self._extract_cards(oSheet, 3, oSheet.nrows, fExp=get_exp, tCols=tCols)

    def _extract_default(self, oSheet):
        """Extract prices from the other sheets."""

        oFirstRow = oSheet.row(0)
        try:
            sVal = oFirstRow[1].value
            sVal = self._dExpansionLookup[sVal]
            sVal = sVal.strip()
            oExp = IExpansion(sVal)
        except Exception, e:
            sMsg = "Could not determine expansion for sheet '%s' (skipping sheet)" % (oSheet.name,)
            self._aWarnings.append(sMsg)
            return

        self._extract_cards(oSheet, 3, oSheet.nrows, fExp=lambda oC, oR: oExp)

    def _extract_cards(self, oSheet, iStart, iEnd, fExp, tCols=(0, 1, 2)):
        """Extract the card info from the cards.

           oSheet - the sheet to extract from
           iStart, iEnd - range of rows to process
           fExp - function fExp(oAbsCard, oRow) -> oExp for
                  obtaining the expansion for a given row and card.
                  fExp should return None if the expansion could not be
                  determined.
           tCols - quantity, name and price column numbers (default 0, 1, 2).
           """

        QUANTITY, NAME, PRICE = tCols

        for n in range(iStart, iEnd):
            oRow = oSheet.row(n)

            # skip blank rows and some summary lines
            if not (oRow[NAME].value and oRow[QUANTITY].value and oRow[PRICE].value):
                    continue

            try:
                sCardName = str(oRow[NAME].value)
                iStock = int(oRow[QUANTITY].value)
                fPrice = float(oRow[PRICE].value)
            except Exception, e:
                sMsg = "Could not read card information from sheet %s," \
                       " row %d (skipping row)" % (oSheet.name, n)
                self._aWarnings.append(sMsg)
                continue

            # Fix advanced vampires
            sCardName = sCardName.replace('(Adv)', '(Advanced)')

            try:
                oAbsCard = IAbstractCard(sCardName)
            except SQLObjectNotFound:
                continue

            oExp = fExp(oAbsCard, oRow)
            if oExp is None:
                sExp = CardListModel.sUnknownExpansion
            else:
                sExp = oExp.name

            tKey = (sCardName, sExp)
            if tKey in self._dPriceCache:
                fOldPrice, iOldStock = self._dPriceCache[tKey]
                sMsg = "Found duplicate information for card '%s' in" \
                       " expansion '%s' (replacing original entry ; " \
                       " original price: %.2f ; original stock: %d)" \
                       % (sCardName, sExp, fOldPrice, iOldStock)
                self._aWarnings.append(sMsg)
            self._dPriceCache[tKey] = (fPrice, iStock)

            tKey = (sCardName, None)
            fOverallPrice = self._dPriceCache.get(tKey, (fPrice, 0))[0]
            iOverallStock = self._dPriceCache.get(tKey, (fPrice, 0))[1]
            self._dPriceCache[tKey] = (min(fPrice, fOverallPrice), iStock + iOverallStock)

    # pylint: enable-msg=W0142

    def _get_key_for_card_list(self, oIter):
        """For the given iterator, get the associated card name and expansion
           name. This tuple is the key used to look up prices and stock numbers
           if the cache.  None is returned for the expansion name if there is
           no relevant expansion.  None is returned as the *key* if there is no
           relevant card.

           This is the key retrieval version for CardListModels.
           """
        oPath = self.model.get_path(oIter)
        sName, sExpansion, iCount, iDepth = self.model.get_all_from_path(oPath)
        if sName is not None:
            # sExpansion may be None.
            return sName, sExpansion
        else:
            return None

    def _get_key_for_card_set_list(self, oIter):
        """For the given iterator, get the associated card name and expansion
           name. This tuple is the key used to look up prices and stock numbers
           if the cache.  None is returned for the expansion name if there is
           no relevant expansion.  None is returned as the *key* if there is no
           relevant card.

           This is the key retrieval version for CardSetListModels.
           """
        oPath = self.model.get_path(oIter)
        sName, sExpansion, sCardSet = self.model.get_all_names_from_path(oPath)
        if sName is not None:
            # sExpansion may be None.
            return sName, sExpansion
        else:
            return None

    # Rendering Functions

    # pylint: disable-msg=R0201, W0613
    # Making these functions for clarity
    # several unused paramaters due to function signatures

    def _get_data_price(self, tKey):
        """get the price for the given key"""
        return self._dPriceCache.get(tKey, (None, None))[0]

    def _render_price(self, oColumn, oCell, oModel, oIter):
        """Display the card price."""
        tKey = self._get_key(oIter)
        fPrice = self._get_data_price(tKey)
        if fPrice is None:
            oCell.set_data(["-"], [None], SHOW_TEXT_ONLY)
        else:
            oCell.set_data(["%.2f" % (fPrice,)], [None], SHOW_TEXT_ONLY)

    def _get_data_stock(self, tKey):
        """get the stock for the given key"""
        return self._dPriceCache.get(tKey, (0.0, 0))[1]

    def _render_stock(self, oColumn, oCell, oModel, oIter):
        """Display the number of cards available."""
        tKey = self._get_key(oIter)
        iStock = self._get_data_stock(tKey)
        if iStock is None:
            oCell.set_data(["-"], [None], SHOW_TEXT_ONLY)
        else:
            oCell.set_data(["%d" % (iStock,)], [None], SHOW_TEXT_ONLY)

    # pylint: enable-msg=R0201
    # Dialog and Menu Item Creation

    def get_menu_item(self):
        """Register on 'Plugins' menu"""
        if not self.check_versions() or not self.check_model_type():
            return None

        if self.model is not None:
            oToggle = gtk.CheckMenuItem("Show Lasombra Prices")
            oToggle.set_active(False)
            oToggle.connect('toggled', self._toggle_prices)
            return [('Plugins', oToggle)]
        else:
            oConfigMenuItem = gtk.MenuItem("Configure Lasombra Sales Plugin")
            oConfigMenuItem.connect("activate", self.config_activate)
            return [('Plugins', oConfigMenuItem)]

    def setup(self):
        """Prompt the user to download/setup the plugin the first time"""
        if not os.path.exists(self._sPrefsPath):
            # Looks like the first time
            oDialog = LasombraConfigDialog(self.parent, True)
            self.handle_config_response(oDialog)
            # Don't get called next time
            ensure_dir_exists(self._sPrefsPath)

    # pylint: disable-msg=W0613
    # oMenuWidget needed by gtk function signature
    def config_activate(self, oMenuWidget):
        """Launch the configuration dialog."""
        oDialog = LasombraConfigDialog(self.parent, False)
        self.handle_config_response(oDialog)

    def handle_config_response(self, oConfigDialog):
        """Handle the response from the config dialog"""
        iResponse = oConfigDialog.run()

        if iResponse == gtk.RESPONSE_OK:
            fInventory = StringIO(oConfigDialog.get_binary_data())
            self._initialize_cache(fInventory)

            if self._aWarnings:
                do_complaint_error('\n'.join(self._aWarnings))

        # get rid of the dialog
        oConfigDialog.destroy()

    # W0613 - oWidget required by function signature
    def _toggle_prices(self, oToggle):
        """Handle menu activation"""
        if oToggle.get_active():
            self.set_cols_in_use(['Price', 'Stock'])
        else:
            self.set_cols_in_use([])

    # W0613: oModel required by gtk's function signature
    def sort_column(self, oModel, oIter1, oIter2, oGetData):
        """Stringwise comparision of oIter1 and oIter2.

           Return -1 if oIter1 < oIter, 0 in ==, 1 if >
           """
        tKey1 = self._get_key(oIter1)
        tKey2 = self._get_key(oIter2)
        if tKey1 is None or tKey2 is None:
            # Not comparing cards, sort on name only
            sName1 = self.model.get_name_from_iter(oIter1).lower()
            sName2 = self.model.get_name_from_iter(oIter2).lower()
            if sName1 < sName2:
                iRes = -1
            elif sName1 > sName2:
                iRes = 1
            else:
                iRes = 0
            return iRes

        oVal1 = oGetData(tKey1)
        oVal2 = oGetData(tKey2)

        if oVal1 < oVal2:
            iRes = -1
        elif oVal1 > oVal2:
            iRes = 1
        else:
            # Values agree, so sort keys themselves
            iRes = cmp(tKey1, tKey2)
        return iRes

    # pylint: enable-msg=W0613

    # Actions

    def set_cols_in_use(self, aCols):
        """Add columns to the view"""
        # pylint: disable-msg=W0612
        # iDir is returned, although we don't need it
        iSortCol, iDir = self.model.get_sort_column_id()
        # pylint: enable-msg=W0612
        if iSortCol is not None and iSortCol > 1:
            # We're changing the columns, so restore sorting to default
            self.model.set_sort_column_id(0, 0)

        for oCol in self._get_col_objects():
            self.view.remove_column(oCol)

        if self._dPriceCache is None:
            do_complaint_error("Lasombra price data not available. " \
                " Use the configuration option under the main menu " \
                " to provide it.")
            return

        for iNum, sCol in enumerate(aCols):
            oCell = CellRendererIcons()
            oColumn = gtk.TreeViewColumn(sCol, oCell)
            oColumn.set_cell_data_func(oCell, self._dCols[sCol])
            oColumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            oColumn.set_fixed_width(self._dWidths.get(sCol, 100))
            oColumn.set_resizable(True)
            self.view.insert_column(oColumn, iNum + 3)
            oColumn.set_sort_column_id(iNum + 3)
            self.model.set_sort_func(iNum + 3, self.sort_column,
                    self._dSortDataFuncs[sCol])

    def get_cols_in_use(self):
        """Get which extra columns have been added to view"""
        return [oCol.get_property("title") for oCol in self._get_col_objects()]

    def _get_col_objects(self):
        """Get the actual TreeColumn in the view"""
        return [oCol for oCol in self.view.get_columns() if
                oCol.get_property("title") in self._dCols]

# pylint: disable-msg=C0103
# accept plugin name
plugin = LasombraSales
