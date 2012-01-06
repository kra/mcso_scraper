from flask import Flask, g, render_template
import sqlite3
import json
import datetime

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

def booking_index_rows(cur):
    index_rows = rows(cur)
    # XXX should do this in the view, or maybe a model
    for row in index_rows:
        row['name_link'] = (
            "<a href='/booking?booking=" + row['swisid'] + "'>" +
            row['name'] + '</a>')
    return index_rows

def charge_index_rows(cur):
    index_rows = rows(cur)
    # XXX should do this in the view, or maybe a model
    for row in index_rows:
        row['charge_link'] = (
            "<a href='/booking?booking=" + str(row["swisid"]) + "'>" +
            row['charge'] + '</a>')
    return index_rows

@app.route('/data/booking/<swisid>')
def data_booking(swisid):
    # XXX not sure swisid is unique, it could be per inmate or otherwise reused,
    #     this will raise if we get a dup
    (booking_row,) = rows(g.db.execute(
        'SELECT rowid, * FROM bookings WHERE swisid=?', [swisid]))
    # XXX should be a model for this kind of thing
    #booking_row['mugshot_url'] = booking_row['siw
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

@app.route('/data/mugshots/<mugshotid>')
def booking_mugshot(mugshotid):
    # use send_file or send_from_directory
    # http://stackoverflow.com/questions/4239825/static-files-in-flask-robot-txt-sitemap-xml-mod-wsgi
    return None

# XXX we get the entire set each call and let the datatable filter/sort it;
#     switch to server-side to make this more efficient.
@app.route('/data/booking_index')
def data_booking_index():
    return json.dumps(booking_index_rows(g.db.execute(
        'SELECT '
        'rowid, name, age, swisid, race, gender, arrestdate, arrestingagency '
        'FROM bookings')))

# XXX we get the entire set each call and let the datatable filter/sort it;
#     switch to server-side to make this more efficient.
@app.route('/data/charge_index')
def data_charge_index():
    return json.dumps(charge_index_rows(g.db.execute(
        'SELECT bookings.swisid, charges.charge, charges.bail, charges.status '
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
