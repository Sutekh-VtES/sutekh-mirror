# test_WriteArdbHTML.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an Ardb HTML file"""

import time
from sutekh.SutekhInfo import SutekhInfo
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import aCardSetNames, \
        get_phys_cards
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.io.WriteArdbHTML import  WriteArdbHTML, sHTMLStyle
import unittest

sExpected1 = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta content="text/html; charset=&quot;us-ascii&quot;" http-equiv="content-type" />
    <style type="text/css">%s</style>
    <title>VTES deck : Test Set 1 by A test author</title>
  </head><body>
    <div id="info">
      <h1 id="nametitle">
        <span>Deck Name :</span>
        <span class="value" id="namevalue">Test Set 1</span>
      </h1><h2 id="authortitle">
        <span>Author : </span>
        <span class="value" id="authornamevalue">A test author</span>
      </h2><h2 id="description">
        <span>Description : </span>
      </h2><p>
        <span class="value" id="descriptionvalue">A test comment</span>
      </p>
    </div><div id="crypt">
      <h3 id="crypttitle">
        <span>Crypt</span>
        <span>[1 vampires] Capacity min : 4 max : 4 average : 4.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showvamp.html?NAME=Abebe">Abebe</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">4</span>
              </td><td>
                <span class="tablevalue">nec obf thn</span>
              </td><td />
              <td>
                <span class="tablevalue">Samedi (group 4)</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div id="library">
      <h3 id="librarytitle">
        <span>Library</span>
        <span class="stats" id="librarystats">[4 cards]</span>
      </h3><div class="librarytable">
        <h4 class="librarytype">
          <span>Action</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Abbot">Abbot</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=.44%%20Magnum">.44 Magnum</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=AK-47">AK-47</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Master</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Abombwe">Abombwe</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div>
      <span class="generator">Crafted with : Sutekh [ %s ]. [ %s ]</span>
    </div>
  </body>
</html>""" % (sHTMLStyle, SutekhInfo.VERSION_STR,
        time.strftime('%Y-%m-%d', time.localtime()))

sExpected2 = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta content="text/html; charset=&quot;us-ascii&quot;" http-equiv="content-type" />
    <style type="text/css">%s</style>
    <title>VTES deck : Test Set 1 by A test author</title>
  </head><body>
    <div id="info">
      <h1 id="nametitle">
        <span>Deck Name :</span>
        <span class="value" id="namevalue">Test Set 1</span>
      </h1><h2 id="authortitle">
        <span>Author : </span>
        <span class="value" id="authornamevalue">A test author</span>
      </h2><h2 id="description">
        <span>Description : </span>
      </h2><p>
        <span class="value" id="descriptionvalue">A test comment</span>
      </p>
    </div><div id="crypt">
      <h3 id="crypttitle">
        <span>Crypt</span>
        <span>[1 vampires] Capacity min : 4 max : 4 average : 4.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">Abebe</span>
              </td><td />
              <td>
                <span class="tablevalue">4</span>
              </td><td>
                <span class="tablevalue">nec obf thn</span>
              </td><td />
              <td>
                <span class="tablevalue">Samedi (group 4)</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div id="library">
      <h3 id="librarytitle">
        <span>Library</span>
        <span class="stats" id="librarystats">[4 cards]</span>
      </h3><div class="librarytable">
        <h4 class="librarytype">
          <span>Action</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">Abbot</span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">.44 Magnum</span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">AK-47</span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Master</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">Abombwe</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div>
      <span class="generator">Crafted with : Sutekh [ %s ]. [ %s ]</span>
    </div>
  </body>
</html>""" % (sHTMLStyle, SutekhInfo.VERSION_STR,
        time.strftime('%Y-%m-%d', time.localtime()))

sExpected3 = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta content="text/html; charset=&quot;us-ascii&quot;" http-equiv="content-type" />
    <style type="text/css">%s</style>
    <title>VTES deck : Test Set 1 by A test author</title>
  </head><body>
    <div id="info">
      <h1 id="nametitle">
        <span>Deck Name :</span>
        <span class="value" id="namevalue">Test Set 1</span>
      </h1><h2 id="authortitle">
        <span>Author : </span>
        <span class="value" id="authornamevalue">A test author</span>
      </h2><h2 id="description">
        <span>Description : </span>
      </h2><p>
        <span class="value" id="descriptionvalue">A test comment</span>
      </p>
    </div><div id="crypt">
      <h3 id="crypttitle">
        <span>Crypt</span>
        <span>[1 vampires] Capacity min : 4 max : 4 average : 4.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?crypt=Abebe">Abebe</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">4</span>
              </td><td>
                <span class="tablevalue">nec obf thn</span>
              </td><td />
              <td>
                <span class="tablevalue">Samedi (group 4)</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div id="library">
      <h3 id="librarytitle">
        <span>Library</span>
        <span class="stats" id="librarystats">[4 cards]</span>
      </h3><div class="librarytable">
        <h4 class="librarytype">
          <span>Action</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Abbot">Abbot</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=.44+Magnum">.44 Magnum</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=AK-47">AK-47</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Master</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Abombwe">Abombwe</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div>
      <span class="generator">Crafted with : Sutekh [ %s ]. [ %s ]</span>
    </div>
  </body>
</html>""" % (sHTMLStyle, SutekhInfo.VERSION_STR,
        time.strftime('%Y-%m-%d', time.localtime()))


class ARDBHTMLWriterTests(SutekhTest):
    """class for the ARDB HTML deck writer tests"""

    def test_deck_writer(self):
        """Test HTML deck writing"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        aAddedPhysCards = get_phys_cards()
        # We have a physical card list, so create some physical card sets
        oPhysCardSet1 = PhysicalCardSet(name=aCardSetNames[0])
        oPhysCardSet1.comment = 'A test comment'
        oPhysCardSet1.author = 'A test author'

        for iLoop in range(5):
            oPhysCardSet1.addPhysicalCard(aAddedPhysCards[iLoop].id)
            oPhysCardSet1.syncUpdate()

        # Check output

        oWriter = WriteArdbHTML()
        sTempFileName =  self._create_tmp_file()
        oWriter.write(sTempFileName, oPhysCardSet1, oPhysCardSet1.cards, False)

        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        fIn.close()

        self.assertEqual(sData, sExpected1)

        # Test other modes
        oWriter = WriteArdbHTML('Monger')
        sTempFileName =  self._create_tmp_file()
        oWriter.write(sTempFileName, oPhysCardSet1, oPhysCardSet1.cards, False)

        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        fIn.close()

        self.assertEqual(sData, sExpected1)

        oWriter = WriteArdbHTML('None')
        sTempFileName =  self._create_tmp_file()
        oWriter.write(sTempFileName, oPhysCardSet1, oPhysCardSet1.cards, False)

        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        fIn.close()

        self.assertEqual(sData, sExpected2)

        oWriter = WriteArdbHTML('Secret Library')
        sTempFileName =  self._create_tmp_file()
        oWriter.write(sTempFileName, oPhysCardSet1, oPhysCardSet1.cards, False)

        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        fIn.close()

        self.assertEqual(sData, sExpected3)


if __name__ == "__main__":
    unittest.main()
