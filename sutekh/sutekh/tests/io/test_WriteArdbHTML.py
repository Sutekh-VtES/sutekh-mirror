# test_WriteArdbHTML.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an Ardb HTML file"""

import time
from sutekh.SutekhInfo import SutekhInfo
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteArdbHTML import  WriteArdbHTML, HTML_STYLE
import unittest

EXPECTED_1 = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
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
        <span>[4 vampires] Capacity min : 3 max : 7 average : 5.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showvamp.html?NAME=Siamese,%%20The">The Siamese</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">7</span>
              </td><td>
                <span class="tablevalue">PRE SPI ani pro</span>
              </td><td />
              <td>
                <span class="tablevalue">Ahrimane (group 2)</span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showvamp.html?NAME=Alan%%20Sovereign%%20ADV">Alan Sovereign</a>
                </span>
              </td><td>
                <span class="tablevalue">(Advanced)</span>
              </td><td>
                <span class="tablevalue">6</span>
              </td><td>
                <span class="tablevalue">AUS DOM for pre</span>
              </td><td />
              <td>
                <span class="tablevalue">Ventrue (group 3)</span>
              </td>
            </tr><tr>
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
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showvamp.html?NAME=Inez%%20&quot;Nurse216&quot;%%20Villagrande">Inez "Nurse216" Villagrande</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">3</span>
              </td><td>
                <span class="tablevalue">inn</span>
              </td><td />
              <td>
                <span class="tablevalue">Innocent (Imbued) (group 4)</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div id="library">
      <h3 id="librarytitle">
        <span>Library</span>
        <span class="stats" id="librarystats">[13 cards]</span>
      </h3><div class="librarytable">
        <h4 class="librarytype">
          <span>Action</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Abbot">Abbot</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Ally</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Scapelli,%%20The%%20Family%%20&quot;Mechanic&quot;">Scapelli, The Family "Mechanic"</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[7]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=.44%%20Magnum">.44 Magnum</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=AK-47">AK-47</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Aaron's%%20Feeding%%20Razor">Aaron's Feeding Razor</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Master</span>
          <span class="stats">[3]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Abombwe">Abombwe</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Path%%20of%%20Blood,%%20The">The Path of Blood</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div>
      <span class="generator">Crafted with : Sutekh [ %s ]. [ DATE ]</span>
    </div>
  </body>
</html>""" % (HTML_STYLE, SutekhInfo.VERSION_STR)

EXPECTED_2 = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
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
        <span>[4 vampires] Capacity min : 3 max : 7 average : 5.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">The Siamese</span>
              </td><td />
              <td>
                <span class="tablevalue">7</span>
              </td><td>
                <span class="tablevalue">PRE SPI ani pro</span>
              </td><td />
              <td>
                <span class="tablevalue">Ahrimane (group 2)</span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">Alan Sovereign</span>
              </td><td>
                <span class="tablevalue">(Advanced)</span>
              </td><td>
                <span class="tablevalue">6</span>
              </td><td>
                <span class="tablevalue">AUS DOM for pre</span>
              </td><td />
              <td>
                <span class="tablevalue">Ventrue (group 3)</span>
              </td>
            </tr><tr>
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
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">Inez "Nurse216" Villagrande</span>
              </td><td />
              <td>
                <span class="tablevalue">3</span>
              </td><td>
                <span class="tablevalue">inn</span>
              </td><td />
              <td>
                <span class="tablevalue">Innocent (Imbued) (group 4)</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div id="library">
      <h3 id="librarytitle">
        <span>Library</span>
        <span class="stats" id="librarystats">[13 cards]</span>
      </h3><div class="librarytable">
        <h4 class="librarytype">
          <span>Action</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">Abbot</span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Ally</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">Scapelli, The Family "Mechanic"</span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[7]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">.44 Magnum</span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">AK-47</span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">Aaron's Feeding Razor</span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Master</span>
          <span class="stats">[3]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">Abombwe</span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">The Path of Blood</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div>
      <span class="generator">Crafted with : Sutekh [ %s ]. [ DATE ]</span>
    </div>
  </body>
</html>""" % (HTML_STYLE, SutekhInfo.VERSION_STR)

EXPECTED_3 = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
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
        <span>[4 vampires] Capacity min : 3 max : 7 average : 5.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?crypt=Siamese,+The">The Siamese</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">7</span>
              </td><td>
                <span class="tablevalue">PRE SPI ani pro</span>
              </td><td />
              <td>
                <span class="tablevalue">Ahrimane (group 2)</span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?crypt=Alan+Sovereign+Adv">Alan Sovereign</a>
                </span>
              </td><td>
                <span class="tablevalue">(Advanced)</span>
              </td><td>
                <span class="tablevalue">6</span>
              </td><td>
                <span class="tablevalue">AUS DOM for pre</span>
              </td><td />
              <td>
                <span class="tablevalue">Ventrue (group 3)</span>
              </td>
            </tr><tr>
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
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?crypt=Inez+Nurse216+Villagrande">Inez "Nurse216" Villagrande</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">3</span>
              </td><td>
                <span class="tablevalue">inn</span>
              </td><td />
              <td>
                <span class="tablevalue">Innocent (Imbued) (group 4)</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div id="library">
      <h3 id="librarytitle">
        <span>Library</span>
        <span class="stats" id="librarystats">[13 cards]</span>
      </h3><div class="librarytable">
        <h4 class="librarytype">
          <span>Action</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Abbot">Abbot</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Ally</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Scapelli,+The+Family+Mechanic">Scapelli, The Family "Mechanic"</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[7]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=.44+Magnum">.44 Magnum</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=AK-47">AK-47</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Aaron's+Feeding+Razor">Aaron's Feeding Razor</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Master</span>
          <span class="stats">[3]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Abombwe">Abombwe</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Path+of+Blood,+The">The Path of Blood</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div>
      <span class="generator">Crafted with : Sutekh [ %s ]. [ DATE ]</span>
    </div>
  </body>
</html>""" % (HTML_STYLE, SutekhInfo.VERSION_STR)

EXPECTED_4 = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
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
        <span>[4 vampires] Capacity min : 3 max : 7 average : 5.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?crypt=Siamese,+The">The Siamese</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">7</span>
              </td><td>
                <span class="tablevalue">PRE SPI ani pro</span>
              </td><td />
              <td>
                <span class="tablevalue">Ahrimane (group 2)</span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?crypt=Alan+Sovereign+Adv">Alan Sovereign</a>
                </span>
              </td><td>
                <span class="tablevalue">(Advanced)</span>
              </td><td>
                <span class="tablevalue">6</span>
              </td><td>
                <span class="tablevalue">AUS DOM for pre</span>
              </td><td />
              <td>
                <span class="tablevalue">Ventrue (group 3)</span>
              </td>
            </tr><tr>
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
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?crypt=Inez+Nurse216+Villagrande">Inez "Nurse216" Villagrande</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">3</span>
              </td><td>
                <span class="tablevalue">inn</span>
              </td><td />
              <td>
                <span class="tablevalue">Innocent (Imbued) (group 4)</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div id="library">
      <h3 id="librarytitle">
        <span>Library</span>
        <span class="stats" id="librarystats">[13 cards]</span>
      </h3><div class="librarytable">
        <h4 class="librarytype">
          <span>Action</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Abbot">Abbot</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Ally</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Scapelli,+The+Family+Mechanic">Scapelli, The Family "Mechanic"</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[7]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=.44+Magnum">.44 Magnum</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=AK-47">AK-47</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Aaron's+Feeding+Razor">Aaron's Feeding Razor</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Master</span>
          <span class="stats">[3]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Abombwe">Abombwe</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Path+of+Blood,+The">The Path of Blood</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div><div id="cardtext">
      <h3 class="cardtext">
        <span>Card Texts</span>
      </h3><h4 class="librarytype">Crypt</h4>
      <h5>The Siamese</h5>
      <ul>
        <li>
          <span class="label">Capacity:</span>
          <span class="capacity">7</span>
        </li><li>
          <span class="label">Group:</span>
          <span class="group">2</span>
        </li><li>
          <span class="label">Clan:</span>
          <span class="clan">Ahrimane</span>
        </li><li>
          <span class="label">Disciplines:</span>
          <span class="disciplines">PRE SPI ani pro</span>
        </li>
      </ul><div class="text">
        <p>Sabbat: +1 bleed. Sterile.</p>
      </div><h5>Alan Sovereign (Advanced)</h5>
      <ul>
        <li>
          <span class="label">Capacity:</span>
          <span class="capacity">6</span>
        </li><li>
          <span class="label">Group:</span>
          <span class="group">3</span>
        </li><li>
          <span class="label">Clan:</span>
          <span class="clan">Ventrue</span>
        </li><li>
          <span class="label">Disciplines:</span>
          <span class="disciplines">AUS DOM for pre</span>
        </li>
      </ul><div class="text">
        <p>Advanced, Camarilla: While Alan is ready, you may pay some or all of the pool cost of equipping from any investment cards you control.</p>
        <p>[MERGED] During your master phase, if Alan is ready, you may move a counter from any investment card to your pool.</p>
      </div><h5>Abebe</h5>
      <ul>
        <li>
          <span class="label">Capacity:</span>
          <span class="capacity">4</span>
        </li><li>
          <span class="label">Group:</span>
          <span class="group">4</span>
        </li><li>
          <span class="label">Clan:</span>
          <span class="clan">Samedi</span>
        </li><li>
          <span class="label">Disciplines:</span>
          <span class="disciplines">nec obf thn</span>
        </li>
      </ul><div class="text">
        <p>Independent.</p>
      </div><h5>Inez "Nurse216" Villagrande</h5>
      <ul>
        <li>
          <span class="label">Capacity:</span>
          <span class="capacity">3</span>
        </li><li>
          <span class="label">Group:</span>
          <span class="group">4</span>
        </li><li>
          <span class="label">Clan:</span>
          <span class="clan">Innocent (Imbued)</span>
        </li><li>
          <span class="label">Disciplines:</span>
          <span class="disciplines">inn</span>
        </li>
      </ul><div class="text">
        <p>When Inez enters play, you may search your library (shuffle afterward) or hand for a power that requires innocence and put it on her.</p>
      </div><h4 class="libraryttype">Action</h4>
      <h5 class="cardname">Abbot</h5>
      <div class="text">
        <p>+1 stealth action. Requires a Sabbat vampire.</p>
        <p>Put this card on this acting Sabbat vampire and untap him or her. This Sabbat vampire gets +1 intercept against (D) actions directed at his or her controller. A vampire may have only one Abbot.</p>
      </div><h4 class="libraryttype">Ally</h4>
      <h5 class="cardname">Scapelli, The Family "Mechanic"</h5>
      <ul>
        <li>
          <span class="label">Requires:</span>
          <span class="requirement">Giovanni</span>
        </li><li>
          <span class="label">Cost:</span>
          <span class="cost">3 pool</span>
        </li>
      </ul><div class="text">
        <p>Unique {mortal} with 3 life. {0 strength}, 1 bleed.</p>
        <p>{Scapelli may strike for 2R damage.} Once each combat, Scapelli may press to continue combat.</p>
      </div><h4 class="libraryttype">Equipment</h4>
      <h5 class="cardname">.44 Magnum</h5>
      <ul>
        <li>
          <span class="label">Cost:</span>
          <span class="cost">2 pool</span>
        </li>
      </ul><div class="text">
        <p>Weapon, gun.</p>
        <p>2R damage each strike, with an optional maneuver each combat.</p>
      </div><h5 class="cardname">AK-47</h5>
      <ul>
        <li>
          <span class="label">Cost:</span>
          <span class="cost">5 pool</span>
        </li>
      </ul><div class="text">
        <p>Weapon. Gun.</p>
        <p>2R damage each strike, with an optional maneuver {each combat}. When bearer strikes with this gun, he or she gets an optional additional strike this round, only usable to strike with this gun.</p>
      </div><h5 class="cardname">Aaron's Feeding Razor</h5>
      <ul>
        <li>
          <span class="label">Cost:</span>
          <span class="cost">1 pool</span>
        </li>
      </ul><div class="text">
        <p>Unique equipment.</p>
        <p>When this vampire successfully hunts, he or she gains 1 additional blood.</p>
      </div><h4 class="libraryttype">Master</h4>
      <h5 class="cardname">Abombwe</h5>
      <div class="text">
        <p>Master: Discipline. Trifle.</p>
        <p>Put this card on a Laibon or on a vampire with Protean [pro]. This vampire gains one level of Abombwe [abo]. Capacity increases by 1: the vampire is one generation older. Cannot be placed on a vampire with superior Abombwe.</p>
      </div><h5 class="cardname">The Path of Blood</h5>
      <ul>
        <li>
          <span class="label">Requires:</span>
          <span class="requirement">Assamite</span>
        </li><li>
          <span class="label">Cost:</span>
          <span class="cost">1 pool</span>
        </li>
      </ul><div class="text">
        <p>Unique master.</p>
        <p>Put this card in play. Cards that require Quietus [qui] {cost Assamites 1 less blood}. Any minion may burn this card as a (D) action; if that minion is a vampire, he or she then takes 1 unpreventable damage when this card is burned.</p>
      </div>
    </div><div>
      <span class="generator">Crafted with : Sutekh [ %s ]. [ DATE ]</span>
    </div>
  </body>
</html>""" % (HTML_STYLE, SutekhInfo.VERSION_STR)


class ARDBHTMLWriterTests(SutekhTest):
    """class for the ARDB HTML deck writer tests"""

    def test_deck_writer(self):
        """Test HTML deck writing"""
        oPhysCardSet1 = make_set_1()

        sCurDate = time.strftime('[ %Y-%m-%d ]', time.localtime())
        # Check output

        oWriter = WriteArdbHTML(bDoText=False)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self.assertEqual(sData, EXPECTED_1)

        # Test other modes
        oWriter = WriteArdbHTML('Monger', False)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self.assertEqual(sData, EXPECTED_1)

        oWriter = WriteArdbHTML('None', False)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self.assertEqual(sData, EXPECTED_2)

        oWriter = WriteArdbHTML('Secret Library', False)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self.assertEqual(sData, EXPECTED_3)

        oWriter = WriteArdbHTML('Secret Library', True)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self.assertEqual(sData, EXPECTED_4)


if __name__ == "__main__":
    unittest.main()
