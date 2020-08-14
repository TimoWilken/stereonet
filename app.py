#!/usr/bin/env python3

'''User interface in Tk for plotting stereonets.'''

import sys
import os.path
import json
import tkinter as tk
from tkinter import ttk, filedialog
from math import pi, radians

import analysis
from stereonets import EqualAngle, EqualArea
from transformation import Line, Plane
from grouping import DataGroup
from serialize import stereonet_object_encoder, stereonet_object_decoder
from ui import StereonetInput


class StereonetApp(ttk.Frame):  # pylint: disable=too-many-ancestors
    '''Main Tk Frame for the stereonet application.'''

    def __init__(self, master, stereonet_size=750):
        super().__init__(master)
        self.winfo_toplevel().title('Stereonet')
        self.grid(row=0, column=0, sticky=tk.NSEW)
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(99, weight=0)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self._setup_menus_and_toolbars()

        statusbar = ttk.Frame(self)
        statusbar.grid(row=99, column=0, columnspan=99, sticky=tk.NSEW)
        for row in range(99):
            statusbar.columnconfigure(row, weight=1)
        statusbar.columnconfigure(99, weight=0)
        ttk.Sizegrip(statusbar).grid(row=0, column=99, sticky=tk.NSEW)
        self._status_message = tk.StringVar(self)
        ttk.Label(statusbar, textvariable=self._status_message) \
           .grid(row=0, column=0, sticky=tk.NSEW)

        self._stereonets = []
        self._setup_stereonets(stereonet_size)

        self.data_groups = []
        self._net_input = StereonetInput(self, status_var=self._status_message,
                                         on_selection_change=self._on_group_selection_change)
        self._net_input.grid(row=1, column=2, sticky=tk.NSEW)
        for group in [DataGroup('test', Line, False),
                      DataGroup('test 2', Plane, False)]:
            self.add_group(group)
        self.data_groups[0].add_net_object(Line(*map(radians, (10, 180))))
        self.data_groups[0].add_net_object(Line(*map(radians, (5, 330))))
        self.data_groups[1].add_net_object(Plane(*map(radians, (210, 85))))

        self._current_file_name = None
        filed_opts = {'initialdir': os.curdir, 'parent': self}
        saveopend_opts = {
            'defaultextension': '.snet',
            'filetypes': (('Stereonet data', '*.snet'), ('JSON data', '*.json'),
                          ('Text files', '*.txt'), ('All files', '*')),
            **filed_opts
        }
        self._open_dialog = filedialog.Open(
            title='Open file', multiple=False, **saveopend_opts)
        self._save_dialog = filedialog.SaveAs(
            title='Save file', **saveopend_opts)

        if len(sys.argv) > 1:
            self.open_file(sys.argv[1])

        for net in self._stereonets:
            for event in '<Enter>', '<Leave>':
                net.bind_netobject(event, self._net_object_handler)

    def _setup_menus_and_toolbars(self):
        '''Create and populate the main menu and toolbar.'''

        def add_command(label, command, keycode=None, *,
                        menu=None, toolbar=None, underline=None):
            def norm_command(*_):
                return command()
            if keycode:
                self.bind_all(keycode, norm_command)
            options = {}
            if underline is not None:
                options['underline'] = underline
            if menu:
                menu.add_command(label=label, command=norm_command, **options)
            if toolbar:
                btn = ttk.Button(toolbar, text=label, command=norm_command)
                btn.pack(side=tk.LEFT, padx=2, pady=2)
                return btn
            return None

        def add_separator(*, menu=None, toolbar=None):
            if menu:
                menu.add_separator()
            if toolbar:
                ttk.Separator(toolbar, orient=tk.VERTICAL) \
                   .pack(side=tk.LEFT, padx=2, pady=2, fill=tk.Y)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, columnspan=99, sticky=tk.NSEW)

        menubar = tk.Menu(self)
        self.winfo_toplevel().config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='File', underline=0, menu=file_menu)
        groups_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='Groups', underline=0, menu=groups_menu)

        add_command('New', self.new_file, '<Control-n>', menu=file_menu,
                    toolbar=toolbar, underline=0)
        add_command('Open', self.open_file, '<Control-o>', menu=file_menu,
                    toolbar=toolbar, underline=0)
        add_command('Save', self.save_file, '<Control-s>', menu=file_menu,
                    toolbar=toolbar, underline=0)
        add_command('Save as', self.save_as_file, '<Control-Shift-s>',
                    menu=file_menu, toolbar=toolbar, underline=5)
        add_separator(menu=file_menu)
        add_command('Export', self.export, '<Control-e>', menu=file_menu,
                    toolbar=toolbar, underline=1)
        add_separator(menu=file_menu)
        add_command('Quit', self.quit, '<Control-q>', menu=file_menu,
                    toolbar=toolbar, underline=0)

        add_separator(toolbar=toolbar)
        add_command('Add group', self.add_group, '<Control-g>',
                    menu=groups_menu, toolbar=toolbar, underline=0)
        rmbtn = add_command('Remove current group', self.remove_current_group,
                            '<Control-d>', menu=groups_menu, toolbar=toolbar,
                            underline=0)

        analysis_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='Analysis', underline=0, menu=analysis_menu)
        add_command('Poles <-> Planes', self._poles_from_to_planes,
                    menu=analysis_menu, underline=0)
        add_command('Fold analysis', self._fold_analysis,
                    menu=analysis_menu, underline=0)

        # These widgets should be disabled when no group is selected.
        self._group_dependent_widgets_configures = [
            rmbtn.configure,
            lambda **kw: groups_menu.entryconfigure(1, **kw),
            lambda **kw: analysis_menu.entryconfigure(0, **kw),
            lambda **kw: analysis_menu.entryconfigure(1, **kw),
        ]

        theme_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='Theme', underline=0, menu=theme_menu)
        theme_var = tk.StringVar(theme_menu, ttk.Style().theme_use())
        theme_var.trace('w', lambda *_: ttk.Style().theme_use(theme_var.get()))
        for theme in ttk.Style().theme_names():
            theme_menu.add_radiobutton(label=theme, variable=theme_var)

    def _fold_analysis(self):
        cur_group = self._net_input.currently_selected_group()
        netobjs = cur_group.net_objects()
        fold = analysis.Fold(netobjs)
        group = DataGroup(cur_group.name.get() + ' (fold analysis)', Plane,
                          enabled=cur_group.enabled.get())
        group.add_net_object(fold.profile_plane())
        group.add_net_object(fold.axial_plane())
        self.add_group(group)

    def _poles_from_to_planes(self):
        '''Convert poles to planes and planes to poles.'''
        cur_group = self._net_input.currently_selected_group()
        conversion = analysis.planes_to_poles if cur_group.data_type == Plane \
                     else analysis.poles_to_planes
        self.add_group(conversion(cur_group))

    def _setup_stereonets(self, size):
        '''Create stereonets and populate them with guide lines.'''
        stereonets = ttk.Notebook(self)
        stereonets.grid(row=1, column=1, sticky=tk.NSEW)
        stereonets.enable_traversal()
        nb_tab_opts = {'underline': 7, 'sticky': tk.NSEW}

        self._stereonets.append(EqualArea(stereonets, size=size))
        stereonets.add(self._stereonets[-1], text='Equal Area', **nb_tab_opts)
        self._stereonets.append(EqualAngle(stereonets, size=size))
        stereonets.add(self._stereonets[-1], text='Equal Angle', **nb_tab_opts)

        for net in self._stereonets:
            for lat in range(-90, 91, 10):
                net.plot_latitude_guide(radians(lat))
            for dip in range(0, 90, 10):
                for left_hemisphere in True, False:
                    net.plot_dip_guide(radians(dip), left_hemisphere)
            net.plot_dip_guide(pi / 2)

    def _clear_all(self):
        '''Remove all plotted data and start over.'''
        for group in self.data_groups[:]:
            group.delete()

    def new_file(self):
        '''Handle requests to create a new, empty file.'''
        self._current_file_name = None
        self._clear_all()
        self._status_message.set('New file')

    def open_file(self, filename=None):
        '''Handle requests to open a different file.'''
        if not filename:
            filename = self._open_dialog.show()
        if not filename:
            self._status_message.set('Opening file cancelled.')
            return
        self._current_file_name = filename
        self._save_dialog.options.update({
            'initialdir': os.path.dirname(filename),
            'initialfile': os.path.basename(filename),
        })

        self._clear_all()
        try:
            with open(filename) as cur_file:
                decoder = stereonet_object_decoder
                data_groups = json.load(cur_file, object_hook=decoder)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as err:
            self._status_message.set(f'Failed to open {filename}! Error: {err}')
            print(type(err).__name__, err, sep=': ', file=sys.stderr)
        else:
            for group in data_groups:
                self.add_group(group)
            self._status_message.set(f'Opened file {filename}.')

    def save_file(self):
        '''Handle requests to save the current file.'''
        if not self._current_file_name:
            self.save_as_file()
            return
        with open(self._current_file_name, 'w') as cur_file:
            json.dump(self.data_groups, cur_file,
                      default=stereonet_object_encoder)
        self._status_message.set(f'Saved file {self._current_file_name}.')

    def save_as_file(self):
        '''Handle requests to save the current file under a different name.'''
        filename = self._save_dialog.show()
        if not filename:
            self._status_message.set('Saving file cancelled.')
            return
        self._current_file_name = filename
        self._open_dialog.options['initialdir'] = os.path.dirname(filename)
        self.save_file()

    def export(self):
        '''Handle requests for exporting stereonets.'''
        dirname = filedialog.askdirectory(mustexist=True)
        if not dirname:
            self._status_message.set('Exporting cancelled.')
            return
        export_fnames = []
        for i, net in enumerate(self._stereonets):
            export_fnames.append(f'{dirname}/net{i}.eps')
            net.postscript(x=0, y=0, width=net.size, height=net.size,
                           file=export_fnames[-1])
        self._status_message.set(
            'Exported files ' + ', '.join(export_fnames) + '.')

    def add_group(self, group=None):
        '''Add a new group to the list of data groups.'''
        def plot_group_netobjs(group):
            for netobj in group.net_objects():
                for net in self._stereonets:
                    if group.enabled.get():
                        net.plot(netobj, **group.style)
                    else:
                        net.remove_net_object(netobj)
                    net.update()
        def unplot_group_item(group, netobj):
            if group.enabled.get():
                for net in self._stereonets:
                    net.remove_net_object(netobj)
                    net.update()
        def plot_group_item(group, netobj):
            if group.enabled.get():
                for net in self._stereonets:
                    net.plot(netobj, **group.style)
                    net.update()

        group = self._net_input.add_group(group)
        group.bind(change_group_enabled=plot_group_netobjs,
                   add_item=plot_group_item, remove_item=unplot_group_item,
                   remove_group=self.remove_group)
        self.data_groups.append(group)
        plot_group_netobjs(group)
        return group

    def remove_current_group(self):
        '''Remove the currently selected group from the list of data groups.'''
        self.remove_group()

    def remove_group(self, group=None):
        '''Remove the specified group from the list of data groups.'''
        if not group:
            group = self._net_input.currently_selected_group()
            if not group:
                self._status_message.set('Select a group to delete first!')
                return
        self._net_input.remove_group(group)
        self.data_groups.remove(group)

    def _net_object_handler(self, event, net_object):
        if event.type == tk.EventType.Enter:
            self._status_message.set(net_object)
        elif event.type == tk.EventType.Leave and \
             self._status_message.get() == str(net_object):
            self._status_message.set('')

    def _on_group_selection_change(self, group):
        for configure in self._group_dependent_widgets_configures:
            configure(state=tk.NORMAL if group else tk.DISABLED)


if __name__ == '__main__':
    StereonetApp(tk.Tk()).mainloop()
