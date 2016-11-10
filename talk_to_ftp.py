import logging
import os
from ftplib import FTP

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


class TalkToFTP:
    def __init__(self, ftp_website):
        my_srv = ftp_website.split(",")
        self.host = my_srv[0]
        self.user = my_srv[1]
        self.password = my_srv[2]
        self.directory = my_srv[3]
        self.ftp = False

    def connect(self):
        self.ftp = FTP(self.host, self.user, self.password)
        logging.info("Connect to %s", self.host)

    def disconnect(self):
        self.ftp.quit()
        logging.info("Disconnect")

    def go_to(self, folder_path):
        self.ftp.cwd(folder_path)

    def create_folder(self, folder):
        self.ftp.mkd(folder)

    def remove_folder(self, folder):
        self.ftp.rmd(folder)

    def file_transfer(self, path, srv_path, file_name):
        file = open(os.path.join(path, file_name), 'rb')
        self.ftp.storbinary('STOR ' + srv_path, file)
        file.close()

    def remove_file(self, file):
        self.ftp.delete(file)

    def get_folder_content(self, path):
        return self.ftp.nlst(path)

    def if_exists(self, element, list):
        for path in list:
            path_split = path.split("/")
            element_name = path_split[1]
            if element_name == element:
                return True
        return False

    def if_exist(self, element, list):
        if element in list:
            return True
        else:
            return False

if __name__ == "__main__":
    logging.info("test")
    test = TalkToFTP("localhost,Xion,xion,tata")
    test.connect()

