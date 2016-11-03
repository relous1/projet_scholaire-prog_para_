import logging
from directory_manager import DirectoryManager
from get_parameters import get_user_parameters

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


if __name__ == "__main__":
    # get parameters from command line
    ftp_website, local_directory, max_depth, refresh_frequency, excluded_extensions = get_user_parameters()

    # init directory manager with local directory and maximal depth
    directory_manager = DirectoryManager(local_directory, max_depth, excluded_extensions)

    # launch the synchronization
    directory_manager.synchronize_directory(refresh_frequency)