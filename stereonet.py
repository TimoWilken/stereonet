#!/usr/bin/env python3

'''Plots a stereonet of planes and lines.'''

import sys
import functools as ft
import itertools as it
import operator as op
import numpy as np
import matplotlib as mp
import matplotlib.pyplot as plot


class Plane:
    '''Represents a plane on a stereonet.'''

    __slots__ = 'strike', 'dip'

    def __init__(self, strike, dip):
        self.strike, self.dip = strike, dip

    def pole(self):
        '''Get the pole (normal vector) to the plane as a Line.'''
        return Line(trend=self.strike - np.pi/2, plunge=np.pi/2 - self.dip)


class Line:
    '''Represents a line on a stereonet.'''

    __slots__ = 'plunge', 'trend'

    def __init__(self, plunge, trend):
        self.plunge, self.trend = plunge, trend


def read_data(filename, sep='/'):
    '''Generator of data points from the specified file.'''
    valid_fields = 'strike', 'dip', 'plunge', 'trend'
    with open(filename, 'rt') as dataf:
        fields = dataf.readline().strip().split(sep)
        assert all(map(ft.partial(op.contains, valid_fields), fields)), fields
        yield fields
        yield from (tuple(map(int, line.split(sep))) for line in dataf)


def main():
    '''Main entry point.'''
    data = read_data(sys.argv[1])
    fields = next(data)
    data = list(data)

    if 'plunge' in fields and 'trend' in fields:
        # poles
        radii = [90 - p[fields.index('plunge')] for p in data]
        thetas = np.radians([p[fields.index('trend')] - 90 for p in data])
        plot.polar(thetas, radii, 'b.')

    if 'strike' in fields and 'dip' in fields:
        # planes
        for point in data:
            strike, dip = np.radians((point[fields.index('strike')],
                                      point[fields.index('dip')]))
            rotations = []

            for rot_angle in np.linspace(0, np.pi, 100):
                cosa, cosb, cosg, cosw = np.cos((strike, np.pi/2 - strike,
                                                 np.pi/2, rot_angle))
                sinw = np.sin(rot_angle)

                rotation = (1 - cosw) * np.matrix([[
                    cosw + cosa**2,
                    -cosw * sinw + cosa * cosb,
                    -cosb * sinw + cosa * cosg,
                ], [
                    cosg * sinw + cosb * cosa,
                    cosw + cosb**2,
                    -cosa * sinw + cosb * cosg,
                ], [
                    -cosb * sinw + cosg * cosa,
                    cosa * sinw + cosg * cosb,
                    cosw + cosg**2,
                ]])
                trans_coord = (
                )
            plot.polar(rotations)

    plot.show()


if __name__ == '__main__':
    main()
