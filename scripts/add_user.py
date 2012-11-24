#!/usr/bin/env python

import sys

from scrapy.conf import settings
import common

def add_user(conn, username, password):
    conn.execute(
        'INSERT INTO users (name, password, active) VALUES (?, ?, 1)',
        (username, common.users.password_create(password)))
    conn.commit()

if __name__ == '__main__':
    try:
        [username, password] = sys.argv[1:]
    except ValueError:
        print 'usage: add_user username password'
        sys.exit(1)
    conn = common.db.get_conn()
    add_user(conn, username, password)
