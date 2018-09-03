#!/usr/bin/env python3

'''Extra user interface widgets for plotting stereonets.'''

import tkinter as tk
from tkinter import ttk

from grouping import DataGroup


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


class StyleEditor(tk.Toplevel):
    '''A window for editing the style of groups.'''

    def __init__(self, master, group):
        super().__init__(
            master, background=ttk.Style().lookup('TFrame', 'background'))
        self.group = group

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        ttk.Button(self, text='Close', underline=0, command=self.destroy) \
           .grid(row=1, column=1, sticky=tk.NSEW)
        ttk.Button(self, text='Apply', underline=0, command=self.save) \
           .grid(row=1, column=2, sticky=tk.NSEW)

        base = ttk.Frame(self)
        base.grid(row=0, column=0, columnspan=3, sticky=tk.NSEW)
        base.columnconfigure(1, weight=1)

        self._color = tk.StringVar(self)
        self._thickness = tk.IntVar(self)

        ttk.Label(base, text='Colour') \
           .grid(row=0, column=0, sticky=tk.NSEW)
        ttk.Entry(base, textvariable=self._color) \
           .grid(row=0, column=1, sticky=tk.NSEW)
        ttk.Label(base, text='Thickness') \
           .grid(row=1, column=0, sticky=tk.NSEW)
        ttk.Scale(base, from_=0, to=10, variable=self._thickness,
                  orient=tk.HORIZONTAL) \
           .grid(row=1, column=1, sticky=tk.NSEW)

    def save(self, *_):
        '''Modify the group with changes made in this dialog.'''
        self.group.style['fill'] = self._color.get()
        self.group.style['width'] = self._thickness.get()


class GroupListItem(ttk.Frame):  # pylint: disable=too-many-ancestors
    '''A widget for editing and selecting a group out of a list.'''

    def __init__(self, master, group, sel_variable, *, on_delete=None):
        super().__init__(master)
        self.group = group
        self.on_delete = on_delete
        self.columnconfigure(1, weight=1)
        ttk.Radiobutton(self, value=id(group), variable=sel_variable) \
           .grid(row=0, column=0, sticky=tk.NSEW)
        ttk.Checkbutton(self, variable=group.enabled) \
           .grid(row=0, column=1, sticky=tk.NSEW)
        ttk.Entry(self, textvariable=group.name) \
           .grid(row=0, column=2, sticky=tk.NSEW)
        ttk.Button(self, text='Style', command=self.edit_style) \
           .grid(row=0, column=3, sticky=tk.NSEW)
        ttk.Button(self, text='Delete', command=self.delete) \
           .grid(row=0, column=99, sticky=tk.NSEW)

    def edit_style(self):
        '''Show a style editor window to the user.'''
        StyleEditor(self, self.group)

    def delete(self):
        '''Delete the widget, removing the group from all stereonets.'''
        self.group.hide_group()
        if callable(self.on_delete):
            self.on_delete(self.group)
        self.destroy()


class StereonetInput(ttk.PanedWindow):  # pylint: disable=too-many-ancestors
    '''A widget for inputting structural data for display on a stereonet.'''

    def __init__(self, master, data_groups, *,
                 focus_key_groups=None, focus_key_data=None):
        super().__init__(master, orient=tk.VERTICAL)
        self._cur_new_group_counter = 1
        self._data_groups = data_groups
        self._group_widgets = {}

        groups_frm = ttk.LabelFrame(self, text='Groups',
                                    underline=0 if focus_key_groups else None)
        self.add(groups_frm, weight=1)
        groups_frm.rowconfigure(0, weight=1)
        groups_frm.columnconfigure(0, weight=1)

        self._groups_scroll = ScrollableFrame(
            groups_frm, grid={'row': 0, 'column': 0, 'sticky': tk.NSEW})

        self._groups_sel_var = tk.IntVar(self)
        for group in data_groups:
            self.add_group(group)

        data_frm = ttk.LabelFrame(self, text='Data',
                                  underline=0 if focus_key_data else None)
        self.add(data_frm, weight=3)
        data_frm.rowconfigure(0, weight=1)
        data_frm.columnconfigure(0, weight=1)

        data_tree_columns = {'type': 'Type of data',
                             'num_data': 'Number of data',
                             'displayed_as': 'Displayed as'}
        self._data_tree = data_tree = ttk.Treeview(
            data_frm, columns=tuple(data_tree_columns.keys()))
        data_tree.grid(row=0, column=0, sticky=tk.NSEW)
        data_tree.heading('#0', text='Group')
        data_tree.column('#0', stretch=True)
        for col, name in data_tree_columns.items():
            data_tree.heading(col, text=name)
        for col in data_tree_columns:
            data_tree.column(col, stretch=False)
        data_tree.insert('', tk.END, text='Test',
                         values=('Planes', 10, 'Poles'))

        data_entry = ttk.Frame(data_frm)
        data_entry.grid(row=1, column=0, sticky=tk.NSEW)
        ttk.Entry(data_entry) \
           .grid(row=0, column=0, sticky=tk.NSEW)

        if focus_key_groups:
            self.bind_all(focus_key_groups, lambda _: groups_frm.focus())
        if focus_key_data:
            self.bind_all(focus_key_data, lambda _: data_frm.focus())

    def add_group(self, group=None):
        '''Add a widget for the given group, creating one if none is given.'''
        if not group:
            new_group_name = f'New group #{self._cur_new_group_counter}'
            self._cur_new_group_counter += 1
            group = DataGroup(new_group_name)
        self._data_groups.append(group)
        self._group_widgets[group] = widget = \
            GroupListItem(self._groups_scroll, group, self._groups_sel_var)
        widget.grid(column=0, sticky=tk.NSEW)

    def currently_selected_group(self):
        '''Return the group that is currently selected, or None if none is.'''
        for group in self._data_groups:
            if id(group) == self._groups_sel_var.get():
                return group
        return None

    def remove_group(self, group=None):
        '''Remove the specified group, else the currently selected one.'''
        if not group:
            group = self.currently_selected_group()
            if not group:
                raise ValueError('no group given or selected')
        self._group_widgets[group].delete()
        del self._group_widgets[group]
        self._data_groups.remove(group)
