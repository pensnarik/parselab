# -*- coding: utf-8 -*-

import time
import psycopg2
import psycopg2.extensions
import psycopg2.extras
import logging

logger = logging.getLogger(__name__)

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)


class Database(object):

    conn = None

    def __init__(self):
        pass

    def connect(self, conn):
        # If we want to reconnect, we need to save conn for further using
        if self.conn is None:
            self.conn = conn
        self.__conn = psycopg2.connect(conn)
        self.__conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    def close(self):
        self.__conn.close()

    def reconnect(self):
        logger.error('Connection error, trying to reconnect')
        self.connect(self.conn)

    def execute_cursor(self, cursor, query, params=None, fetch=True, dict=False):
        while True:
            try:
                if params is not None:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if fetch is True:
                    fetch_result = cursor.fetchall()
                else:
                    fetch_result = None
            except psycopg2.OperationalError:
                time.sleep(5)
                self.reconnect()
                if dict:
                    cursor = self.__conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                else:
                    cursor = self.__conn.cursor()
                continue
            else:
                break
        return fetch_result

    def query(self, query):
        cursor = self.__conn.cursor()
        data = self.execute_cursor(cursor, query, fetch=True)
        cursor.close()
        return data

    def query_dict(self, query, params=None):
        cursor = self.__conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        data = self.execute_cursor(cursor, query, params, fetch=True, dict=True)
        cursor.close()
        return [row for row in data]

    def query_row(self, query, params=None):
        cursor = self.__conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        data = self.execute_cursor(cursor, query, params, fetch=False, dict=True)
        row = cursor.fetchone()
        cursor.close()
        return row

    def query_value(self, query, params=None):
        result = self.query_dict(query, params)
        if result:
            return result[0][0]
        else:
            return None

    def execute(self, query, params):
        cursor = self.__conn.cursor()
        self.execute_cursor(cursor, query, params, fetch=False)
        cursor.close()
        return

db = Database()

class DatabaseHandler(logging.Handler):

    sql = '''
    insert into core.log (message, module, level, traceback)
    values (%(message)s, %(module)s, %(level)s, %(traceback)s)
    '''

    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        self.format(record)
        if record.exc_info:
            traceback = logging._defaultFormatter.formatException(record.exc_info)
        else:
            traceback = ''

        db.execute(self.sql, {'message': record.message, 'module': record.module,
            'level': record.levelname.lower(), 'traceback': traceback})
