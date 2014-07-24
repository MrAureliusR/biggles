#
# $Id: func.py,v 1.21 2007/04/19 15:51:46 mrnolta Exp $
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

import biggles, config
import string
import numpy
import itertools,operator,copy

LINE_TYPES=["solid","dotted","dotdashed","shortdashed",
            "longdashed","dotdotdashed","dotdotdotdashed"]
DEFAULT_SYMBOL='filled circle'

def plot(xin, yin, visible=True, plt=None, **kw):
    """
    A wrapper to perform a quick scatter plot with biggles.
    
    For anything more complex, it is better to use the object oriented
    interface.

    parameters
    ----------
    x: scalar, sequence or array
        The x data to plot
    y: scalar, sequence or array
        The y data to plot
    yerr: optional scalar, sequence or array
        Optional error bars in the y direction
    xerr: optional scalar, sequence or array
        Optional error bars in the x direction
    visible: bool
        If True, show plot on the screen.  Default True
    plt: biggles plot object
        If sent, add symbols or lines to this object.

    **keywords:
        Other optional Keywords for the FramedPlot instance (or whatever is
        passed though plt=), the Points, and Curve instances.

    Example keywords...

    # plot range keywords
    xrange: 2-element sequence
        Optional range for x axis
    yrange: 2-element sequence
        Optional range for y axis

    # marker type keywords can be sent explicitly as symboltype=, linetype=
    # or shorthand as type=.  If type= is sent, the marker type is
    # determined by the name (e.g. 'filled circle' implies a symbol
    # while 'longdashed' implies a line.
    #
    # If not type is sent, the overall biggles default is used (currently
    # open diamond symbol)
    #
    # Also if both symboltype= and linetype= are sent, then both will be
    # plotted

    type: string, optional keyword
        The marker type.  If one of 
            ["solid","dotted","dotdashed","shortdashed", "longdashed",
            "dotdotdashed","dotdotdotdashed"]
        then a Curve is plotted, else symbols.

    symboltype: string
        Explicitly specify a Point is to be plotted, with the
        indicated type.
    linetype: string
        Explicitly specify a Curve is to be plotted, with the
        indicated type.

    [symbol|line]color: string
        Color to be used for the marker.  Either the short color=
        can be used or the more explicity symbolcolor= or linecolor=
        can be used.

    xlabel: string
        Label for x axis.  Tex sequences are allowed, e.g.
        r'$\sigma$'
    ylabel: string
        Label for y axis.
    title: string
        Label for top of plot

    returned value
    ---------------
    The biggles plot object.

    examples
    --------

    import biggles
    biggles.plot(x, y, yerr=yerr, type='filled circle')
    """

    splt=ScatterPlot(xin, yin, plt=plt, **kw)

    if visible:
        splt.show()

    plt=splt.get_plot()

    return plt

class ScatterPlot(dict):
    """
    Wrapper class to create a scatter plot

    parameters
    ----------
    x: scalar, sequence or array
        The x data to plot
    y: scalar, sequence or array
        The y data to plot
    yerr: optional scalar, sequence or array
        Optional error bars in the y direction
    xerr: optional scalar, sequence or array
        Optional error bars in the x direction
    visible: bool
        If True, show plot on the screen.  Default True
    plt: biggles plot object
        If sent, add symbols or lines to this object.

    **keywords:
        Other optional Keywords for the FramedPlot instance (or whatever is
        passed though plt=), the Points, and Curve instances.

    Example keywords...

    # plot range keywords
    xrange: 2-element sequence
        Optional range for x axis
    yrange: 2-element sequence
        Optional range for y axis

    # marker type keywords can be sent explicitly as symboltype=, linetype=
    # or shorthand as type=.  If type= is sent, the marker type is
    # determined by the name (e.g. 'filled circle' implies a symbol
    # while 'longdashed' implies a line.
    #
    # If not type is sent, the overall biggles default is used (currently
    # open diamond symbol)
    #
    # Also if both symboltype= and linetype= are sent, then both will be
    # plotted

    type: string, optional keyword
        The marker type.  If one of 
            ["solid","dotted","dotdashed","shortdashed", "longdashed",
            "dotdotdashed","dotdotdotdashed"]
        then a Curve is plotted, else symbols.

    symboltype: string
        Explicitly specify a Point is to be plotted, with the
        indicated type.
    linetype: string
        Explicitly specify a Curve is to be plotted, with the
        indicated type.

    [symbol|line]color: string
        Color to be used for the marker.  Either the short color=
        can be used or the more explicity symbolcolor= or linecolor=
        can be used.

    xlabel: string
        Label for x axis.  Tex sequences are allowed, e.g.
        r'$\sigma$'
    ylabel: string
        Label for y axis.
    title: string
        Label for top of plot

    returned value
    ---------------
    The biggles plot object.

    examples
    --------

    import biggles
    plt=biggles.ScatterPlot(x, y, yerr=yerr, type='filled circle')

    """
    def __init__(self, xin, yin, plt=None, **keys):

        self.update(keys)

        self._set_pts(xin, yin)
        self._set_log_axes()
        self._set_range_and_subpts()
        self._set_markers_from_shorthand()
        self._set_plot_object(plt, **keys)

        self._add_markers()

    def show(self):
        """
        show the plot
        """
        self.plt.show()

    def get_plot(self):
        """
        get the plot object
        """
        return self.plt

    def _set_pts(self, xin, yin):
        """
        make sure the points are arrays of the same size
        """
        self.x=numpy.array(xin, ndmin=1, copy=False)
        self.y=numpy.array(yin, ndmin=1, copy=False)

        if self.x.size != self.y.size:
            raise ValueError("x and y are different "
                             "size: %s %s" % (self.x.size, self.y.size))

        xerr = self.get('xerr',None)
        yerr = self.get('yerr',None)
        if xerr is not None:
            xerr=numpy.array(xerr, ndmin=1, copy=False)
            if xerr.size != self.x.size:
                raise ValueError("xerr and points are different "
                                 "size: %s %s" % (xerr.size, self.y.size))

        if yerr is not None:
            yerr=numpy.array(yerr, ndmin=1, copy=False)
            if yerr.size != self.x.size:
                raise ValueError("yerr and points are different "
                                 "size: %s %s" % (yerr.size, self.y.size))

        self.xerr=xerr
        self.yerr=yerr

    def _set_log_axes(self):
        self['xlog'] = self.get('xlog',False)
        self['ylog'] = self.get('ylog',False)

    def _set_range_and_subpts(self):
        """
        keys['xerr'] and 'yerr' could be modified to be 1-d arrays in the range,
        so make sure keys was already a copy of original keys
        """

        x=self.x
        y=self.y
        xerr=self.xerr
        yerr=self.yerr

        xrng = self.get('xrange',None)
        yrng = self.get('yrange',None)

        # For log, Don't plot points less than zero
        w=None
        if self['xlog'] and self['ylog']:
            xrng = get_log_plot_range(x, err=xerr, input_range=xrng)
            yrng = get_log_plot_range(y, err=yerr, input_range=yrng)
            w,=numpy.where( (x > xrng[0]) & (y > yrng[0]) )
        elif self['xlog']:
            xrng = get_log_plot_range(x, err=xerr, input_range=xrng)
            w,=numpy.where( x > xrng[0])
        elif self['ylog']:
            yrng = get_log_plot_range(y, err=yerr, input_range=yrng)
            w,=numpy.where( y > yrng[0])

        if w is not None:
            if w.size == 0:
                raise ValueError("no points are in range")
        self.indices=w
        self.xrng=xrng
        self.yrng=yrng

    def _set_markers_from_shorthand(self):
        """
        set long-form marker type in the case where the shorthand type= is sent
        """

        # shorthand for either symbol or line type
        type = self.get('type', None)

        # figure out what marker type we have
        if type is not None:
            # figure out the marker type from the marker name
            if type in LINE_TYPES:
                self['linetype']=type
            else:
                self['symboltype']=type

    def _set_plot_object(self, plt, **keys):
        """
        set the plot object, potentially re-using the input
        """
        if plt is None:
            plt = biggles.FramedPlot(**keys)
        else:
            for key,value in keys.iteritems():
                if hasattr(plt,key):
                    setattr(plt,key,value)
            plt=plt

        xrng=self.xrng
        yrng=self.yrng
        if xrng is not None:
            plt.xrange=xrng
        if yrng is not None:
            plt.yrange=yrng

        self.plt=plt


    def _add_markers(self):
        """
        add the actual markers, including error bars
        """
        linetype=self['linetype']
        symboltype=self['symboltype']

        # note we default to symbols if no type is set.  Also if both types are
        # sent, we plot both
        plt=self.plt
        if symboltype is not None or (symboltype is None and linetype is None):
            self._add_symbols()

        if linetype is not None:
            self._add_curve()

        self._add_error_bars()

    def _add_symbols(self):
        symboltype=self['symboltype']
        if symboltype is None:
            self['symboltype']=DEFAULT_SYMBOL

        indices=self.indices
        if indices is None:
            self.plt.add(biggles.Points(self.x, self.y, **self))
        else:
            self.plt.add(biggles.Points(self.x[indices], self.y[indices], **self))

    def _add_curve(self):

        plt=self.plt
        indices=self.indices
        if indices is None:
            plt.add(biggles.Curve(self.x, self.y, **self))
        else:
            x=self.x
            y=self.y
            for key, grps in itertools.groupby(enumerate(indices), lambda (i,x):i-x):
                wgrp = map(operator.itemgetter(1), grps)
                plt.add(biggles.Curve(x[wgrp], y[wgrp], **self))


    def _add_error_bars(self):
        from .biggles import SymmetricErrorBarsY,SymmetricErrorBarsX

        x=self.x
        y=self.y
        xerr=self.xerr
        yerr=self.yerr

        plt=self.plt
        if xerr is not None or yerr is not None:


            keys = {}
            keys.update(self)
            if 'errlinetype' in keys:
                if 'errlinetype' in keys:
                    keys['linetype'] = keys['errlinetype']
                else:
                    keys['linetype'] = 'solid'
            if 'errlinewidth' in keys:
                keys['linewidth'] = keys['errlinewidth']
            if 'errlinecolor' in keys:
                keys['linecolor'] = keys['errlinecolor']

            if yerr is not None:
                if self['ylog']:
                    add_log_error_bars(plt, 'y', x, y, yerr, self.yrng, **keys)
                else:
                    p_yerr=SymmetricErrorBarsY(x, y, yerr, **keys)
                    plt.add(p_yerr)
            if xerr is not None:
                if self['xlog']:
                    add_log_error_bars(plt, 'y', x, y, xerr, self.xrng, **keys)
                else:
                    p_xerr=SymmetricErrorBarsX(x, y, xerr, **keys)
                    plt.add(p_xerr)



def get_log_plot_range(x, err=None, input_range=None, get_good=False):
    """
    Get a plot range in the case of log axes
    """
    if input_range is not None:
        if len(input_range) < 2:
            raise ValueError("expected [xmin,xmax] for input range")
        if input_range[0] <= 0. or input_range[1] <= 0.:
            raise ValueError("cannot use plot range < 0 for log plots, got [%s,%s]" % tuple(input_range))
        if get_good:
            w,=numpy.where((x >= input_range[0]) & (x <= input_range[1]))
            return input_range, w
        else:
            return input_range

    w,=numpy.where(x > 0.)
    if w.size == 0:
        raise ValueError("No values are greater than zero in log plot")

    minval = min(x[w])
    if err is not None:
        w2, = numpy.where( (x[w] - err[w]) > 0 )
        if w2.size > 0:
            minval2 =  min(x[w[w2]] - err[w[w2]])
            minval = min(minval,minval2)

        maxval = max(x+err)
    else:
        maxval = max(x)

    minval *= 0.5
    maxval *= 2

    if get_good:
        return [minval,maxval], w
    else:
        return [minval,maxval]

def add_log_error_bars(plt, axis, x, y, err, prange, **keys):
    from .biggles import ErrorBarsX, ErrorBarsY
    if axis == 'x':
        low = x-err
        high = x+err
    else:
        low = y-err
        high = y+err

    w,=numpy.where(high > 0)
    if w.size > 0:
        high = high[w]

        # outside range to avoid seeing hat
        low = low[w].clip(0.5*prange[0], 2.0*max(max(high),prange[1]) )

        if axis == 'x':
            p=biggles.ErrorBarsX(y[w], low, high, **keys)
        else:
            p=biggles.ErrorBarsY(x[w], low, high, **keys)
        plt.add(p)

        return p


