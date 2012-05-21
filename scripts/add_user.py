#!/usr/bin/env python

import sqlite3
import sys

from scrapy.conf import settings
from common import users

def add_user(conn, username, password):
    conn.execute(
        'INSERT INTO users (name, password, active) VALUES (?, ?, 1)',
        (username, users.password_create(password)))
    conn.commit()

if __name__ == '__main__':
    try:
        [username, password] = sys.argv[1:]
    except ValueError:
        print 'usage: add_user username password'
        sys.exit(1)
    conn = sqlite3.connect(settings['SQLITE_FILENAME'])

    add_user(conn, username, password)
