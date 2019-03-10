# -*- coding: utf-8 -*-

import requests
import logging
import pickle
import random
import time

from requests.exceptions import ConnectionError

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8,ru;q=0.6',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/46.0.2490.80 Safari/537.36'
    }

logger = logging.getLogger(__name__)

class PageNotFound(Exception):
    pass

class InternalServerError(Exception):
    pass

class NetworkManager(object):

    pageDownloadTriesCount = 3

    def __init__(self, proxies={}):
        self.session = requests.session()
        self.proxies = proxies
        logging.info('NetworkManager initialized with proxy setting: %s' % self.proxies)

    def load_cookies(self, filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

    def download_page(self, url, cookies=None, binary=False):
        tries = 0

        while tries < self.pageDownloadTriesCount:
            if self.proxies != {}:
                proxies = dict(https=random.choice(self.proxies))
                logging.info('Using proxies: %s' % proxies)
            else:
                proxies = None

            try:
                response = self.session.get(url, headers=headers, proxies=proxies)
                break
            except ConnectionError:
                tries += 1
                logger.info('Connection error, sleeping for 10 s')
                time.sleep(10)
            logging.error('Could not download page in %s tries' % self.pageDownloadTriesCount)
            return None

        logger.info('Page fetched with HTTP status code = %s' % response.status_code)

        if response.status_code == 200:
            if binary:
                return response
            else:
                return response.text
        elif response.status_code == 404:
            raise PageNotFound('Page not found')
        elif response.status_code == 500:
            raise InternalServerError
        else:
            return None
