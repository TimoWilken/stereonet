#!/usr/bin/env python3

'''Basic representations of structural data.'''

import operator as op
from math import sqrt, pi, sin, cos, atan, asin, degrees


def to_int_degrees(rad):
    '''Round radians to integer degrees.'''
    return int(round(degrees(rad)))


class DirectionCosines(tuple):
    '''Represents direction cosines, acting like a cartesian vector.'''

    def __add__(self, other):
        return DirectionCosines(self[i] + comp for i, comp in enumerate(other))

    def __sub__(self, other):
        return DirectionCosines(self[i] - comp for i, comp in enumerate(other))

    def __mul__(self, other):
        # scalar multiplication, DirectionCosines * scalar
        return DirectionCosines(comp * other for comp in self)
    # scalar multiplication, scalar * DirectionCosines
    __rmul__ = __mul__

    def __truediv__(self, other):
        return DirectionCosines(comp / other for comp in self)

    def __floordiv__(self, other):
        return DirectionCosines(comp // other for comp in self)

    def __neg__(self):
        return DirectionCosines(-comp for comp in self)

    def __pos__(self):
        return self

    def __abs__(self):
        return DirectionCosines(map(abs, self))

    def __int__(self):
        # vector length
        return int(float(self))

    def __float__(self):
        # vector length
        return sqrt(sum(comp**2 for comp in self))

    def cross_product(self, other):
        '''Calculate the vector cross product (self x other).'''
        s_i, s_j, s_k = self
        o_i, o_j, o_k = other
        cross_prod = s_j*o_k - s_k*o_j, s_k*o_i - s_i*o_k, s_i*o_j - s_j*o_i
        return DirectionCosines(cross_prod)


class Rotation:
    '''The plane spanned by one line rotated around an axis.'''

    __slots__ = 'rot_axis', 'base_line'
    FIELDS = __slots__

    def __init__(self, rot_axis, base_line):
        self.rot_axis = rot_axis
        self.base_line = base_line

    def constituent_lines(self, samples=100):
        '''Rotate the base line around the axis incrementally.'''
        for angle in (i * pi / samples for i in range(samples + 1)):
            yield self.base_line.rotate_around(self.rot_axis, angle)

    def __str__(self):
        return '{!s} around {!s}'.format(self.base_line, self.rot_axis)

    def __hash__(self):
        return hash((self.rot_axis, self.base_line))


class Plane(Rotation):
    '''Represents a plane on a stereonet.'''

    __slots__ = 'strike', 'dip'
    FIELDS = __slots__

    def __init__(self, strike, dip):
        self.strike, self.dip = strike, dip
        super().__init__(self.pole(), Line(0, self.strike))

    @classmethod
    def from_direction_cosines(cls, cosines):
        '''Create a plane from the given direction cosines of its pole.'''
        return cls.from_pole(Line.from_direction_cosines(cosines))

    @classmethod
    def from_pole(cls, pole):
        '''Create a plane perpendicular to the given line.'''
        return cls(strike=pole.trend + pi/2, dip=pi/2 - pole.dip)

    @classmethod
    def from_spanning_lines(cls, line1, line2):
        '''Create the plane that is spanned by two non-parallel lines.'''
        dircos1, dircos2 = line1.direction_cosines(), line2.direction_cosines()
        return cls.from_direction_cosines(dircos1.cross_product(dircos2))

    def direction_cosines(self):
        '''Returns north, east, down direction cosines of the plane's pole.'''
        return DirectionCosines((sin(self.dip) * sin(self.strike),
                                 -sin(self.dip) * cos(self.strike),
                                 cos(self.dip)))

    def pole(self):
        '''Get the pole (normal vector) to the plane as a Line.'''
        return Line(trend=self.strike - pi/2, plunge=pi/2 - self.dip)

    def __str__(self):
        return '{:03d}/{:02d}' \
            .format(*map(to_int_degrees, (self.strike, self.dip)))

    def __hash__(self):
        return hash((self.strike, self.dip))


class Line:
    '''Represents a line on a stereonet.'''

    __slots__ = 'plunge', 'trend'
    FIELDS = __slots__

    def __init__(self, plunge, trend):
        self.plunge, self.trend = plunge, trend

    @classmethod
    def from_direction_cosines(cls, cosines):
        '''Create a line from the given north, east, down direction cosines.'''
        north, east, down = cosines
        trend = pi / 2 if east >= 0 else 3 * pi / 2
        if north != 0:
            trend = atan(east / north)
            if north < 0:
                trend += pi
        return cls(trend=trend % (2*pi), plunge=asin(down))

    def direction_cosines(self):
        '''Returns north, east, down direction cosines of the line.'''
        return DirectionCosines((cos(self.plunge) * cos(self.trend),
                                 cos(self.plunge) * sin(self.trend),
                                 sin(self.plunge)))

    def rotate_around(self, axis, lat):
        '''Returns the line rotated around the given axis by the given lat.'''
        north, east, down = axis.direction_cosines()
        rotcos, rotsin = cos(lat), sin(lat)
        multiplier = 1 - rotcos
        transform = [[
            rotcos + north**2*multiplier,
            -down*rotsin + north*east*multiplier,
            east*rotsin + north*down*multiplier,
        ], [
            down*rotsin + east*north*multiplier,
            rotcos + east**2*multiplier,
            -north*rotsin + east*down*multiplier,
        ], [
            -east*rotsin + down*north*multiplier,
            north*rotsin + down*east*multiplier,
            rotcos + down**2*multiplier,
        ]]

        unrot_cosines = self.direction_cosines()
        rot_cosines = [sum(trans_row[j] * unrot
                           for j, unrot in enumerate(unrot_cosines))
                       for trans_row in transform]
        if rot_cosines[2] < 0:
            rot_cosines = tuple(map(op.neg, rot_cosines))
        return Line.from_direction_cosines(rot_cosines)

    def __str__(self):
        return '{:02d}/{:03d}' \
            .format(*map(to_int_degrees, (self.plunge, self.trend)))

    def __hash__(self):
        return hash((self.plunge, self.trend))
