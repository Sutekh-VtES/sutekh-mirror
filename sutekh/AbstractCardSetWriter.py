# AbstractCardSetWriter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Write cards from a AbstractCardSet out to an XML file which
looks like:
<abstractcardset name='AbstractCardSetName' author='Author' comment='Comment' annotations='annotations'>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />
</abstractcardset>
"""

from sutekh.SutekhObjects import AbstractCardSet
from sqlobject import SQLObjectNotFound
from xml.dom.ext import PrettyPrint
from xml.dom.minidom import getDOMImplementation

class AbstractCardSetWriter(object):
    sMyVersion="1.0"

    def genDoc(self,sAbstractCardSetName):
        dCards = {}

        try:
            oACS = AbstractCardSet.byName(sAbstractCardSetName)
            sAuthor=oACS.author
            sComment=oACS.comment
            sAnnotations=oACS.annotations
            if sAnnotations is None:
                # prettytoxml will barf if this isn't done
                sAnnotations=''
        except SQLObjectNotFound:
            print "Failed to find %s" % sAbstractCardSetName
            return

        for oAbs in oACS.cards:
            try:
                dCards[(oAbs.id, oAbs.name)] += 1
            except KeyError:
                dCards[(oAbs.id, oAbs.name)] = 1


        oDoc = getDOMImplementation().createDocument(None,'abstractcardset',None)

        oCardsElem = oDoc.firstChild
        oCardsElem.setAttribute('sutekh_xml_version',self.sMyVersion)
        oCardsElem.setAttribute('name',sAbstractCardSetName)
        oCardsElem.setAttribute('author',sAuthor)
        oCardsElem.setAttribute('comment',sComment)
        oCardsElem.setAttribute('annotations',sAnnotations)

        for tKey, iNum in dCards.iteritems():
            iId, sName = tKey
            oCardElem = oDoc.createElement('card')
            oCardElem.setAttribute('id',str(iId))
            oCardElem.setAttribute('name',sName)
            oCardElem.setAttribute('count',str(iNum))
            oCardsElem.appendChild(oCardElem)

        return oDoc

    def write(self,fOut,sAbstractCardSetName):
        oDoc=self.genDoc(sAbstractCardSetName)
        PrettyPrint(oDoc,fOut)
