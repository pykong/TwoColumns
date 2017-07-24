import sublime
import sublime_plugin

TWO_COL_LAYOUT = {
    "cols": [0.0, 0.5, 1.0],
    "rows": [0.0, 1.0],
    "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
}

SHARE_OBJECT = 'max_pane_share.sublime-settings'


class TwoColumns(sublime_plugin.EventListener):

    def on_new_async(self, view):
        print("on_new_async called")
        self._set_two_columns(view)

    def on_load_async(self, view):
        print("on_load_async called")
        self._set_two_columns(view)

    def __call__(self):
        print("plugin_loaded called")
        view = sublime.active_window().active_view()
        self._set_two_columns(view)

    def _set_two_columns(self, view):
        window = view.window()
        if not window:
            return

        layout = window.get_layout()

        # try to fetch list of maximized window ids from MaxPane plugin
        try:
            s = sublime.load_settings(SHARE_OBJECT)
            maxed_wnds = s.get("maxed_wnds")
        except:
            maxed_wnds = []

        if layout != TWO_COL_LAYOUT and window.id() not in maxed_wnds:
            print("layout is different")
            window.set_layout(TWO_COL_LAYOUT)
        else:
            print("layout is the same")


# this is run at sublime text startup
def plugin_loaded():
    TwoColumns()()


class CloneFileToPaneCommand(sublime_plugin.WindowCommand):
    def is_duplicated(self):
        active_buf = self.window.active_view().buffer_id()
        dupe_bufs = [view
                     for view in self.window.views()
                     if view.buffer_id() == active_buf]
        return True if len(dupe_bufs) > 1 else False

    def clone_file_to_pane(self):
        if not self.window.active_view():
            # If we're in an empty group, there's no active view
            print("Empty group. Nothing to clone.")
            return
        if not self.is_duplicated():
            print("No duplicates. Cloning.")
            original = self.window.active_view()
            self.window.run_command("clone_file")
            self.window.run_command("move_to_neighboring_group")
            self.window.focus_view(original)  # set focus back to original
        else:
            print("Duplicates found.")

    def run(self):
        self.clone_file_to_pane()
