==================================
CodeCollaborator for ClearCase UCM
==================================

:Author: Miki Tebeka <mtebeka@qualcomm.com>
:Version: _VERSION_

.. contents::

About
=====
These are wrapper tools around CodeCollaborator_ to make it play nice with
ClearCase UCM.

Please note that uploading the files takes a *looooong* time, be patient :)

Prerequisites
=============
ClearCase
---------
You need clear case install with `cleartool` in PATH

.. ATTENTION::
  We work under the assumption that the "life span" of an activity does not
  cross delivery. Meaning that you can deliver an activity only once.

Code Collaborator Client
------------------------
You need Code Collaborator Client [#]_ installed with `ccollab` in PATH.

1. Make sure you have a user in `QCT CodeCollaborator server`_ [#]_
2. Download the `command line client`_ and install it
3. Run `ccollab set collab http://qctcollab.qualcomm.com:8080 <login>` (where
   `<login>` is your login name)


Installing
==========
Just run the installer_.

The Tools
=========

UCMCC
-----
This tool lets you to pick files from the next delivery activities and submit them for review.

.. ATTENTION::
    Developer branch must be rebased before starting the tool.

UCMCC - Baseline
----------------
This tools let you select baselines to compare and create a review from them.

Changes
=======

Version _VERSION_ (20/08/2006)

* Allow to login as different user
* Code improvements

For full list of changes see the ChangeLog_

Known Bugs
==========
* If a file was added the "old" version is an empty file
* Due to bug in `ccollab` utility we don't know if the upload of the files
  failed

Building
========
To build you will need the following tools:

* Python from http://www.python.org
* wxPython from http://www.wxPython.org
* A `make` utility [4]_
* Unix like utilities: `cp`, `sed`, `zip`, `mkdir` and `rm` [4]_
* ReStructuredText from http://docutils.sf.net
* InnoSetup installer from http://www.jrsoftware.org/isinfo.php

When you have all of the above just run `make`, to build the installer run
`make installer`.


License
=======
See `LICENSE.txt`_ [#]_

-----

.. [#] *Not* Code Collaborator Windows Client
.. [#] You can do it from the `QCT CodeCollaborator server`_, or ask Miki_ for help
.. [#] BSD license.
.. [4] You can get all of these if you install Cygwin_ or UnxUtils_

.. _ChangeLog: ChangeLog
.. _CodeCollaborator: http://smartbearsoftware.com/codecollab.php
.. _Cygwin: http://www.cygwin.com
.. _Miki: mailto:mtebeka@qualcomm.com
.. _UnxUtils: http://unxutils.sf.net
.. _`LICENSE.txt`: LICENSE.txt
.. _`command line client`: http://smartbearsoftware.com/downloads/ccollab_client_1_2_502_windows.exe
.. _installer: ucmcc__VERSION__setup.exe
.. _QCT CodeCollaborator server: http://qctcollab.qualcomm.com:8080

.. comment: vim:ft=rst spell
