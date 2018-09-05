#!/usr/bin/env python3

'''Grouping of structural data for display.'''

from collections import defaultdict
from tkinter import StringVar, BooleanVar


class DataGroup:
    '''A group of data of the same type.'''

    def __init__(self, name, data_type=None, enabled=True, **style):
        self._data = []
        self._data_type = data_type
        self.name = StringVar(None, name)
        self.enabled = BooleanVar(None, enabled)
        def update_hidden_status(*_):
            if self.enabled.get():
                self.show_group()
            else:
                self.hide_group()
        self.enabled.trace('w', update_hidden_status)
        self.style = style
        self._callbacks = defaultdict(list)

    @property
    def data_type(self):
        '''The type of structural data stored in this group.'''
        return self._data_type
    @data_type.setter
    def data_type(self, value):
        if not self._data:
            self._data_type = value
        elif self._data_type != value:
            raise ValueError('cannot change data_type if the group holds data')

    def add_net_object(self, netobj):
        '''Append the specified structural datum to the group.'''
        if not self._data and not self._data_type:
            self._data_type = type(netobj)
        elif self._data and not isinstance(netobj, self._data_type):
            raise TypeError('expected a {}, but got a {}'.format(
                self._data_type.__name__, type(netobj).__name__))
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
