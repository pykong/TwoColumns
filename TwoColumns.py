import sublime
import sublime_plugin

TWO_COL_LAYOUT = {
    "cols": [0.0, 0.5, 1.0],
    "rows": [0.0, 1.0],
    "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
}


### taken from MaxPane by jisacks: https://github.com/jisaacks/MaxPane


class PaneManager:
    layouts = {}
    maxgroup = {}
    lock_wnds = set([])

    @staticmethod
    def isWindowMaximized(window):
        w = window
        if PaneManager.hasLayout(w):
            return True
        elif PaneManager.looksMaximized(w):
            return True
        return False

    @staticmethod
    def looksMaximized(window):
        w = window
        l = window.get_layout()
        c = l["cols"]
        r = l["rows"]
        if w.num_groups() > 1:
            if set(c + r) == set([0.0, 1.0]):
                return True
        return False

    @staticmethod
    def storeLayout(window):
        w = window
        wid = window.id()
        PaneManager.layouts[wid] = w.get_layout()
        PaneManager.maxgroup[wid] = w.active_group()

    @staticmethod
    def maxedGroup(window):
        wid = window.id()
        if wid in PaneManager.maxgroup:
            return PaneManager.maxgroup[wid]
        else:
            return None

    @staticmethod
    def popLayout(window):
        wid = window.id()
        l = PaneManager.layouts[wid]
        del PaneManager.layouts[wid]
        del PaneManager.maxgroup[wid]
        return l

    @staticmethod
    def hasLayout(window):
        wid = window.id()
        return wid in PaneManager.layouts

# ------


class ToggleMaxPaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        w = self.window
        if PaneManager.isWindowMaximized(w):
            w.run_command("unmaximize_pane")
            PaneManager.lock_wnds.discard(w.id())
        elif w.num_groups() > 1:
            PaneManager.lock_wnds.add(w.id())
            w.run_command("maximize_pane")

# ------


class MaximizePaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        w = self.window
        g = w.active_group()
        l = w.get_layout()
        PaneManager.storeLayout(w)
        current_col = int(l["cells"][g][2])
        current_row = int(l["cells"][g][3])
        new_rows = []
        new_cols = []
        for index, row in enumerate(l["rows"]):
            new_rows.append(0.0 if index < current_row else 1.0)
        for index, col in enumerate(l["cols"]):
            new_cols.append(0.0 if index < current_col else 1.0)
        l["rows"] = new_rows
        l["cols"] = new_cols
        for view in w.views():
            view.set_status('0_maxpane', 'MAX')
        w.set_layout(l)

# ------


class UnmaximizePaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        w = self.window
        if PaneManager.hasLayout(w):
            w.set_layout(PaneManager.popLayout(w))
        elif PaneManager.looksMaximized(w):
            # We don't have a previous layout for this window
            # but it looks like it was maximized, so lets
            # just evenly distribute the layout.
            self.evenOutLayout()
        for view in w.views():
            view.erase_status('0_maxpane')

    def evenOutLayout(self):
        w = self.window
        w.run_command("distribute_layout")

# ------


class DistributeLayoutCommand(sublime_plugin.WindowCommand):
    def run(self):
        w = self.window
        l = w.get_layout()
        l["rows"] = self.distribute(l["rows"])
        l["cols"] = self.distribute(l["cols"])
        w.set_layout(l)

    def distribute(self, values):
        l = len(values)
        r = range(0, l)
        return [n / float(l - 1) for n in r]

# ------


class ShiftPaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        w = self.window
        w.focus_group(self.groupToMoveTo())

    def groupToMoveTo(self):
        w = self.window
        g = w.active_group()
        n = w.num_groups() - 1
        if g == n:
            m = 0
        else:
            m = g + 1
        return m

# ------


class UnshiftPaneCommand(ShiftPaneCommand):
    def groupToMoveTo(self):
        w = self.window
        g = w.active_group()
        n = w.num_groups() - 1
        if g == 0:
            m = n
        else:
            m = g - 1
        return m

# ------


class MaxPaneEvents(sublime_plugin.EventListener):
    def on_window_command(self, window, command_name, args):
        unmaximize_before = ["travel_to_pane", "carry_file_to_pane",
                             "clone_file_to_pane", "create_pane",
                             "destroy_pane", "create_pane_with_file"]
        if command_name in unmaximize_before:
            window.run_command("unmaximize_pane")

        if command_name == "exit":
            # Un maximize all windows before exiting
            windows = sublime.windows()
            for w in windows:
                w.run_command("unmaximize_pane")

        return None

    def on_activated(self, view):
        w = view.window() or sublime.active_window()
        # Is the window currently maximized?
        if w and PaneManager.isWindowMaximized(w):
            # Is the active group the group that is maximized?
            if w.active_group() != PaneManager.maxedGroup(w):
                w.run_command("unmaximize_pane")
                w.run_command("maximize_pane")


### TwoColumns

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
        if layout != TWO_COL_LAYOUT and window.id() not in PaneManager.lock_wnds:
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
