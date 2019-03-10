# -*- coding: utf-8 -*-

import sys
import time
import logging
import argparse
import random

from parselab.db import Database
from parselab.cache import CacheInterface

logger = logging.getLogger(__name__)

class PageDownloadException(Exception):
    pass

class BasicParser(object):

    # Is previous page was fetched from cache?
    is_cache_used = True

    def __init__(self, args=sys.argv):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--init', action='store_true', help='Initialize project in database, if not exists')
        # TODO: call parser.parse_args()!
        logger.info("Init BasicParser")

    def get_cookies(self):
        return dict()

    def sleep(self):
        time_to_sleep = self.get_sleep_time()
        logger.info('Sleeping for %s s' % time_to_sleep)
        time.sleep(time_to_sleep)

    def get_sleep_time(self):
        return 0 if self.is_cache_used else random.randint(0, 10)

    def is_captcha_required(self, data):
        return False

    def get_page(self, url, binary=False):
        self.sleep()
        if sys.version_info[0] < 3:
            url = url.encode('utf-8')
        logger.info('Getting page "%s"...' % url)
        if self.cache.is_in_cache(url):
            logger.info('Page found in cache: %s' % self.cache.get_cached_filename(url))
            data = self.cache.get_file(url, binary)
            if data is None:
                raise PageDownloadException('Cache error')
            self.is_cache_used = True
            return data
        else:
            logger.info('Page was not found in cache')
            tries = 3
            while tries > 0:
                data = self.net.download_page(url, cookies=self.get_cookies(), binary=binary)

                if self.is_captcha_required(data):
                    self.solve_captcha(data)
                    continue

                if data:
                    break

                logger.warning('Network error, trying again...')
                tries -= 1
                if tries == 0:
                    self.cache.save_error_in_cache(url, 'PageDownloadException')
                    raise PageDownloadException('Could not get page')

            if not self.is_captcha_required(data):
                self.cache.write_to_cache(url, data, binary)
                logger.info('Page saved into cache as: %s' % self.cache.get_cached_filename(url))
                self.is_cache_used = False
            else:
                logger.warning('File has not been saved into the cache as it contains captcha data')
            return data

    def setup_project(self, db, project_name):
        try:
            db.setup_project(project_name)
        except InvalidProjectException:
            if self.args.init == True:
                db.create_project(project_name)
            else:
                print('Project "%s" was not found, use argument --init if you want to create one' % project_name)


class InvalidProjectException(Exception):
    """
    Thrown when project not found
    """
    pass

class ParsingDatabase(Database):
    """
    Implements integration with parsing database
    """
    cache = {'attributes': dict()}

    def setup_project(self, project_name):
        id = self.query_value('select id from public.project where name = %s', [project_name])
        if not id:
            raise InvalidProjectException('Invalid project name')
        self.project_id = id

    def create_project(self, project_name):
        self.project_id = self.query_value('insert into public.project (name) values (%s) returning id', [project_name])

    def get_category_id(self, category_name, parent_id=None, url=None):
        qInsert = '''
        insert into public.category (project_id, name, parent_id, url)
        values (%(project_id)s, %(name)s, %(parent_id)s, %(url)s)
        returning id
        '''
        if parent_id:
            qSelect = '''
            select id
              from public.category
             where name = %s and project_id = %s and parent_id = %s
            '''
            args = [category_name, self.project_id, parent_id]
        else:
            qSelect = '''
            select id
              from public.category
             where name = %s and project_id = %s and parent_id is null
            '''
            args = [category_name, self.project_id]

        id = self.query_value(qSelect, args)
        if not id:
            id = self.query_value(qInsert, {'name': category_name, 'parent_id': parent_id,
                                            'project_id': self.project_id, 'url': url})
        return id

    def get_attribute_category_id(self, name, description=None):
        qInsert = '''
        insert into public.attribute_category(project_id, name, description)
        values (%(project_id)s, %(name)s, %(description)s)
        returning id
        '''
        qSelect = '''
        select id
          from attribute_category
         where project_id = %(project_id)s
           and name = %(name)s
        '''
        id = self.query_value(qSelect, {'project_id': self.project_id, 'name': name})

        if not id:
            id = self.query_value(qInsert, {'project_id': self.project_id, 'name': name,
                                            'description': description})
        return id

    def update_product_name(self, sku, name):
        qUpdate = '''
        update public.product set name = %(name)s where sku = %(sku)s and project_id = %(project_id)s
        '''
        self.execute(qUpdate, {'name': name, 'sku': sku, 'product_id': self.project_id})

    def get_product_id(self, product_name, categories, sku, url, manufacturer_id=None, price=None):
        qInsert = '''
        insert into public.product (project_id, sku, name, url, manufacturer_id, price)
        values (%(project_id)s, %(sku)s, %(name)s, %(url)s, %(manufacturer_id)s, %(price)s)
        returning id
        '''
        bAlreadyExists = True

        # Do we have a product with the same SKU but different URL? If yes, raise the error
        if sku is not None:
            product_ = self.query_row('select sku, url from product where project_id = %s and url != %s and sku = %s', [self.project_id, url, sku])
            if product_ is not None:
                raise Exception('Product with the same SKU but different URL has been found. SKU = %s, ' \
                                'new URL %s, existing URL %s' % (sku, url, product_['url']))

        # Product search algorithm
        # 1. Use SKU if it is provided
        # 2. If we don't know the SKU try to use name and manufactirer
        # 3. If manufacturer is not provided we use only product name

        if sku is not None:
            id = self.query_value('select id from public.product where project_id = %s and sku = %s',
                                  [self.project_id, sku])
        elif manufacturer_id is not None:
            id = self.query_value('select id from public.product where project_id = %s and name = %s and manufacturer_id = %s',
                                  [self.project_id, product_name, manufacturer_id])
        else:
            id = self.query_value('select id from public.product where project_id = %s and name = %s',
                                  [self.project_id, product_name])
        if not id:
            bAlreadyExists = False
            id = self.query_value(qInsert, {'project_id': self.project_id, 'sku': sku,
                                            'name': product_name, 'url': url,
                                            'manufacturer_id': manufacturer_id,
                                            'price': price})
        # Update product to category link even if it is found in the database
        for category_id in categories:
            self.add_product_to_category(id, category_id)

        return (id, bAlreadyExists,)

    def add_product_to_category(self, product_id, category_id):
        """
        Adds product to category
        """
        qInsert = '''
        insert into public.product_category (project_id, product_id, category_id)
        select %(project_id)s, %(product_id)s, %(category_id)s
        where not exists (
            select *
              from public.product_category
             where project_id = %(project_id)s and
                   product_id = %(product_id)s and
                   category_id = %(category_id)s
        )
        '''
        self.execute(qInsert, {'project_id': self.project_id,
                               'product_id': product_id,
                               'category_id': category_id})

    def add_product_image(self, product_id, url, priority):
        """
        Add new product image into database
        """
        qSet = '''select public.set_product_image(%(project_id)s, %(product_id)s, %(url)s, %(priority)s)'''
        id = self.query_value(qSet, {'project_id': self.project_id, 'url': url,
                                     'priority': priority, 'product_id': product_id})

        return id

    def set_product_description(self, product_id, description):
        return self.add_product_description(product_id, description)

    def add_product_description(self, product_id, description):
        """
        Add description to product
        """
        qSet = '''
        select public.set_product_description (%(project_id)s, %(product_id)s, %(description)s)
        '''
        id = self.query_value(qSet, {'project_id': self.project_id, 'product_id': product_id,
                                     'description': description})
        return id

    def get_attribute_id(self, attribute_name, attribute_category_id=None, description=None, use_cache=False):
        """
        Returns ID of attributes, creates it if one not exists
        """
        if use_cache and (attribute_name, attribute_category_id,) in self.cache['attributes']:
            return self.cache['attributes'][(attribute_name, attribute_category_id,)]

        qGetAttribute = '''
        select id
          from public.attribute
         where project_id = %(project_id)s
           and name = %(name)s
           and (attribute_category_id = %(attribute_category_id)s or %(attribute_category_id)s is null)
        '''
        qInsert = '''
        insert into public.attribute(project_id, name, attribute_category_id, description)
        values (%(project_id)s, %(name)s, %(attribute_category_id)s, %(description)s)
        returning id
        '''

        data = {'project_id': self.project_id, 'name': attribute_name,
                'attribute_category_id': attribute_category_id, 'description': description}

        id = self.query_value(qGetAttribute, data) or self.query_value(qInsert, data)

        if use_cache:
            if id is None:
                logger.warning('%s, %s, %s', attribute_name, attribute_category_id, description)
                raise Exception('Trying to insert NULL!')
            self.cache['attributes'].update({(attribute_name, attribute_category_id,): id})

        return id

    def set_attribute_value(self, product_id, attribute_id, value, priority=0):
        """
        Sets attribute value
        """
        qUpdate = '''
        select public.set_attribute_value(%(project_id)s, %(product_id)s, %(attribute_id)s, %(value)s, %(priority)s)
        '''
        id = self.query_value(qUpdate, {'project_id': self.project_id, 'product_id': product_id,
                                        'attribute_id': attribute_id, 'value': str(value),
                                        'priority': priority})
        return id

    def set_bulk_attribute_value(self, values):
        """
        Set bulk attribute value
        """
        # TODO: Use adapter to bind variables into cursor
        def escape(s):
            return s.replace("'", "''")

        qQuery = '''
        select public.set_bulk_attribute_value(%s, %s::t_attribute_value[])
        '''
        avalues = 'array[%s]' % ', '.join('(%s)' % ','.join("'%s'" % escape(str(i)) for i in row) for row in values)
        self.execute(qQuery % (self.project_id, avalues), None)

    def add_product_option(self, product_id, option_id):
        """
        Adds product option
        """
        qAddOption = 'select public.add_product_option(%(project_id)s, %(product_id)s, %(option_id)s)'

        self.execute(qAddOption, {'project_id': self.project_id,
                                  'product_id': product_id,
                                  'option_id': option_id})

    def get_manufacturer_id(self, name):
        """
        Returns ID of manufacturer with name = name, create new one if not exists
        """
        qGetManufacturerId = 'select public.get_manufacturer_id(%(project_id)s, %(name)s)'

        return self.query_value(qGetManufacturerId, {'project_id': self.project_id,
                                                     'name': name})

    def get_option_id(self, name):
        """
        Returns option ID
        """
        qGetOptionId = 'select public.get_option_id(%(project_id)s, %(name)s)'

        return self.query_value(qGetOptionId, {'project_id': self.project_id,
                                               'name': name})

    def update_product_at_diagram(self, product_id, diagram, lookup_no):
        """
        Updated product on diagram
        """
        qId = '''
            select extension.update_product_at_diagram
            (
                %(project_id)s,
                %(product_id)s,
                %(diagram)s,
                %(lookup_no)s
            )
        '''
        return self.query_value(qId, {'project_id': self.project_id, 'product_id': product_id,
                                      'diagram': diagram, 'lookup_no': lookup_no})

    def update_product_at_diagram2(self, partnumber, vehicle_id, diagram, lookup_no):
        """
        Updated product on diagram
        """
        qId = '''
            select extension.update_product_at_diagram2
            (
                %(partnumber)s,
                %(diagram)s,
                %(vehicle_id)s,
                %(lookup_no)s
            )
        '''
        return self.query_value(qId, {'partnumber': partnumber, 'vehicle_id': vehicle_id,
                                      'diagram': diagram, 'lookup_no': lookup_no})
