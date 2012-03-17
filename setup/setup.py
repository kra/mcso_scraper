"""
Set up or update storage.
Usage:
  setup.py boot
  setup.py
"""
import sqlite3
import os
import string

from scrapy.conf import settings

def get_conn():
    return sqlite3.connect(settings['SQLITE_FILENAME'])

def setup_fs():
    # partition by prefix of booking_id, which starts with swisid,
    # which is all digits, variable length,
    # so make 2 partitions for now, each 1 char prefix
    for dirname1 in string.digits:
        for dirname2 in string.digits:
            os.makedirs(
                '/'.join((settings['MUGSHOT_DIRNAME'], dirname1, dirname2)))

def setup_db(conn):
    # create, init config table for schema
    conn.execute('CREATE TABLE config (name TEXT, value INTEGER)')
    conn.execute('INSERT INTO config VALUES ("schema", 0)')

def update_schema_1(conn):
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
    conn.commit()

def update_schema_2(conn):
    conn.execute('ALTER TABLE charges ADD COLUMN parsed_bail NUMERIC')
    charge_rows = conn.execute('SELECT rowid, bail FROM charges')
    # update existing rows
    # keep as a string for sqlite's numeric affinity
    # XXX duplicates the item parsed_bail()
    for (rowid, bail) in charge_rows:
        parsed_bail = bail.replace('$', '').replace(',', '')
        conn.execute(
            'UPDATE charges SET parsed_bail=? WHERE rowid=?',
            (parsed_bail, rowid))

    # update config table to reflect current schema version
    conn.execute('UPDATE config SET value=2 WHERE name="schema"')
    conn.commit()

def get_schema(conn):
    ((schema,),) = conn.execute('SELECT value FROM config WHERE name="schema"')
    return schema

def update_db(conn):
    """
    Bring database to current schema.
    """
    print 'at schema', get_schema(conn)
    if get_schema(conn) < 1:
        print 'updating to schema 1'
        update_schema_1(conn)
    if get_schema(conn) < 2:
        print 'updating to schema 2'
        update_schema_2(conn)


if __name__ == '__main__':
    import sys
    conn = get_conn()
    if sys.argv[-1] == 'boot':
        setup_fs()
        setup_db(conn)
    update_db(conn)
