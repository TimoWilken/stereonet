#!/usr/bin/env python3

'''Analysis functions for geological structural data.'''

from transformation import DirectionCosines, Line, Plane


def average(iterable):
    '''Calculate the average of an arbitrarily long iterable in O(1) space.'''
    iter_sum = iter_length = 0
    for i in iterable:
        iter_length += 1
        iter_sum += i
    return iter_sum / iter_length


class Fold:
    '''A best fit of planes describing fold from data from both limbs.'''

    def __init__(self, planes_or_poles, left_limb_proportion=.5):
        self.left_limb_proportion = left_limb_proportion
        self.poles = [item.pole() if hasattr(item, 'pole') else item
                      for i, item in enumerate(planes_or_poles)]

    def profile_plane(self):
        '''Generate a best-fit plane through the collected poles to bedding.'''
        poles_dir_cos = [p.direction_cosines() for p in self.poles]
        seen = []
        _avg_vector = DirectionCosines((0, 0, 0))
        for pole in poles_dir_cos:
            seen.append(pole)
            for other_pole in poles_dir_cos:
                if other_pole not in seen:
                    _avg_vector += other_pole - pole
        _avg_vector /= float(_avg_vector)
        return Plane(strike=Line.from_direction_cosines(_avg_vector).trend,
                     dip=average(p.plunge for p in self.poles))

    def axial_plane(self):
        '''Generate a best-fit axial plane.'''
        profile_plane = self.profile_plane()
