# HTMLTextView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# TextView Object that displays an HTML file
# Copyright 2005, 2006, 2007 Gustavo J. A. M. Carneiro
# Changes for Sutekh, Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# License: GPL - See COPYRIGHT file for details
# Original version downloaded from http://www.gnome.org/~gjc/htmltextview.py
# April 2008

'''
A gtk.TextView-based renderer for XHTML-IM, as described in:
  http://www.jabber.org/jeps/jep-0071.html
'''

import gobject
import pango
import gtk
import re
import warnings
import operator
import xml.sax, xml.sax.handler
from pkg_resources import resource_stream
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

oWhiteSpaceRegex = re.compile("\\s+")
oAllWhiteSpaceRegex = re.compile("^\\s*$")

## pixels = points * fResolution
fResolution = 0.3514598*(gtk.gdk.screen_height() /
                    float(gtk.gdk.screen_height_mm()))

def _parse_css_color(sColor):
    '''_parse_css_color(css_color) -> gtk.gdk.Color'''
    if sColor.startswith("rgb(") and sColor.endswith(')'):
        iRed, iGreen, iBlue = [int(c)*257 for c in sColor[4:-1].split(',')]
        return gtk.gdk.Color(iRed, iGreen, iBlue)
    else:
        return gtk.gdk.color_parse(sColor)

class HtmlHandler(xml.sax.handler.ContentHandler):
    """Parse the HTML imput and update the gtk.TextView"""
    def __init__(self, textview, startiter):
        xml.sax.handler.ContentHandler.__init__(self)
        self._oTextBuf = textview.get_buffer()
        self._oTextView = textview
        self._oIter = startiter
        self._sText = ''
        self.styles = [] # a gtk.TextTag or None, for each span level
        self._aListCounters = [] # stack (top at head) of list
                                # counters, or None for unordered list
        self._bInTitle = False

    def _parse_style_color(self, oTag, sValue):
        oColor = _parse_css_color(sValue)
        oTag.set_property("foreground-gdk", oColor)

    def _parse_style_background_color(self, oTag, sValue):
        oColor = _parse_css_color(sValue)
        oTag.set_property("background-gdk", oColor)
        if gtk.gtk_version >= (2, 8):
            oTag.set_property("paragraph-background-gdk", oColor)


    if gtk.gtk_version >= (2, 8, 5) or gobject.pygtk_version >= (2, 8, 1):

        def _get_current_attributes(self):
            aAttrs = self._oTextView.get_default_attributes()
            self._oIter.backward_char()
            self._oIter.get_attributes(aAttrs)
            self._oIter.forward_char()
            return aAttrs

    else:

        ## Workaround http://bugzilla.gnome.org/show_bug.cgi?id=317455
        def _get_current_style_attr(self, propname, comb_oper=None):
            aTags = [oTag for oTag in self.styles if oTag is not None]
            aTags.reverse()
            is_set_name = propname + "-set"
            oValue = None
            for oTag in aTags:
                if oTag.get_property(is_set_name):
                    if oValue is None:
                        oValue = oTag.get_property(propname)
                        if comb_oper is None:
                            return oValue
                    else:
                        oValue = comb_oper(oValue, oTag.get_property(propname))
            return oValue

        class _FakeAttrs(object):
            """Fake class with default attributes"""
            __slots__ = ("font", "font_scale")

        def _get_current_attributes(self):
            aAttrs = self._FakeAttrs()
            aAttrs.font_scale = self._get_current_style_attr("scale",
                                                            operator.mul)
            if aAttrs.font_scale is None:
                aAttrs.font_scale = 1.0
            aAttrs.font = self._get_current_style_attr("font-desc")
            if aAttrs.font is None:
                aAttrs.font = self._oTextView.style.font_desc
            return aAttrs

    def __parse_length_frac_size_allocate(self, textview, allocation,
                                          frac, callback, args):
        callback(allocation.width*frac, *args)

    def _parse_length(self, value, font_relative, callback, *args):
        """Parse/calc length, converting to pixels.

           calls callback(length, *args) when the length is first computed
           or changes
           """
        if value.endswith('%'):
            frac = float(value[:-1])/100
            if font_relative:
                attrs = self._get_current_attributes()
                font_size = attrs.font.get_size() / pango.SCALE
                callback(frac*fResolution*font_size, *args)
            else:
                ## CSS says "Percentage values: refer to width of the closest
                ##           block-level ancestor"
                ## This is difficult/impossible to implement, so we use
                ## textview width instead; a reasonable approximation..
                alloc = self._oTextView.get_allocation()
                self.__parse_length_frac_size_allocate(self._oTextView, alloc,
                                                       frac, callback, args)
                self._oTextView.connect("size-allocate",
                                      self.__parse_length_frac_size_allocate,
                                      frac, callback, args)

        elif value.endswith('pt'): # points
            callback(float(value[:-2])*fResolution, *args)

        elif value.endswith('em'): # ems, the height of the element's font
            attrs = self._get_current_attributes()
            font_size = attrs.font.get_size() / pango.SCALE
            callback(float(value[:-2])*fResolution*font_size, *args)

        elif value.endswith('ex'): # x-height, ~ the height of the letter 'x'
            ## FIXME: figure out how to calculate this correctly
            ##        for now 'em' size is used as approximation
            attrs = self._get_current_attributes()
            font_size = attrs.font.get_size() / pango.SCALE
            callback(float(value[:-2])*fResolution*font_size, *args)

        elif value.endswith('px'): # pixels
            callback(int(value[:-2]), *args)

        else:
            warnings.warn("Unable to parse length value '%s'" % value)

    def __parse_font_size_cb(length, oTag):
        oTag.set_property("size-points", length/fResolution)
    __parse_font_size_cb = staticmethod(__parse_font_size_cb)

    def _parse_style_font_size(self, oTag, value):
        try:
            scale = {
                "xx-small": pango.SCALE_XX_SMALL,
                "x-small": pango.SCALE_X_SMALL,
                "small": pango.SCALE_SMALL,
                "medium": pango.SCALE_MEDIUM,
                "large": pango.SCALE_LARGE,
                "x-large": pango.SCALE_X_LARGE,
                "xx-large": pango.SCALE_XX_LARGE,
                } [value]
        except KeyError:
            pass
        else:
            attrs = self._get_current_attributes()
            oTag.set_property("scale", scale / attrs.font_scale)
            return
        if value == 'smaller':
            oTag.set_property("scale", pango.SCALE_SMALL)
            return
        if value == 'larger':
            oTag.set_property("scale", pango.SCALE_LARGE)
            return
        self._parse_length(value, True, self.__parse_font_size_cb, oTag)

    def _parse_style_font_style(self, oTag, value):
        try:
            style = {
                "normal": pango.STYLE_NORMAL,
                "italic": pango.STYLE_ITALIC,
                "oblique": pango.STYLE_OBLIQUE,
                } [value]
        except KeyError:
            warnings.warn("unknown font-style %s" % value)
        else:
            oTag.set_property("style", style)

    def __frac_length_tag_cb(length, oTag, propname):
        oTag.set_property(propname, length)
    __frac_length_tag_cb = staticmethod(__frac_length_tag_cb)

    def _parse_style_margin_left(self, oTag, value):
        self._parse_length(value, False, self.__frac_length_tag_cb,
                           oTag, "left-margin")

    def _parse_style_margin_right(self, oTag, value):
        self._parse_length(value, False, self.__frac_length_tag_cb,
                           oTag, "right-margin")

    def _parse_style_font_weight(self, oTag, value):
        ## TODO: missing 'bolder' and 'lighter'
        try:
            weight = {
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
                } [value]
        except KeyError:
            warnings.warn("unknown font-style %s" % value)
        else:
            oTag.set_property("weight", weight)

    def _parse_style_font_family(self, oTag, value):
        oTag.set_property("family", value)

    def _parse_style_text_align(self, oTag, value):
        try:
            align = {
                'left': gtk.JUSTIFY_LEFT,
                'right': gtk.JUSTIFY_RIGHT,
                'center': gtk.JUSTIFY_CENTER,
                'justify': gtk.JUSTIFY_FILL,
                } [value]
        except KeyError:
            warnings.warn("Invalid text-align:%s requested" % value)
        else:
            oTag.set_property("justification", align)

    def _parse_style_text_decoration(self, oTag, value):
        if value == "none":
            oTag.set_property("underline", pango.UNDERLINE_NONE)
            oTag.set_property("strikethrough", False)
        elif value == "underline":
            oTag.set_property("underline", pango.UNDERLINE_SINGLE)
            oTag.set_property("strikethrough", False)
        elif value == "overline":
            warnings.warn("text-decoration:overline not implemented")
            oTag.set_property("underline", pango.UNDERLINE_NONE)
            oTag.set_property("strikethrough", False)
        elif value == "line-through":
            oTag.set_property("underline", pango.UNDERLINE_NONE)
            oTag.set_property("strikethrough", True)
        elif value == "blink":
            warnings.warn("text-decoration:blink not implemented")
        else:
            warnings.warn("text-decoration:%s not implemented" % value)


    ## build a dictionary mapping styles to methods, for greater speed
    __style_methods = dict()
    for style in ["background-color", "color", "font-family", "font-size",
                  "font-style", "font-weight", "margin-left", "margin-right",
                  "text-align", "text-decoration"]:
        try:
            method = locals()["_parse_style_%s" % style.replace('-', '_')]
        except KeyError:
            warnings.warn("Style attribute '%s' not yet implemented" % style)
        else:
            __style_methods[style] = method

    def _get_style_tags(self):
        return [oTag for oTag in self.styles if oTag is not None]

    def _begin_span(self, style, oTag=None):
        if style is None:
            self.styles.append(oTag)
            return None
        if oTag is None:
            oTag = self._oTextBuf.create_tag()
        for attr, val in [item.split(':', 1) for item in style.split(';')]:
            attr = attr.strip().lower()
            val = val.strip()
            try:
                method = self.__style_methods[attr]
            except KeyError:
                warnings.warn("Style attribute '%s' requested "
                              "but not yet implemented" % attr)
            else:
                method(self, oTag, val)
        self.styles.append(oTag)

    def _end_span(self):
        self.styles.pop(-1)

    def _insert_text(self, text):
        tags = self._get_style_tags()
        if tags:
            self._oTextBuf.insert_with_tags(self._oIter, text, *tags)
        else:
            self._oTextBuf.insert(self._oIter, text)

    def _flush_text(self):
        if not self._sText:
            return
        self._insert_text(self._sText.replace('\n', ''))
        self._sText = ''

    def _anchor_event(self, oTag, textview, event, iter, href, type_):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            self._oTextView.emit("url-clicked", href, type_)
            return True
        return False

    def characters(self, content):
        if oAllWhiteSpaceRegex.match(content) is not None:
            return
        if self._bInTitle:
            return
        #if self._sText:
        #    self._sText += ' '
        self._sText += oWhiteSpaceRegex.sub(' ', content)

    def startElement(self, sName, attrs):
        self._flush_text()
        try:
            style = attrs['style']
        except KeyError:
            style = None

        oTag = None
        if sName == 'a':
            oTag = self._oTextBuf.create_tag()
            oTag.set_property('foreground', '#0000ff')
            oTag.set_property('underline', pango.UNDERLINE_SINGLE)
            try:
                type_ = attrs['type']
            except KeyError:
                type_ = None
            oTag.connect('event', self._anchor_event, attrs['href'], type_)
            oTag.is_anchor = True
        elif sName in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
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

        self._begin_span(style, oTag)

        if sName == 'br':
            pass # handled in endElement
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
            self._aListCounters.insert(0, None)
        elif sName == 'ol':
            if not self._oIter.starts_line():
                self._insert_text("\n")
            self._aListCounters.insert(0, 0)
        elif sName == 'li':
            if self._aListCounters[0] is None:
                li_head = unichr(0x2022)
            else:
                self._aListCounters[0] += 1
                li_head = "%i." % self._aListCounters[0]
            self._sText = ' '*len(self._aListCounters)*4 + li_head + ' '
        elif sName == 'img':
            try:
                # FIXME: Fix this to avoid the ../docs/ hack
                oFile = resource_stream(__name__, '../docs/' + attrs['src'])
                oLoader = gtk.gdk.PixbufLoader()
                oLoader.write(oFile.read())
                oLoader.close()
                oPixbuf = oLoader.get_pixbuf()
            except Exception, ex:
                oPixbuf = None
                try:
                    sAlt = attrs['alt']
                except KeyError:
                    sAlt = "Broken image"
            if oPixbuf is not None:
                tags = self._get_style_tags()
                if tags:
                    tmpmark = self._oTextBuf.create_mark(None, self._oIter,
                            True)

                self._oTextBuf.insert_pixbuf(self._oIter, oPixbuf)

                if tags:
                    start = self._oTextBuf.get_iter_at_mark(tmpmark)
                    for oTag in tags:
                        self._oTextBuf.apply_tag(oTag, start, self._oIter)
                    self._oTextBuf.delete_mark(tmpmark)
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
        elif sName in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            pass
        else:
            warnings.warn("Unhandled element '%s'" % sName)

    def endElement(self, sName):
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
        elif sName in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if not self._oIter.starts_line():
                self._insert_text("\n")
        else:
            warnings.warn("Unhandled element '%s'" % sName)
        self._end_span()

class HTMLTextView(gtk.TextView):
    """TextView subclass to display HTML"""
    __gtype_name__ = 'HTMLTextView'
    __gsignals__ = {
        'url-clicked': (gobject.SIGNAL_RUN_LAST, None, (str, str)),
        # href, type
    }

    def __init__(self):
        gtk.TextView.__init__(self)
        self.set_wrap_mode(gtk.WRAP_CHAR)
        self.set_editable(False)
        self._bChangedCursor = False
        self.connect("motion-notify-event", self.__motion_notify_event)
        self.connect("leave-notify-event", self.__leave_event)
        self.connect("enter-notify-event", self.__motion_notify_event)
        self.set_pixels_above_lines(3)
        self.set_pixels_below_lines(3)

    def __leave_event(self, widget, event):
        if self._bChangedCursor:
            window = widget.get_window(gtk.TEXT_WINDOW_TEXT)
            window.set_cursor(gtk.gdk.Cursor(gtk.gdk.XTERM))
            self._bChangedCursor = False

    def __motion_notify_event(self, widget, event):
        iX, iY, _ = widget.window.get_pointer()
        iX, iY = widget.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT, iX, iY)
        aTags = widget.get_iter_at_location(iX, iY).get_tags()
        for oTag in aTags:
            if getattr(oTag, 'is_anchor', False):
                bOverAnchor = True
                break
        else:
            bOverAnchor = False
        if not self._bChangedCursor and bOverAnchor:
            window = widget.get_window(gtk.TEXT_WINDOW_TEXT)
            window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
            self._bChangedCursor = True
        elif self._bChangedCursor and not bOverAnchor:
            window = widget.get_window(gtk.TEXT_WINDOW_TEXT)
            window.set_cursor(gtk.gdk.Cursor(gtk.gdk.XTERM))
            self._bChangedCursor = False
        return False

    def display_html(self, fHTMLInput):
        """Displa the HTML from the file-like object fHTMLInput"""
        oBuffer = self.get_buffer()
        oEndOfBuf = oBuffer.get_end_iter()
        parser = xml.sax.make_parser()
        # parser.setFeature(xml.sax.handler.feature_validation, True)
        parser.setContentHandler(HtmlHandler(self, oEndOfBuf))
        #parser.setEntityResolver(HtmlEntityResolver())
        parser.parse(fHTMLInput)

        if not oEndOfBuf.starts_line():
            oBuffer.insert(oEndOfBuf, "\n")

if gobject.pygtk_version < (2, 8):
    gobject.type_register(HTMLTextView)

class HTMLViewDialog(SutekhDialog):
    """Dialog Window that wraps the HTMLTextView

       Used to show HTML Manuals in Sutekh.
       """

    def __init__(self, oParent, fInput):
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
        self._aPastUrls=[]
        self._aFutureUrls=[]
        self.vbox.pack_start(oDirButtons, False, False)
        self._oHTMLTextView = HTMLTextView()
        self._oView = AutoScrolledWindow(self._oHTMLTextView)
        self.set_default_size(400, 600)
        self._oHTMLTextView.display_html(fInput)
        self.vbox.pack_start(self._oView, True,
                True)
        self._oHTMLTextView.connect('url-clicked', self._url_clicked)
        self.show_all()

    def _url_clicked(self, oWidget, sUrl, oType):
        """Update the HTML widget with the new url"""
        fInput = resource_stream(__name__, '../docs/' + sUrl)
        self._aPastUrls.append(self._fCurrent)
        self._aFutureUrls = [] # Forward history is lost
        self._fCurrent = fInput
        self._update_view()

    def _update_view(self):
        """Redraw the pane with the contents of self._fCurrent"""
        self._fCurrent.seek(0)
        self._oView.remove(self._oHTMLTextView)
        self._oHTMLTextView = HTMLTextView()
        self._oHTMLTextView.display_html(self._fCurrent)
        self._oHTMLTextView.connect('url-clicked', self._url_clicked)
        self._oView.add(self._oHTMLTextView)
        if len(self._aPastUrls) > 0:
            self._oBackButton.set_sensitive(True)
        else:
            self._oBackButton.set_sensitive(False)
        if len(self._aFutureUrls) > 0:
            self._oForwardButton.set_sensitive(True)
        else:
            self._oForwardButton.set_sensitive(False)
        self.show_all()

    def _go_back(self, oWidget):
        """Go backwards through the list of visited urls"""
        if len(self._aPastUrls) == 0:
            return
        print self._aPastUrls
        self._aFutureUrls.append(self._fCurrent)
        self._fCurrent = self._aPastUrls.pop()
        self._update_view()

    def _go_forward(self, oWidget):
        """Go forward through the list of visited urls"""
        if len(self._aFutureUrls) == 0:
            return
        self._aPastUrls.append(self._fCurrent)
        self._fCurrent = self._aFutureUrls.pop()
        self._update_view()
