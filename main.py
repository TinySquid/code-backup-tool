"""
Running this is simple:
usage: python backup.py [config.json]

Obviously you need python.
"""

import os  # For path stuff
import sys  # For args
import shutil  # For file copy / overwrite / metadata
import json  # For parsing config
from time import time, sleep  # Getting operation time, sleep to reduce cpu usage

# File system watchdog module
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# TODO - Allow for full commandline only operation as a second option (instead of loading from a config file)


def print_usage(error_message=None):
    """
    Prints optional error message and usage statement
    """
    if error_message:
        print(error_message)

    print(
        "usage: python main.py [help] [config_file.json]\n[help]: Prints usage statement\n[config_file]: Path to custom config"
    )
    # LEAVE!!!
    exit()


def load_config(file: str) -> list:
    """
    Loads and parses a provided config file 
    """
    config = {}

    if os.path.exists(file):
        with open(file) as config_file:
            # Returning from inside a "with" statement will close file
            # automatically still.
            try:
                config = json.load(config_file)
            except json.JSONDecodeError:
                print_usage("Not a valid JSON file")

            return config
    else:
        print_usage(f"Config file {file} does not exist.")


def parse_args(args: list) -> list:
    """
    Parses commandline arguments and returns a config dict
    """
    default_config_path = "config.json"

    args_len = len(args)

    if args_len == 1:
        # Run with default config
        return load_config(default_config_path)
    elif args_len == 2:
        if args[1] == "help":
            # Run usage statement
            print_usage()
        else:
            # Run with provided config
            return load_config(args[1])
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


def backup_files(config: list, src_paths: list, dest_paths: list) -> list:
    """
    Backs up files from backup_src to backup_dest, creating
    directories and intermediate directiories as needed. If 
    a file already exists in backup_dest, then it will be 
    overwritten based on modified date. Returns list of files
    copied over.
    """

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


def file_on_created(event):
    print(f"{event.src_path} created.")


def file_on_deleted(event):
    print(f"{event.src_path} deleted.")


def file_on_modified(event):
    print(f"{event.src_path} modified.")


def file_on_moved(event):
    print(f"{event.src_path} moved to {event.dest_path}")


def setup_filesystem_watchdog(path):
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

    return fs_observer


if __name__ == "__main__":
    # Parse args and return loaded config
    config = parse_args(sys.argv)

    print("Running with config:\n")
    for key in config:
        print(f"{key}: {config[key]}")
    print("")

    start_time = time()

    src_paths = build_backup_src_paths(config)

    dest_paths = build_backup_dest_paths(config, src_paths)

    print("Beginning backup...")

    backed_up_files = backup_files(config, src_paths, dest_paths)

    print(f"Backup completed in {round(time() - start_time, 6)} seconds.\n")
    print(f"Files backed up: {len(backed_up_files)}")
