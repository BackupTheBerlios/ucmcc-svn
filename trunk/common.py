'''Common stuff'''
# Copyright (c) 2006 by QUALCOMM INCORPORATED  All Rights Reserved.

# Miki Tebeka <mtebeka@qualcomm.com>

import wx
from wx.lib.dialogs import messageDialog
from os.path import dirname, isfile, join, isdir, basename
from sys import path, stdout
from decimal import Inf
from getpass import getuser
from os import popen, chdir, environ, makedirs, getpid, environ
from time import time
from _winreg import OpenKey, CloseKey, EnumKey, HKEY_CURRENT_USER, \
    QueryValueEx
from shutil import copy
from itertools import count
from threading import Thread
import re
try:
    from version import VERSION
except ImportError:
    VERSION = "???"

try:
    from sys import frozen
    is_frozen = 1
except ImportError:
    is_frozen = 0

# Find actvity name in delivery preview line:
# activity:fix_typo_in_TxReportCode@\ldc_pvob     liorb   "fix typo in TxReportCode"
_find_activity_name = re.compile(":([^@]*)@").search

# Find replica name in path (@\qitools_pvob)
_find_replica_name = re.compile("@\\\\[^\@]+$").search

# Split view owner by delimiter
split_view_owner = re.compile("[\\\\/]").split

class Error(Exception):
    pass

def log(message):
    if is_frozen:
        return

    print message
    stdout.flush()

def system(command, no_split=0):
    log(command)
    pipe = popen("%s 2>&1" % command)
    out = pipe.read()
    if pipe.close():
        raise Error("Error in running %s:\n%s" % (command, out))

    if no_split:
        return out
    return out.split("\n")

def cleartool(command, no_split=0):
    return system("cleartool %s" % command, no_split)

def ccollab(command, no_split=0):
    return system("ccollab %s" % command, no_split)

def get_user_views(user):
    curr_view = ""
    for line in cleartool("lsview -long"):
        line = line.strip()
        if line.startswith("Tag:"):
            curr_view = line.split()[1]
        elif curr_view and line.startswith("View owner:"):
            owner = split_view_owner(line)[-1]
            if owner == user:
                yield curr_view

def replica_name(stream):
    '''Name of replica in stream name (stream@\some_vob -> @\some_vob)'''
    match = _find_replica_name(stream)
    if not match:
        raise Error("can't find replica name in stream %s" % stream)
    return match.group()


_VIEW2STREAM = {}
def view_to_stream(view):
    '''Find main stream of view'''
    if view not in _VIEW2STREAM:
        out = cleartool("lsstream -fmt \"%%n %%[master]p\" -view %s" % view, 1)
        if not out.strip():
            raise Error("Can't find stream for view %s" % view)
        stream_name, master = out.split()

        stream = "%s%s" % (stream_name, replica_name(master))
        _VIEW2STREAM[view] = stream

    return _VIEW2STREAM[view]

def is_snapshot_view(view):
    for line in cleartool("lsview -long %s" % view):
        if "attributes" not in line:
            continue
        return "snapshot" in line

    # If there is not "View attributes:" line, assume dynamic
    # FIXME: Find a way not to guess
    return 0

VIEWS_KEY = \
    r"Software\Atria\ClearCase\CurrentVersion\ClearCase Explorer\ViewsPage"

def find_snapshot_view_root(view):
    root_key = OpenKey(HKEY_CURRENT_USER, VIEWS_KEY)
    for root_index in count():
        try:
            subkey_name = EnumKey(root_key, root_index)
            try:
                subkey = OpenKey(root_key, "%s\\%s" % (subkey_name, view))
                root, type = QueryValueEx(subkey, "AccessString")
                return root
            except WindowsError:
                continue
        except WindowsError:
            raise Error("Can't find root of view %s in registry" % view)

def get_delivery_activities(stream):
    activities = []
    get = 0
    for line in cleartool("deliver -preview -stream %s" % stream):
        line = line.strip()
        if "Activities included in this operation:" in line:
            get = 1
            continue
        if (not line) or (not get):
            continue
        m = _find_activity_name(line)
        if not m:
            raise Error("Bad activity line in delivery preview for %s" % \
                    stream)
        activities.append(m.groups()[0])

    return activities

def set_view(view):
    '''Set view, we need this since some cleartool call won't work unless
       we're in the view directory.
    '''
    if is_snapshot_view(view):
        root = find_snapshot_view_root(view)
    else:
        # Make sure it's mapped
        root = "M:\\%s" % view
        if not isdir(root):
            cleartool("startview %s" % view)
    chdir(root)

class Change:
    def __init__(self, filename, base_version, current_version, activity):
        self.filename = filename
        self.base_version = base_version
        self.current_version = current_version
        self.activity = activity

def version_number(version):
    '''Version number of change'''
    if is_checked_out(version):
        return Inf
    else:
        return int(basename(version))

def get_activity_changes(activity):
    get = 0
    files = {} # name -> version list
    for line in cleartool("lsact -long %s" % activity):
        line = line.strip()
        if "change set versions:" in line:
            get = 1
            continue
        if (not line) or (not get):
            continue
        path, version = line.split("@@")
        if not isfile(path):
            continue
        files.setdefault(path, []).append(version)

    changes = []
    for name in files:
        versions = files[name]
        assert len(version) > 1, "only one version for %s" % name
        versions.sort(key = version_number)
        base_version_number = max(0, version_number(versions[0]) - 1)
        base_version = join(dirname(versions[0]), "%s" % base_version_number)
        
        changes.append(Change(name, base_version, versions[-1], activity))

    return changes

# Output root directory
ROOT_DIR = join(environ["TEMP"], "ucmcc")

def gen_root():
    return join(ROOT_DIR, "%s_%s" % (getpid(), int(time())))

def is_checked_out(version):
    return "CHECKEDOUT" in version

def get_version(dest, filename, version):
    '''Get a version of file to dest'''
    if not isdir(dirname(dest)):
        try:
            makedirs(dirname(dest))
        except OSError:
            raise Error("Can't create directory %s" % dirname(dest))

    if is_checked_out(version):
        copy(filename, dest)
    else:
        cleartool("get -to \"%s\" \"%s@@%s\"" % (dest, filename, version))

def create_review(changes):
    base, curr = generate_directories(changes)
    upload_changes(base, curr)

def generate_directories(changes):
    '''Generate directories for review'''
    root = gen_root()
    base = join(root, "base")
    curr = join(root, "curr")
    for change in changes:
        path = change.filename[3:] # Remove directory

        basefile = join(base, path)
        get_version(basefile, change.filename, change.base_version)

        currfile = join(curr, path)
        get_version(currfile, change.filename, change.current_version)

    return base, curr

def merge_changes(changes):
    changed_files = {} # filename -> [change1, change2 ...]
    for change in changes:
        changed_files.setdefault(change.filename, []).append(change)

    merged = []
    for filename, change_list in changed_files.iteritems():
        current_list = [c.current_version for c in change_list]
        current_version = sorted(current_list, key=version_number)[-1]

        base_list = [c.base_version for c in change_list]
        base_version = sorted(base_list, key=version_number)[0]

        change = Change(filename, base_version, current_version, "<merge>")
        merged.append(change)

    return merged

def upload_changes(base, curr):
    ccollab("set scm clearcase") # Make sure we're in the right SCM
    ccollab("--quiet adddiffs new \"%s\" \"%s\"" % (base, curr))

def assert_clearcase():
    try:
        cleartool("help")
    except Error:
        raise Error("Can't find ClaseCase (not in path?)")

def assert_ccollab():
    try:
        ccollab("--help")
    except Error:
        raise Error("Can't find ccollab (not in path?)")

# Application directory
APPDIR = path[0]
if isfile(APPDIR): # py2exe
    APPDIR = dirname(APPDIR)

ICONFILE = join(APPDIR, "ucmcc.ico")

DIALOG_STYLE = \
    wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX

class BaseDialog(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, style=DIALOG_STYLE)
        icon = wx.Icon(ICONFILE, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # User: __________________
        # View: _______________v
        gsizer = wx.FlexGridSizer(2, 2)
        gsizer.Add(wx.StaticText(self, -1, "Login:"), 0,
                wx.ALIGN_CENTER_VERTICAL)
        self._login = wx.TextCtrl(self, -1, value=getuser(),
                style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnLoginChange, self._login)
        gsizer.Add(self._login, 1, wx.EXPAND)
        gsizer.Add(wx.StaticText(self, -1, "View:"), 0,
                wx.ALIGN_CENTER_VERTICAL)
        self._view = wx.ComboBox(self, -1, style=wx.CB_READONLY, 
                size=(500, -1))
        self.Bind(wx.EVT_COMBOBOX, self.OnView, self._view)
        gsizer.Add(self._view, 1, wx.EXPAND)
        gsizer.AddGrowableCol(1)

        sizer.Add(gsizer, 0, wx.EXPAND|wx.TOP, 3)

        sl = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL, size=(-1, 2))
        sizer.Add(sl, 0, wx.EXPAND|wx.NORTH|wx.SOUTH, 5)

        self.create_gui(sizer)
        self.set_views()

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.CenterOnScreen()

        self._view.SetFocus()

    def set_title(self, name):
        title = "%s (version %s)" % (name, VERSION)
        self.SetTitle(title)

    def create_gui(self, sizer):
        pass # Will be filled by subclass

    def start_busy(self):
        wx.BeginBusyCursor()

    def end_busy(self):
        wx.EndBusyCursor()

    def upload_changes(self, changes):
        run_with_progress(create_review, (changes, ),
                "Uploading Changes",
                "Please wait while uploading changes to server")
        self.RequestUserAttention()
        messageDialog(self, "Please finish the review on the web browser", 
                      "Review created", wx.OK)

    def get_views_progress(self):
        login = self._login.GetValue().strip()
        if not login:
            return []
        return run_with_progress(
                get_user_views, 
                (login, ), 
                "Getting Views", 
                "Please wait while fetching your views")

    def set_views(self):
        self.start_busy()
        try:
            login = self._login.GetValue().strip()
            if not login:
                return
            self._view.Clear()
            views = run_with_progress(
                    get_user_views, 
                    (login, ), 
                    "Getting Views", 
                    "Please wait while fetching your views")

            found_views = 0
            for view in views:
                found_views = 1
                self._view.Append(view)

            if not found_views:
                error("Can't find views belonging to %s" % login)
        finally:
            self.end_busy()

    def OnLoginChange(self, evt):
        self.set_views()

    def OnView(self, evt):
        pass

def error(message):
    messageDialog(None, "%s" % message, "UCMCC Error", wx.OK|wx.ICON_ERROR)

def run_with_progress(func, args, title, message):
    class T(Thread):
        def __init__(self):
            Thread.__init__(self)
            self.result = None
            self.error = None

        def run(self):
            try:
                self.result = func(*args)
            except Exception, e:
                self.error = e

    thread = T()
    max_progress = 10
    next = count(0).next

    progress = wx.ProgressDialog(
            title,
            message,
            maximum = max_progress,
            style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
    thread.start()

    while thread.isAlive():
        progress.Update(next() % max_progress)
        wx.MilliSleep(200)

    progress.Destroy()

    if thread.error:
        raise thread.error

    return thread.result

def main(DlgClass):
    app = wx.PySimpleApp()
    try:
        assert_clearcase()
        assert_ccollab()
        dlg = DlgClass()
        dlg.ShowModal()
        dlg.Destroy()
    except Exception, e:
        error(e)
        raise SystemExit(1)
