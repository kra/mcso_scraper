$(document).ready(function() {
    
    $.datepicker.regional[""].dateFormat = 'yy-mm-dd';
    $.datepicker.setDefaults($.datepicker.regional['']);

    var booking_index_href = '../data/booking_index'
    booking_index_href += '?_=' + Number(new Date());
    // XXX we don't need to getJSON anymore
    $.getJSON(booking_index_href, function(index_objs) {
        $('#booking_table').dataTable({
            "bProcessing": true,
            "bServerSide": true,
            "sAjaxSource": booking_index_href,
            "aoColumns": [
                { "sTitle": "name" },
                { "sTitle": "age" },
                { "sTitle": "swisid", "bSortable": false },
                { "sTitle": "race" },
                { "sTitle": "gender" },
                { "sTitle": "parsed_arrestdate" },
                { "sTitle": "parsed_bookingdate", "bSearchable": true },
                { "sTitle": "assignedfac" },
                { "sTitle": "arrestingagency" },
                { "sTitle": "currentstatus" }],
        }).columnFilter({
            "sPlaceHolder": "foot",
            "aoColumns": [
                null, null, null, null, null, null,
                { "type": "date-range"},
                null, null, null,
            ]});
    });
    
});    
