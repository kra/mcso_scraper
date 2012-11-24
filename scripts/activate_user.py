#!/usr/bin/env python

import sys

from scrapy.conf import settings
import common

def activate_user(conn, username):
    conn.execute(
        'UPDATE users SET active=1 WHERE name=?',
        (username,))
    conn.commit()

if __name__ == '__main__':
    try:
        [username] = sys.argv[1:]
    except ValueError:
        print 'usage: deactivate_user username'
        sys.exit(1)
    conn = common.db.get_conn()
    activate_user(conn, username)
