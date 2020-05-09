# Goals for this tool

This was the initial doc that I created to write down what my problem was, and how I could solve it. I also went a little bit into the process for some of the components of the tool, and some of the initial features I thought of. It has not been updated since. For a current list of features and info, check the main repo [README](README.md)

## Problem:

Using google drive to backup my /dev folder (with all my projects and stuff),
I can't backup everything because some projects have the dreaded node_modules dir
inside them...

I want to have a utility script that will go through and backup everything - minus the node_modules
folder. In the future it would be nice to load up a config from a text file for folder/file name exclusions
instead of just node_modules.

## How will I solve this?

1. Set Google Drive to backup a specific main folder like "backup"
2. Have this script load up an exclusion config and then recursively
   go into and copy files / folders into the main backup folder, minus
   the excluded folders / files specified in the config

## Future features...

-   Check if folder / file already exists in backup, and if so, only
    overwrite if backup dir has an older (modified date/time?) version
-   Turn into a service that runs on startup?

## Process:

Load config file from args, parse exclusion names (files/folders)
parse the root dir to backup FROM and dir to backup TO

Commence the backup process by recursively going through dirs,
copying files over as necessary.

Path doesn't exist in backup folder -> create dirs + intermediate dirs and copy over file
Path exists but file doesn't -> Copy file over
Path and file exists -> Overwrite if older
