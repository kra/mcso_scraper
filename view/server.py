from flask import Flask, g, render_template, helpers, request
import sqlite3
import json
import datetime
import urllib

import mcso.spiders.mcso_spider

app = Flask(__name__)

# must match mcso/settings.py
DATA_DIRNAME = '../data'
SQLITE_FILENAME = '/'.join([DATA_DIRNAME, 'db'])
MUGSHOT_DIRNAME = '/'.join([DATA_DIRNAME, 'mugshots'])

def connect_db():
    conn = sqlite3.connect(SQLITE_FILENAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

def rows(cur):
    def row_to_dict(row):
        return dict([(k, row[k]) for k in row.keys()])
    return [row_to_dict(row) for row in cur]

def data_tables_json(items, secho, count):
    """ return a JSON structure suitable for display by a DataTable """
    return json.dumps(
        {"sEcho": secho,
         "iTotalRecords": count,
         "iTotalDisplayRecords": count, # XXX no filtering
         "aaData": items})

def booking_index_rows(cur):
    index_rows = rows(cur)
    # XXX should do this in the view, or maybe InmateItem
    for row in index_rows:
        row['name_link'] = (
            "<a href='/booking?booking=" + str(row['rowid']) + "'>" +
            row['name'] + '</a>')
    return index_rows

def charge_index_rows(cur):
    index_rows = rows(cur)
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
    (booking_row,) = rows(g.db.execute(
        'SELECT rowid, * FROM bookings WHERE rowid=?', (bookingid,)))
    # XXX should use InmateItem for this
    # booking_row['mugshot_filename'] = (
    #     mcso.spiders.mcso_spider.booking_mugshot_path(
    #         booking_row['rowid']))
    booking_row['mugshot_path'] = booking_row['rowid']
    # XXX should be a model for this kind of thing
    case_rows = rows(g.db.execute(
            'SELECT rowid, * FROM cases WHERE booking_id=?',
            [booking_row['rowid']]))
    for case_row in case_rows:
        charge_rows = rows(g.db.execute(
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
    path = '/'.join((MUGSHOT_DIRNAME, path))
    return helpers.send_from_directory(path, mugshotid)

def query_mods(columns):
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
    # NOT using sql parameter substitution.  All templated values must be
    # lookups, inted, or otherwise filtered!
    return 'ORDER BY %s %s LIMIT %s, %s' % (
        sort_col, sort_dir, offset, length)

@app.route('/data/booking_index')
def data_booking_index():
    secho = request.args.get('sEcho')

    columns = ["name", "age", "swisid", "race",
               "gender", "parsed_arrestdate",
               "parsed_bookingdate", "assignedfac",
               "arrestingagency", "currentstatus"]
    mods = query_mods(columns)
    query = (
        'SELECT '
        'rowid, name, age, swisid, race, gender, parsed_arrestdate, '
        'bookingdate, parsed_bookingdate, '
        'assignedfac, arrestingagency, currentstatus '
        'FROM bookings')
    query = ' '.join((query, mods))
    count = g.db.execute('SELECT COUNT(rowid) FROM bookings').next()[0]
    rows = booking_index_rows(g.db.execute(query))
    rows = [[row["name_link"], row["age"], row["swisid"], row["race"],
             row["gender"], row["parsed_arrestdate"],
             row["parsed_bookingdate"], row["assignedfac"],
             row["arrestingagency"], row["currentstatus"]]
            for row in rows]
    return data_tables_json(rows, secho, count)

# XXX we get the entire set each call and let the datatable filter/sort it;
#     switch to server-side to make this more efficient.
@app.route('/data/charge_index')
def data_charge_index():
    return json.dumps(charge_index_rows(g.db.execute(
        'SELECT bookings.rowid, bookings.swisid, '
        'bookings.arrestdate, bookings.bookingdate, '
        'charges.charge, charges.bail, charges.status '
        'FROM charges '
        'JOIN cases ON charges.case_id = cases.rowid '
        'JOIN bookings ON cases.booking_id = bookings.rowid')))

@app.route('/booking_index')
def booking_index():
    return render_template('booking_index.html')

@app.route('/charge_index')
def charge_index():
    return render_template('charge_index.html')

@app.route('/')
def index():
    (bookings_count,) = rows(g.db.execute(
        'SELECT COUNT(rowid) FROM bookings'))
    bookings_count = bookings_count['COUNT(rowid)']
    day_1 = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    day_7 = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    (bookings_1_count,) = rows(g.db.execute(
        'SELECT COUNT(rowid) FROM bookings WHERE updated_on>?',
        (day_1.strftime('%Y-%m-%d %H:%M:%S'),)))
    bookings_1_count = bookings_1_count['COUNT(rowid)']
    (bookings_7_count,) = rows(g.db.execute(
        'SELECT COUNT(rowid) FROM bookings WHERE updated_on>?',
        (day_7.strftime('%Y-%m-%d %H:%M:%S'),)))
    bookings_7_count = bookings_7_count['COUNT(rowid)']

    return render_template(
        'index.html',
        bookings_count=bookings_count,
        bookings_1_count=bookings_1_count,
        bookings_7_count=bookings_7_count)

if __name__ == '__main__':
    #app.run(host='0.0.0.0')
    app.run(debug=True)
