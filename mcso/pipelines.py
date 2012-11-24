from scrapy.conf import settings
import os
import common


class McsoPipeline(object):

    def __init__(self):
        self.conn = common.db.get_conn()

    def process_item(self, item, spider):
        item.validate()
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
        # primary key is swisid + arrestdate
        ((row_id,),) = cursor.execute(
            'SELECT rowid FROM bookings WHERE swisid=? AND arrestdate=?',
            (item['swisid'], item['arrestdate']))
        # delete any existing associated rows
        cursor.execute(
            'DELETE FROM charges '
            'WHERE case_id IN '
            '(SELECT rowid FROM cases WHERE booking_id=?)', (row_id,))
        cursor.execute(
            'DELETE FROM cases WHERE booking_id=?', (row_id,))
        # add or re-add new cases, charges
        for case in item.get('cases'):
            cursor.execute(
                'INSERT INTO cases '
                '(booking_id, court_case_number, da_case_number, '
                'citation_number) '
                'VALUES (?, ?, ?, ?)',
                (row_id,
                 case.get('court_case_number'),
                 case.get('da_case_number'),
                 case.get('citation_number')))
            case_id = cursor.lastrowid
            for charge in case.get('charges', []):
                cursor.execute(
                    'INSERT INTO charges '
                    '(case_id, charge, bail, parsed_bail, status) '
                    'VALUES (?, ?, ?, ?, ?)',
                    (case_id, charge.get('charge'),
                     charge.get('bail'), charge.parsed_bail(charge.get('bail')),
                     charge.get('status')))
        self.conn.commit()
        item['booking_id'] = row_id
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
