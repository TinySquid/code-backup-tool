"""
This is the service version of the tool.
It is meant to run on startup and will watch
the provided dir and its subdirs for changes
& sync to backup-dest path.
"""

# Logger
import logging

from classes.BackupManager import BackupManager

if __name__ == "__main__":
    backup_mgr = BackupManager()
    default_config_file = "tests/test-config.json"

    backup_mgr.load_config(default_config_file)

    paths = backup_mgr.backup_all_files()

    logging.debug(paths)

    # Parse args and return loaded config
    # parse_args(sys.argv)

    # print("Running with config:\n")
    # for key in config:
    #     print(f"{key}: {config[key]}")
    # print("")

    # start_time = time()

    # print("Beginning initial backup...")

    # backed_up_files = backup_all_files(config)

    # print(f"Backup completed in {round(time() - start_time, 6)} seconds.\n")
    # print(f"Files backed up: {len(backed_up_files)}")

    # Watch backup-src dir for changes
    # fs_observer = setup_filesystem_watchdog(config["backup-src"])

    # fs_observer.start()

    # logging.debug("fs observer thread started.")

    # # Check every n seconds
    # while True:
    #     sleep(3)

    logging.debug("Backup service exited")
