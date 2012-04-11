#!/usr/bin/env python

from flask import Flask, g, render_template, helpers, request, abort
import sqlite3
import json
import datetime
import urllib

import mcso.spiders.mcso_spider
from scrapy.conf import settings

app = Flask(__name__)

def connect_db():
    conn = sqlite3.connect(settings['SQLITE_FILENAME'])
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

def row_ds(cur):
    def row_to_dict(row):
        return dict([(k, row[k]) for k in row.keys()])
    return [row_to_dict(row) for row in cur]

def data_tables_json(items, secho, count_all, count_rows):
    """ return a JSON structure suitable for display by a DataTable """
    return json.dumps(
        {"sEcho": secho,
         "iTotalRecords": count_all,
         "iTotalDisplayRecords": count_rows,
         "aaData": items})

def booking_index_rows(cur):
    index_rows = row_ds(cur)
    # XXX should do this in the view, or maybe InmateItem
    for row in index_rows:
        row['name_link'] = (
            "<a href='/booking?booking=" + str(row['rowid']) + "'>" +
            row['name'] + '</a>')
    return index_rows

def charge_index_rows(cur):
    index_rows = row_ds(cur)
    # XXX should do this in the view, or maybe InmateItem
    for row in index_rows:
        # XXX should use InmateItem
        row['charge_link'] = (
            "<a href='/booking?booking=" + str(row['rowid']) + "'>" +
            row['charge'] + '</a>')
    return index_rows

@app.route('/data/booking/<bookingid>')
def data_booking(bookingid):
    # bookingid = urllib.unquote(bookingid)
    (booking_row,) = row_ds(g.db.execute(
        'SELECT rowid, * FROM bookings WHERE rowid=?', (bookingid,)))
    # XXX should use InmateItem for this
    # booking_row['mugshot_filename'] = (
    #     mcso.spiders.mcso_spider.booking_mugshot_path(
    #         booking_row['rowid']))
    booking_row['mugshot_path'] = booking_row['rowid']
    # XXX should be a model for this kind of thing
    case_rows = row_ds(g.db.execute(
            'SELECT rowid, * FROM cases WHERE booking_id=?',
            [booking_row['rowid']]))
    for case_row in case_rows:
        charge_rows = row_ds(g.db.execute(
                'SELECT rowid, * FROM charges WHERE case_id=?',
                [case_row['rowid']]))
        case_row['charges'] = charge_rows
    booking_row['cases'] = case_rows

    return json.dumps(booking_row)

@app.route('/booking')
def booking():
    return render_template('booking.html')

# XXX ideally static files are served by a server in front of us
@app.route('/data/mugshots/<mugshotid>')
def booking_mugshot(mugshotid):
    path = mcso.spiders.mcso_spider.booking_mugshot_dir(mugshotid)
    path = '/'.join((settings['MUGSHOT_DIRNAME'], path))
    return helpers.send_from_directory(path, mugshotid)

def query_sort_args(columns):
    # single-column sortable only
    # multi-col with _n and iSortingCols
    try:
        sort_col = columns[int(request.args.get('iSortCol_0'))]
    except TypeError:
        sort_col = columns[0]
    if request.args.get('sSortDir_0') == 'desc':
        sort_dir = 'DESC'
    else:
        sort_dir = 'ASC'
    try:
        offset = int(request.args.get('iDisplayStart'))
        length = int(request.args.get('iDisplayLength'))
    except TypeError:
        offset = 0
        length = 10
    return (sort_col, sort_dir, offset, length)

def query_sort(columns):
    return 'ORDER BY %s %s LIMIT %s, %s' % query_sort_args(columns)

def query_filter(field, start, end):
    """
    Return a query clause to sort the given datetime field by the given
    columnFilter datetime values.
    """
    # XXX this needs subsitution
    clauses = []
    # assume date picker validates
    if start or end:
        if start:
            start = '%s 00:00:00' % start
            clauses.append('%s >= "%s"' % (field, start))
        if end:
            end = '%s 23:59:59' % end
            clauses.append('%s <= "%s"' % (field, end))
        return ' AND '.join(clauses)
    return None

@app.route('/data/booking_index')
def data_booking_index():
    try:
        secho = int(request.args.get('sEcho'))
    except TypeError:
        secho = None

    sort_columns = ["name", "age", "swisid", "race",
                    "gender", "parsed_arrestdate",
                    "parsed_bookingdate", "assignedfac",
                    "arrestingagency", "currentstatus"]
    query = (
        'SELECT '
        'rowid, name, age, swisid, race, gender, arrestdate, '
        'bookingdate, assignedfac, arrestingagency, '
        'currentstatus '
        'FROM bookings')
    sort_clause = query_sort(sort_columns)
    filter_clause = query_filter(
        'parsed_bookingdate',
        request.args.get('booking_date_start'),
        request.args.get('booking_date_end'))
    if filter_clause:
        query = ' WHERE '.join((query, filter_clause))
    query = ' '.join((query, sort_clause))
    count_all = g.db.execute('SELECT COUNT(rowid) FROM bookings').next()[0]
    if filter_clause:
        count_rows = g.db.execute(
            ' WHERE '.join(
                ('SELECT COUNT(rowid) FROM bookings',
                 filter_clause))).next()[0]
    else:
        count_rows = count_all
    rows = booking_index_rows(g.db.execute(query))
    rows = [[row["name_link"], row["age"], row["swisid"], row["race"],
             row["gender"], row["arrestdate"],
             row["bookingdate"], row["assignedfac"],
             row["arrestingagency"], row["currentstatus"]]
            for row in rows]
    return data_tables_json(rows, secho, count_all, count_rows)

@app.route('/data/charge_index')
def data_charge_index():
    try:
        secho = int(request.args.get('sEcho'))
    except TypeError:
        secho = None

    sort_columns = ["charge", "status", "parsed_bail",
                    "parsed_arrestdate", "parsed_bookingdate"]
    query = (
        'SELECT bookings.rowid, bookings.swisid, '
        'bookings.arrestdate, bookings.bookingdate, '
        'charges.charge, charges.bail, charges.status '
        'FROM charges '
        'JOIN cases ON charges.case_id = cases.rowid '
        'JOIN bookings ON cases.booking_id = bookings.rowid')
    sort_clause = query_sort(sort_columns)
    filter_clause = query_filter(
        'parsed_bookingdate',
        request.args.get('booking_date_start'),
        request.args.get('booking_date_end'))
    if filter_clause:
        query = ' WHERE '.join((query, filter_clause))
    query = ' '.join((query, sort_clause))
    count_all = g.db.execute('SELECT COUNT(rowid) FROM charges').next()[0]
    if filter_clause:
        count_rows = g.db.execute(
            ' WHERE '.join(
                ('SELECT COUNT(charges.rowid) FROM charges '
                 'JOIN cases ON charges.case_id = cases.rowid '
                 'JOIN bookings ON cases.booking_id = bookings.rowid',
                 filter_clause))).next()[0]
    else:
        count_rows = count_all
    rows = charge_index_rows(g.db.execute(query))
    rows = [[row["charge_link"], row["status"], row["bail"],
             row["arrestdate"], row["bookingdate"]]
            for row in rows]
    return data_tables_json(rows, secho, count_all, count_rows)

@app.route('/data/health/booking_index')
def data_health_booking_index():
    period = request.args.get('period')
    if not period:
        period = 'week'
    if period not in ['week', 'day']:
        abort(400)

    try:
        secho = int(request.args.get('sEcho'))
    except TypeError:
        secho = None

    sort_columns = ['COUNT(rowid)']
    (sort_col, sort_dir, offset, length) = query_sort_args(sort_columns)
    if sort_dir != 'ASC':
        raise NotImplementedError

    def weeks():
        """
        Yield week beginning datetimes in descending order,
        starting with the most recent in the past.
        """
        # beginning of today
        now = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0)
        # beginning of this week
        now = now - datetime.timedelta(days=now.weekday())
        while True:
            yield now
            now = now - datetime.timedelta(days=7)

    def days():
        """
        Yield day beginning datetimes in descending order,
        starting with the most recent in the past.
        """
        # beginning of today
        now = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0)
        while True:
            yield now
            now = now - datetime.timedelta(days=1)

    if period == 'week':
        periods = weeks()
    else:
        periods = days()

    to_offset = offset
    while to_offset:
        periods.next()
        to_offset -= 1

    def period_healths(periods):
        """
        Yield counts of bookings in preceeding period intervals, starting
        with the most recent in the past.
        """
        (min_date,) = row_ds(
            g.db.execute('SELECT MIN(parsed_bookingdate) FROM bookings'))
        min_date = datetime.datetime.strptime(
            min_date['MIN(parsed_bookingdate)'], '%Y-%m-%d %H:%M:%S')
        end = periods.next()
        while True:
            start = periods.next()
            if end < min_date:
                raise StopIteration
            (updated_on,) = row_ds(g.db.execute(
                'SELECT COUNT(rowid) FROM bookings '
                'WHERE updated_on>? AND updated_on<?',
                (start.strftime('%Y-%m-%d %H:%M:%S'),
                 end.strftime('%Y-%m-%d %H:%M:%S'))))
            (parsed_bookingdate,) = row_ds(g.db.execute(
                'SELECT COUNT(rowid) FROM bookings '
                'WHERE parsed_bookingdate>? AND parsed_bookingdate<?',
                (start.strftime('%Y-%m-%d %H:%M:%S'),
                 end.strftime('%Y-%m-%d %H:%M:%S'))))
            out = {
                'updated_on_count':updated_on["COUNT(rowid)"],
                'parsed_bookingdate_count':parsed_bookingdate["COUNT(rowid)"],
                'period':start.strftime('%m/%d/%Y')}
            yield out
            end = start

    period_healths = period_healths(periods)
    # We have to spool out the generator to find the total length.  For
    # effieciency, we could find the earliest date when generating periods
    # and only spool out that generator.
    all_rows = [w for w in period_healths]
    rows = all_rows[:length]
    rows = [[row['period'],
             row['updated_on_count'],
             row['parsed_bookingdate_count']] for row in rows]
    return data_tables_json(
        rows, secho, len(all_rows) + offset, len(all_rows) + offset)

@app.route('/booking_index')
def booking_index():
    return render_template('booking_index.html')

@app.route('/charge_index')
def charge_index():
    return render_template('charge_index.html')

@app.route('/health/booking_index')
def health_booking_index():
    return render_template('health_booking_index.html')


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    #app.run(host='192.168.56.101')
    #app.run(debug=True)
