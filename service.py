"""
This is the service version of the tool.
It is meant to run on startup and will watch
the provided dir and its subdirs for changes
& sync to backup-dest path.
"""

# Logger
import logging

from time import sleep  # Reduce poll rate to keep CPU usage down

from classes.BackupManager import BackupManager

if __name__ == "__main__":
    # Get manager instance
    backup_mgr = BackupManager()

    # *DEBUG*
    default_config_file = "tests/test-config.json"
    # * ^
    backup_mgr.load_config(default_config_file)

    # Traverse all files / dirs in backup-src and backup
    # to backup-dest
    # backup_list = backup_mgr.backup_all_files()

    # logging.debug(backup_list)

    # init fs watchdog and run observer
    backup_mgr.setup_filesystem_watchdog()
    backup_mgr.start_fs_watchdog()

    # Check every n seconds to reduce CPU usage
    try:
        while True:
            sleep(3)
    except KeyboardInterrupt as e:
        logging.debug("Backup service stopped via keyboard interrupt")
        exit(0)
