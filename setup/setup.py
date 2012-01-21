"""
Set up database.
To be run once, will need a schema version and migrations at some point.
"""

import sqlite3
import os
import string

# must match msco/settings.py

DATA_DIRNAME = '../data'
SQLITE_FILENAME = '/'.join([DATA_DIRNAME, 'db'])
MUGSHOT_DIRNAME = '/'.join([DATA_DIRNAME, 'mugshots'])

def get_conn():
    sql_filename = '/'.join(
        (os.path.dirname(os.path.abspath(__file__)), SQLITE_FILENAME))
    return sqlite3.connect(sql_filename)

def setup_fs():
    mugshot_dirname = '/'.join(
        (os.path.dirname(os.path.abspath(__file__)), MUGSHOT_DIRNAME))
    # partition by prefix of booking_id, which starts with swisid,
    # which is all digits, variable length,
    # so make 2 partitions for now, each 1 char prefix
    for dirname1 in string.digits:
        for dirname2 in string.digits:
            os.makedirs('/'.join((mugshot_dirname, dirname1, dirname2)))

def update(conn):
    """
    Bring database to current schema.
    """
    # currently just one schema version, must check/update when we have real
    # migrations

    # create, init config table for schema
    conn.execute('CREATE TABLE config (name TEXT, value INTEGER)')
    conn.execute('INSERT INTO config VALUES ("schema", 0)')

    # create data tables
    conn.execute(
        'CREATE TABLE charges '
        '(case_id INTEGER, charge TEXT, bail TEXT, status TEXT)')
    conn.execute(
        'CREATE TABLE cases '
        '(booking_id INTEGER, '
        'court_case_number TEXT, da_case_number TEXT, citation_number TEXT)')
    conn.execute(
        'CREATE TABLE bookings '
        '(mugshot_url TEXT, url TEXT, swisid TEXT, name TEXT, age TEXT, '
        'gender TEXT, race TEXT, height TEXT, weight TEXT, hair TEXT, '
        'eyes TEXT, arrestingagency TEXT, arrestdate TEXT, bookingdate TEXT, '
        'currentstatus TEXT, assignedfac TEXT, projreldate TEXT, '
        'releasedate TEXT, releasereason TEXT, '
        'parsed_arrestdate TEXT, parsed_bookingdate TEXT, '
        'parsed_projreldate TEXT, parsed_releasedate TEXT, '
        'updated_on TEXT default CURRENT_TIMESTAMP, '
        'PRIMARY KEY (swisid, arrestdate))')

    # update config table to reflect current schema version
    conn.execute('UPDATE config SET value=1 WHERE name="schema"')

if __name__ == '__main__':
    setup_fs()
    conn = get_conn()
    update(conn)
