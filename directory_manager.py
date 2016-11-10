import logging
import os
import time
import operator
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
        self.to_remove_from_dict = []
        self.ftp = TalkToFTP(ftp_website)
        self.ftp.connect()
        if not self.ftp.if_exist(self.ftp.directory, self.ftp.get_folder_content("")):
            self.ftp.create_folder(self.ftp.directory)
        self.ftp.disconnect()

    def synchronize_directory(self, frequency):  # frequency in seconds
        while True:
            # init the path explored to an empty list before each synchronization
            self.paths_explored = []

            # search for an eventual updates of files in the root directory
            self.ftp.connect()
            self.search_updates(self.root_directory)

            # look for any removals of files / folders
            self.any_removals()
            self.ftp.disconnect()

            # wait before next synchronization
            time.sleep(frequency)

    def search_updates(self, directory):
        for path_file, dirs, files in os.walk(directory):

            for dir_name in dirs:
                folder_path = os.path.join(path_file, dir_name)

                if self.is_superior_max_depth(folder_path) is False:
                    self.paths_explored.append(folder_path)
                    # a folder can't be updated, the only data we get is his creation time
                    # a folder get created during running time if not present in our list

                    if folder_path not in self.synchronize_dict:
                        # directory created
                        self.synchronize_dict[folder_path] = Directory(folder_path)
                        split_path = folder_path.split(self.root_directory)
                        srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                        self.ftp.create_folder(srv_full_path)

            for file_name in files:
                file_path = os.path.join(path_file, file_name)

                if self.is_superior_max_depth(file_path) is False and \
                        (self.contain_excluded_extensions(file_path) is False):

                    self.paths_explored.append(file_path)
                    if file_path in self.synchronize_dict:
                        if self.synchronize_dict[file_path].update_instance() == 1:

                            # file get updates
                            split_path = file_path.split(self.root_directory)
                            srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                            self.ftp.remove_file(srv_full_path)
                            self.ftp.file_transfer(path_file, srv_full_path, file_name)

                    else:

                        # file get created
                        self.synchronize_dict[file_path] = File(file_path)
                        split_path = file_path.split(self.root_directory)
                        srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                        self.ftp.file_transfer(path_file, srv_full_path, file_name)

    def any_removals(self):
        # if the length of the files to synchronize and the files explored are the same
        # no file / folder got removed
        if len(self.synchronize_dict.keys()) == len(self.paths_explored):
            return

        path_removed_list = [key for key in self.synchronize_dict.keys() if key not in self.paths_explored]
        for removed_path in path_removed_list:
            # if the current path not in the list of path already deleted
            # indeed we can't modify path_removed_list because we're iterating over it
            if removed_path not in self.to_remove_from_dict:
                if isinstance(self.synchronize_dict[removed_path], File):
                    split_path = removed_path.split(self.root_directory)
                    srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                    self.ftp.remove_file(srv_full_path)
                    self.to_remove_from_dict.append(removed_path)

                elif isinstance(self.synchronize_dict[removed_path], Directory):
                    split_path = removed_path.split(self.root_directory)
                    srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                    self.to_remove_from_dict.append(removed_path)
                    # if it's a directory, we need to delete all the files and directories he contains
                    self.remove_all_in_directory(removed_path, srv_full_path, path_removed_list)

        # all the files / folders deleted in system need to be deleted from the dictionary use to synchronize
        for to_remove in self.to_remove_from_dict:
            if to_remove in self.synchronize_dict.keys():
                del self.synchronize_dict[to_remove]
        self.to_remove_from_dict = []

    def remove_all_in_directory(self, removed_directory, srv_full_path, path_removed_list):
        directory_containers = {}
        for path in path_removed_list:
            # path string contains removed_directory
            if removed_directory != path and removed_directory in path and path not in self.to_remove_from_dict:
                if len(path.split(os.path.sep)) not in directory_containers.keys():
                    directory_containers[len(path.split(os.path.sep))] = [path]
                else:
                    directory_containers[len(path.split(os.path.sep))].append(path)
        # sort depending on the file depth
        # for each depth number we define a list of path for this depth
        sorted_containers = sorted(directory_containers.values())
        for i in range(len(sorted_containers)-1, -1, -1):
            for to_delete in sorted_containers[i]:
                to_delete_ftp = "{0}{1}{2}".format(srv_full_path, os.path.sep, to_delete.split(os.path.sep)[-1])
                if isinstance(self.synchronize_dict[to_delete], File):
                    self.ftp.remove_file(to_delete_ftp)
                    self.to_remove_from_dict.append(to_delete)
                else:
                    self.remove_all_in_directory(to_delete, to_delete_ftp, path_removed_list)
        self.ftp.remove_folder(srv_full_path)
        self.to_remove_from_dict.append(removed_directory)

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
