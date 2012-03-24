$(document).ready(function() {
    
    $.datepicker.regional[""].dateFormat = 'yy-mm-dd';
    $.datepicker.setDefaults($.datepicker.regional['']);

    var booking_index_href = '../data/booking_index'
    booking_index_href += '?_=' + Number(new Date());
    $('#booking_table').dataTable({
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": booking_index_href,
        "aoColumns": [
            { "sTitle": "Name" },
            { "sTitle": "Age" },
            { "sTitle": "SWISID", "bSortable": false },
            { "sTitle": "Race" },
            { "sTitle": "Gender" },
            { "sTitle": "Arrest Date" },
            { "sTitle": "Booking Date", "bSearchable": true },
            { "sTitle": "Assigned Facility" },
            { "sTitle": "Arresting Agency" },
            { "sTitle": "Current Status" }],
    }).columnFilter({
        "sPlaceHolder": "foot",
        "aoColumns": [
            null, null, null, null, null, null,
            { "type": "date-range"},
            null, null, null,
        ]});
    
});    
