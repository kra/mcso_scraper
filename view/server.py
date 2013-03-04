#!/usr/bin/env python

from flask import Flask, flash, g, render_template, helpers, request, abort
from flask import redirect, url_for
from flask.ext.login import LoginManager, login_required
from flask.ext.login import login_user, logout_user, current_user

import json
import datetime
import urllib

import mcso.spiders.mcso_spider
from scrapy.conf import settings
import common

app = Flask(__name__)
login_manager = LoginManager()
app.secret_key = settings['SECRET_KEY']
login_manager.setup_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(id):
    # XXX do we need a seprate conn?
    conn = common.db.get_conn()
    user = common.users.get_user_id(conn, int(id))
    conn.close()
    return user

# DB setup stuff

@app.before_request
def before_request():
    g.db = common.db.get_conn()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

# helpers

def render(template, *args, **kwargs):
    return render_template(template, current_user=current_user, *args, **kwargs)

def data_tables_json(items, secho, count_all, count_rows):
    """ return a JSON structure suitable for display by a DataTable """
    return json.dumps(
        {"sEcho": secho,
         "iTotalRecords": count_all,
         "iTotalDisplayRecords": count_rows,
         "aaData": items})

def booking_index_rows(cur):
    index_rows = common.db.row_ds(cur)
    # XXX should do this in the view, or maybe InmateItem
    for row in index_rows:
        row['name_link'] = (
            "<a href='/booking?booking=" + str(row['rowid']) + "'>" +
            row['name'] + '</a>')
    return index_rows

def charge_index_rows(cur):
    index_rows = common.db.row_ds(cur)
    # XXX should do this in the view, or maybe InmateItem
    for row in index_rows:
        # XXX should use InmateItem
        row['charge_link'] = (
            "<a href='/booking?booking=" + str(row['rowid']) + "'>" +
            row['charge'] + '</a>')
    return index_rows

def query_sort_args(columns):
    """
    Return injection-safe (sort_col, sort_dir, offset, length)
    from given sort columns and request.
    Assume column names are injection-safe.
    """
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
    """
    Return injection-safe sort clause from given sort columns and request.
    """
    return 'ORDER BY %s %s LIMIT %s, %s' % query_sort_args(columns)

def query_filter(field, start, end):
    """
    Return an injection-safe query clause and args
    to filter the given datetime field by the given
    columnFilter datetime values.
    Assume field is injection-safe.
    """
    # assume date picker validates
    if start or end:
        args = []
        clauses = []
        if start:
            start = '%s 00:00:00' % start
            clauses.append('%s >= ?' % field)
            args.append(start)
        if end:
            end = '%s 23:59:59' % end
            clauses.append('%s <= ?' % field)
            args.append(end)
        return ('WHERE ' + ' AND '.join(clauses), args)
    return ('', [])

# URL handlers

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        password = request.form["password"]
        remember = request.form.get("remember", "no") == "yes"
        user = common.users.get_user_username(g.db, username)
        if (user
            and common.users.auth_user(user, password)
            and login_user(user, remember=remember)):
            flash("Logged in.")
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash("Could not log in.", category="error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/data/booking/<bookingid>')
@login_required
def data_booking(bookingid):
    # bookingid = urllib.unquote(bookingid)
    (booking_row,) = common.db.row_ds(g.db.execute(
            'SELECT rowid, * FROM bookings WHERE rowid=?', (bookingid,)))
    # XXX should use InmateItem for this
    # booking_row['mugshot_filename'] = (
    #     mcso.spiders.mcso_spider.booking_mugshot_path(
    #         booking_row['rowid']))
    booking_row['mugshot_path'] = booking_row['rowid']
    # XXX should be a model for this kind of thing
    case_rows = common.db.row_ds(g.db.execute(
            'SELECT rowid, * FROM cases WHERE booking_id=?',
            [booking_row['rowid']]))
    for case_row in case_rows:
        charge_rows = common.db.row_ds(g.db.execute(
                'SELECT rowid, * FROM charges WHERE case_id=?',
                [case_row['rowid']]))
        case_row['charges'] = charge_rows
    booking_row['cases'] = case_rows

    return json.dumps(booking_row)

@app.route('/booking')
@login_required
def booking():
    return render_template('booking.html')

# XXX ideally static files are served by a server in front of us
@app.route('/data/mugshots/<mugshotid>')
@login_required
def booking_mugshot(mugshotid):
    path = mcso.spiders.mcso_spider.booking_mugshot_dir(mugshotid)
    path = '/'.join((settings['MUGSHOT_DIRNAME'], path))
    return helpers.send_from_directory(path, mugshotid)

@app.route('/data/booking_index')
@login_required
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
    query_args = []
    sort_clause = query_sort(sort_columns)
    (filter_clause, filter_args) = query_filter(
        'parsed_bookingdate',
        request.args.get('booking_date_start'),
        request.args.get('booking_date_end'))
    query = ' '.join((query, filter_clause))
    query_args.extend(filter_args)
    query = ' '.join((query, sort_clause))
    count_all = g.db.execute('SELECT COUNT(rowid) FROM bookings').next()[0]
    if filter_clause:
        count_query = 'SELECT COUNT(rowid) FROM bookings'
        count_query = ' '.join((count_query, filter_clause))
        count_rows = g.db.execute(count_query, query_args).next()[0]
    else:
        count_rows = count_all
    rows = booking_index_rows(g.db.execute(query, query_args))
    rows = [[row["name_link"], row["age"], row["swisid"], row["race"],
             row["gender"], row["arrestdate"],
             row["bookingdate"], row["assignedfac"],
             row["arrestingagency"], row["currentstatus"]]
            for row in rows]
    return data_tables_json(rows, secho, count_all, count_rows)

@app.route('/data/charge_index')
@login_required
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
    query_args = []
    sort_clause = query_sort(sort_columns)
    (filter_clause, filter_args) = query_filter(
        'parsed_bookingdate',
        request.args.get('booking_date_start'),
        request.args.get('booking_date_end'))
    query = ' '.join((query, filter_clause))
    query_args.extend(filter_args)
    query = ' '.join((query, sort_clause))
    count_all = g.db.execute('SELECT COUNT(rowid) FROM charges').next()[0]
    if filter_clause:
        count_query = (
            'SELECT COUNT(charges.rowid) FROM charges '
            'JOIN cases ON charges.case_id = cases.rowid '
            'JOIN bookings ON cases.booking_id = bookings.rowid')
        count_query = ' '.join((count_query, filter_clause))
        count_rows = g.db.execute(count_query, query_args).next()[0]
    else:
        count_rows = count_all
    rows = charge_index_rows(g.db.execute(query, query_args))
    rows = [[row["charge_link"], row["status"], row["bail"],
             row["arrestdate"], row["bookingdate"]]
            for row in rows]
    return data_tables_json(rows, secho, count_all, count_rows)

@app.route('/data/health/booking_index')
@login_required
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

    # discard period starts until we're at the start of our ofset
    to_offset = offset
    while to_offset:
        periods.next()
        to_offset -= 1

    def period_healths(periods):
        """
        Yield counts of bookings in preceeding period intervals, starting
        with the most recent in the past.
        """
        # stop when we won't find bookings anymore
        (min_date,) = common.db.row_ds(
            g.db.execute('SELECT MIN(parsed_bookingdate) FROM bookings'))
        min_date = datetime.datetime.strptime(
            min_date['MIN(parsed_bookingdate)'], '%Y-%m-%d %H:%M:%S')
        # yield data between each two periods until we're before min_date
        end = periods.next()
        while True:
            start = periods.next()
            if end < min_date:
                raise StopIteration
            (updated_on,) = common.db.row_ds(g.db.execute(
                'SELECT COUNT(rowid) FROM bookings '
                'WHERE updated_on>? AND updated_on<?',
                (start.strftime('%Y-%m-%d %H:%M:%S'),
                 end.strftime('%Y-%m-%d %H:%M:%S'))))
            (parsed_bookingdate,) = common.db.row_ds(g.db.execute(
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
    # efficiency, we could figure this out some other way based on the earliest
    # available date.
    all_rows = [w for w in period_healths]
    rows = all_rows[:length]
    rows = [[row['period'],
             row['updated_on_count'],
             row['parsed_bookingdate_count']] for row in rows]
    return data_tables_json(
        rows, secho, len(all_rows) + offset, len(all_rows) + offset)

@app.route('/booking_index')
@login_required
def booking_index():
    return render_template('booking_index.html')

@app.route('/charge_index')
@login_required
def charge_index():
    return render_template('charge_index.html')

@app.route('/health/booking_index')
@login_required
def health_booking_index():
    return render_template('health_booking_index.html')

@app.route('/')
@login_required
def index():
    return render('index.html')

# main

if __name__ == '__main__':
    #app.run(host='0.0.0.0')
    #app.run(host='192.168.56.101')
    app.run(host='0.0.0.0', debug=True)
    #app.run(host='0.0.0.0', port=80, debug=True)
