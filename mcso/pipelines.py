from scrapy.conf import settings
import sqlite3
import os

# records in sql, images in fs
# contrib.pipeline.images.FSImagesStore
# sqlite: db size limited by single file size - ext3 2TB ext4 16TB

# conn.row_factory = sqlite3.Row
# cursor = conn.cursor()
# cursor.execute('select rowid, * from bookings')
# row = cursor.fetchone()
# row['rowid']

class McsoPipeline(object):

    def __init__(self):
        self.conn = self.get_conn()

    def get_conn(self):
        # assume / pathsep
        sql_filename = '/'.join(
            (os.path.dirname(os.path.abspath(__file__)),
             settings['SQLITE_FILENAME']))
        return sqlite3.connect(sql_filename)

    def process_item(self, item, spider):
        self.write_mugshot(item)
        cursor = self.conn.cursor()
        # create/replace new booking
        cursor.execute(
            'REPLACE INTO bookings '
            '(url, swisid, name, age, gender, race, '
            'height, weight, hair, eyes, arrestingagency, '
            'arrestdate, bookingdate, currentstatus, assignedfac, '
            'projreldate, releasedate, releasereason) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (item.get('url'), item.get('swisid'), item.get('name'), item.get('age'),
             item.get('gender'), item.get('race'), item.get('height'), item.get('weight'),
             item.get('hair'), item.get('eyes'), item.get('arrestingagency'),
             item.get('arrestdate'), item.get('bookingdate'), item.get('currentstatus'),
             item.get('assignedfac'), item.get('projreldate'),
             item.get('releasedate'), item.get('releasereason')))
        ((booking_id,),) = cursor.execute(
            'SELECT rowid FROM bookings WHERE swisid=?', (item['swisid'],))
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
        return item

    # XXX there is probably an async pipeline helper
    def write_mugshot(self, item):
        """ write mugshot to file and return it's ID """
        # XXX assume swisid is unique
        # XXX this should be on a model
        mugshot_id = item['swisid']
        # mugshot files are partitioned by 2 1-char prefix subdirs
        mugshot_dir = '/'.join(
            (os.path.dirname(os.path.abspath(__file__)),
             settings['MUGSHOT_DIRNAME'],
             mugshot_id[0],
             mugshot_id[1]))
        mugshot_filename = '/'.join((mugshot_dir, mugshot_id))
        mugshot_file = open(mugshot_filename, 'wb')
        item['mugshot'].seek(0)

        while True:
            buf = item['mugshot'].read(65536)
            if len(buf) == 0:
                break
            mugshot_file.write(buf)
        mugshot_file.close()

        return mugshot_id
