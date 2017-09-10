import sublime
import sublime_plugin

TWO_COL_LAYOUT = {
    "cols": [0.0, 0.5, 1.0],
    "rows": [0.0, 1.0],
    "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
}


def set_two_columns(view):
    window = view.window()
    if not window:
        return

    layout = window.get_layout()

    if layout != TWO_COL_LAYOUT:
        print("TwoColumns: layout is different")
        window.set_layout(TWO_COL_LAYOUT)
    else:
        print("TwoColumns: layout is the same")


class TwoColumns(sublime_plugin.EventListener):
    def on_new_async(self, view):
        set_two_columns(view)

    def on_load_async(self, view):
        set_two_columns(view)

    def __call__(self):
        view = sublime.active_window().active_view()
        set_two_columns(view)


# this is run at sublime text startup
def plugin_loaded():
    TwoColumns()()


class CloneFileToPaneCommand(sublime_plugin.WindowCommand):
    def is_duplicated(self):
        active_buf = self.window.active_view().buffer_id()
        dupe_bufs = [
            view for view in self.window.views()
            if view.buffer_id() == active_buf
        ]
        return True if len(dupe_bufs) > 1 else False

    def clone_file_to_pane(self):
        if not self.window.active_view():
            # If we're in an empty group, there's no active view
            print("TwoColumns: Empty group. Nothing to clone.")
            return
        if not self.is_duplicated():
            print("TwoColumns: No duplicates. Cloning.")
            original = self.window.active_view()
            self.window.run_command("clone_file")
            self.window.run_command("move_to_neighboring_group")
            self.window.focus_view(original)  # set focus back to original
        else:
            print("TwoColumns: Duplicates found. Not cloning")

    def run(self):
        self.clone_file_to_pane()
