$(document).ready(function() {

    function mugshot_img(obj) {
        // return mugshot img tag for obj
        //var filename = obj_url.split('/').pop();
        //filename = filename.split('?')[1]
        //filename = filename.split('&')[0]
        filename = obj['swisid']
        return '<img src="' + '../data/mugshots/' + filename + '"/>';
        //return filename;
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

    function obj_to_dlist(obj) {
        // return a string of <dt><dd> elements from the given object
        var items = [];
        items.push(['mugshot', mugshot_img(obj)]);
        $.each(obj, function(key, val) {
            // munge attributes
            if (key == 'url') {
                val = orig_url(val);
            }
            else if (key == 'mugshot_url') {
                val = mugshot_img(val);
            }
            if ((key == 'cases') || (key == 'charges')) {
                if (key == 'cases') {
                    var name = 'case';
                } else if (key == 'charges') {
                    var name = 'charge';
                }
                val = array_to_dlist(val, name);
            }
            items.push([key, val]);
        });
        var items_out = [];
        $.each(items, function(index, tup) {
            var key = tup[0];
            var val = tup[1];
            items_out.push('<dt>' + key + '</dt><dd>' + val + '</dd>');
        });
        
        return items_out.join('');
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
        var items = obj_to_dlist(data);
        $('<dl/>', {
            'class': 'booking-list',
            'html': items
        }).appendTo('body');
    });
    
});    
