"""
This is the service version of the tool.
It is meant to run on startup and will watch
the provided dir and its subdirs for changes
& sync to backup-dest path.
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


def load_config(file: str):
    """
    Attempts to load and parse a provided config file.
    Returns config dict or None if error encountered.
    """
    logging.debug(f"Loading config {file}...")

    config = {}

    if os.path.exists(file):
        with open(file) as config_file:
            try:
                config = json.load(config_file)

                logging.debug("Config loaded.")

            except json.JSONDecodeError:
                logging.error(f"Config file {file} not a valid JSON file.")
                return None
    else:
        logging.error(f"Config file {file} not found.")
        return None

    return config


def parse_args(args: list) -> list:
    """
    Parses commandline arguments and returns a config dict
    """
    default_config_path = "config.json"

    args_len = len(args)

    if args_len == 1:
        # Run with default config
        load_config(default_config_path)
    elif args_len == 2:
        if args[1] == "help":
            # Run usage statement
            print_usage()
        else:
            # Run with provided config
            load_config(args[1])
    else:
        print_usage("Invalid number of arguments provided")


def build_backup_src_paths(config: list) -> list:
    """
    Returns a list of filtered full paths from the backup-src directory and its subdirectories
    """

    # Backup from path
    backup_src_path = config["backup-src"]

    folder_exclusions = config["folder-exclusions"]
    filetype_exclusions = config["filetype-exclusions"]
    filename_exclusions = config["filename-exclusions"]

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


def build_backup_dest_paths(config: list, src_paths: list) -> list:
    """
    Returns a list of full paths with parent dir switched 
    from backup_src to backup_dest
    """

    backup_src_path = config["backup-src"]
    backup_dest_path = config["backup-dest"]

    dest_paths = []

    for path in src_paths:
        dest_paths.append(
            os.path.join(backup_dest_path, os.path.relpath(path, backup_src_path))
        )

    return dest_paths


def backup_all_files(config: list) -> list:
    """
    Backs up files from backup_src to backup_dest, creating
    directories and intermediate directiories as needed. If 
    a file already exists in backup_dest, then it will be 
    overwritten based on modified date. Returns list of files
    copied over.
    """

    src_paths = build_backup_src_paths(config)
    dest_paths = build_backup_dest_paths(config, src_paths)

    # Progress tracker
    percent_complete = 0
    percent_step = 10
    prev_percent = 0

    print("...Progress: 0")

    files_backed_up = []

    for i, full_path in enumerate(dest_paths):
        percent_complete = int((i / len(src_paths)) * 100)

        if percent_complete != prev_percent and percent_complete % percent_step == 0:
            print(f"...Progress: {round(percent_complete, 2)}")

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
                print("Path already exists")

            # Copy over file
            shutil.copy2(src_paths[i], full_path)
            files_backed_up.append(full_path)

    print("...Progress: 100")

    return files_backed_up


def remove_file(path: str) -> bool:
    """
    Deletes a file specified by the path. Returns True if
    successful, False otherwise.
    """

    if os.path.isdir(path):
        # Remove dir and contents
        try:
            shutil.rmtree(path, False)
        except OSError as error:
            logging.critical(error)

    else:
        # Remove file
        try:
            os.remove(path)
        except OSError as error:
            logging.critical(error)


def file_on_created(event):
    """
    This function is run when a new file is created
    """
    print(f"{event.src_path} created.")


def file_on_deleted(event):
    """
    This function is run when a file is deleted
    """
    print(f"{event.src_path} deleted.")

    path_to_delete = os.path.join(
        config["backup-dest"], os.path.relpath(event.src_path, config["backup-src"])
    )

    if remove_file(path_to_delete):
        logging.debug(f"Deleted {path_to_delete}.")
    else:
        logging.error(f"Unable to delete {path_to_delete}")


def file_on_modified(event):
    """
    This function is run when a file is modified
    """
    print(f"{event.src_path} modified.")


def file_on_moved(event):
    """
    This function is run when a file is moved
    """
    print(f"{event.src_path} moved to {event.dest_path}")


def setup_filesystem_watchdog(path: str) -> Observer:
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

    fs_event_handler.on_created = file_on_created
    fs_event_handler.on_deleted = file_on_deleted
    fs_event_handler.on_modified = file_on_modified
    fs_event_handler.on_moved = file_on_moved

    fs_observer = Observer()
    fs_observer.schedule(fs_event_handler, path, recursive=True)

    logging.debug("fs watchdog created.")

    return fs_observer


# Global config object
config = {}
default_config_file = "tests/test-config.json"

#  Setup logging
log_file_name = datetime.now().strftime("logs/code-backup_%Y-%m-%d_%H-%M.log")
logging.basicConfig(
    filename=log_file_name,
    filemode="w",
    level=logging.DEBUG,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%I:%M:%S %p",
)

# Log unhandled exceptions to file
def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handler for unhandled exceptions that will write to the logs"""
    logging.critical(
        "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
    )


# Assign exception handler
sys.excepthook = handle_unhandled_exception

logging.debug(f"Backup-Tool Started.")

if __name__ == "__main__":
    config = load_config(default_config_file)

    if config is None:
        exit(1)

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
    fs_observer = setup_filesystem_watchdog(config["backup-src"])

    fs_observer.start()

    logging.debug("fs observer thread started.")

    # Check every n seconds
    while True:
        sleep(3)

    logging.debug("Backup-Tool Exited")
