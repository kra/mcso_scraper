#!/usr/bin/env python

import sys

from scrapy.conf import settings
import common

def show_users(conn):
    for (name, active) in conn.execute('SELECT name, active FROM users'):
        print name, 'active' if active else 'inactive'

if __name__ == '__main__':
    conn = common.db.get_conn()
    show_users(conn)
