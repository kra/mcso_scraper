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

    function array_to_dlist(arr, name) {
        // return a string of <dt><dd> elements from the given array
        var items = [];
        $.each(arr, function(index, val) {
            items.push('<dt>' + name + '</dt><dd><dl>' + 
                       obj_to_dlist(val) + '</dl></dd>');
        });
        return '<dl>' + items.join('') + '</dl>';
    }

    function munge_booking_obj(obj) {
        // munge obj XXX destructively
        obj['mugshot'] = mugshot_img(obj);
        obj['url'] = orig_url(obj['url']);
        $.each(obj['cases'], function(index, case_obj) {
            case_obj['charges'] = array_to_dlist(case_obj['charges'], 'charge');
        });
        obj['cases'] = array_to_dlist(obj['cases'], 'case');
        return obj;
    }

    function booking_to_dlist(obj) {
        return obj_to_dlist(munge_booking_obj(obj));
    }

    function obj_to_dlist(obj) {
        // return a string of <dt><dd> elements from the given object
        var items = [];
        $.each(obj, function(key, val) {
            items.push('<dt>' + key + '</dt><dd>' + val + '</dd>');
        });
        return items.join('');
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
        var items = booking_to_dlist(data);
        $('<dl/>', {
            'class': 'booking-list',
            'html': items
        }).appendTo('body');
    });
    
});    
