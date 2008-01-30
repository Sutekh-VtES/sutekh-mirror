# CardSetExportHTML.py
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
import time
import os
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, IAbstractCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error, do_complaint_warning
from sutekh.io.WriteArdbXML import WriteArdbXML
from sutekh.SutekhInfo import SutekhInfo
from sutekh.SutekhUtility import pretty_xml
try:
    from xml.etree.ElementTree import ElementTree, Element, SubElement
except ImportError:
    from elementtree.ElementTree import ElementTree, Element, SubElement

class CardSetExportHTML(CardListPlugin):
    dTableVersions = { AbstractCardSet: [2, 3],
                       PhysicalCardSet: [2, 3, 4]}
    aModelsSupported = [AbstractCardSet, PhysicalCardSet]

    # HTML style definition
    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None

        iDF = gtk.MenuItem("Export Card Set to HTML")
        iDF.connect("activate", self.activate)
        return iDF

    def get_desired_menu(self):
        return "Plugins"

    def activate(self, oWidget):
        oDlg = self.make_dialog()
        oDlg.run()
        oDlg.destroy()

    def make_dialog(self):
        oDlg = SutekhDialog("Filename to save as", self.parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oFileChooser = gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_SAVE)
        oDlg.vbox.pack_start(self.oFileChooser)
        self.oTextButton = gtk.CheckButton("Include Card _Texts?")
        self.oTextButton.set_active(False)
        oDlg.vbox.pack_start(self.oTextButton)
        oDlg.connect("response", self.handle_response)
        oDlg.show_all()
        return oDlg

    def handle_response(self, oWidget, oResponse):
        if oResponse ==  gtk.RESPONSE_OK:
            sFileName = self.oFileChooser.get_filename()
            if sFileName is not None:
                if os.path.exists(sFileName):
                    bContinue = do_complaint_warning("Overwrite existing file %s?" % sFileName) != gtk.RESPONSE_CANCEL
                    if not bContinue:
                        return
                try:
                    fOut = file(sFileName, "w")
                except Exception, oExp:
                    sMsg = "Failed to open output file.\n\n" + str(oExp)
                    do_complaint_error(sMsg)
                    return
                if self.view.cSetType == PhysicalCardSet:
                    oCardSet = PhysicalCardSet.byName(self.view.sSetName)
                elif self.view.cSetType == AbstractCardSet:
                    oCardSet = AbstractCardSet.byName(self.view.sSetName)
                else:
                    fOut.close()
                    sMsg = "unsupported Card Set type"
                    do_complaint_error(sMsg)
                    return
                bDoText = False
                if self.oTextButton.get_active():
                    bDoText = True
                oETree = self.gen_tree(self.view.sSetName,
                        oCardSet.author,
                        oCardSet.comment,
                        self.get_cards(),
                        bDoText)
                # We're producing XHTML output, so we need a doctype header
                fOut.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
                # We have the elementree with the needed information,
                # need to produce decent HTML output
                oETree.write(fOut)
                fOut.close()

    def gen_tree(self, sSetName, sAuthor, sComment, dCards, bDoText):
        """Convert the Cards to a element tree containing 'nice' HTML"""
        oDocRoot = Element('html', xmlns='http://www.w3.org/1999/xhtml', lang='en')
        oDocRoot.attrib["xml:lang"] = 'en'
        oHead = SubElement(oDocRoot, 'head')
        oStyle = SubElement(oHead, 'style', type="text/css")
        oArdbXMLObj = WriteArdbXML()
        (dVamps, iCryptSize, iMin, iMax, fAvg) = oArdbXMLObj.extract_crypt(dCards)
        (dLib, iLibSize) = oArdbXMLObj.extract_library(dCards)
        # Is there a better idea here?
        oStyle.text = """
                  body {
                     background: #000000;
                     color: #AAAAAA;
                     margin: 0
                  }

                  div#crypt { background: #000000; }

                  div#info {
                     background: #331111;
                     width: 100%;
                  }

                  div#library {
                     background: #000000
                     url("http://www.white-wolf.com/VTES/images/CardsImg.jpg")
                     no-repeat scroll top right;
                  }

                  h1 {
                     font-size: x-large;
                     margin-left: 1cm
                  }

                  h2 {
                     font-size: large;
                     margin-left: 1cm
                  }

                  h3 {
                     font-size: large;
                     border-bottom: solid;
                     border-width: 2px;
                  }

                  h4 {
                     font-size: medium;
                     margin-bottom: 0px
                  }

                  div#cardtext { background: #000000 }

                  div#cardtext h4 { text-decoration: underline; }

                  div#cardtext h5 {
                     font-weight: normal;
                     text-decoration: underline;
                     margin-left: 1em;
                     margin-bottom: 0.1em;
                  }

                  div#cardtext div.text { margin-left: 1em; }

                  div#cardtext ul {
                     list-style-type: none;
                     margin-top: 0.1em;
                     margin-bottom: 0.1em;
                     padding-left: 1em;
                  }

                  div#cardtext .label { font-style: italic; }

                  div#cardtext p {
                     margin-left: 0.3em;
                     margin-bottom: 0.1em;
                     margin-top: 0em;
                  }

                  table { line-height: 70% }

                  .generator {
                     color: #555555;
                     position: relative;
                     top: 20px;
                  }

                  .librarytype { }

                  .stats {
                     color: #777777;
                     margin: 5px;
                  }

                  .tablevalue {
                      color: #aaaa88;
                      margin: 5px
                  }

                  .value { color: #aaaa88 }

                  hr { color: sienna }

                  p { margin-left: 60px }

                  a {
                      color: #aaaa88;
                      margin: 5px;
                      text-decoration: none
                  }

                  a:hover {
                      color: #ffffff;
                      margin: 5px;
                      text-decoration: none
                  } """
        oTitle = SubElement(oHead, "title")
        oTitle.text = "VTES deck : %s by %s" % (sSetName, sAuthor)

        oBody = SubElement(oDocRoot, "body")
        oInfo = SubElement(oBody, "div", id="info")
        oName = SubElement(oInfo, "h1", id="nametitle")
        oSpan = SubElement(oName, "span")
        oSpan.text = "Deck Name :"
        oSpan = SubElement(oName, "span", id="namevalue")
        # class is a reserved word, so need to set attribute here
        oSpan.attrib["class"] = "value"
        oSpan.text = sSetName
        oAuthor = SubElement(oInfo, "h2", id="authortitle")
        oSpan = SubElement(oAuthor, "span")
        oSpan.text = "Author : "
        oSpan = SubElement(oAuthor, "span", id="authornamevalue")
        oSpan.attrib["class"] = "value"
        oSpan.text = sAuthor
        oDesc = SubElement(oInfo, "h2", id="description")
        oSpan = SubElement(oDesc, "span")
        oSpan.text = "Description : "
        oPara = SubElement(oInfo, "p")
        oSpan = SubElement(oPara, "span", id="descriptionvalue")
        oSpan.attrib["class"] = "value"
        oSpan.text = sComment

        oCrypt = SubElement(oBody, "div", id="crypt")
        oCryptTitle = SubElement(oCrypt, "h3", id="crypttitle")
        oSpan = SubElement(oCryptTitle, "span")
        oSpan.text = "Crypt "
        oSpan = SubElement(oCryptTitle, "span", id="cryptstats")
        oSpan.attrib["class"] = "stats"
        oSpan.text = "[%d vampires] Capacity min : %d max : %d average : %.2f" \
                % (iCryptSize, iMin, iMax, fAvg)
        oCryptTable = SubElement(oCrypt, "div", id="crypttable")
        oTheTable = SubElement(oCryptTable, "table", summary="Crypt card table")
        oCryptTBody = SubElement(oTheTable, "tbody")

        # Need to sort vampires by number, then capacity
        aSortedVampires = []
        for iId, sVampName in dVamps:
            oCard = IAbstractCard(sVampName)
            iCount = dVamps[(iId, sVampName)]
            if len(oCard.creed) > 0:
                iCapacity = oCard.life
                sClan = "Imbued"
            else:
                iCapacity = oCard.capacity
                sClan = [oClan.name for oClan in oCard.clan][0]
            aSortedVampires.append((iCount, iCapacity, sVampName, oCard, sClan))
        # We reverse sort by Capacity and Count, by normal sort by name
        # fortunately, python's sort is stable, so this works
        aSortedVampires.sort(key=lambda x: x[2])
        aSortedVampires.sort(key=lambda x: (x[0], x[1]), reverse=True)
        # This doesn't get the same ordering for advanced vampires as
        # the XSLT approach, but I don't care enough to tweak that
        for iCount, iCapacity, sVampName, oCard, sClan in aSortedVampires:
            oTR = SubElement(oCryptTBody, "tr")
            # Card Count
            oTD = SubElement(oTR, "td")
            oSpan = SubElement(oTD, "span")
            oSpan.attrib["class"] = "tablevalue"
            oSpan.text = "%dx" % iCount
            # Card Name + Monger href
            oTD = SubElement(oTR, "td")
            oSpan = SubElement(oTD, "span")
            oSpan.attrib["class"] = "tablevalue"
            if oCard.level is not None:
                sName = sVampName.replace(' (Advanced)', '')
                sMongerURL = "http://monger.vekn.org/showcard.html?NAME=%s ADV" % sName
            else:
                sName = sVampName
                sMongerURL = "http://monger.vekn.org/showcard.html?NAME=%s" % sVampName
            sMongerURL = sMongerURL.replace(' ', '%20') # May be able to get away without this, but being safe
            oMongerHREF = SubElement(oSpan, "a", href=sMongerURL)
            oMongerHREF.text = sName
            oTD = SubElement(oTR, "td")
            oSpan = Element("span")
            oSpan.attrib["class"] = "tablevalue"
            # Advanced status
            if oCard.level is not None:
                oSpan.text = '(Advanced)'
                oTD.append(oSpan)
            # Capacity
            oTD = SubElement(oTR, "td")
            oSpan = SubElement(oTD, "span")
            oSpan.attrib["class"] = "tablevalue"
            oSpan.text = str(iCapacity)
            # Disciplines
            oTD = SubElement(oTR, "td")
            oSpan = SubElement(oTD, "span")
            oSpan.attrib["class"] = "tablevalue"
            oSpan.text = oArdbXMLObj.get_disciplines(oCard)
            # Title
            oTD = SubElement(oTR, "td")
            oSpan = Element("span")
            oSpan.attrib["class"] = "tablevalue"
            if len(oCard.title) > 0:
                oSpan.text = [oTitle.name for oTitle in oCard.title][0]
                oTD.append(oSpan)
            # Clan
            oTD = SubElement(oTR, "td")
            oSpan = SubElement(oTD, "span")
            oSpan.attrib["class"] = "tablevalue"
            oSpan.text = "%s (group %d)" % (sClan, oCard.group)

        # Library cards
        oLib = SubElement(oBody, "div", id="library")
        oLibTitle = SubElement(oLib, "h3", id="librarytitle")
        oSpan = SubElement(oLibTitle, "span")
        oSpan.text = "Library "
        oSpan = SubElement(oLibTitle, "span", id="librarystats")
        oSpan.attrib["class"] = "stats"
        oSpan.text = '[%d cards]' % iLibSize
        oLibTable = SubElement(oLib, "div")
        oLibTable.attrib["class"] = "librarytable"

        dTypes = {}
        # Group by type
        for tKey in dLib:
            iId, sName, sType = tKey
            iCount = dLib[tKey]
            dTypes.setdefault(sType, [0])
            dTypes[sType][0] += iCount
            dTypes[sType].append((iCount, sName))

        aSortedLibCards = sorted(dTypes.items())

        # Need to sort by type
        for sType, aList in aSortedLibCards:
            oTypeHead = SubElement(oLibTable, "h4")
            oTypeHead.attrib["class"] = "librarytype"
            oSpan = SubElement(oTypeHead, "span")
            oSpan.text = sType
            oSpan = SubElement(oTypeHead, "span")
            oSpan.attrib["class"] = "stats"
            oSpan.text = "[%d]" % aList[0]
            oTable = SubElement(oLibTable, "table", summary="Library card table")
            oTBody = SubElement(oTable, "tbody")
            # Sort alphabetically within cards
            for iCount, sName in sorted(aList[1:], key=lambda x: x[1]):
                oTR = SubElement(oTBody, "tr")
                oTD = SubElement(oTR, "td")
                oSpan = SubElement(oTD, "span")
                oSpan.attrib["class"] = "tablevalue"
                oSpan.text = "%dx" % iCount
                oTD = SubElement(oTR, "td")
                oSpan = SubElement(oTD, "span")
                oSpan.attrib["class"] = "tablevalue"
                sMongerURL = "http://monger.vekn.org/showcard.html?NAME=%s" % sName
                sMongerURL = sMongerURL.replace(' ', '%20') # May be able to get away without this, but being safe
                oMongerHRef = SubElement(oSpan, "a", href=sMongerURL)
                oMongerHRef.text = sName

        if bDoText:
            oCardText = SubElement(oBody, "div", id="cardtext")
            oTextHead = SubElement(oCardText, "h3")
            oTextHead.attrib["class"] = "cardtext"
            oSpan = SubElement(oTextHead, "span")
            oSpan.text = "Card Texts"
            # Vampires
            oCryptTextHead = SubElement(oCardText, "h4")
            oCryptTextHead.attrib["class"] = "librarytype"
            oCryptTextHead.text = "Crypt"
            for iCount, iCapacity, sVampName, oCard, sClan in aSortedVampires:
                oCardName = SubElement(oCardText, "h5")
                oCardName.text = sVampName
                oList = SubElement(oCardText, "ul")
                # Capacity
                oListItem = SubElement(oList, "li")
                oSpan = SubElement(oListItem, "span")
                oSpan.attrib["class"] = "label"
                oSpan.text = "Capacity:"
                oSpan = SubElement(oListItem, "span")
                oSpan.attrib["class"] = "capacity"
                oSpan.text = str(iCapacity)
                # Group
                oListItem = SubElement(oList, "li")
                oSpan = SubElement(oListItem, "span")
                oSpan.attrib["class"] = "label"
                oSpan.text = "Group:"
                oSpan = SubElement(oListItem, "span")
                oSpan.attrib["class"] = "group"
                oSpan.text = str(oCard.group)
                # Clan
                oListItem = SubElement(oList, "li")
                oSpan = SubElement(oListItem, "span")
                oSpan.attrib["class"] = "label"
                oSpan.text = "Clan:"
                oSpan = SubElement(oListItem, "span")
                oSpan.attrib["class"] = "clan"
                oSpan.text = sClan
                # Disciplines
                oListItem = SubElement(oList, "li")
                oSpan = SubElement(oListItem, "span")
                oSpan.attrib["class"] = "label"
                oSpan.text = "Disciplines:"
                oSpan = SubElement(oListItem, "span")
                oSpan.attrib["class"] = "disciplines"
                oSpan.text = oArdbXMLObj.get_disciplines(oCard)
                # Text
                oTextDiv = SubElement(oCardText, "div")
                oTextDiv.attrib["class"] = "text"
                for sLine in oCard.text.splitlines():
                    oPara = SubElement(oTextDiv, 'p')
                    oPara.text = sLine

            # Library cards
            for sType, aList in aSortedLibCards:
                oTypeHead = SubElement(oCardText, "h4")
                oTypeHead.attrib["class"] = "libraryttype"
                oTypeHead.text = sType
                for iCount, sName in sorted(aList[1:], key=lambda x: x[1]):
                    oCard = IAbstractCard(sName)
                    oCardHead = SubElement(oCardText, "h5")
                    oCardHead.attrib["class"] = "cardname"
                    oCardHead.text = sName
                    oList = Element("ul") # We'll add this to oCardText if it's not empty
                    # Requirements
                    aClan = [x.name for x in oCard.clan]
                    if len(aClan) > 0:
                        oListItem = SubElement(oList, "li")
                        oSpan = SubElement(oListItem, "span")
                        oSpan.attrib["class"] = "label"
                        oSpan.text = "Requires:"
                        oSpan = SubElement(oListItem, "span")
                        oSpan.attrib["class"] = "requirement"
                        oSpan.text = "/".join(aClan)
                    # Cost
                    if oCard.costtype is not None:
                        oListItem = SubElement(oList, "li")
                        oSpan = SubElement(oListItem, "span")
                        oSpan.attrib["class"] = "label"
                        oSpan.text = "Cost:"
                        oSpan = SubElement(oListItem, "span")
                        oSpan.attrib["class"] = "cost"
                        oSpan.text = "%d %s" % (oCard.cost, oCard.costtype)
                    # Disciplines
                    sDisciplines = oArdbXMLObj.get_disciplines(oCard)
                    if sDisciplines != "":
                        oListItem = SubElement(oList, "li")
                        oSpan = SubElement(oListItem, "span")
                        oSpan.attrib["class"] = "label"
                        oSpan.text = "Disciplines:"
                        oSpan = SubElement(oListItem, "span")
                        oSpan.attrib["class"] = "disciplines"
                        oSpan.text = sDisciplines
                    # Add List
                    if len(oList) > 0:
                        oCardText.append(oList)
                    # Text
                    oTextDiv = SubElement(oCardText, "div")
                    oTextDiv.attrib["class"] = "text"
                    for sLine in oCard.text.splitlines():
                        oPara = SubElement(oTextDiv, 'p')
                        oPara.text = sLine

        # Closing stuff
        oGenerator = SubElement(oBody, "div")
        oSpan = SubElement(oGenerator, "span")
        oSpan.attrib["class"] = "generator"
        oSpan.text = "Crafted with : Sutekh [ %s ]. [ %s ]" \
                % (SutekhInfo.VERSION_STR,
                        time.strftime('%Y-%m-%d', time.localtime()))

        pretty_xml(oDocRoot)
        return ElementTree(oDocRoot)

    def get_cards(self):
        dDict = {}
        for oCard in self.model.getCardIterator(None):
            oACard = IAbstractCard(oCard)
            dDict.setdefault((oACard.id, oACard.name), 0)
            dDict[(oACard.id, oACard.name)] += 1
        return dDict

plugin = CardSetExportHTML
