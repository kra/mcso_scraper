$(document).ready(function() {

    var booking_index_href = '../data/booking_index'
    booking_index_href += '?_=' + Number(new Date());
    $.getJSON(booking_index_href, function(index_objs) {
        $('#booking_table').dataTable({
            "bProcessing": true,
            "bServerSide": true,
            "sAjaxSource": booking_index_href,
            "bFilter": false,
            "aoColumns": [
                { "sTitle": "name" },
                { "sTitle": "age" },
                { "sTitle": "swisid", "bSortable": false },
                { "sTitle": "race" },
                { "sTitle": "gender" },
                { "sTitle": "parsed_arrestdate" },
                { "sTitle": "parsed_bookingdate" },
                { "sTitle": "assignedfac" },
                { "sTitle": "arrestingagency" },
                { "sTitle": "currentstatus" }],
        });
    });
    
});    
