"""
  Problem:
    Using google drive to backup my /dev folder (with all my projects and stuff), 
    I can't backup everything because some projects have the dreaded node_modules dir
    inside them... 

    I want to have a utility script that will go through and backup everything - minus the node_modules
    folder. In the future it would be nice to load up a config from a text file for folder/file name exclusions
    instead of just node_modules.

  How will I solve this?
  1. Set Google Drive to backup a specific main folder like "backup"
  2. Have this script load up an exclusion config and then recursively
     go into and copy files / folders into the main backup folder, minus
     the excluded folders / files specified in the config
  
  Future features...
  - Check if folder / file already exists in backup, and if so, only
    overwrite if backup dir has an older (modified date/time?) version
  - Turn into a service that runs on startup?

  Process:
    Load config file from args, parse exclusion names (files/folders)
    parse the root dir to backup FROM and dir to backup TO

    Commence the backup process by recursively going through dirs,
    copying files over as necessary.
"""

import os  # For path stuff
import sys  # For args
import shutil  # For file copy / overwrite / metadata
import json  # For parsing config


def print_usage(error_message):
    """
    Prints optional error message and usage statement
    """
    if error_message:
        print(error_message)

    print(
        "usage: python main.py [help] [config_file]\n[help]: Prints usage statement\n[config_file]: Path to custom config"
    )
    # LEAVE!!!
    exit()


def load_config(file):
    """
    Loads and parses a provided config file 
    """
    config = {}

    if os.path.exists(file):
        with open(file) as config_file:
            # Returning from inside a "with" statement will close file
            # automatically still.
            return json.load(config_file)
    else:
        print(f"Error: Config file {file} does not exist.")
        exit(1)


def parse_args(args):
    """
    Parses commandline arguments and returns a config dict
    """
    default_config_path = "config.json"

    args_len = len(args)

    if args_len == 1:
        return load_config(default_config_path)
    elif args_len == 2:
        if args[1] == "-h":
            print_usage()
        else:
            return load_config(args[1])
    else:
        print_usage("Invalid number of arguments provided")


# * TODO - Allow for full commandline only operation as a second option (instead of loading from a config file)

if __name__ == "__main__":
    # Parse args and return loaded config
    config = parse_args(sys.argv)

    # # Pull config into vars
    # backup_from_folder = config["backup-from-folder"]
    # backup_to_folder = config["backup-to-folder"]
    # folder_exclusions = config["folder-exclusions"]
    # filetype_exclusions = config["filetype-exclusions"]
    # filename_exclusions = config["filename-exclusions"]

    # # Bools to toggle exclusion functionality
    # enable_folder_exclusions = True if len(folder_exclusions) > 0 else False
    # enable_filename_exclusions = True if len(filename_exclusions) > 0 else False
    # enable_filetype_exclusions = True if len(filetype_exclusions) > 0 else False

    # print(config)
    # print("Config loaded!")
    # print("Starting...")

    # # List to store filtered paths + filenames
    # # foo/bar.txt
    # paths = []

    # # Traverse all files and folders that pass the critera (exclusions)
    # for path, subdirs, files in os.walk(backup_from_folder, topdown=True):
    #     # * Filter by folder name (in-place)
    #     if enable_folder_exclusions:
    #         subdirs[:] = [d for d in subdirs if d not in folder_exclusions]

    #     # * iterate over all files in this directory
    #     for file in files:
    #         # Get file extension
    #         file_type = os.path.splitext(file)[1]

    #         if enable_filename_exclusions:
    #             # Does filename pass exclusion filter?
    #             if file not in filename_exclusions:
    #                 # * Filter by filename & filetype
    #                 if enable_filetype_exclusions:
    #                     # Does filetype pass exclusion filter?
    #                     if file_type not in filetype_exclusions:
    #                         paths.append(os.path.join(path, file))
    #                 else:
    #                     # * Filter by just filename
    #                     paths.append(os.path.join(path, file))
    #         elif enable_filetype_exclusions:
    #             # Does filetype pass exclusion filter?
    #             if file_type not in filetype_exclusions:
    #                 # * Filter by just filetype
    #                 paths.append(os.path.join(path, file))
    #         else:
    #             # * No filters besides folder name
    #             paths.append(os.path.join(path, file))

    # from_paths = paths

    # to_paths = []

    # for path in from_paths:
    #     to_paths.append(
    #         os.path.join(backup_to_folder, os.path.relpath(path, backup_from_folder))
    #     )

    # for i, full_path in enumerate(to_paths):
    #     print(f"{i}: {full_path} | {to_paths[i]}")
    #     # if os.path.exists(os.path.dirname(full_path)):
    #     #     # * Path exists, but does the file?
    #     #     if os.path.exists(full_path):
    #     #         # * Overwrite file if newer than backup
    #     #         pass
    #     #     else:
    #     #         # * Path exists, but file doesn't. Copy over file
    #     #         pass
    #     # else:
    #     #     # * Path doesn't exist, so neither does the file. Create dirs and copy over file
    #     #     path = os.path.dirname(full_path)

    #     #     try:
    #     #         os.makedirs(path)
    #     #     except FileExistsError:
    #     #         print("Path already exists")

    #     #     # Copy over file
    #     #     shutil.copy2()

    #     # if os.path.exists(path):
    #     #     # File already exists, check modified date and overwrite if newer
    #     # else:
    #     #     # Either the path doesn't exist (dirs) or the file doesn't exist
    #     #     if os.path.exists(os.path.dirname(path)):
    #     #         #* Path exits
    #     #     else:
    #     #         # * Path doesn't exist, and therfore neither does the file
    #     #     pass
    #     # else:
    #     #     # File doesn't exist, copy over and build dir + intermediate dirs if needed
    #     #     # Extract path

    # print("Done!")
