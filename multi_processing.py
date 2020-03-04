import os
import multiprocessing
from logger import Logger
from talk_to_ftp import TalkToFTP

class Queue_initialisation:

    QUEUE = multiprocessing.Queue()
    IS_RUNNING = True

    def __init__(self,path, srv_path, file_name):
        self.path = path
        self.srv_path = srv_path
        self.file_name = file_name

def updating_file_p(ftp_website, JobQueue):

    while True:
        # wait for job to be sent over from queue
        if not JobQueue.empty():
            job = JobQueue.get()
            pathToFile = os.path.join(job.path, job.file_name)
            # if file exists, we send it to ftp server
            if os.path.isfile(pathToFile):
                with open(pathToFile, 'rb') as file:
                    connection_ftp = TalkToFTP(ftp_website)
                    connection_ftp.connect()
                    Logger.log_info("  FILE Starting : {0} - (Process : {1})".format(Job.srv_path, os.getpid()))
                    connection_ftp.ftp.storbinary('STOR ' + Job.srv_path, file)
                    connection_ftp.disconnect()
                    Logger.log_info("  FILE Done     : {0} - (Process : {1})".format(Job.srv_path, os.getpid()))
