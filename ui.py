'''Extra user interface widgets for plotting stereonets.'''

import functools as ft
import operator as op
import tkinter as tk
from tkinter import ttk
from math import radians, degrees

from grouping import DataGroup
from transformation import Plane, Line


def chain(*functions, start=None):
    '''Chain functions left-to-right.'''
    def chained(start):
        return ft.reduce(lambda acc, f: f(acc), functions, start)
    return chained if start is None else chained(start)


# pylint: disable=invalid-name
var_to_radians = chain(op.methodcaller('get'), float, radians)


class ScrollableFrame(ttk.Frame):  # pylint: disable=too-many-ancestors
    '''Tk Frame that is scrollable (by nesting it inside a Canvas).'''

    def __init__(self, master, grid, **kwargs):
        wrapper = ttk.Frame(master)
        wrapper.rowconfigure(0, weight=1)
        wrapper.columnconfigure(0, weight=1)
        wrapper.columnconfigure(1, weight=0)
        wrapper.grid(**grid)

        style_bg = ttk.Style().lookup('TFrame', 'background')
        canvas = tk.Canvas(wrapper, borderwidth=0, highlightthickness=0,
                           background=style_bg)
        canvas.grid(row=0, column=0, sticky=tk.NSEW)

        scrollbar = ttk.Scrollbar(wrapper, orient=tk.VERTICAL,
                                  command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NSEW)
        canvas.configure(yscrollcommand=scrollbar.set)

        super().__init__(canvas, **kwargs)
        frame_id = canvas.create_window(0, 0, window=self, anchor=tk.NW)

        def configure_scrolled_frame(event):
            canvas.config(scrollregion=(0, 0, event.width, event.height))
            if canvas.winfo_width() != event.width:
                canvas.configure(width=event.width)

        def configure_canvas(event):
            if self.winfo_reqwidth() != event.width:
                event.widget.itemconfigure(frame_id, width=event.width)

        self.bind('<Configure>', configure_scrolled_frame)
        canvas.bind('<Configure>', configure_canvas)


class StyleEditor(tk.Frame):  # pylint: disable=too-many-ancestors
    '''A window for editing the style of groups.'''

    def __init__(self, master):
        super().__init__(
            master, background=ttk.Style().lookup('TFrame', 'background'))
        self.group = None

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        layout = {'sticky': tk.NSEW, 'padx': 5, 'pady': 3}

        ttk.Button(self, text='Apply', underline=0, command=self.save) \
           .grid(row=1, column=1, **layout)

        base = ttk.Frame(self)
        base.grid(row=0, column=0, columnspan=3, sticky=tk.NSEW)
        base.columnconfigure(1, weight=1)

        self._color = tk.StringVar(self)
        self._thickness = tk.IntVar(self)

        ttk.Label(base, text='Colour') \
           .grid(row=0, column=0, **layout)
        ttk.Entry(base, textvariable=self._color) \
           .grid(row=0, column=1, **layout)
        ttk.Label(base, text='Thickness') \
           .grid(row=1, column=0, **layout)
        ttk.Scale(base, from_=1, to=10, variable=self._thickness,
                  orient=tk.HORIZONTAL) \
           .grid(row=1, column=1, **layout)

        self.set_group(None)

    def set_group(self, group):
        '''Allow editing the given group's style, replacing previous groups.'''
        self.group = group
        if group is not None:
            self._color.set(group.style.get('fill', 'blue'))
            self._thickness.set(group.style.get('width', 2))
            group.bind(remove_group=lambda group: self.set_group(None))
        else:
            self._color.set('')
            self._thickness.set(0)

    def save(self, *_):
        '''Modify the group with changes made in this dialog.'''
        self.group.style['fill'] = self._color.get()
        self.group.style['width'] = self._thickness.get()
        if self.group.enabled.get():
            # TODO: Not the most elegant way of doing this.
            self.group.enabled.set(False)
            self.group.enabled.set(True)


class GroupListItem(ttk.Frame):  # pylint: disable=too-many-ancestors
    '''A widget for editing and selecting a group out of a list.'''

    def __init__(self, master, group, sel_variable):
        super().__init__(master)
        self.columnconfigure(2, weight=1)
        ttk.Radiobutton(self, value=id(group), variable=sel_variable) \
           .grid(row=0, column=0, sticky=tk.NSEW)
        ttk.Checkbutton(self, variable=group.enabled) \
           .grid(row=0, column=1, sticky=tk.NSEW)
        ttk.Entry(self, textvariable=group.name) \
           .grid(row=0, column=2, sticky=tk.NSEW)
        ttk.Button(self, text='Delete', width=6, command=group.delete) \
           .grid(row=0, column=99, sticky=tk.NSEW)


class DataDisplay(ttk.Treeview):  # pylint: disable=too-many-ancestors
    '''A widget for displaying structural data from a single group.'''

    def __init__(self, master):
        self._group = None
        self._netobj_treeitems = {}
        data_tree_columns = 0, 1
        super().__init__(master, columns=data_tree_columns)
        self.heading('#0', text='#')
        self.column('#0', width=50, stretch=False)
        for col in data_tree_columns:
            self.column(col, width=75, stretch=True, anchor=tk.CENTER)

    def display_data(self, group):
        '''Display the data contained in the given group.'''
        bindings = {
            'add_item': self._add_group_item,
            'remove_item': self._remove_group_item,
            'change_data_type': self._change_group_type,
        }
        if self._group:
            self._group.unbind(**bindings)
            self._netobj_treeitems.clear()
            self.selection_set()
            self.set_children('')
        self._group = group
        self._change_group_type(self._group)
        if group:
            self._group.bind(**bindings)
            for item in self._group.net_objects():
                self._add_group_item(self._group, item)

    def _add_group_item(self, group, netobj):
        item_values = tuple(int(round(degrees(getattr(netobj, field))))
                            for field in group.data_type.FIELDS)
        item_num = len(self.get_children()) + 1
        tree_item = self.insert('', tk.END, text=item_num, values=item_values)
        self.see(tree_item)
        self._netobj_treeitems[netobj] = tree_item

    def _remove_group_item(self, _, netobj):
        self.delete(self._netobj_treeitems[netobj])
        del self._netobj_treeitems[netobj]
        for i, tree_item in enumerate(self.get_children()):
            self.item(tree_item, text=i)

    def _change_group_type(self, group):
        if group and group.data_type:
            for i, field in enumerate(group.data_type.FIELDS):
                self.heading(i, text=field.title())
        else:
            for i in range(2):
                self.heading(i, text='?')


class DataEntry(ttk.Frame):  # pylint: disable=too-many-ancestors
    '''A widget for entering structural data.'''

    def __init__(self, master, data_type=None, status_var=None):
        super().__init__(master)
        self._data_type = None
        self.data_type = data_type

        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)

        self._field_name_vars = tk.StringVar(self), tk.StringVar(self)
        field_vars = tk.StringVar(self), tk.StringVar(self)

        ttk.Label(self, text='/') \
           .grid(row=0, column=2, sticky=tk.NSEW)
        ttk.Label(self, textvariable=self._field_name_vars[0]) \
           .grid(row=0, column=0, sticky=tk.NSEW)
        ttk.Label(self, textvariable=self._field_name_vars[1]) \
           .grid(row=0, column=4, sticky=tk.NSEW)

        field1_entry = ttk.Entry(self, textvariable=field_vars[0])
        field1_entry.grid(row=0, column=1, sticky=tk.NSEW)
        field2_entry = ttk.Entry(self, textvariable=field_vars[1])
        field2_entry.grid(row=0, column=3, sticky=tk.NSEW)

        def on_submit_input(_):
            try:
                fields = map(var_to_radians, field_vars)
            except ValueError as err:
                if status_var:
                    status_var.set(f'Error adding data point: {err}')
                return
            if not self.data_type:
                if status_var:
                    status_var.set('Cannot add data point: unknown data type'
                                   ' (have you selected a group?)')
                return
            # pylint: disable=not-callable
            new_netobj = self.data_type(*fields)
            counter = max(self._submitted_netobjs.keys(), default=-1) + 1
            self._submitted_netobjs[counter] = new_netobj
            self.event_generate('<<Netobject-Submit>>', x=counter)
            for var in field_vars:
                var.set('')
            field1_entry.focus()

        for entry in field1_entry, field2_entry:
            entry.bind('<Return>', on_submit_input)

        self._submitted_netobjs = {}

    @property
    def data_type(self):
        '''The type of data to be created from data submitted by the user.

        User input is taken as two numbers, which will be converted from
        degrees to radians and fed as positional arguments, in order from left
        to right, to the type's constructor. The result is assigned to the
        'netobj' member of a <<Netobject-Submit>> event generated.
        '''
        return self._data_type

    @data_type.setter
    def data_type(self, value):
        if value != self._data_type:
            self._data_type = value
            for i, var in enumerate(self._field_name_vars):
                try:
                    var.set(value.FIELDS[i][0].upper())
                except (KeyError, AttributeError):
                    var.set('?')

    def pop_net_object(self, event):
        '''Get the user-submitted net object associated with an event.'''
        # Tkinter does not support the data/user_data attribute of events.
        return self._submitted_netobjs.pop(event.x)


class StereonetInput(ttk.PanedWindow):  # pylint: disable=too-many-ancestors
    '''A widget for inputting structural data for display on a stereonet.'''

    def __init__(self, master, status_var=None, on_selection_change=None):
        super().__init__(master, orient=tk.VERTICAL)
        self._cur_new_group_counter = 1
        self._group_widgets = {}
        self._select_group_callback = \
            on_selection_change if callable(on_selection_change) \
            else lambda _: None

        groups_frm = ttk.LabelFrame(self, text='Groups')
        self.add(groups_frm, weight=1)
        groups_frm.rowconfigure(0, weight=1)
        groups_frm.columnconfigure(0, weight=1)

        self._groups_scroll = ScrollableFrame(
            groups_frm, grid={'row': 0, 'column': 0, 'sticky': tk.NSEW})
        self._groups_scroll.columnconfigure(0, weight=1)

        self._style_editor = StyleEditor(groups_frm)
        self._style_editor.grid(row=1, column=0, sticky=tk.NSEW)

        data_frm = ttk.LabelFrame(self, text='Data')
        self.add(data_frm, weight=3)
        data_frm.rowconfigure(1, weight=1)
        data_frm.columnconfigure(0, weight=1)

        self._group_type_var = tk.StringVar(self)
        possible_types = Line, Plane
        def update_group_type(*_):
            group = self.currently_selected_group()
            if not group:
                # No group is selected.
                if status_var:
                    status_var.set('Select a group using the radio buttons'
                                   ' before adding data.')
                return

            for type_ in possible_types:
                if self._group_type_var.get() == type_.__name__:
                    try:
                        group.data_type = type_
                    except ValueError:
                        self._group_type_var.set(group.data_type.__name__)
        self._group_type_var.trace('w', update_group_type)
        group_type = ttk.OptionMenu(data_frm, self._group_type_var, '',
                                    *(t.__name__ for t in possible_types))
        group_type.grid(row=0, column=0, sticky=tk.NSEW)

        self._data_display = DataDisplay(data_frm)
        self._data_display.grid(row=1, column=0, sticky=tk.NSEW)

        data_entry = DataEntry(data_frm, status_var=status_var)
        data_entry.grid(row=2, column=0, sticky=tk.NSEW)
        data_entry.bind('<<Netobject-Submit>>',
                        lambda event: self.currently_selected_group()
                        .add_net_object(event.widget.pop_net_object(event)))
        def update_data_entry_type(*_):
            data_entry.data_type = self.currently_selected_group().data_type \
                                   if self.currently_selected_group() else None
        self._group_type_var.trace('w', update_data_entry_type)

        self._groups_sel_var = tk.IntVar(self)
        self._groups_sel_var.trace('w', lambda *_: self.select_group())

    def add_group(self, group=None):
        '''Add a widget for the given group, creating one if none is given.'''
        NEW_GROUP_PREFIX = 'New group #'
        if not group:
            new_group_name = NEW_GROUP_PREFIX + str(self._cur_new_group_counter)
            self._cur_new_group_counter += 1
            group = DataGroup(new_group_name)
        else:
            new_group_name = group.name.get()
            if new_group_name.startswith(NEW_GROUP_PREFIX):
                try:
                    group_num = int(new_group_name[len(NEW_GROUP_PREFIX):])
                except (KeyError, ValueError):
                    pass
                else:
                    if self._cur_new_group_counter <= group_num:
                        self._cur_new_group_counter = group_num + 1
        self._group_widgets[group] = widget = \
            GroupListItem(self._groups_scroll, group, self._groups_sel_var)
        widget.grid(column=0, sticky=tk.NSEW)
        return group

    def currently_selected_group(self):
        '''Return the group that is currently selected, or None if none is.'''
        for group in self._group_widgets:
            if id(group) == self._groups_sel_var.get():
                return group
        return None

    def remove_group(self, group=None):
        '''Remove the specified group, else the currently selected one.'''
        if not group:
            group = self.currently_selected_group()
            if not group:
                raise ValueError('no group given or selected')
        self._group_widgets[group].grid_forget()
        del self._group_widgets[group]
        self._groups_sel_var.set(0)
        self._group_type_var.set(type(self.currently_selected_group()).__name__)
        self._data_display.display_data(self.currently_selected_group())

    def select_group(self, group=None):
        '''Select the given group and allow the user to edit its data.'''
        if not group:
            group = self.currently_selected_group()
        if group:
            self._group_type_var.set(group.data_type.__name__
                                     if group.data_type else '')
            self._style_editor.set_group(group)
            self._data_display.display_data(group)
        self._select_group_callback(group)
