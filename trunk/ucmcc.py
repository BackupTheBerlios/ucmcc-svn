'''CodeCollaborator for UCM'''

# Copyright (c) 2006 by QUALCOMM INCORPORATED  All Rights Reserved.
# Miki Tebeka <mtebeka@qualcomm.com>

import wx
from common import ICONFILE, BaseDialog, Error, \
    create_review, error, main, merge_changes, run_with_progress, set_view, \
    view_to_stream, get_delivery_activities, get_activity_changes
from wx.lib.dialogs import messageDialog
from getpass import getuser

VIEW_CHANGES = {} # view -> change list

def get_view_changes(view):
    '''Get current view changes (ones that will be in next delivery)'''
    if view in VIEW_CHANGES:
        return VIEW_CHANGES[view]
    set_view(view)
    stream = view_to_stream(view)
    activities = get_delivery_activities(stream)
    changes = []
    for activity in activities:
        changes += get_activity_changes(activity)

    VIEW_CHANGES[view] = changes
    return changes

def get_view_changes_progress(view):
    return run_with_progress(
            get_view_changes, 
            (view, ), 
            "Getting View Changes", 
            "Please wait while fetching changes of view %s" % view)

class UCMCC(BaseDialog):
    def create_gui(self, sizer):
        self.set_title("UCM CodeCollaborator")


        # Files:
        # +--------------+
        # |[] file 1     |
        # |[] file 2     |
        # |[] file 3     |
        # +--------------+
        sizer.Add(wx.StaticText(self, -1, "Files:"))
        self._files = wx.CheckListBox(self, -1, size=(-1, 300))
        sizer.Add(self._files, 1, wx.EXPAND)
        self.file_list = []

        def add_button(name, handler, sizer, id=-1):
            b = wx.Button(self, id, name)
            if handler:
                self.Bind(wx.EVT_BUTTON, handler, b)
            sizer.Add(b)

        # [Select All] [Unselect All] [Invert Selection]
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        add_button("Select All", self.OnSelectAll, hsizer)
        add_button("Unselect All", self.OnUnselectAll, hsizer)
        add_button("Invert Selection", self.OnInvertSelection, hsizer)
        sizer.Add(hsizer, 0, wx.EXPAND)

        # ------------------
        # [Create Review] [Quit]
        sl = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL, size=(-1, 2))
        sizer.Add(sl, 0, wx.EXPAND|wx.NORTH|wx.SOUTH, 5)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        add_button("Create Review", self.OnReview, hsizer)
        add_button("Quit", None, hsizer, wx.ID_CANCEL)
        sizer.Add(hsizer, 0, wx.EXPAND)

    def OnView(self, evt):
        self.start_busy()
        try:
            self._files.Clear()
            try:
                self.changes = get_view_changes_progress(evt.GetString())
            except Error, e:
                error(e)
                return

            for i, change in enumerate(self.changes):
                self._files.Append("%s (%s)" % (change.filename, change.activity))
                self._files.Check(i)
        finally:
            self.end_busy()

    def OnReview(self, evt):
        review_changes = []
        for i, change in enumerate(self.changes):
            if self._files.IsChecked(i):
                review_changes.append(change)

        if not review_changes:
            error("No files selected")
            return

        review_changes = merge_changes(review_changes)

        self.start_busy()
        try:
            self.upload_changes(review_changes)
        finally:
            self.end_busy()


    def OnSelectAll(self, evt):
        for i in range(self._files.GetCount()):
            self._files.Check(i, 1)

    def OnUnselectAll(self, evt):
        for i in range(self._files.GetCount()):
            self._files.Check(i, 0)

    def OnInvertSelection(self, evt):
        for i in range(self._files.GetCount()):
            self._files.Check(i, not self._files.IsChecked(i))


if __name__ == "__main__":
    main(UCMCC)
