from flask import Flask, g, render_template
import sqlite3
import json

app = Flask(__name__)

# must match mcso/settings.py
DATABASE = '../data/db'

def connect_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

@app.route('/data/booking/<swisid>')
def data_booking(swisid):
    def row_to_dict(row):
        return dict([(k, row[k]) for k in row.keys()])
    def rows(cur, one=False):
        rows = [row for row in cur]
        if one:
            (row,) = rows
            return row_to_dict(row)
        return [row_to_dict(row) for row in rows]
    # XXX not sure swisid is unique, it could be per inmate or otherwise reused
    #     rows() will raise if we get a dup
    booking_row = rows(g.db.execute(
        'SELECT rowid, * FROM bookings WHERE swisid=?', [swisid]), one=True)
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

if __name__ == '__main__':
    #app.run(host='0.0.0.0')
    app.run(debug=True)
