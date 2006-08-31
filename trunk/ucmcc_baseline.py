'''CodeCollaborator for UCM - Baseline diff'''

# Copyright (c) 2006 by QUALCOMM INCORPORATED  All Rights Reserved.
# Miki Tebeka <mtebeka@qualcomm.com>

import wx
from wx.lib.dialogs import messageDialog
from common import ICONFILE, BaseDialog, view_to_stream, \
     Error, replica_name, set_view, get_activity_changes, create_review, \
     error, main, cleartool, merge_changes, run_with_progress
from operator import itemgetter
from itertools import count

# To undersantd the format string run "cleartool man fmt_ccase"
LSBL_FORMAT = "\"%n (%[owner]p %Sd)\\n\""

def get_baselines(view):
    baselines = []
    view = view_to_stream(view)
    for line in cleartool("lsbl -fmt %s -stream %s" % (LSBL_FORMAT, view)):
        line = line.strip()
        if not line:
            continue
        baselines.append(line)
    baselines.reverse()

    return baselines

def get_baselines_progress(view):
    return run_with_progress(
            get_baselines,
            (view, ),
            "Getting Baseline List",
            "Please wait while getting baselines of %s" % view)


BASELINE_ACTIVITIES = {} # (view, basenline) -> activity list

def get_baseline_activities(view, baseline, pred=None):
    if (view, baseline) in BASELINE_ACTIVITIES:
        return BASELINE_ACTIVITIES[(view, baseline)]

    set_view(view)
    # FIXME: Find a better way
    stream = view_to_stream(view)
    replica = replica_name(stream)

    if not pred:
        pred = "-pred"
    else:
        pred += replica

    full_base = baseline + replica

    activities = []
    for line in cleartool("diffbl %s %s" % (pred, full_base)):
        line = line.strip()
        if not line:
            continue
        fields = line.split()
        activities.append(fields[1])

    BASELINE_ACTIVITIES[(view, baseline)] = activities
    return activities

def get_baseline_activities_progress(view, baseline, pred=None):
    return run_with_progress(
            get_baseline_activities,
            (view, baseline, pred),
            "Getting Baseline Activities",
            "Please wait while gettting baseline %s activities" % baseline)

def get_baseline_changes(view, baseline, pred=None):
    set_view(view)
    changes = []
    for activity in get_baseline_activities(view, baseline, pred):
        changes += get_activity_changes(activity)

    merged = merge_changes(changes)

    return merged

BASELINE_TEMPLATE = '''
Baseline %s
===========
Owner: %s
Date: %s
Activities:
%s
'''.strip()

class UCMCCBaseline(BaseDialog):
    def create_gui(self, sizer):
        self.set_title("UCM CodeCollaborator - Baseline")

        # Baseline: ________________________v [?]
        # Baseline: ________________________v [?]
        # [] Manually select baseline to compare
        gsizer = wx.FlexGridSizer(2, 3)
        def add_baseline():
            self.add_text(gsizer, "Baseline")
            combo = self.add_combo(gsizer)
            b = wx.Button(self, -1, "?", style=wx.BU_EXACTFIT)
            self.Bind(wx.EVT_BUTTON, self.OnExplainBaseline, b)
            b.combo = combo
            gsizer.Add(b)

            return combo

        self._baselines = add_baseline()
        self._manual_baselines = add_baseline()
        self._manual_baselines.Disable()
        sizer.Add(gsizer, 1, wx.EXPAND)

        self._manual = wx.CheckBox(self, -1, "Manually select baseline to compare")
        self.Bind(wx.EVT_CHECKBOX, self.OnManual, self._manual)
        sizer.Add(self._manual)

        # ----------------------
        # [Create Review] [Quit]
        sl = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL, size=(-1, 2))
        sizer.Add(sl, 0, wx.EXPAND|wx.NORTH|wx.SOUTH, 5)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        def add_button(name, handler, sizer, id=-1):
            b = wx.Button(self, id, name)
            if handler:
                self.Bind(wx.EVT_BUTTON, handler, b)
            sizer.Add(b)
        add_button("Create Review", self.OnReview, hsizer)
        add_button("Quit", None, hsizer, wx.ID_CANCEL)
        sizer.Add(hsizer, 0, wx.EXPAND)

    def OnView(self, evt):
        try:
            self.start_busy()
            try:
                view_name = evt.GetString()
                baseline_list = get_baselines_progress(view_name)
            except Error, e:
                error("%s" % e)
                baseline_list = []
            
            for combo in (self._baselines, self._manual_baselines):
                combo.Clear()
                for baseline in baseline_list:
                    combo.Append(baseline)
                combo.SetSelection(0)
            self.baseline_list = baseline_list

            self.GetSizer().Fit(self)
            self.Update()
        finally:
            self.end_busy()

    def OnReview(self, evt):
        def extract_baseline_name(line):
            return line.split()[0]

        baseline = self._baselines.GetStringSelection()
        if not baseline:
            error("Please select a baseline first")
            return

        if self._manual.IsChecked():
            prev_baseline = self._manual_baselines.GetStringSelection()
            if prev_baseline == baseline:
                error("Can't compare baseline to itself")
                return
        else:
            index = self.baseline_list.index(baseline)
            if index == len(self.baseline_list) - 1:
                error("There is no previous baseline")
                return
            prev_baseline = None

        baseline_name = extract_baseline_name(baseline)
        if prev_baseline:
            prev_baseline_name = extract_baseline_name(prev_baseline)
        else:
            prev_baseline_name = None

        self.start_busy()
        try:
            try:
                view = self._view.GetStringSelection()
                changes = get_baseline_changes(view, baseline_name,
                                               prev_baseline_name)
                self.upload_changes(changes)
            except Error, e:
                error("%s" % e)
                return
        finally:
            self.end_busy()

    def OnManual(self, evt):
        self._manual_baselines.Enable(evt.IsChecked())


    def OnExplainBaseline(self, evt):
        combo = evt.GetEventObject().combo
        baseline = combo.GetStringSelection()
        if not baseline:
            return
        view = self._view.GetStringSelection()
        baseline = baseline.replace("(", "")
        baseline = baseline.replace(")", "")
        name, owner, date = baseline.split()
        activities = get_baseline_activities_progress(view, name)

        activitires_str = "\t" + "\n\t".join(activities)
        messageDialog(
            self, 
            BASELINE_TEMPLATE  % (name, owner, date, activitires_str),
            "Baseline Information for %s" % name, 
            wx.OK)

    def add_text(self, sizer, caption):
        text = wx.StaticText(self, -1, "%s:" % caption)
        sizer.Add(text, 0, wx.ALIGN_CENTER_VERTICAL)

    def add_combo(self, sizer, choices=None):
        if choices is None:
            choices = []
        combo = wx.ComboBox(self, -1, choices=choices,
                style=wx.CB_READONLY, size=(500, -1))
        sizer.Add(combo, 0, wx.EXPAND)
        return combo


if __name__ == "__main__":
    main(UCMCCBaseline)
