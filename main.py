import logging
from get_parameters import get_user_parameters

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

if __name__ == "__main__":
    get_user_parameters()