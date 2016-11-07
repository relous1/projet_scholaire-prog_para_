import logging
import os
import time
from Directory import Directory
from File import File
from talk_to_ftp import TalkToFTP

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


class DirectoryManager:
    def __init__(self, ftp_website, directory, depth, excluded_extensions):
        self.root_directory = directory
        self.depth = depth
        self.excluded_extensions = excluded_extensions
        self.synchronize_dict = {}
        self.os_separator_count = len(directory.split(os.path.sep))
        self.updates = []
        self.paths_explored = []
        self.ftp = TalkToFTP(ftp_website)
        self.ftp.connect()
        if not self.ftp.if_exist(self.ftp.directory, self.ftp.get_folder_content("")):
            self.ftp.create_folder(self.ftp.directory)
        # init files / folders to synchronize with the FTP server
        self.init_synchronization(self.root_directory)
        self.ftp.disconnect()
        logging.info(self.synchronize_dict)

    def init_synchronization(self, directory):
        for path_file, dirs, files in os.walk(directory):

            for dir_name in dirs:
                folder_path = os.path.join(path_file, dir_name)
                if self.is_superior_max_depth(folder_path) is False:
                    self.synchronize_dict[folder_path] = Directory(folder_path)
                    split_path = folder_path.split(self.root_directory)
                    srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                    split_path = path_file.split(self.root_directory)
                    srv_path = '{}{}'.format(self.ftp.directory, split_path[1])
                    if not self.ftp.if_exists(dir_name, self.ftp.get_folder_content(srv_path)):
                        self.ftp.create_folder(srv_full_path)
                    # explore recursively the current directory
                    self.init_synchronization(folder_path)

            for file_name in files:
                file_path = os.path.join(path_file, file_name)

                if (self.is_superior_max_depth(file_path) is False) and \
                        (self.contain_excluded_extensions(file_path) is False):
                    self.synchronize_dict[file_path] = File(file_path)
                    split_path = file_path.split(self.root_directory)
                    srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                    self.ftp.file_transfer(path_file, srv_full_path, file_name)

    def synchronize_directory(self, frequency):  # frequency in seconds
        while True:
            # init the path explored to an empty list before each synchronization
            self.paths_explored = []

            # init the list of updates to an empty list before each synchronization
            self.updates = []

            # search for an eventual updates of files in the root directory
            self.ftp.connect()
            self.search_updates(self.root_directory)

            # look for any removals of files / folders
            self.any_removals()
            self.ftp.disconnect()

            # wait before next synchronization
            time.sleep(frequency)

            # print updates
            #logging.info(self.updates)

    def search_updates(self, directory):
        for path_file, dirs, files in os.walk(directory):

            for dir_name in dirs:
                folder_path = os.path.join(path_file, dir_name)

                if self.is_superior_max_depth(folder_path) is False:
                    self.paths_explored.append(folder_path)
                    # a folder can't be updated, the only data we get is his creation time
                    # a folder get created during running time if not present in our list
                    if folder_path not in self.synchronize_dict:
                        self.synchronize_dict[folder_path] = Directory(folder_path)
                        # directory created
                        self.updates.append(folder_path)
                        logging.info("directory created %s", folder_path)
                        split_path = folder_path.split(self.root_directory)
                        srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                        self.ftp.create_folder(srv_full_path)
                    # continue the recursive walk only if it's a folder
                    self.search_updates(folder_path)

            for file_name in files:
                file_path = os.path.join(path_file, file_name)

                if self.is_superior_max_depth(file_path) is False and \
                        (self.contain_excluded_extensions(file_path) is False):
                    self.paths_explored.append(file_path)
                    if file_path in self.synchronize_dict:
                        if self.synchronize_dict[file_path].update_instance() == 1:
                            # file get updates
                            self.updates.append(file_path)
                            logging.info("file updated %s", file_path)
                            split_path = file_path.split(self.root_directory)
                            srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                            self.ftp.remove_file(srv_full_path)
                            self.ftp.file_transfer(path_file, srv_full_path, file_name)
                    else:
                        # file get created
                        self.updates.append(file_path)
                        self.synchronize_dict[file_path] = File(file_path)
                        logging.info("file created %s", file_path)
                        split_path = file_path.split(self.root_directory)
                        srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                        self.ftp.file_transfer(path_file, srv_full_path, file_name)

    def any_removals(self):
        # if the length of the files to synchronize and the files explored are the same
        # no file / folder got removed
        if len(self.synchronize_dict.keys()) == len(self.paths_explored):
            return

        for removed_path in [key for key in self.synchronize_dict.keys() if key not in self.paths_explored]:
            logging.info("file removed %s", removed_path)
            self.updates.append(removed_path)

            if isinstance(self.synchronize_dict[removed_path], File):
                split_path = removed_path.split(self.root_directory)
                srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                self.ftp.remove_file(srv_full_path)
            elif isinstance(self.synchronize_dict[removed_path], Directory):
                split_path = removed_path.split(self.root_directory)
                srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                files = self.ftp.ftp.nlst(srv_full_path)
                for file in files:
                    self.ftp.remove_file(file)
                self.ftp.remove_folder(srv_full_path)
            del self.synchronize_dict[removed_path]

    # substract current number of os separator to the number of os separator for the root directory
    # if it's superior to the max depth, we do nothing
    def is_superior_max_depth(self, path):
        if (len(path.split(os.path.sep)) - self.os_separator_count) <= self.depth:
            return False
        else:
            return True

    # check if the file contains a prohibited extensions
    def contain_excluded_extensions(self, file):
        extension = file.split(".")[1]
        if ".{0}".format(extension) in self.excluded_extensions:
            return True
        else:
            return False
