#!/usr/bin/env python

import sqlite3
import sys

from scrapy.conf import settings
#from common import users

def deactivate_user(conn, username):
    conn.execute(
        'UPDATE users SET active=0 WHERE name=?',
        (username,))
    conn.commit()

if __name__ == '__main__':
    try:
        [username] = sys.argv[1:]
    except ValueError:
        print 'usage: deactivate_user username'
        sys.exit(1)
    conn = sqlite3.connect(settings['SQLITE_FILENAME'])

    deactivate_user(conn, username)
