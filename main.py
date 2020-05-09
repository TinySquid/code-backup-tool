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

import sys  # For args
import os  # For path stuff
import json  # For parsing config


def load_config(file):
    """
    Loads and parses a provided config file 
    """
    if os.path.exists(file):
        with open(file) as config_file:
            return json.load(config_file)
    else:
        print(f"Error: {file} does not exist.")
        exit(1)


# * TODO - Allow for full commandline only operation as a second option (instead of loading from a config file)

if __name__ == "__main__":
    # Setup defaults
    default_config_path = "config.json"
    config = {}

    print("Loading config...")

    # Make it easier to work with args
    args = sys.argv
    args_len = len(args)

    if args_len == 1:
        # Load default config
        config = load_config(default_config_path)
    elif args_len == 2:
        # Load config file from arg
        config = load_config(args[1])

    # Pull config into vars
    backup_from_folder = config["backup-from-folder"]
    backup_to_folder = config["backup-to-folder"]
    folder_exclusions = config["folder-exclusions"]
    filetype_exclusions = config["filetype-exclusions"]
    filename_exclusions = config["filename-exclusions"]

    # Bools to toggle exclusion functionality
    enable_folder_exclusions = True if len(folder_exclusions) > 0 else False
    enable_filename_exclusions = True if len(filename_exclusions) > 0 else False
    enable_filetype_exclusions = True if len(filetype_exclusions) > 0 else False

    print(config)
    print("Config loaded!")
    print("Starting...")

    # List to store filtered paths + filenames
    # foo/bar.txt
    paths = []

    # Traverse all files and folders that pass the critera (exclusions)
    for path, subdirs, files in os.walk(backup_from_folder, topdown=True):
        # * Filter by folder name (in-place)
        if enable_folder_exclusions:
            subdirs[:] = [d for d in subdirs if d not in folder_exclusions]

        # * iterate over all files in this directory
        for file in files:
            # Get file extension
            file_type = os.path.splitext(file)[1]

            if enable_filename_exclusions:
                # Does filename pass exclusion filter?
                if file not in filename_exclusions:
                    # * Filter by filename & filetype
                    if enable_filetype_exclusions:
                        # Does filetype pass exclusion filter?
                        if file_type not in filetype_exclusions:
                            paths.append(os.path.join(path, file))
                    else:
                        # * Filter by just filename
                        paths.append(os.path.join(path, file))
            elif enable_filetype_exclusions:
                # Does filetype pass exclusion filter?
                if file_type not in filetype_exclusions:
                    # * Filter by just filetype
                    paths.append(os.path.join(path, file))
            else:
                # * No filters besides folder name
                paths.append(os.path.join(path, file))

    print(len(paths))
    print("Done!")
