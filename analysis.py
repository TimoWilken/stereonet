#!/usr/bin/env python3

'''Analysis functions for geological structural data.'''

from math import pi, radians

from transformation import Line, Plane
from grouping import DataGroup


def average(iterable):
    '''Calculate the average of an arbitrarily long iterable in O(1) space.'''
    iterable = iter(iterable)
    iter_sum = next(iterable)
    iter_length = 1
    for i in iterable:
        iter_length += 1
        iter_sum += i
    return iter_sum / iter_length


def sum_iterable(iterable):
    '''Sum an iterable.'''
    iterable = iter(iterable)
    value = next(iterable)
    for i in iterable:
        value += i
    return value


def planes_to_poles(planes):
    '''Convert a DataGroup of Planes to poles of Planes.'''
    out_group = DataGroup(planes.name.get() + ' (poles)', Line,
                          enabled=planes.enabled.get())
    for plane in planes.net_objects():
        out_group.add_net_object(plane.pole())
    return out_group


def poles_to_planes(poles):
    '''Convert a DataGroup of poles of Planes to Planes.'''
    out_group = DataGroup(poles.name.get() + ' (planes)', Plane,
                          enabled=poles.enabled.get())
    for pole in poles.net_objects():
        out_group.add_net_object(Plane.from_pole(pole))
    return out_group


class Fold:
    '''A best fit of planes describing a fold from data from both limbs.'''

    def __init__(self, planes_or_poles, top_limb_proportion=.5):
        '''Initialise the Fold instance with collected data.

        planes_or_poles should be a (possibly mixed) list of Planes and Lines.
        Lines are assumed to be poles to bedding; Planes are assumed to be
        bedding and their pole will be used in calculations.

        top_limb_proportion is taken to be the proportion of data collected on
        the limb that is a bearing of the profile plane's strike from the fold
        axis. For instance, if the profile plane is 090/80, the east limb would
        be the top limb.
        '''
        self.top_limb_proportion = top_limb_proportion
        self.poles = [item.pole() if hasattr(item, 'pole') else item
                      for i, item in enumerate(planes_or_poles)]

    def profile_plane_strike(self):
        '''Compute the strike of the best-fit profile plane.'''
        poles_dir_cos = [p.direction_cosines() for p in self.poles]
        poles_dir_cos.sort(key=lambda c: c.down, reverse=True)
        avg_pole = Line.from_direction_cosines(sum_iterable(poles_dir_cos))
        seen, differences = [], []
        for pole in poles_dir_cos:
            seen.append(pole)
            differences.extend(p - pole for p in poles_dir_cos if p not in seen)
        positive_diff_dir = Line(0, avg_pole.trend - pi/2).direction_cosines()
        return Line.from_direction_cosines(sum_iterable(
            diff if positive_diff_dir.dot_product(diff) >= 0 else -diff
            for diff in differences)).trend

    def profile_plane_dip(self, strike=None, increment=radians(.1)):
        '''Compute the dip of the best-fit profile plane, given a strike.

        If no strike is given, calls self.profile_plane_strike().
        '''
        if strike is None:
            strike = self.profile_plane_strike()

        def is_left_of_plane(axis, dip):
            return lambda pole: pole.rotate_around(axis, dip) \
                                    .direction_cosines().east < 0

        half_points = int(round(len(self.poles) / 2))
        possible_dips = []
        axis, dip = Line(0, strike), -pi/2
        while dip <= pi/2:
            below_best_fit = filter(is_left_of_plane(axis, dip), self.poles)
            if sum(1 for _ in below_best_fit) == half_points:
                possible_dips.append(dip)
            dip += increment

        if possible_dips:
            return average(possible_dips)
        raise ValueError('no profile plane found')

    def profile_plane(self, dip_increment=radians(.1)):
        '''Generate a best-fit plane through the collected poles to bedding.'''
        strike = self.profile_plane_strike()
        dip = self.profile_plane_dip(strike, dip_increment)
        return Plane(strike, dip)

    def axial_plane(self, profile_plane=None):
        '''Generate a best-fit axial plane.'''
        if not profile_plane:
            profile_plane = self.profile_plane()
        # Rotate poles so they are in a cluster elongate north to south.
        ns_dircos = [pole.rotate_around(Line(pi/2, 0), -profile_plane.strike)
                     .direction_cosines() for pole in self.poles]
        # reverse=True sorts poles north to south.
        ns_dircos.sort(key=lambda c: c.north, reverse=True)
        cutoff = int(round(self.top_limb_proportion * len(self.poles)))
        avg_midpoint = average(ns_dircos[cutoff-1:cutoff+2])
        avg_midpoint = Line.from_direction_cosines(avg_midpoint)
        return Plane.from_spanning_lines(avg_midpoint, profile_plane.pole())
