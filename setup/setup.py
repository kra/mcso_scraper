"""
Set up database.
To be run once, will need a schema version and migrations at some point.
"""

import sqlite3
import os

# must match msco/settings.py

SQLITE_FILENAME = '../data/db'

def get_conn():
    # assume / pathsep
    sql_filename = '/'.join(
        (os.path.dirname(os.path.abspath(__file__)), SQLITE_FILENAME))
    return sqlite3.connect(sql_filename)

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
    # XXX assume swisid is unique
    conn.execute(
        'CREATE TABLE bookings '
        '(mugshot_id TEXT, url TEXT, swisid TEXT UNIQUE, name TEXT, age TEXT, '
        'gender TEXT, race TEXT, height TEXT, weight TEXT, hair TEXT, '
        'eyes TEXT, arrestingagency TEXT, arrestdate TEXT, bookingdate TEXT, '
        'currentstatus TEXT, assignedfac TEXT, projreldate TEXT, '
        'updated_on TEXT default CURRENT_TIMESTAMP)')

    # update config table to reflect current schema version
    conn.execute('UPDATE config SET value=1 WHERE name="schema"')

if __name__ == '__main__':
    conn = get_conn()
    update(conn)
