import sqlite3
from scrapy.conf import settings

def get_conn():
    conn = sqlite3.connect(settings['SQLITE_FILENAME'])
    conn.row_factory = sqlite3.Row
    return conn

def row_ds(cur):
    def row_to_dict(row):
        return dict([(k, row[k]) for k in row.keys()])
    return [row_to_dict(row) for row in cur]
