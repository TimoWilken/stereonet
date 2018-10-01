#!/usr/bin/env python3

'''Stereonet projections of planes and lines.'''

import abc
import itertools as it
import tkinter as tk
from math import sqrt, pi, sin, cos, tan

from transformation import Plane, Line, Rotation


def updated_dict(original, new_values):
    '''Copy and update the original dict with new_values.

    This does no copying and returns the original dict if new_values is empty,
    saving space and time.
    '''
    if new_values:
        updated = original.copy()
        updated.update(new_values)
        return updated
    return original


# pylint: disable=too-many-ancestors
class Stereonet(tk.Canvas, metaclass=abc.ABCMeta):
    '''Represents an abstract stereonet, including drawing code.

    Coordinate transformations must be implemented in subclasses.
    '''

    def __init__(self, master, line_options=None, plane_options=None, *,
                 size=750, background='white'):
        super().__init__(master, bg=background, height=size, width=size)
        self._size = size
        self._netobjs, self._callbacks = {}, {}

        self._line_options = {
            'width': 1,  # outline thickness
            'fill': 'green',
            'outline': 'darkgreen',
            'activefill': 'red',
            'activeoutline': 'darkred',
        }
        if line_options:
            self._line_options.update(line_options)
        self._plane_options = {
            'width': 2,
            'fill': 'blue',
            'activefill': 'red',
            'activewidth': 3,
            'disabledwidth': 1,
            'disabledfill': 'gray',
        }
        if plane_options:
            self._plane_options.update(plane_options)

        self.bind('<Configure>', self._resize_all)

    @property
    def point_radius(self):
        '''Radius of "points" (that represent Lines) on the stereonet.'''
        return self.size // 200

    @property
    def size(self):
        '''Current width and height (one number as the widget is square).'''
        return self._size
    @size.setter
    def size(self, value):
        if self._size != value:
            # <Configure> handler (_resize_all) will set self._size.
            self.configure(width=value, height=value)

    def _resize_all(self, event):
        old_size, new_size = self._size, min(event.width, event.height)
        for widget in self._netobjs.values():
            self.coords(widget, tuple(c * new_size / old_size
                                      for c in self.coords(widget)))
        self._size = new_size

    def bind_netobject(self, event_code, command):
        '''Register a callback for the specified event code on each net object.

        A net object is a Plane or Line. This will bind to events of existing
        and future net objects.

        The callback will be called as command(event, netobj), with netobj being
        the net object (Plane or Line) that triggered the event.
        '''
        if event_code not in self._callbacks:
            self._bind_all_netobjs(event_code)
        self._callbacks.setdefault(event_code, []).append(command)

    def _bind_all_events(self, netobj, widget):
        for event_code in self._callbacks:
            self._bind_handler(event_code, netobj, widget)

    def _bind_all_netobjs(self, event_code):
        for netobj, widget in self._netobjs.items():
            self._bind_handler(event_code, netobj, widget)

    def _bind_handler(self, event_code, netobj, widget):
        def handler(event):
            for callback in self._callbacks.get(event_code, ()):
                callback(event, netobj)
        self.tag_bind(widget, event_code, handler)

    def _to_screen_coords(self, math_x, math_y):
        '''Convert mathematical coordinates to screen coordinates.'''
        # Mathematical y increases upwards, screen y increases downwards.
        math_y = -math_y
        return (math_x + 1) * self._size / 2, (math_y + 1) * self._size / 2

    def plot(self, netobj, **override_options):
        '''Plot an arbitrary net object.'''
        if isinstance(netobj, Line):
            self.plot_line(netobj, **override_options)
        elif isinstance(netobj, Rotation):
            self.plot_rotation(netobj, **override_options)
        else:
            raise TypeError(type(netobj))

    def plot_line(self, line, **override_line_options):
        '''Plot a line (represented as a point) on the stereonet.'''
        # pylint: disable=invalid-name
        x, y = self._to_screen_coords(*self.line_coordinates(line))
        point_r = self.point_radius
        # Top & left bounds are inclusive, bottom & right bounds are exclusive.
        coords = x - point_r, y - point_r, x + point_r + 1, y + point_r + 1
        line_options = updated_dict(self._line_options, override_line_options)
        self._netobjs[line] = self.create_oval(*coords, **line_options)
        self._bind_all_events(line, self._netobjs[line])

    def plot_rotation(self, rotation, samples=100, **override_plane_options):
        '''Plot the rotation of a line about an axis by 180 degrees.'''
        coords = it.chain(*(self._to_screen_coords(*self.line_coordinates(line))
                            for line in rotation.constituent_lines(samples)))
        plane_opts = updated_dict(self._plane_options, override_plane_options)
        self._netobjs[rotation] = self.create_line(*coords, **plane_opts)
        self._bind_all_events(rotation, self._netobjs[rotation])

    def plot_latitude_guide(self, latitude):
        '''Show a small circle at the specified -pi/2 <= latitude <= pi/2.'''
        assert -pi/2 <= latitude <= pi/2, latitude
        small_circle = Rotation(Line(0, 0), Line(0, pi/2 - latitude))
        self.plot_rotation(small_circle, state=tk.DISABLED)

    def plot_dip_guide(self, dip, left_hemisphere=False):
        '''Show a great circle at the specified 0 <= dip <= pi/2.

        Pass left_hemisphere=True to plot the guide with strike pi so that it
        appears to dip left, else it'll dip to the right.
        '''
        assert 0 <= dip <= pi/2, dip
        strike = pi if left_hemisphere else 0
        great_circle = Rotation(Plane(strike, dip).pole(), Line(0, strike))
        self.plot_rotation(great_circle, state=tk.DISABLED)

    def remove_net_object(self, netobj):
        '''Destroy the specified net object, removing it from the plot.

        If the object is not plotted, do nothing.
        '''
        try:
            netobj = self._netobjs[netobj]
        except KeyError:
            # Net object not plotted.
            pass
        else:
            self.delete(netobj)

    @classmethod
    @abc.abstractmethod
    def line_coordinates(cls, line):
        '''Calculate where a point representing a line should be placed.

        This works in mathematical space -- x increases right, y increases up;
        the centre of the stereonet is (0, 0).
        '''
        raise NotImplementedError


class EqualAngle(Stereonet):  # pylint: disable=too-many-ancestors
    '''Equal angle stereonet -- preserves angles, but not areas.'''

    @classmethod
    def line_coordinates(cls, line):
        return (tan(pi/4 - line.plunge/2) * sin(line.trend),
                tan(pi/4 - line.plunge/2) * cos(line.trend))


class EqualArea(Stereonet):  # pylint: disable=too-many-ancestors
    '''Equal area stereonet -- preserves areas, but not angles.'''

    @classmethod
    def line_coordinates(cls, line):
        return (sqrt(2) * sin(pi/4 - line.plunge/2) * sin(line.trend),
                sqrt(2) * sin(pi/4 - line.plunge/2) * cos(line.trend))
