from scrapy.conf import settings
import sqlite3
import os

class McsoPipeline(object):

    def __init__(self):
        self.conn = self.get_conn()

    def get_conn(self):
        return sqlite3.connect(settings['SQLITE_FILENAME'])

    def process_item(self, item, spider):
        cursor = self.conn.cursor()
        # create/replace new booking
        cursor.execute(
            'REPLACE INTO bookings '
            '(url, swisid, name, age, gender, race, '
            'height, weight, hair, eyes, arrestingagency, '
            'arrestdate, parsed_arrestdate, '
            'bookingdate, parsed_bookingdate, currentstatus, assignedfac, '
            'projreldate, parsed_projreldate, releasedate, parsed_releasedate, '
            'releasereason, mugshot_url) '
            'VALUES '
            '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '
            '?, ?, ?, ?, ?)',
            (item.get('url'), item.get('swisid'), item.get('name'),
             item.get('age'),
             item.get('gender'), item.get('race'), item.get('height'),
             item.get('weight'),
             item.get('hair'), item.get('eyes'), item.get('arrestingagency'),
             item.get('arrestdate'),
             item.parsed_date(item.get('arrestdate')),
             item.get('bookingdate'),
             item.parsed_date(item.get('bookingdate')),
             item.get('currentstatus'),
             item.get('assignedfac'),
             item.get('projreldate'),
             item.parsed_date(item.get('projreldate')),
             item.get('releasedate'),
             item.parsed_date(item.get('releasedate')),
             item.get('releasereason'),
             item.get('mugshot_url')))
        # primary key is swisid + bookingdate
        ((booking_id,),) = cursor.execute(
            'SELECT rowid FROM bookings WHERE swisid=? AND bookingdate=?',
            (item['swisid'], item['bookingdate']))
        # delete any existing associated rows
        cursor.execute(
            'DELETE FROM charges '
            'WHERE case_id IN '
            '(SELECT rowid FROM cases WHERE booking_id=?)', (booking_id,))
        cursor.execute(
            'DELETE FROM cases WHERE booking_id=?', (booking_id,))
        # add or re-add new cases, charges
        for case in item.get('cases'):
            cursor.execute(
                'INSERT INTO cases VALUES (?, ?, ?, ?)',
                (booking_id,
                 case.get('court_case_number'),
                 case.get('da_case_number'),
                 case.get('citation_number')))
            case_id = cursor.lastrowid
            for charge in case.get('charges', []):
                cursor.execute(
                    'INSERT INTO charges VALUES (?, ?, ?, ?)',
                    (case_id, charge.get('charge'),
                     charge.get('bail'),
                     charge.get('status')))
        self.conn.commit()
        item['booking_id'] = booking_id
        self.write_mugshot(item)
        return item

    # XXX there is probably an async pipeline helper
    def write_mugshot(self, item):
        """ write mugshot to file and return it's ID """
        mugshot_filename = '/'.join(
            (settings['MUGSHOT_DIRNAME'], item.mugshot_path()))
        mugshot_file = open(mugshot_filename, 'wb')
        item['mugshot'].seek(0)

        while True:
            buf = item['mugshot'].read(65536)
            if len(buf) == 0:
                break
            mugshot_file.write(buf)
        mugshot_file.close()
