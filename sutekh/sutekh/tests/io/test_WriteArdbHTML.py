# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# pylint: disable=too-many-lines
# HTML output is verbose and long when we include card texts

"""Test Writing a card set to an Ardb HTML file"""

import time
import unittest

from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.SutekhInfo import SutekhInfo
from sutekh.io.WriteArdbHTML import WriteArdbHTML, HTML_STYLE
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1

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
        <span>[6 vampires] Capacity min : 3 max : 9 average : 6.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
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
                  <a href="http://monger.vekn.org/showvamp.html?NAME=Hektor">Hektor</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">9</span>
              </td><td>
                <span class="tablevalue">CEL POT PRE QUI for</span>
              </td><td>
                <span class="tablevalue">Priscus</span>
              </td><td>
                <span class="tablevalue">Brujah antitribu (group 4)</span>
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
        <span class="stats" id="librarystats">[28 cards]</span>
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
          <span>Action Modifier</span>
          <span class="stats">[3]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">3x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Aire%%20of%%20Elation">Aire of Elation</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Action Modifier/Combat</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Swallowed%%20by%%20the%%20Night">Swallowed by the Night</a>
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
          <span>Combat</span>
          <span class="stats">[8]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Immortal%%20Grapple">Immortal Grapple</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Walk%%20of%%20Flame">Walk of Flame</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[8]</span>
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
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Anarch%%20Manifesto,%%20An">An Anarch Manifesto</a>
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
        </table><h4 class="librarytype">
          <span>Reaction</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://monger.vekn.org/showcard.html?NAME=Hide%%20the%%20Heart">Hide the Heart</a>
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
        <span>[6 vampires] Capacity min : 3 max : 9 average : 6.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
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
                <span class="tablevalue">Hektor</span>
              </td><td />
              <td>
                <span class="tablevalue">9</span>
              </td><td>
                <span class="tablevalue">CEL POT PRE QUI for</span>
              </td><td>
                <span class="tablevalue">Priscus</span>
              </td><td>
                <span class="tablevalue">Brujah antitribu (group 4)</span>
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
        <span class="stats" id="librarystats">[28 cards]</span>
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
          <span>Action Modifier</span>
          <span class="stats">[3]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">3x</span>
              </td><td>
                <span class="tablevalue">Aire of Elation</span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Action Modifier/Combat</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">Swallowed by the Night</span>
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
          <span>Combat</span>
          <span class="stats">[8]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">Immortal Grapple</span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">Walk of Flame</span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[8]</span>
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
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">An Anarch Manifesto</span>
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
        </table><h4 class="librarytype">
          <span>Reaction</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">Hide the Heart</span>
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
        <span>[6 vampires] Capacity min : 3 max : 9 average : 6.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
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
                  <a href="http://www.secretlibrary.info/?crypt=Hektor">Hektor</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">9</span>
              </td><td>
                <span class="tablevalue">CEL POT PRE QUI for</span>
              </td><td>
                <span class="tablevalue">Priscus</span>
              </td><td>
                <span class="tablevalue">Brujah antitribu (group 4)</span>
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
        <span class="stats" id="librarystats">[28 cards]</span>
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
          <span>Action Modifier</span>
          <span class="stats">[3]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">3x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Aire+of+Elation">Aire of Elation</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Action Modifier/Combat</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Swallowed+by+the+Night">Swallowed by the Night</a>
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
          <span>Combat</span>
          <span class="stats">[8]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Immortal+Grapple">Immortal Grapple</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Walk+of+Flame">Walk of Flame</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[8]</span>
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
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Anarch+Manifesto,+An">An Anarch Manifesto</a>
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
        </table><h4 class="librarytype">
          <span>Reaction</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Hide+the+Heart">Hide the Heart</a>
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
        <span>[6 vampires] Capacity min : 3 max : 9 average : 6.00</span>
      </h3><div id="crypttable">
        <table summary="Crypt card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
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
                  <a href="http://www.secretlibrary.info/?crypt=Hektor">Hektor</a>
                </span>
              </td><td />
              <td>
                <span class="tablevalue">9</span>
              </td><td>
                <span class="tablevalue">CEL POT PRE QUI for</span>
              </td><td>
                <span class="tablevalue">Priscus</span>
              </td><td>
                <span class="tablevalue">Brujah antitribu (group 4)</span>
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
        <span class="stats" id="librarystats">[28 cards]</span>
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
          <span>Action Modifier</span>
          <span class="stats">[3]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">3x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Aire+of+Elation">Aire of Elation</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Action Modifier/Combat</span>
          <span class="stats">[2]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">2x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Swallowed+by+the+Night">Swallowed by the Night</a>
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
          <span>Combat</span>
          <span class="stats">[8]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Immortal+Grapple">Immortal Grapple</a>
                </span>
              </td>
            </tr><tr>
              <td>
                <span class="tablevalue">4x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Walk+of+Flame">Walk of Flame</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table><h4 class="librarytype">
          <span>Equipment</span>
          <span class="stats">[8]</span>
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
            </tr><tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Anarch+Manifesto,+An">An Anarch Manifesto</a>
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
        </table><h4 class="librarytype">
          <span>Reaction</span>
          <span class="stats">[1]</span>
        </h4><table summary="Library card table">
          <tbody>
            <tr>
              <td>
                <span class="tablevalue">1x</span>
              </td><td>
                <span class="tablevalue">
                  <a href="http://www.secretlibrary.info/?lib=Hide+the+Heart">Hide the Heart</a>
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
      </div><h5>Hektor</h5>
      <ul>
        <li>
          <span class="label">Capacity:</span>
          <span class="capacity">9</span>
        </li><li>
          <span class="label">Group:</span>
          <span class="group">4</span>
        </li><li>
          <span class="label">Clan:</span>
          <span class="clan">Brujah antitribu</span>
        </li><li>
          <span class="label">Disciplines:</span>
          <span class="disciplines">CEL POT PRE QUI for</span>
        </li>
      </ul><div class="text">
        <p>Sabbat priscus: Damage from Hektor\'s hand strikes is aggravated. Baali get +1 bleed</p>
        <p>when bleeding you.</p>
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
        <p>Put this card on this acting Sabbat vampire and unlock him or her. This Sabbat vampire gets +1 intercept against (D) actions directed at his or her controller. A vampire may have only one Abbot.</p>
      </div><h4 class="libraryttype">Action Modifier</h4>
      <h5 class="cardname">Aire of Elation</h5>
      <ul>
        <li>
          <span class="label">Cost:</span>
          <span class="cost">1 blood</span>
        </li><li>
          <span class="label">Disciplines:</span>
          <span class="disciplines">PRE</span>
        </li>
      </ul><div class="text">
        <p>You cannot play another action modifier to further increase the bleed for this action.</p>
        <p>[pre] +1 bleed; +2 bleed if the acting vampire is Toreador. [PRE] +2 bleed; +3 bleed if the acting vampire is Toreador.</p>
      </div><h4 class="libraryttype">Action Modifier/Combat</h4>
      <h5 class="cardname">Swallowed by the Night</h5>
      <ul>
        <li>
          <span class="label">Disciplines:</span>
          <span class="disciplines">OBF</span>
        </li>
      </ul><div class="text">
        <p>[obf] [ACTION MODIFIER] +1 stealth.</p>
        <p>[OBF] [COMBAT] Maneuver.</p>
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
      </div><h4 class="libraryttype">Combat</h4>
      <h5 class="cardname">Immortal Grapple</h5>
      <ul>
        <li>
          <span class="label">Disciplines:</span>
          <span class="disciplines">POT</span>
        </li>
      </ul><div class="text">
        <p>Only usable at close range before strikes are chosen. Grapple.</p>
        <p>[pot] Strikes that are not hand strikes may not be used this round (by either combatant). A vampire may play only one Immortal Grapple each round. [POT] As above, with an optional press. If another round of combat occurs, that round is at close range; skip the determine range step for that round.</p>
      </div><h5 class="cardname">Walk of Flame</h5>
      <ul>
        <li>
          <span class="label">Disciplines:</span>
          <span class="disciplines">THA</span>
        </li>
      </ul><div class="text">
        <p>Not usable on the first round of combat.</p>
        <p>[tha] Strike: 1R aggravated damage. [THA] Strike: 2R aggravated damage.</p>
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
        <p>Unique.</p>
        <p>The bearer gets +1 hunt.</p>
      </div><h5 class="cardname">An Anarch Manifesto</h5>
      <div class="text">
        <p>Equipment.</p>
        <p>The anarch with this equipment gets +1 stealth on actions that require an anarch. Titled non-anarch vampires get +1 strength in combat with this minion. A minion may have only one Anarch Manifesto.</p>
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
      </div><h4 class="libraryttype">Reaction</h4>
      <h5 class="cardname">Hide the Heart</h5>
      <ul>
        <li>
          <span class="label">Disciplines:</span>
          <span class="disciplines">AUS VAL</span>
        </li>
      </ul><div class="text">
        <p>[aus] Reduce a bleed against you by 1.</p>
        <p>[val] The action ends (unsuccessfully). The acting minion may burn 1 blood to cancel this card as it is played. Only one Hide the Heart may be played at [val] each action. [VAL] Reduce a bleed against you by 2, or lock to reduce a bleed against any Methuselah by 2.</p>
      </div>
    </div><div>
      <span class="generator">Crafted with : Sutekh [ %s ]. [ DATE ]</span>
    </div>
  </body>
</html>""" % (HTML_STYLE, SutekhInfo.VERSION_STR)


class ARDBHTMLWriterTests(SutekhTest):
    """class for the ARDB HTML deck writer tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_deck_writer(self):
        """Test HTML deck writing"""
        oPhysCardSet1 = make_set_1()

        sCurDate = time.strftime('[ %Y-%m-%d ]', time.localtime())
        # Check output

        oWriter = WriteArdbHTML(bDoText=False)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self._compare_xml_strings(sData, EXPECTED_1)

        # Test other modes
        oWriter = WriteArdbHTML('Monger', False)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self._compare_xml_strings(sData, EXPECTED_1)

        oWriter = WriteArdbHTML('None', False)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self._compare_xml_strings(sData, EXPECTED_2)

        oWriter = WriteArdbHTML('Secret Library', False)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self._compare_xml_strings(sData, EXPECTED_3)

        oWriter = WriteArdbHTML('Secret Library', True)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self._compare_xml_strings(sData, EXPECTED_4)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
