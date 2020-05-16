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
import os  # For path stuff
import sys  # To override exception hook
import shutil  # For file copy / overwrite / metadata
import json  # For parsing config
from datetime import datetime  # To get timestamp for log file
from time import time, sleep  # Getting operation time, sleep to reduce cpu usage

# File system watchdog module
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# Logger
import logging


class BackupManager:
    def __init__(self):
        self.config = None
        self.fs_observer = None

        #  Setup logging
        log_file_name = datetime.now().strftime("logs/code-backup_%Y-%m-%d_%H-%M.log")
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(asctime)s][%(levelname)s] %(message)s",
            datefmt="%I:%M:%S %p",
            handlers=[
                logging.FileHandler(log_file_name),
                logging.StreamHandler(sys.stdout),
            ],
        )

        # Log unhandled exceptions to file
        def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
            """Handler for unhandled exceptions that will write to the logs"""
            logging.critical(
                "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
            )

        # Assign exception handler
        sys.excepthook = handle_unhandled_exception

        logging.debug(f"BackupManager created.")

    def load_config(self, file):
        """
        Attempts to load and parse a provided config file.
        """
        logging.debug(f"Loading config {file}...")

        if os.path.exists(file):
            with open(file) as config_file:
                try:
                    self.config = json.load(config_file)

                    logging.debug("Config loaded.")

                except json.JSONDecodeError:
                    logging.critical(f"Config file {file} not a valid JSON file.")
                    exit(1)
        else:
            logging.critical(f"Config file {file} not found.")
            exit(1)

    def build_backup_src_paths(self):
        """
        Returns a list of filtered full paths from the backup-src directory and its subdirectories
        """

        # Backup from path
        backup_src_path = self.config["backup-src"]

        folder_exclusions = self.config["folder-exclusions"]
        filetype_exclusions = self.config["filetype-exclusions"]
        filename_exclusions = self.config["filename-exclusions"]

        # Bools to toggle exclusion functionality
        enable_folder_exclusions = True if len(folder_exclusions) > 0 else False
        enable_filename_exclusions = True if len(filename_exclusions) > 0 else False
        enable_filetype_exclusions = True if len(filetype_exclusions) > 0 else False

        """
        In order to not have a ton of if blocks for checking if files meet
        options and criteria, setup a var to hold a unique number that corresponds
        with the possible options. Then check if the file meets the criteria by
        adding the unique number for each passing test and then checking against
        the initial inclusion criteria variable
        """
        inclusion_criteria = 0

        if enable_filename_exclusions > 0:
            inclusion_criteria += 1
        if enable_filetype_exclusions > 0:
            inclusion_criteria += 2

        # List object to hold full paths that meet inclusion_criteria above
        src_paths = []

        # Traverse all files and folders that pass the exclusion checks
        for path, subdirs, files in os.walk(backup_src_path, topdown=True):
            # * Don't search subdir if in exclusion list (in-place)
            if enable_folder_exclusions:
                subdirs[:] = [d for d in subdirs if d not in folder_exclusions]

            # Iterate over all files in this directory
            for file in files:
                # Get file name and extension for exclusion checking
                [file_name, file_type] = os.path.splitext(file)

                checks_passed = 0

                # * Filename filter
                if enable_filename_exclusions:
                    if file_name not in filename_exclusions:
                        checks_passed += 1

                # * Filetype filter
                if enable_filetype_exclusions:
                    if file_type not in filetype_exclusions:
                        checks_passed += 2

                # * Do we pass criteria defined in the config?
                if checks_passed == inclusion_criteria:
                    src_paths.append(os.path.join(path, file))

        return src_paths

    def build_backup_dest_paths(self, src_paths):
        """
        Returns a list of full paths with parent dir switched 
        from backup_src to backup_dest
        """

        backup_src_path = self.config["backup-src"]
        backup_dest_path = self.config["backup-dest"]

        dest_paths = []

        for path in src_paths:
            dest_paths.append(
                os.path.join(backup_dest_path, os.path.relpath(path, backup_src_path))
            )

        return dest_paths

    def backup_all_files(self):
        """
        Backs up files from backup_src to backup_dest, creating
        directories and intermediate directiories as needed. If 
        a file already exists in backup_dest, then it will be 
        overwritten based on modified date. Returns list of files
        copied over.
        """

        src_paths = self.build_backup_src_paths()
        dest_paths = self.build_backup_dest_paths(src_paths)

        # Progress tracker
        percent_complete = 0
        percent_step = 10
        prev_percent = 0

        logging.debug("...Progress: 0")

        files_backed_up = []

        for i, full_path in enumerate(dest_paths):
            percent_complete = int((i / len(src_paths)) * 100)

            if (
                percent_complete != prev_percent
                and percent_complete % percent_step == 0
            ):
                logging.debug(f"...Progress: {round(percent_complete, 2)}")

            prev_percent = percent_complete

            if os.path.exists(os.path.dirname(full_path)):
                # Path exists, but does the file?
                if os.path.exists(full_path):
                    # * Overwrite file if newer than backup
                    dest_mod_time = os.path.getmtime(full_path)
                    src_mod_time = os.path.getmtime(src_paths[i])

                    if dest_mod_time < src_mod_time:
                        # Backup-src file is newer
                        shutil.copy2(src_paths[i], full_path)
                        files_backed_up.append(full_path)
                else:
                    # * Path exists, but file doesn't. Copy over file
                    shutil.copy2(src_paths[i], full_path)
                    files_backed_up.append(full_path)
            else:
                # * Path doesn't exist, so neither does the file. Create dirs and copy over file
                path = os.path.dirname(full_path)

                try:
                    os.makedirs(path)
                except FileExistsError:
                    logging.debug("Path already exists")

                # Copy over file
                shutil.copy2(src_paths[i], full_path)
                files_backed_up.append(full_path)

        logging.debug("...Progress: 100")

        return files_backed_up

    def delete_item(self, path):
        """
        Deletes a file / dir specified by the path. Returns True if
        successful, False otherwise.
        """

        try:

            if os.path.isdir(path):
                # Remove dir and contents
                shutil.rmtree(path, False)

            else:
                # Remove file
                os.remove(path)

            return True
        except OSError as error:
            logging.critical(error)

        return False

    def setup_filesystem_watchdog(self):
        """
        Initializes a filesystem watchdog (sets up file system event handler) and returns an observer object
        """

        logging.debug("Initializing fs watchdog...")

        patterns = "*"
        ignore_patterns = ""
        ignore_directories = False
        case_sensitive = True

        fs_event_handler = PatternMatchingEventHandler(
            patterns, ignore_patterns, ignore_directories, case_sensitive
        )

        fs_event_handler.on_created = self.file_on_created
        fs_event_handler.on_deleted = self.file_on_deleted
        fs_event_handler.on_modified = self.file_on_modified
        fs_event_handler.on_moved = self.file_on_moved

        self.fs_observer = Observer()
        self.fs_observer.schedule(
            fs_event_handler, self.config["backup-src"], recursive=True
        )

        logging.debug("fs watchdog created.")

    def start_fs_watchdog(self):
        self.fs_observer.start()
        logging.debug("fs watchdog running.")

    def stop_fs_watchdog(self):
        self.fs_observer.stop()
        logging.debug("fs watchdog stopped.")

    def file_on_created(self, event):
        """
        This function is run when a new file is created
        """
        logging.debug(f"{event.src_path} created.")

        dest_path = os.path.join(
            self.config["backup-dest"],
            os.path.relpath(event.src_path, self.config["backup-src"]),
        )

        if os.path.isdir(event.src_path):
            logging.debug("Item is a directory")
            shutil.copytree(event.src_path, dest_path)
        else:
            logging.debug("Item is a file")
            shutil.copy2(event.src_path, dest_path)

    def file_on_deleted(self, event):
        """
        File / dir delete event handler. Removes file / dir from backup
        """
        logging.debug(f"{event.src_path} deleted by external process.")

        # Get path to file / dir in backup
        delete_path = os.path.join(
            self.config["backup-dest"],
            os.path.relpath(event.src_path, self.config["backup-src"]),
        )

        # Delete
        if self.delete_item(delete_path):
            logging.debug(f"Deleted {delete_path} from backup.")
        else:
            logging.error(f"Unable to delete {event.src_path} from backup")

    def file_on_modified(self, event):
        """
        This function is run when a file is modified
        """
        # logging.debug(f"{event.src_path} modified.")
        logging.debug(f"{event}")

        dest_path = os.path.join(
            self.config["backup-dest"],
            os.path.relpath(event.src_path, self.config["backup-src"]),
        )
        if os.path.isfile(event.src_path):
            shutil.copy2(event.src_path, dest_path)

    def file_on_moved(self, event):
        """
        This function is run when a file is moved
        """
        logging.debug(f"{event.src_path} moved to {event.dest_path}")
        dest_orig_path = os.path.join(
            self.config["backup-dest"],
            os.path.relpath(event.src_path, self.config["backup-src"]),
        )

        dest_rename = os.path.join(
            self.config["backup-dest"],
            os.path.relpath(event.dest_path, self.config["backup-src"]),
        )

        os.rename(dest_orig_path, dest_rename)