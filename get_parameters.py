import os
import argparse
import logging
from logger import Logger

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def get_user_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("ftp_website", help="Full FTP Website ", type=str)
    parser.add_argument("local_directory", help="Directory of the file we want to save", type=str)
    parser.add_argument("refresh_frequency", help="Refresh frequency to synchronize with FTP server", type=str)
    parser.add_argument("excluded_extensions", nargs='*', help="List of the extensions to excluded when synchronizing",
                        type=str, default=[])
    # nargs = '*' : the last argument take zero or more parameter
    args = parser.parse_args()

    wrong_input = False

    # get the ftp website
    ftp_website = args.ftp_website

    # get the local directory to synchronize
    local_directory = args.local_directory
    if os.path.exists(local_directory) is False:
        Logger.log_error("Invalid FTP website")
        wrong_input = True

    # get the refresh frequency
    try:
        refresh_frequency = int(args.refresh_frequency)
    except ValueError:
        Logger.log_error("Invalid input for the refresh frequency : must be an integer")
        wrong_input = True
    else:
        if refresh_frequency <= 0:
            Logger.log_error("Invalid value for the refresh frequency : it can not be inferior or equal to 0")
            wrong_input = True

    # get a list of the excluded extensions
    excluded_extensions = args.excluded_extensions

    if wrong_input is False:
        Logger.log_info("Valid parameters")
        return ftp_website, local_directory, refresh_frequency, excluded_extensions
    else:
        return 0
