'''Grouping of structural data for display.'''

from collections import defaultdict
from tkinter import StringVar, BooleanVar


class DataGroup:
    '''A group of data of the same type.'''

    def __init__(self, name, data_type=None, enabled=True, **style):
        self._data = []
        self._data_type = data_type
        self._callbacks = defaultdict(list)
        self.style = style
        self.name = StringVar(None, name)
        self.enabled = BooleanVar(None, enabled)
        def update_hidden_status(*_):
            for callback in self._callbacks['change_group_enabled']:
                callback(self)
        self.enabled.trace('w', update_hidden_status)

    @property
    def data_type(self):
        '''The type of structural data stored in this group.'''
        return self._data_type

    @data_type.setter
    def data_type(self, value):
        if not self._data:
            self._data_type = value
            for callback in self._callbacks['change_data_type']:
                callback(self)
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

    def delete(self):
        '''Delete the entire group.'''
        self.enabled.set(False)
        for callback in self._callbacks['remove_group']:
            callback(self)

    def net_objects(self):
        '''Return structural data held in the group.'''
        return self._data.copy()

    def bind(self, **callbacks):
        '''Register a function to be called when an event is raised.

        Available events are change_group_enabled, add_item, remove_item,
        remove_group.
        '''
        for key, callback in callbacks.items():
            self._callbacks[key].append(callback)

    def unbind(self, **callbacks):
        '''Unregister a previously registered function for specified events.'''
        for key, callback in callbacks.items():
            try:
                self._callbacks[key].remove(callback)
            except ValueError:
                # callback was not in list to begin with
                pass
