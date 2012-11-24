#!/usr/bin/env python

import sys

from scrapy.conf import settings
import common

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
    conn = common.db.get_conn()

    deactivate_user(conn, username)
