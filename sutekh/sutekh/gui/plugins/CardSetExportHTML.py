# CardSetExportHTML.py
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.SutekhObjects import PhysicalCardSet, AbstractCardSet, IAbstractCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.WriteArdbXML import WriteArdbXML
from pkg_resources import resource_string

try:
    import libxml2
    import libxslt
    bHaveXmlParser = True
except ImportError:
    bHaveXmlParser = False

class CardSetExportHTML(CardListPlugin):
    dTableVersions = {"AbstractCardSet" : [2,3], 
                      "PhysicalCardSet" : [2,3]}
    aModelsSupported = ["AbstractCardSet","PhysicalCardSet"]
    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None

        global bHaveXmlParser
        if not bHaveXmlParser:
            print "Could not load libxml2 and/or libxslt. Can't export to HTML."
            return None

        # Check we can find the deck2html.xsl file
        try:
            sDeckXSL = resource_string(__name__,"deck2html.xsl")
            styledoc = libxml2.parseDoc(sDeckXSL)
            self._style = libxslt.parseStylesheetDoc(styledoc)
        except libxml2.parserError:
            print "Unable to load deck2html.xsl style sheet."
            return None

        # Check if we can enable the "Include Card Text" Option
        try:
            sDeckXSL = resource_string(__name__,"deck2html_with_text.xsl")
            styledocText = libxml2.parseDoc(sDeckXSL)
            self._styleText = libxslt.parseStylesheetDoc(styledocText)
        except libxml2.parserError:
            self._styleText=None

        iDF = gtk.MenuItem("Export Card Set to HTML")
        iDF.connect("activate", self.activate)
        return iDF

    def getDesiredMenu(self):
        return "CardSet"

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()
        oDlg.destroy()

    def makeDialog(self):
        parent = self.view.getWindow()
        self.oDlg = gtk.Dialog("Filename to save as",parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oFileChooser=gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_SAVE)
        self.oFileChooser.set_do_overwrite_confirmation(True)
        self.oDlg.vbox.pack_start(self.oFileChooser)
        if self._styleText is not None:
            self.TextButton=gtk.CheckButton("Include Card _Texts?")
            self.TextButton.set_active(False)
            self.oDlg.vbox.pack_start(self.TextButton)
        self.oDlg.connect("response", self.handleResponse)
        self.oDlg.show_all()
        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
        if oResponse ==  gtk.RESPONSE_OK:
            sFileName=self.oFileChooser.get_filename()
            if sFileName is not None:
                if self.view.sSetType == "PhysicalCardSet":
                    oCardSet = PhysicalCardSet.byName(self.view.sSetName)
                elif self.view.sSetType == "AbstractCardSet":
                    oCardSet = AbstractCardSet.byName(self.view.sSetName)
                else:
                    # TODO: alert user to error somehow
                    return
                oW = WriteArdbXML()
                oDoc = oW.genDoc(self.view.sSetName,
                        oCardSet.author,
                        oCardSet.comment,
                        self.getCards())
                doc = libxml2.parseDoc(oDoc.toprettyxml())
                bDoText=False
                if self._styleText is not None:
                    if self.TextButton.get_active():
                        bDoText=True
                if bDoText:
                    result = self._styleText.applyStylesheet(doc, None)
                else:
                    result = self._style.applyStylesheet(doc, None)
                self._style.saveResultToFilename(sFileName, result, 0)

    def getCards(self):
        dDict = {}
        for oCard in self.model.getCardIterator(None):
            oCard = IAbstractCard(oCard)
            dDict.setdefault((oCard.id,oCard.name),0)
            dDict[(oCard.id,oCard.name)]+=1
        return dDict

plugin = CardSetExportHTML
