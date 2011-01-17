# HTMLTextView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# TextView Object that displays an HTML file
# Copyright 2005, 2006, 2007 Gustavo J. A. M. Carneiro
# Changes for Sutekh, Copyright 2008, 2009, 2010
#           Neil Muller <drnlmuller+sutekh@gmail.com>
# License: GPL - See COPYRIGHT file for details
# Original version downloaded from http://www.gnome.org/~gjc/htmltextview.py
# April 2008
#   Original version released under the GNU Lesser General Public License
#   (version 2 or later) - see
#       http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html

"""A gtk.TextView-based renderer for XHTML-IM, as described in:
   http://www.jabber.org/jeps/jep-0071.html .
   """

import gobject
import pango
import gtk
import re
import warnings
import HTMLParser
from cStringIO import StringIO
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

WHITE_SPACE_REGEX = re.compile("\\s+")

# set for fast inclusion queries, since we hit this list multiple times
HTML_HEADING_TAGS = set(('h1', 'h2', 'h3', 'h4', 'h5', 'h6'))

# don't throw an exception if no screen during import - we'll catch that later
if gtk.gdk.screen_get_default() is None:
    SCREEN_RESOLUTION = 0
else:
    ## pixels = points * SCREEN_RESOLUTION
    SCREEN_RESOLUTION = 0.3514598 * (gtk.gdk.screen_height() /
            float(gtk.gdk.screen_height_mm()))


def _parse_css_color(sColor):
    '''_parse_css_color(css_color) -> gtk.gdk.Color'''
    if sColor.startswith("rgb(") and sColor.endswith(')'):
        iRed, iGreen, iBlue = [int(c) * 257 for c in sColor[4:-1].split(',')]
        return gtk.gdk.Color(iRed, iGreen, iBlue)
    else:
        return gtk.gdk.color_parse(sColor)


class HtmlHandler(HTMLParser.HTMLParser):
    # pylint: disable-msg=R0201, R0902
    # R0201: can't break these into functions
    # R0902: We need to keep a lot of state to handle HTML properly
    """Parse the HTML input and update the gtk.TextView"""
    def __init__(self, oTextView, oStartIter, fLinkLoader):
        HTMLParser.HTMLParser.__init__(self)
        self._oTextBuf = oTextView.get_buffer()
        self._oTextView = oTextView
        self._oIter = oStartIter
        self._sText = ''
        self._aStyles = []  # a gtk.TextTag or None, for each span level
        self._aListCounters = []  # stack (top at head) of list
                                # counters, or None for unordered list
        self._bInTitle = False
        self._dTargets = {}
        self._fLinkLoader = fLinkLoader

    def _parse_style_color(self, oTag, sValue):
        """Convert style value to TextView foreground color"""
        oColor = _parse_css_color(sValue)
        oTag.set_property("foreground-gdk", oColor)

    def _parse_style_background_color(self, oTag, sValue):
        """Convert background value to TextView background color."""
        oColor = _parse_css_color(sValue)
        oTag.set_property("background-gdk", oColor)
        oTag.set_property("paragraph-background-gdk", oColor)

    def _get_current_attributes(self):
        """Get current attributes."""
        aAttrs = self._oTextView.get_default_attributes()
        self._oIter.backward_char()
        self._oIter.get_attributes(aAttrs)
        self._oIter.forward_char()
        return aAttrs

    def _parse_length(self, sValue, bFontRelative, fCallback, *args):
        """Parse/calc length, converting to pixels.

           calls callback(length, *args) when the length is first computed
           or changes
           """
        # pylint: disable-msg=W0142
        # *magic required here
        if sValue.endswith('%'):
            fFrac = float(sValue[:-1]) / 100
            if bFontRelative:
                oAttrs = self._get_current_attributes()
                fFontSize = oAttrs.font.get_size() / pango.SCALE
                fCallback(fFrac * SCREEN_RESOLUTION * fFontSize, *args)
            else:
                ## CSS says "Percentage values: refer to width of the closest
                ##           block-level ancestor"
                ## This is difficult/impossible to implement, so we use
                ## textview width instead; a reasonable approximation..
                oAlloc = self._oTextView.get_allocation()
                self.__parse_length_frac_cb(self._oTextView, oAlloc,
                        fFrac, fCallback, args)
                self._oTextView.connect("size-allocate",
                        self.__parse_length_frac_cb, fFrac,
                        fCallback, args)

        elif sValue.endswith('pt'):  # points
            fCallback(float(sValue[:-2]) * SCREEN_RESOLUTION, *args)
        elif sValue.endswith('em'):  # ems, the height of the element's font
            oAttrs = self._get_current_attributes()
            fFontSize = oAttrs.font.get_size() / pango.SCALE
            fCallback(float(sValue[:-2]) * SCREEN_RESOLUTION * fFontSize,
                    *args)
        elif sValue.endswith('ex'):  # x-height, ~ the height of the letter 'x'
            ## FIXME: figure out how to calculate this correctly
            ##        for now 'em' size is used as approximation
            oAttrs = self._get_current_attributes()
            fFontSize = oAttrs.font.get_size() / pango.SCALE
            fCallback(float(sValue[:-2]) * SCREEN_RESOLUTION * fFontSize,
                    *args)
        elif sValue.endswith('px'):  # pixels
            fCallback(int(sValue[:-2]), *args)
        else:
            warnings.warn("Unable to parse length value '%s'" % sValue)

    @staticmethod
    def __parse_font_size_cb(fLength, oTag):
        """Callback for font size calculations."""
        oTag.set_property("size-points", fLength / SCREEN_RESOLUTION)

    def _parse_style_font_size(self, oTag, sValue):
        """Parse the font size attribute"""
        try:
            iScale = {
                "xx-small": pango.SCALE_XX_SMALL,
                "x-small": pango.SCALE_X_SMALL,
                "small": pango.SCALE_SMALL,
                "medium": pango.SCALE_MEDIUM,
                "large": pango.SCALE_LARGE,
                "x-large": pango.SCALE_X_LARGE,
                "xx-large": pango.SCALE_XX_LARGE,
                } [sValue]
        except KeyError:
            pass
        else:
            oAttrs = self._get_current_attributes()
            oTag.set_property("scale", iScale / oAttrs.font_scale)
            return
        if sValue == 'smaller':
            oTag.set_property("scale", pango.SCALE_SMALL)
            return
        if sValue == 'larger':
            oTag.set_property("scale", pango.SCALE_LARGE)
            return
        self._parse_length(sValue, True, self.__parse_font_size_cb, oTag)

    def _parse_style_font_style(self, oTag, sValue):
        """Parse the font style attribute"""
        try:
            iStyle = {
                "normal": pango.STYLE_NORMAL,
                "italic": pango.STYLE_ITALIC,
                "oblique": pango.STYLE_OBLIQUE,
                } [sValue]
        except KeyError:
            warnings.warn("unknown font-style %s" % sValue)
        else:
            oTag.set_property("style", iStyle)

    @staticmethod
    def __frac_length_tag_cb(fLength, oTag, sPropName):
        """Callback used by _parse_length for handling the margin style
           settings."""
        oTag.set_property(sPropName, fLength)

    def _parse_style_margin_left(self, oTag, sValue):
        """Handle the margin left style attribute."""
        self._parse_length(sValue, False, self.__frac_length_tag_cb, oTag,
                "left-margin")

    def _parse_style_margin_right(self, oTag, sValue):
        """Handle the margin right style attribute."""
        self._parse_length(sValue, False, self.__frac_length_tag_cb, oTag,
                "right-margin")

    def _parse_style_font_weight(self, oTag, sValue):
        """Adjust the font to match the font weight specification."""
        ## missing 'bolder' and 'lighter', but that's not important for us
        try:
            iWeight = {
                '100': pango.WEIGHT_ULTRALIGHT,
                '200': pango.WEIGHT_ULTRALIGHT,
                '300': pango.WEIGHT_LIGHT,
                '400': pango.WEIGHT_NORMAL,
                '500': pango.WEIGHT_NORMAL,
                '600': pango.WEIGHT_BOLD,
                '700': pango.WEIGHT_BOLD,
                '800': pango.WEIGHT_ULTRABOLD,
                '900': pango.WEIGHT_HEAVY,
                'normal': pango.WEIGHT_NORMAL,
                'bold': pango.WEIGHT_BOLD,
                } [sValue]
        except KeyError:
            warnings.warn("unknown font-style %s" % sValue)
        else:
            oTag.set_property("weight", iWeight)

    def _parse_style_font_family(self, oTag, sValue):
        """Change the font family."""
        oTag.set_property("family", sValue)

    def _parse_style_text_align(self, oTag, sValue):
        """Set the text alignment style."""
        try:
            iAlign = {
                'left': gtk.JUSTIFY_LEFT,
                'right': gtk.JUSTIFY_RIGHT,
                'center': gtk.JUSTIFY_CENTER,
                'justify': gtk.JUSTIFY_FILL,
                } [sValue]
        except KeyError:
            warnings.warn("Invalid text-align:%s requested" % sValue)
        else:
            oTag.set_property("justification", iAlign)

    def _parse_style_text_decoration(self, oTag, sValue):
        """Set the pango properties for the tag to match the desired html text
           decoration."""
        if sValue == "none":
            oTag.set_property("underline", pango.UNDERLINE_NONE)
            oTag.set_property("strikethrough", False)
        elif sValue == "underline":
            oTag.set_property("underline", pango.UNDERLINE_SINGLE)
            oTag.set_property("strikethrough", False)
        elif sValue == "overline":
            warnings.warn("text-decoration:overline not implemented")
            oTag.set_property("underline", pango.UNDERLINE_NONE)
            oTag.set_property("strikethrough", False)
        elif sValue == "line-through":
            oTag.set_property("underline", pango.UNDERLINE_NONE)
            oTag.set_property("strikethrough", True)
        elif sValue == "blink":
            warnings.warn("text-decoration:blink not implemented")
        else:
            warnings.warn("text-decoration:%s not implemented" % sValue)

    ## build a dictionary mapping styles to methods, for greater speed
    __style_methods = dict()
    for sStyle in ("background-color", "color", "font-family", "font-size",
                  "font-style", "font-weight", "margin-left", "margin-right",
                  "text-align", "text-decoration"):
        try:
            fMethod = locals()["_parse_style_%s" % sStyle.replace('-', '_')]
        except KeyError:
            warnings.warn("Style attribute '%s' not yet implemented" % sStyle)
        else:
            __style_methods[sStyle] = fMethod

    def _get_style_tags(self):
        """Get the current set of style tags"""
        return [oTag for oTag in self._aStyles if oTag is not None]

    def _begin_span(self, sStyle, oTag=None):
        """Start a <span> section"""
        if oTag is None:
            oTag = self._oTextBuf.create_tag()
        oTag.set_property("wrap-mode", gtk.WRAP_WORD)
        if sStyle is None:
            self._aStyles.append(oTag)
            return None
        for sAttr, sVal in [item.split(':', 1) for item in sStyle.split(';')]:
            sAttr = sAttr.strip().lower()
            sVal = sVal.strip()
            try:
                fMethod = self.__style_methods[sAttr]
            except KeyError:
                warnings.warn("Style attribute '%s' requested "
                              "but not yet implemented" % sAttr)
            else:
                fMethod(self, oTag, sVal)
        self._aStyles.append(oTag)

    def _end_span(self):
        """End a <span> section"""
        self._aStyles.pop(-1)

    def _insert_text(self, sText):
        """Insert text into the TextBuffer"""
        aTags = self._get_style_tags()
        if aTags:
            # pylint: disable-msg=W0142
            # * magic required
            self._oTextBuf.insert_with_tags(self._oIter, sText, *aTags)
        else:
            self._oTextBuf.insert(self._oIter, sText)

    def _flush_text(self):
        """Flush any pending text."""
        if not self._sText:
            return
        if self._oIter.starts_line():
            self._sText = self._sText.lstrip()
        self._insert_text(self._sText.replace('\n', ''))
        self._sText = ''

    # pylint: disable-msg=R0913
    # Arguments needed by function signature
    def _anchor_event(self, _oTag, _oView, oEvent, _oIter, oHref, oType):
        """Something happened to a link, so see if we need to react."""
        if oEvent.type == gtk.gdk.BUTTON_PRESS and oEvent.button == 1:
            self._oTextView.emit("url-clicked", oHref, oType)
            return True
        return False

    # Arguments needed so this can be called via 'size-allocate' event
    def __parse_length_frac_cb(self, oTextView, oAllocation,
            fFrac, fCallback, args):
        """call the required callback function when the size allocation
           changes."""
        # pylint: disable-msg=W0142
        # *magic required here
        fCallback(oAllocation.width * fFrac, *args)

    # pylint: enable-msg=R0913

    def handle_data(self, sContent):
        """Process the character comments of an element."""
        if self._bInTitle:
            return
        self._sText += WHITE_SPACE_REGEX.sub(' ', sContent)

    def get_targets(self):
        """Get the list of target anchors."""
        return self._dTargets

    # pylint: disable-msg=R0912, R0915, R0914
    # entity handler, so it is is a massive if..elif.. statement
    def handle_entityref(self, sEntity):
        """Convert entity to something we can use"""
        # This looks like all that textile will produce as entities
        if sEntity == 'lt':
            self.handle_data('<')
        elif sEntity == 'gt':
            self.handle_data('>')
        elif sEntity == 'amp':
            self.handle_data('&')
        elif sEntity == 'quot':
            self.handle_data('"')
        #else:
        #    print 'Unknown entity', sEntity

    # handle charrefs produced by textile as great if statement
    def handle_charref(self, sCharref):
        """Convert charref to something we can use"""
        self.handle_data(unichr(int(sCharref)))

    # start tag handler, so it is is a massive if..elif.. statement
    def handle_starttag(self, sName, oAttrs):
        """Parser start element handler"""
        oAttrs = dict(oAttrs)
        self._flush_text()
        try:
            oStyle = oAttrs['style']
        except KeyError:
            oStyle = None

        oTag = None
        if sName == 'a':
            oTag = self._oTextBuf.create_tag()
            oTag.set_property('foreground', '#0000ff')
            oTag.set_property('underline', pango.UNDERLINE_SINGLE)
            try:
                oType_ = oAttrs['type']
            except KeyError:
                oType_ = None
            if oAttrs.has_key('href'):
                oTag.connect('event', self._anchor_event, oAttrs['href'],
                        oType_)
                oTag.is_anchor = True
            if oAttrs.has_key('name'):
                # Add it to the list of valid targets
                oMark = self._oTextBuf.create_mark(None, self._oIter, True)
                self._dTargets[oAttrs['name']] = oMark
        elif sName in HTML_HEADING_TAGS:
            oTag = self._oTextBuf.create_tag()
            oTag.set_property('underline', pango.UNDERLINE_SINGLE)
            if sName == 'h1':
                oTag.set_property('weight', pango.WEIGHT_HEAVY)
                oTag.set_property('scale', pango.SCALE_X_LARGE)
            elif sName == 'h2':
                oTag.set_property('weight', pango.WEIGHT_ULTRABOLD)
                oTag.set_property('scale', pango.SCALE_LARGE)
            elif sName == 'h3':
                oTag.set_property('weight', pango.WEIGHT_BOLD)
        elif sName == 'title':
            self._bInTitle = True
            return
        elif sName == 'em' or sName == 'i':
            oTag = self._oTextBuf.create_tag()
            oTag.set_property('style', pango.STYLE_ITALIC)
        elif sName == 'strong' or sName == 'b':
            oTag = self._oTextBuf.create_tag()
            oTag.set_property('weight', pango.WEIGHT_BOLD)
        elif sName == 'font':
            oTag = self._oTextBuf.create_tag()
            dFontSize = {
                '-2': pango.SCALE_X_SMALL,
                '-1': pango.SCALE_SMALL,
                '1': pango.SCALE_LARGE,
                '2': pango.SCALE_X_LARGE,
            }
            if 'size' in oAttrs and oAttrs['size'] in dFontSize:
                oTag.set_property('scale', dFontSize[oAttrs['size']])
        elif sName == 'li':
            # indent 2em per list
            oTag = self._oTextBuf.create_tag()
            oTextAttrs = self._get_current_attributes()
            fFontSize = oTextAttrs.font.get_size() / pango.SCALE
            iDepth = len(self._aListCounters)
            oTag.set_property('left-margin', 2.0 * iDepth * SCREEN_RESOLUTION
                    * fFontSize)

        self._begin_span(oStyle, oTag)

        if oAttrs.has_key('id'):
            # Add it to the list of valid targets
            oMark = self._oTextBuf.create_mark(None, self._oIter, True)
            self._dTargets[oAttrs['id']] = oMark

        if sName == 'br':
            pass  # handled in endElement
        elif sName == 'p':
            if not self._oIter.starts_line():
                self._insert_text("\n")
        elif sName == 'div':
            if not self._oIter.starts_line():
                self._insert_text("\n")
        elif sName == 'span':
            pass
        elif sName == 'ul':
            if not self._oIter.starts_line():
                self._insert_text("\n")
            self._aListCounters.append(None)
        elif sName == 'ol':
            if not self._oIter.starts_line():
                self._insert_text("\n")
            self._aListCounters.append(0)
        elif sName == 'li':
            if self._aListCounters[-1] is None:
                sListHead = unichr(0x2022)
            else:
                self._aListCounters[-1] += 1
                sListHead = "%i." % self._aListCounters[-1]
            self._sText = sListHead + ' '
        elif sName == 'img':
            # pylint: disable-msg=W0703
            # we want to catch all errors here
            try:
                oFile = self._fLinkLoader(oAttrs['src'])
                oLoader = gtk.gdk.PixbufLoader()
                oLoader.write(oFile.read())
                oLoader.close()
                oPixbuf = oLoader.get_pixbuf()
            except Exception:
                oPixbuf = None
                try:
                    sAlt = oAttrs['alt']
                except KeyError:
                    sAlt = "Broken image"
            if oPixbuf is not None:
                aTags = self._get_style_tags()
                if aTags:
                    oTmpMark = self._oTextBuf.create_mark(None, self._oIter,
                            True)

                self._oTextBuf.insert_pixbuf(self._oIter, oPixbuf)

                if aTags:
                    oStart = self._oTextBuf.get_iter_at_mark(oTmpMark)
                    for oTag in aTags:
                        self._oTextBuf.apply_tag(oTag, oStart, self._oIter)
                    self._oTextBuf.delete_mark(oTmpMark)
            else:
                self._insert_text("[IMG: %s]" % sAlt)
        elif sName == 'body':
            pass
        elif sName == 'a':
            pass
        elif sName == 'head':
            pass
        elif sName == 'html':
            pass
        elif sName in HTML_HEADING_TAGS:
            pass
        elif sName == 'em' or sName == 'i':
            pass
        elif sName == 'strong' or sName == 'b':
            pass
        elif sName == 'font':
            pass
        else:
            warnings.warn("Unhandled start tag '%s'" % sName)

    # end tag handler, so it is is a massive if..elif.. statement
    def handle_endtag(self, sName):
        """Handle the end of a tag"""
        if sName == 'title':
            self._bInTitle = False
            return
        self._flush_text()

        if sName == 'p':
            if not self._oIter.starts_line():
                self._insert_text("\n")
        elif sName == 'div':
            if not self._oIter.starts_line():
                self._insert_text("\n")
        elif sName == 'span':
            pass
        elif sName == 'body':
            pass
        elif sName == 'br':
            self._insert_text("\n")
        elif sName == 'ul':
            self._aListCounters.pop()
        elif sName == 'ol':
            self._aListCounters.pop()
        elif sName == 'li':
            if not self._oIter.starts_line():
                self._insert_text("\n")
        elif sName == 'img':
            pass
        elif sName == 'body':
            pass
        elif sName == 'html':
            pass
        elif sName == 'head':
            pass
        elif sName == 'a':
            pass
        elif sName in HTML_HEADING_TAGS:
            if not self._oIter.starts_line():
                self._insert_text("\n")
        elif sName == 'em' or sName == 'i':
            pass
        elif sName == 'strong' or sName == 'b':
            pass
        elif sName == 'font':
            pass
        else:
            warnings.warn("Unhandled end tag '%s'" % sName)

        self._end_span()


class HTMLTextView(gtk.TextView):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """TextView subclass to display HTML"""
    __gtype_name__ = 'HTMLTextView'
    __gsignals__ = {
        'url-clicked': (gobject.SIGNAL_RUN_LAST, None, (str, str)),
        # href, type
    }

    def __init__(self, fLinkLoader):
        """TextView subclass to display HTML.

           fLinkLoader: function to load links with
                        (takes local URL, returns file-like object)
           """
        gtk.TextView.__init__(self)
        self.set_wrap_mode(gtk.WRAP_CHAR)
        self.set_editable(False)
        self._bChangedCursor = False
        self.connect("motion-notify-event", self.__motion_notify_event)
        self.connect("leave-notify-event", self.__leave_event)
        self.connect("enter-notify-event", self.__motion_notify_event)
        self.set_pixels_above_lines(3)
        self.set_pixels_below_lines(3)
        self._dTargets = {}
        self._fLinkLoader = fLinkLoader

    def __leave_event(self, oWidget, _oEvent):
        """Cursor has left the widget."""
        if self._bChangedCursor:
            oWindow = oWidget.get_window(gtk.TEXT_WINDOW_TEXT)
            oWindow.set_cursor(gtk.gdk.Cursor(gtk.gdk.XTERM))
            self._bChangedCursor = False

    def __motion_notify_event(self, oWidget, _oEvent):
        """Change the cursor if the pointer is over a link"""
        iXPos, iYPos, _oIgnore = oWidget.window.get_pointer()
        iXPos, iYPos = oWidget.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT,
                iXPos, iYPos)
        aTags = oWidget.get_iter_at_location(iXPos, iYPos).get_tags()
        for oTag in aTags:
            if getattr(oTag, 'is_anchor', False):
                bOverAnchor = True
                break
        else:
            bOverAnchor = False
        if not self._bChangedCursor and bOverAnchor:
            oWindow = oWidget.get_window(gtk.TEXT_WINDOW_TEXT)
            oWindow.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
            self._bChangedCursor = True
        elif self._bChangedCursor and not bOverAnchor:
            oWindow = oWidget.get_window(gtk.TEXT_WINDOW_TEXT)
            oWindow.set_cursor(gtk.gdk.Cursor(gtk.gdk.XTERM))
            self._bChangedCursor = False
        return False

    def set_text_pos(self, sTextAnchor):
        """Set the position to the anchor sTextAnchor"""
        if self._dTargets.has_key(sTextAnchor):
            oMark = self._dTargets[sTextAnchor]
            self.scroll_to_mark(oMark, 0, True)
        # We just silently ignore invalid anchors

    def display_html(self, fHTMLInput):
        """Display the HTML from the file-like object fHTMLInput"""
        oBuffer = self.get_buffer()
        oStartOfBuf, oEndOfBuf = oBuffer.get_bounds()
        oBuffer.delete(oStartOfBuf, oEndOfBuf)
        oEndOfBuf = oBuffer.get_end_iter()

        oHandler = HtmlHandler(self, oEndOfBuf, self._fLinkLoader)
        oHandler.feed(fHTMLInput.read())

        if not oEndOfBuf.starts_line():
            oBuffer.insert(oEndOfBuf, "\n")

        # Need the anchor -> tag mappings
        self._dTargets = oHandler.get_targets()


class HTMLViewDialog(SutekhDialog):
    # pylint: disable-msg=R0904, R0902
    # R0904: gtk.Widget, so many public methods
    # R0902: We need to keep a lot of state to handle navigation
    """Dialog Window that wraps the HTMLTextView

       Used to show HTML Manuals in Sutekh.
       """

    _sError = """<html>
    <body>
    <h1>Resource not found</h1>
    <p>Unable to load the resource %(missing)s</p>
    </body>
    </html>
    """

    def __init__(self, oParent, fInput, fLinkLoader):
        """Dialog Window that wraps the HTMLTextView

           fInput: file-like object to read the HTML from.
           fLinkLoader: function to load links with (passed to HTMLTextView)
           """
        super(HTMLViewDialog, self).__init__('Help', oParent,
                oButtons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oDirButtons = gtk.HButtonBox()
        self._oBackButton = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self._oBackButton.connect('pressed', self._go_back)
        self._oForwardButton = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self._oForwardButton.connect('pressed', self._go_forward)
        oDirButtons.pack_start(self._oBackButton)
        oDirButtons.pack_start(self._oForwardButton)
        self._oBackButton.set_sensitive(False)
        self._oForwardButton.set_sensitive(False)
        self._fCurrent = fInput
        self._fLinkLoader = fLinkLoader
        self._sTextAnchor = None
        self._aPastUrls = []
        self._aFutureUrls = []
        self.vbox.pack_start(oDirButtons, False, False)
        self._oHTMLTextView = HTMLTextView(self._fLinkLoader)
        self._oView = AutoScrolledWindow(self._oHTMLTextView)
        self.set_default_size(400, 600)
        self.vbox.pack_start(self._oView, True,
                True)
        self._oHTMLTextView.connect('url-clicked', self._url_clicked)
        self.connect('response', lambda x, but: self.hide())
        # ignore the delete event (response handler will hide)
        self.connect('delete-event', lambda x, dlg: True)
        self._update_view()

    def _update_view(self):
        """Redraw the pane with the contents of self._fCurrent"""
        self._fCurrent.seek(0)
        self._oHTMLTextView.display_html(self._fCurrent)
        if self._sTextAnchor:
            self._oHTMLTextView.set_text_pos(self._sTextAnchor)
        if len(self._aPastUrls) > 0:
            self._oBackButton.set_sensitive(True)
        else:
            self._oBackButton.set_sensitive(False)
        if len(self._aFutureUrls) > 0:
            self._oForwardButton.set_sensitive(True)
        else:
            self._oForwardButton.set_sensitive(False)
        self.show_all()

    def show_page(self, fInput, sPos=None):
        """Display the html file in fInput in the current window."""
        self._aPastUrls.append((self._fCurrent, self._sTextAnchor))
        self._aFutureUrls = []  # Forward history is lost
        if fInput:
            self._fCurrent = fInput
        self._sTextAnchor = sPos
        self._update_view()

    def _url_clicked(self, _oWidget, sUrl, _oType):
        """Update the HTML widget with the new url"""
        aParts = sUrl.split('#')
        sFile = aParts[0]
        if len(aParts) > 1:
            sPos = aParts[1]  # Get anchor
        else:
            sPos = None
        if sFile:
            # pylint: disable-msg=W0703
            # we really do want all the exceptions
            try:
                fInput = self._fLinkLoader(sFile)
            except Exception, _oExp:
                sError = self._sError % {'missing': sUrl}
                fInput = StringIO(sError)
                sPos = None
            self.show_page(fInput, sPos)
        else:
            self.show_page(None, sPos)

    def _go_back(self, _oWidget):
        """Go backwards through the list of visited urls"""
        if len(self._aPastUrls) == 0:
            return
        self._aFutureUrls.append((self._fCurrent, self._sTextAnchor))
        self._fCurrent, self._sTextAnchor = self._aPastUrls.pop()
        self._update_view()

    def _go_forward(self, _oWidget):
        """Go forward through the list of visited urls"""
        if len(self._aFutureUrls) == 0:
            return
        self._aPastUrls.append((self._fCurrent, self._sTextAnchor))
        self._fCurrent, self._sTextAnchor = self._aFutureUrls.pop()
        self._update_view()
