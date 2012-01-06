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
            'arrestdate, bookingdate, currentstatus, assignedfac, projreldate) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (item['url'], item['swisid'], item['name'], item['age'],
             item['gender'], item['race'], item['height'], item['weight'],
             item['hair'], item['eyes'], item['arrestingagency'],
             item['arrestdate'], item['bookingdate'], item['currentstatus'],
             item['assignedfac'], item['projreldate']))
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
        for case in item['cases']:
            cursor.execute(
                'INSERT INTO cases VALUES (?, ?, ?, ?)',
                (booking_id,
                 case['court_case_number'],
                 case['da_case_number'],
                 case['citation_number']))
            case_id = cursor.lastrowid
            for charge in case['charges']:
                cursor.execute(
                    'INSERT INTO charges VALUES (?, ?, ?, ?)',
                    (case_id, charge['charge'],
                     charge['bail'],
                     charge['status']))
        self.conn.commit()
        return item

    # XXX there is probably an async pipeline helper
    def write_mugshot(self, item):
        """ write mugshot to file and return it's ID """
        # XXX assume swisid is unique
        mugshot_id = item['swisid']
        mugshot_filename = '/'.join(
            (os.path.dirname(os.path.abspath(__file__)),
             settings['MUGSHOT_DIRNAME'],
             mugshot_id))
        mugshot_file = open(mugshot_filename, 'wb')
        item['mugshot'].seek(0)

        while True:
            buf = item['mugshot'].read(65536)
            if len(buf) == 0:
                break
            mugshot_file.write(buf)
        mugshot_file.close()

        return mugshot_id


