# PhysicalCardSetWriter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Write physical cards from a PhysicalCardSet out to an XML file which
looks like:
<physicalcardset name='SetName' author='Author' comment='Comment' annotations='annotations'>
  <card id='3' name='Some Card' count='5' expansion='Some Expansion' />
  <card id='3' name='Some Card' count='2' expansion='Some Other Expansion' />
  <card id='5' name='Some Other Card' count='2' expansion='Some Other Expansion' />
</physicalcardset>
"""

from sutekh.core.SutekhObjects import PhysicalCardSet
from sqlobject import SQLObjectNotFound
from xml.dom.minidom import getDOMImplementation

class PhysicalCardSetWriter(object):
    sMyVersion = "1.0"

    def genDoc(self, sPhysicalCardSetName):
        dPhys = {}

        try:
            oPCS = PhysicalCardSet.byName(sPhysicalCardSetName)
            sAuthor = oPCS.author
            sComment = oPCS.comment
            sAnnotations = oPCS.annotations
            if sAnnotations is None:
                # prettytoxml will barf if this isn't done
                sAnnotations = ''
        except SQLObjectNotFound:
            print "Failed to find %s" % sPhysicalCardSetName
            return

        for oCard in oPCS.cards:
            oAbs = oCard.abstractCard
            try:
                dPhys[(oAbs.id, oAbs.name, oCard.expansion)] += 1
            except KeyError:
                dPhys[(oAbs.id, oAbs.name, oCard.expansion)] = 1

        oDoc = getDOMImplementation().createDocument(None, 'physicalcardset', None)

        oCardsElem = oDoc.firstChild
        oCardsElem.setAttribute('sutekh_xml_version', self.sMyVersion)
        oCardsElem.setAttribute('name', sPhysicalCardSetName)
        oCardsElem.setAttribute('author', sAuthor)
        oCardsElem.setAttribute('comment', sComment)
        oCardsElem.setAttribute('annotations', sAnnotations)

        for tKey, iNum in dPhys.iteritems():
            iId, sName, sExpansion = tKey
            oCardElem = oDoc.createElement('card')
            oCardElem.setAttribute('id', str(iId))
            oCardElem.setAttribute('name', sName)
            if sExpansion is None:
                oCardElem.setAttribute('expansion', 'None Specified')
            else:
                oCardElem.setAttribute('expansion', sExpansion)
            oCardElem.setAttribute('count', str(iNum))
            oCardsElem.appendChild(oCardElem)

        return oDoc

    def write(self, fOut, sPhysicalCardSetName):
        oDoc = self.genDoc(sPhysicalCardSetName)
        fOut.write(oDoc.toprettyxml())
