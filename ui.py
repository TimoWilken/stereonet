#!/usr/bin/env python3

'''Extra user interface widgets for plotting stereonets.'''

import tkinter as tk
from tkinter import ttk
from math import radians, degrees

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

    def __init__(self, master, group, sel_variable, *, selected=True,
                 on_delete=None):
        super().__init__(master)
        self.group = group
        self.on_delete = on_delete
        self.columnconfigure(2, weight=1)
        sel_btn = ttk.Radiobutton(self, value=id(group), variable=sel_variable)
        sel_btn.grid(row=0, column=0, sticky=tk.NSEW)
        if selected:
            sel_btn.invoke()
        ttk.Checkbutton(self, variable=group.enabled) \
           .grid(row=0, column=1, sticky=tk.NSEW)
        ttk.Entry(self, textvariable=group.name) \
           .grid(row=0, column=2, sticky=tk.NSEW)
        ttk.Button(self, text='Style', width=5, command=self.edit_style) \
           .grid(row=0, column=3, sticky=tk.NSEW)
        ttk.Button(self, text='Delete', width=6, command=self.delete) \
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
        self._data_groups = []
        self._group_widgets = {}

        groups_frm = ttk.LabelFrame(self, text='Groups',
                                    underline=0 if focus_key_groups else None)
        self.add(groups_frm, weight=1)
        groups_frm.rowconfigure(0, weight=1)
        groups_frm.columnconfigure(0, weight=1)

        self._groups_scroll = ScrollableFrame(
            groups_frm, grid={'row': 0, 'column': 0, 'sticky': tk.NSEW})
        self._groups_scroll.columnconfigure(0, weight=1)

        data_frm = ttk.LabelFrame(self, text='Data',
                                  underline=0 if focus_key_data else None)
        self.add(data_frm, weight=3)
        data_frm.rowconfigure(0, weight=1)
        data_frm.columnconfigure(0, weight=1)

        self._data_tree_items = {}
        data_tree_columns = {0: 'Strike', 1: 'Dip'}
        self._data_tree = data_tree = ttk.Treeview(
            data_frm, columns=(0, 1))
        data_tree.grid(row=0, column=0, sticky=tk.NSEW)
        data_tree.heading('#0', text='#')
        data_tree.column('#0', width=50, stretch=False)
        for col, name in data_tree_columns.items():
            data_tree.column(col, width=75, stretch=True, anchor=tk.CENTER)
            data_tree.heading(col, text=name)
        data_tree.insert('', tk.END, text='1', values=(310, 10))
        data_tree.insert('', tk.END, text='2', values=(0, 4))

        data_entry = ttk.Frame(data_frm)
        data_entry.grid(row=1, column=0, sticky=tk.NSEW)
        data_entry.columnconfigure(1, weight=1)
        data_entry.columnconfigure(3, weight=1)

        field1_var, field2_var = tk.StringVar(self), tk.StringVar(self)
        field1_entry = ttk.Entry(data_entry, textvariable=field1_var)
        field1_entry.grid(row=0, column=1, sticky=tk.NSEW)
        ttk.Label(data_entry, text='/') \
           .grid(row=0, column=2, sticky=tk.NSEW)
        field2_entry = ttk.Entry(data_entry, textvariable=field2_var)
        field2_entry.grid(row=0, column=3, sticky=tk.NSEW)

        def entry_submit(*_):
            try:
                field1, field2 = (radians(float(field1_var.get())),
                                  radians(float(field2_var.get())))
            except ValueError:
                return
            group = self.currently_selected_group()
            new_netobj = group.data_type(field1, field2)
            group.add_net_object(new_netobj)
            field1_var.set('')
            field2_var.set('')
            field1_entry.focus()

        for entry in field1_entry, field2_entry:
            entry.bind('<Return>', entry_submit)

        if focus_key_groups:
            self.bind_all(focus_key_groups, lambda _: groups_frm.focus())
        if focus_key_data:
            self.bind_all(focus_key_data, lambda _: data_frm.focus())

        self._groups_sel_var = tk.IntVar(self)
        self._groups_sel_var.trace('w', lambda *_: self.select_group())
        for group in data_groups:
            self.add_group(group)

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

        def add_item_to_tree(group, item):
            if group == self.currently_selected_group():
                item_values = tuple(int(round(degrees(getattr(item, field))))
                                    for field in group.data_type.FIELDS)
                item_num = len(self._data_tree.get_children()) + 1
                tree_item = self._data_tree.insert('', tk.END, text=item_num,
                                                   values=item_values)
                self._data_tree.see(tree_item)
                self._data_tree_items[item] = tree_item

        def remove_item_from_tree(group, item):
            if group == self.currently_selected_group():
                self._data_tree.delete(self._data_tree_items[item])
                del self._data_tree_items[item]
                for i, tree_item in enumerate(self._data_tree.get_children()):
                    self._data_tree.item(tree_item, text=i)

        group.register_add_item(add_item_to_tree)
        group.register_remove_item(remove_item_from_tree)

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

    def select_group(self, group=None):
        '''Select the given group and allow the user to edit its data.'''
        if not group:
            group = self.currently_selected_group()
        if group.data_type:
            for i, field in enumerate(group.data_type.FIELDS):
                self._data_tree.heading(i, text=field.title())
        self._data_tree.selection_set()
        self._data_tree.delete(*self._data_tree.get_children())
        for i, netobj in enumerate(group.net_objects()):
            item_values = tuple(int(round(degrees(getattr(netobj, field))))
                                for field in group.data_type.FIELDS)
            self._data_tree.insert('', tk.END, text=i+1, values=item_values)
