#!/usr/bin/env python3

'''Grouping of structural data for display.'''

from collections import defaultdict
from tkinter import StringVar, BooleanVar


class DataGroup:
    '''A group of data of the same type.'''

    def __init__(self, name, enabled=True, **style):
        self._data = []
        self.name = StringVar(None, name)
        self.enabled = BooleanVar(None, enabled)
        self.style = style
        self._callbacks = defaultdict(list)

    def add_net_object(self, netobj):
        '''Append the specified structural datum to the group.'''
        if self._data and not isinstance(netobj, type(self._data[0])):
            raise TypeError('all data in a group must be of the same type')
        self._data.append(netobj)
        for callback in self._callbacks['add_item']:
            callback(self, netobj)

    def remove_net_object(self, netobj):
        '''Remove the specified structural datum from the group.'''
        self._data.remove(netobj)
        for callback in self._callbacks['remove_item']:
            callback(self, netobj)

    def net_objects(self):
        '''Return structural data held in the group.'''
        return self._data.copy()

    def hide_group(self):
        '''Call callbacks registered for hiding the group.'''
        for callback in self._callbacks['hide_group']:
            callback(self)

    def show_group(self):
        '''Call callbacks registered for showing the group.'''
        for callback in self._callbacks['show_group']:
            callback(self)

    def register_hide_group(self, callback):
        '''Register a function to be called when the group is hidden.'''
        self._callbacks['hide_group'].append(callback)

    def register_show_group(self, callback):
        '''Register a function to be called when the group is unhidden.'''
        self._callbacks['show_group'].append(callback)

    def register_remove_item(self, callback):
        '''Register a function to be called when an item is removed.'''
        self._callbacks['remove_item'].append(callback)

    def register_add_item(self, callback):
        '''Register a function to be called when an item is added.'''
        self._callbacks['add_item'].append(callback)
