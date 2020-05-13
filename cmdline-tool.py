"""
This is the commandline version of the tool. 
with this you can manually backup one location
to another.
"""

import os  # For path stuff
import sys  # To override exception hook
import shutil  # For file copy / overwrite / metadata
import json  # For parsing config
from time import time  # Getting operation time

# Logger
import logging


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


if __name__ == "__main__":
    # Parse args to determine what to do

    # Load config

    # Execute requested operation

    # Return results
    pass
