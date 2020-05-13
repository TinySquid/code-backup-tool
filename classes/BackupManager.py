"""
The Backup class will encapsulate the backup functionality 
so that both the service and commandline versions of the 
tool stay DRY.

Actual features and their implementation is currently in a
dynamic state while I iron out what I actually need for 
initial release vs future goals

* One-time backup or continuous 
* Incorporated file system watcher
* Stats tracking (files backed up, failed attempts, etc)
* File & stream (stdout) logging options?
"""


class BackupManager:
    def __init__(self):
        pass
