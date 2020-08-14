#!/usr/bin/env python3

'''Unit tests for Stereonet.

These mostly test behind-the-scenes maths, to make sure I don't typo or break
complicated formulae.
'''

import unittest
import random
from math import pi

from transformation import DirectionCosines, Plane, Line


def generate_random_dircoses():
    '''Create DirectionCosines with random components.'''
    return [DirectionCosines((random.random(),
                              random.random(),
                              random.random())) for _ in range(100)]


# pylint: disable=invalid-name    # This is to blend in with unittest's names.
def assertAlmostEqualDircos(testcase, dc1, dc2):
    '''Assert that dc1 and dc2 are almost equal after normalisation.'''
    # Get direction cosines if necessary. We might have been given a Line or a
    # Plane. DirectionCosines define .direction_cosines() for compatibility.
    dc1 = dc1.direction_cosines().normalised()
    dc2 = dc2.direction_cosines().normalised()

    testcase.assertAlmostEqual(dc1.north, dc2.north)
    testcase.assertAlmostEqual(dc1.east, dc2.east)
    testcase.assertAlmostEqual(dc1.down, dc2.down)


class TestDirectionCosines(unittest.TestCase):
    '''Test transformation.DirectionCosines.'''

    def setUp(self):
        # Pregenerate random DirectionCosines to save time on individual tests.
        self.random_dircoses = generate_random_dircoses()

    def test_simple_dot_product(self):
        '''Make sure that (1,0,0) . dircos == dircos.north, etc.'''
        x = DirectionCosines((1, 0, 0))
        y = DirectionCosines((0, 1, 0))
        z = DirectionCosines((0, 0, 1))
        for dircos in self.random_dircoses:
            with self.subTest(dircos=dircos):
                self.assertEqual(dircos.dot_product(x), dircos.north)
                self.assertEqual(dircos.dot_product(y), dircos.east)
                self.assertEqual(dircos.dot_product(z), dircos.down)

    def test_normalisation(self):
        '''Make some random direction cosines to test normalisation.'''
        for dircos in self.random_dircoses:
            with self.subTest(dircos=dircos):
                self.assertAlmostEqual(float(dircos.normalised()), 1.0)

    def test_multiplicative_identities(self):
        '''Test multiplication and division by one.'''
        for dircos in self.random_dircoses:
            for one in 1, 1.0, 1+0j:
                with self.subTest(dircos=dircos, one=one):
                    self.assertEqual(dircos * one, dircos)
                    self.assertEqual(one * dircos, dircos)
                    self.assertEqual(dircos / one, dircos)


class TestPlane(unittest.TestCase):
    '''Test transformation.Plane.'''

    def setUp(self):
        # Pregenerate random DirectionCosines to save time on individual tests.
        self.random_dircoses = generate_random_dircoses()

    def test_pole(self):
        '''Test that the pole of a plane is that from which it was created.'''
        dircos2plane = Plane.from_direction_cosines
        for dircos in self.random_dircoses:
            with self.subTest(dircos=dircos):
                assertAlmostEqualDircos(self, dircos, dircos2plane(dircos))

    def test_spanning_parallel(self):
        '''Test that a Plane can't be created from parallel Lines.'''
        for dircos in self.random_dircoses:
            with self.subTest(dircos=dircos):
                self.assertRaises(AssertionError,
                                  Plane.from_spanning_direction_cosines,
                                  dircos, dircos)


class TestLine(unittest.TestCase):
    '''Test transformation.Line.'''

    def setUp(self):
        # Pregenerate random DirectionCosines to save time on individual tests.
        self.random_dircoses = generate_random_dircoses()

    def test_dircos(self):
        '''Test that a Line keeps the direction cosines it was created from.'''
        dircos2line = Line.from_direction_cosines
        for dircos in self.random_dircoses:
            with self.subTest(dircos=dircos):
                assertAlmostEqualDircos(self, dircos, dircos2line(dircos))

    def test_rotation_around_self(self):
        '''Test that a line rotated around itself does not change.'''
        for dircos in self.random_dircoses:
            line = Line.from_direction_cosines(dircos)
            for angle in (random.uniform(-2*pi, 2*pi) for _ in range(100)):
                with self.subTest(dircos=dircos, lat=angle):
                    assertAlmostEqualDircos(self, line,
                                            line.rotate_around(line, angle))

    def test_rotation_correct_hemisphere(self):
        '''Test that rotated Lines always end up in the right hemisphere.'''
        # This is a pathological case that's handled specially.
        axis = Line(pi/4, 3*pi/2)
        assertAlmostEqualDircos(self, Line(0, pi),
                                Line(0, 0).rotate_around(axis, pi))

    def test_creation(self):
        '''Test creation from DirectionCosines.'''
        assertAlmostEqualDircos(
            self, Line(0, 0),
            Line.from_direction_cosines(DirectionCosines((1, 0, 0))))
        assertAlmostEqualDircos(
            self, Line(pi / 2, 0),
            Line.from_direction_cosines(DirectionCosines((0, 0, 1))))
        assertAlmostEqualDircos(
            self, Line(0, pi / 2),
            Line.from_direction_cosines(DirectionCosines((0, 1, 0))))
        assertAlmostEqualDircos(
            self, Line(pi / 2, pi / 2),
            Line.from_direction_cosines(DirectionCosines((0, 0, 1))))
        assertAlmostEqualDircos(
            self, Line(pi / 4, 0),
            Line.from_direction_cosines(DirectionCosines((1, 0, 1))))
        assertAlmostEqualDircos(
            self, Line(0, pi / 4),
            Line.from_direction_cosines(DirectionCosines((1, 1, 0))))


if __name__ == '__main__':
    unittest.main()
