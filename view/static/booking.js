$(document).ready(function() {

    function mugshot_img(obj) {
        // return mugshot img tag for obj
        // XXX the view layer knows this, should be there
        path = obj['mugshot_path']
        return '<img src="' + '../data/mugshots/' + path + '"/>';
    }

    function orig_url(obj_url) {
        // return url for obj in a href tag
        return '<a href="' + obj_url + '">' + obj_url + '</a>';
    }

    function charge_table_row(charge) {
        row = '<tr>';
        row += '<td>' + charge['charge'] + '</td>';
        row += '<td>' + charge['bail'] + '</td>';
        row += '<td>' + charge['status'] + '</td>';
        row += '</tr>';            
        return row;
    }

    function charge_table(charges) {
        ctable = '<div id="charge_table"><table>';
        ctable += '<tr><td>Charge</td><td>Bail</td><td>Status</td></tr>';
        $.each(charges, function(index, charge_obj) {
            ctable += charge_table_row(charge_obj);
        });
        ctable += '</table></div>';
        return ctable;
    }

    function cases_item(cases) {
        var out = '';
        $.each(cases, function(index, case_obj) {
            header = '<div id="case_header"><ul>';
            header += '<li>Court Case No. ' + 
                case_obj['court_case_number'] + '</li>';
            header += '<li>DA Case No. ' + 
                case_obj['da_case_number'] + '</li>';
            header += '<li>Citation No. ' + 
                case_obj['citation_number'] + '</li>';
            header += '</div></ul>';
            out += header + charge_table(case_obj['charges']);
        });
        return out;
    }

    function munge_booking_obj(obj) {
        out = Object;
        $.each(
            {'height': 'Height',
             'weight': 'Weight',
             'hair': 'Hair',
             'swisid': 'SWIS ID',
             'bookingdate': 'Booking Date',
             'currentstatus': 'Current Status',
             'eyes': 'Eyes',
             'releasereason': 'Release Reason',
             'arrestdate': 'Arrest Date',
             'projreldate': 'Projected Release Date',
             'name': 'Name',
             'assignedfac': 'Assigned Facility',
             'age': 'Age',
             'releasedate': 'Release Date',
             'race': 'Race',
             'gender': 'Gender',
             'arrestingagency': 'Arresting Agency'},
            function(key_in, key_out) {
                out[key_out] = obj[key_in];
            });
        out['URL'] = orig_url(obj['url']);
        return out;
    }

    function booking_item(obj) {
        out = '';
        out += mugshot_item(obj);
        out += booking_dlist(munge_booking_obj(obj));
        out += cases_item(obj['cases']);
        return out;
    }

    function mugshot_item(obj) {
        return '<div id="mugshot">' + mugshot_img(obj) + '</div>';
    }

    function booking_dlist(obj) {
        // return a <div><dl><dt><dd> string from the given object
        var items = [];
        $.each(obj, function(key, val) {
            items.push('<dt>' + key + '</dt><dd>' + val + '</dd>');
        });
        return '<div id="booking_list"><dl>' + items.join('') + '</dl></div>';
    }

    function url_param(name) {
        // return the named query paramater from the current url
        var results = new RegExp(
            '[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
        if (!results) { return 0; }
        return results[1] || 0;
    }

    // write HTML from the indicated booking data to document body
    var json_href = '/data/booking/' + url_param('booking');
    $.getJSON(json_href, function(data) {
        var item = booking_item(data);
        $('<div/>', {
            'html': item
        }).appendTo('body');
    });
    
});    
