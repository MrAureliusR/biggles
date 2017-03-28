#
# $Id: renderer.py,v 1.17 2004/03/08 23:30:05 mrnolta Exp $
#
# Copyright (C) 2000-2001 Mike Nolta <mike@nolta.net>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA  02111-1307, USA.
#

import math
from ._libplot_pywrap import Plotter

from .tex2libplot import tex2libplot

# polygon clipping


def sh_inside(p, dim, boundary, side):
    return side * p[dim] >= side * boundary


def sh_intersection(s, p, dim, boundary):
    mid = not dim
    g = 0.
    if p[dim] != s[dim]:
        g = (boundary - s[dim]) / (p[dim] - s[dim])
    q = [0, 0]
    q[dim] = boundary
    q[mid] = s[mid] + g * (p[mid] - s[mid])
    return q[0], q[1]


def sutherland_hodgman(polygon, dim, boundary, side):
    out = []
    s = polygon[-1]
    s_inside = sh_inside(s, dim, boundary, side)
    for p in polygon:
        p_inside = sh_inside(p, dim, boundary, side)

        crosses = (p_inside and not s_inside) or \
                  (not p_inside and s_inside)
        if crosses:
            out.append(sh_intersection(s, p, dim, boundary))

        if p_inside:
            out.append(p)

        s = p
        s_inside = p_inside

    return out


class RendererState(object):

    def __init__(self):
        self.current = {}
        self.saved = []

    def set(self, name, value):
        self.current[name] = value

    def get(self, name, notfound=None):
        if self.current.has_key(name):
            return self.current[name]
        for i in range(len(self.saved)):
            d = self.saved[i]
            if d.has_key(name):
                return d[name]
        return notfound

    def save(self):
        self.saved.insert(0, self.current)
        self.current = {}

    def restore(self):
        self.current = self.saved.pop(0)


def _hexcolor(hextriplet, scale=1):
    s = float(scale) / 0xff
    r = s * ((hextriplet >> 16) & 0xff)
    g = s * ((hextriplet >> 8) & 0xff)
    b = s * ((hextriplet >> 0) & 0xff)
    return r, g, b


def _set_color(pl, color):
    if type(color) == type(''):
        pl.set_colorname_fg(color)
    else:
        r, g, b = _hexcolor(color)
        pl.set_color_fg(r, g, b)

# this doesn't seem to do anything
'''
def _set_bgcolor(pl, color):
    if type(color) == type(''):
        print("setting bgcolor:",color)
        pl.set_colorname_bg(color)
    else:
        r, g, b = _hexcolor(color)
        pl.set_color_bg(r, g, b)
'''
def _set_pen_color(pl, color):
    if type(color) == type(''):
        pl.set_colorname_pen(color)
    else:
        r, g, b = _hexcolor(color)
        pl.set_color_pen(r, g, b)


def _set_fill_color(pl, color):
    if type(color) == type(''):
        pl.set_colorname_fill(color)
    else:
        r, g, b = _hexcolor(color)
        pl.set_color_fill(r, g, b)

_pl_line_type = {
    "dot": "dotted",
    "dash": "shortdashed",
    "dashed": "shortdashed",
}


def _set_line_type(pl, type):
    pl_type = _pl_line_type.get(type, type)
    pl.set_line_type(pl_type)


class LibplotRenderer(Plotter):

    def __init__(self, ll, ur, type='X', parameters=None, file=None):
        if file is None:
            filename = ""
        else:
            filename = file

        self.lowerleft = ll
        self.upperright = ur
        super(LibplotRenderer, self).__init__(type, parameters, filename)

    def open(self):
        self.state = RendererState()
        self.begin_page()
        args = self.lowerleft + self.upperright
        self.space(*args)
        self.clear()

    def close(self):
        self.end_page()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass

    # state commands

    __pl_style_func = {
        "color": _set_color,
        #"bgcolor": _set_bgcolor, # doesn't seem to work
        "linecolor": _set_pen_color,
        "fillcolor": _set_fill_color,
        "linetype": _set_line_type,
        "linewidth": Plotter.set_line_size,
        "filltype": Plotter.set_fill_level,
        "fillmode": Plotter.set_fill_type,
        "fontface": Plotter.set_font_type,
        "fontsize": Plotter.set_font_size,
        "textangle": Plotter.set_string_angle,
    }

    def set(self, key, value):
        self.state.set(key, value)
        if LibplotRenderer.__pl_style_func.has_key(key):
            method = LibplotRenderer.__pl_style_func[key]
            method(self, value)

    def get(self, parameter, notfound=None):
        return self.state.get(parameter, notfound)

    def save_state(self):
        self.state.save()
        self.gsave()

    def restore_state(self):
        self.state.restore()
        self.grestore()

    # drawing commands

    def move(self, p):
        super(LibplotRenderer, self).move(p[0], p[1])

    def lineto(self, p):
        super(LibplotRenderer, self).lineto(p[0], p[1])

    def linetorel(self, p):
        super(LibplotRenderer, self).linetorel(p[0], p[1])

    def line(self, p, q):
        cr = self.get("cliprect")
        if cr is None:
            super(LibplotRenderer, self).line(p[0], p[1], q[0], q[1])
        else:
            self.clipped_line(cr[0], cr[1], cr[2], cr[3],
                              p[0], p[1], q[0], q[1])

    def rect(self, p, q):
        super(LibplotRenderer, self).rect(p[0], p[1], q[0], q[1])

    def circle(self, p, r):
        super(LibplotRenderer, self).circle(p[0], p[1], r)

    def ellipse(self, p, rx, ry, angle=0.):
        super(LibplotRenderer, self).ellipse(p[0], p[1], rx, ry, angle)

    def arc(self, c, p, q):
        super(LibplotRenderer, self).arc(c[0], c[1], p[0], p[1], q[0], q[1])

    __pl_symbol_type = {
        "none": 0,
        "dot": 1,
        "plus": 2,
        "asterisk": 3,
        "circle": 4,
        "cross": 5,
        "square": 6,
        "triangle": 7,
        "diamond": 8,
        "star": 9,
        "inverted triangle": 10,
        "starburst": 11,
        "fancy plus": 12,
        "fancy cross": 13,
        "fancy square": 14,
        "fancy diamond": 15,
        "filled circle": 16,
        "filled square": 17,
        "filled triangle": 18,
        "filled diamond": 19,
        "filled inverted triangle": 20,
        "filled fancy square": 21,
        "filled fancy diamond": 22,
        "half filled circle": 23,
        "half filled square": 24,
        "half filled triangle": 25,
        "half filled diamond": 26,
        "half filled inverted triangle": 27,
        "half filled fancy square": 28,
        "half filled fancy diamond": 29,
        "octagon": 30,
        "filled octagon": 31,
    }

    def symbol(self, p):
        self.symbols([p[0]], [p[1]])

    def symbols(self, x, y):
        DEFAULT_SYMBOL_TYPE = "square"
        DEFAULT_SYMBOL_SIZE = 0.01
        type_str = self.state.get("symboltype", DEFAULT_SYMBOL_TYPE)
        size = self.state.get("symbolsize", DEFAULT_SYMBOL_SIZE)
        if len(type_str) == 1:
            type = ord(type_str[0])
        else:
            type = LibplotRenderer.__pl_symbol_type.get(type_str)

        cr = self.get("cliprect")
        if cr is None:
            super(LibplotRenderer, self).symbols(x, y, type, size)
        else:
            self.clipped_symbols(x, y, type, size,
                                 cr[0], cr[1], cr[2], cr[3])

    def colored_symbols(self, x, y, c):
        DEFAULT_SYMBOL_TYPE = "square"
        DEFAULT_SYMBOL_SIZE = 0.01
        type_str = self.state.get("symboltype", DEFAULT_SYMBOL_TYPE)
        size = self.state.get("symbolsize", DEFAULT_SYMBOL_SIZE)
        if len(type_str) == 1:
            type = ord(type_str[0])
        else:
            type = LibplotRenderer.__pl_symbol_type.get(type_str)

        cr = self.get("cliprect")
        if cr is None:
            # This will cause an error: not written yet
            super(LibplotRenderer, self).colored_symbols(x, y, type, size)
        else:
            self.clipped_colored_symbols(x, y, c,
                                         type, size,
                                         cr[0], cr[1],
                                         cr[2], cr[3])

    def density_plot(self, densgrid, ((xmin, ymin), (xmax, ymax))):
        super(LibplotRenderer, self).density_plot(densgrid, xmin, xmax, ymin, ymax)

    def color_density_plot(self, densgrid, ((xmin, ymin), (xmax, ymax))):
        super(LibplotRenderer, self).color_density_plot(densgrid,
                                                        xmin, xmax, ymin, ymax)

    def curve(self, x, y):
        cr = self.get("cliprect")
        if cr is None:
            super(LibplotRenderer, self).curve(x, y)
        else:
            self.clipped_curve(x, y,
                               cr[0], cr[1], cr[2], cr[3])

    def polygon(self, points):
        pts = points
        cr = self.get("cliprect")
        if cr is not None:
            pts = sutherland_hodgman(pts, 0, cr[0], +1)
            pts = sutherland_hodgman(pts, 0, cr[1], -1)
            pts = sutherland_hodgman(pts, 1, cr[2], +1)
            pts = sutherland_hodgman(pts, 1, cr[3], -1)
        self.move(pts[0])
        map(self.lineto, pts[1:])

    # text commands

    __pl_text_align = {
        "center": ord('c'),
        "baseline": ord('x'),
        "left": ord('l'),
        "right": ord('r'),
        "top": ord('t'),
        "bottom": ord('b'),
    }

    def text(self, p, str):
        plstr = tex2libplot(str)
        hstr = self.state.get("texthalign", "center")
        vstr = self.state.get("textvalign", "center")
        hnum = LibplotRenderer.__pl_text_align.get(hstr)
        vnum = LibplotRenderer.__pl_text_align.get(vstr)
        super(LibplotRenderer, self).move(p[0], p[1])
        self.string(hnum, vnum, plstr)

    def textwidth(self, str):
        plstr = tex2libplot(str)
        return self.get_string_width(plstr)

    def textheight(self, str):
        return self.state.get("fontsize")  # XXX: kludge?


class ScreenRenderer(LibplotRenderer):

    def __init__(self, width=640, height=640, bgcolor="white"):
        ll = 0, 0
        ur = width, height
        parameters = {
            "BITMAPSIZE": "%dx%d" % (width, height),
            "VANISH_ON_DELETE": "no",
            "BG_COLOR":bgcolor,
        }
        super(ScreenRenderer, self).__init__(
            ll,
            ur,
            "X",
            parameters,
        )

    def __exit__(self, exception_type, exception_value, traceback):
        self.flush()
        self.close()

def _str_size_to_pts(str):
    import re
    m = re.compile(r"([\d.]+)([^\s]+)").match(str)
    num_xx = float(m.group(1))
    units = m.group(2)
    # convert to postscipt pt = in/72
    xx2pt = {"in": 72, "pt": 1, "mm": 2.835, "cm": 28.35}
    num_pt = int(num_xx * xx2pt[units])
    return num_pt


class PSRenderer(LibplotRenderer):

    def __init__(self, filename, paper="", width="", height="", **kw):
        ll = 0, 0
        ur = _str_size_to_pts(width), _str_size_to_pts(height)
        pagesize = "%s,xsize=%s,ysize=%s" % (paper, width, height)
        for key, val in kw.items():
            pagesize = pagesize + "," + key + "=" + val
        parameters = {"PAGESIZE": pagesize}
        super(PSRenderer, self).__init__(ll, ur, "ps", parameters, filename)


class ImageRenderer(LibplotRenderer):

    def __init__(self, type, width, height, file):
        ll = 0, 0
        ur = width, height
        parameters = {"BITMAPSIZE": "%dx%d" % (width, height)}
        super(ImageRenderer, self).__init__(ll, ur, type, parameters, file)
