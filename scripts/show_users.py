#!/usr/bin/env python

import sqlite3
import sys

from scrapy.conf import settings
from common import users

def show_users(conn):
    for (name, active) in conn.execute('SELECT name, active FROM users'):
        print name, 'active' if active else 'inactive'

if __name__ == '__main__':
    conn = sqlite3.connect(settings['SQLITE_FILENAME'])

    show_users(conn)
