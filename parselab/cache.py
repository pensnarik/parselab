# -*- encoding: utf-8 -*-

import os
import sys
import hashlib
import logging

__all__ = ['CacheInterface', 'MockCache', 'FileCache']

logger = logging.getLogger(__name__)

class CacheInterface():
    """
    Interface for cache
    """
    def get_file(url):
        """ Gets file from cache """
        raise NotImplementedError

    def write_file(url):
        """ Writes file to cache """
        raise NotImplementedError

    def is_in_cache(url):
        """
        Checks whether file present in cache or not, should always
        be used before get_file() to ensure that file is in cache
        """
        raise NotImplementedError

class MockCache(CacheInterface):

    def is_in_cache(url):
        return False

    def get_file(url):
        """
        Should not be called because is_in_cache() always returns False
        """
        return None

class FileCache(CacheInterface):

    path = None

    def get_cache_path(self):
        return self.path

    def __init__(self, namespace, path):
        if path:
            self.path = os.path.join(path, namespace)
        else:
            self.path = os.path.join(os.path.dirname(sys.path[0]), 'cache')

        logger.info('Cache initialization, path = %s' % self.get_cache_path())
        if not os.path.isdir(self.get_cache_path()):
            os.makedirs(self.get_cache_path())

        for i in range(0,16):
            if not os.path.isdir(os.path.join(self.get_cache_path(), '%x' % i)):
                os.mkdir(os.path.join(self.get_cache_path(), '%x' % i))

            for j in range(0,16):
                if not os.path.isdir(os.path.join(self.get_cache_path(), '%x' % i, '%x%x' % (i,j))):
                    os.mkdir(os.path.join(self.get_cache_path(), '%x' % i, '%x%x' % (i,j)))

    def get_cached_filename(self, url):
        if sys.version_info[0] < 3:
            hash = hashlib.md5(url).hexdigest()
        else:
            hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return os.path.join(self.get_cache_path(), hash[0], hash[0:2], hash)

    def get_cached_filename_compat(self, url):
        if sys.version_info[0] < 3:
            hash = hashlib.md5(url).hexdigest()
        else:
            hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return os.path.join(self.get_cache_path(), hash)

    def get_file_size(self, url):
        statinfo = os.stat(self.get_cached_filename(url))
        return statinfo.st_size

    def is_in_cache(self, url):
        if os.path.exists(self.get_cached_filename_compat(url)):
            os.rename(self.get_cached_filename_compat(url), self.get_cached_filename(url))
            return self.get_file_size(url) > 0

        return os.path.exists(self.get_cached_filename(url)) and self.get_file_size(url) > 0

    def is_in_cache_error(self, url):
        return os.path.exists('%s.error' % self.get_cached_filename(url))

    def save_error_in_cache(self, url, error='ERROR'):
        with open('%s.error' % self.get_cached_filename(url), 'wt') as f:
            f.write(error)

    def get_file(self, url, binary=False):
        if self.is_in_cache_error(url):
            return None

        if binary:
            return open(self.get_cached_filename(url), 'rb').read()
        else:
            return open(self.get_cached_filename(url)).read()

    def write_to_cache(self, url, data, binary=False):
        if binary:
            with open(self.get_cached_filename(url), 'wb') as f:
                # TODO: Think how to avoid requests module dependence
                for chunk in data.iter_content(chunk_size=1024):
                    f.write(chunk)
        else:
            with open(self.get_cached_filename(url), 'w') as f:
                if sys.version_info[0] < 3:
                    f.write(data.encode('utf8'))
                else:
                    f.write(data)
        logging.info('File %s was written' % self.get_cached_filename(url))

    def get_document(self, url):
        return self.get_file(url, binary=False)

    def get_binary_file(self, url, force_download=False):
        return self.get_file(url, binary=True)

    def remove_from_cache(self, url):
        """
        Removes file from cache
        """
        os.remove(self.get_cached_filename(url))
        logger.warning('File %s has been removed from cache' % self.get_cached_filename(url))

# Depricated class name, for compability
class CacheConsumer(FileCache):
    pass
