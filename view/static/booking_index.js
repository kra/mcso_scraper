$(document).ready(function() {
    
    $.datepicker.regional[""].dateFormat = 'yy-mm-dd';
    $.datepicker.setDefaults($.datepicker.regional['']);

    $('#booking_date_start').datepicker();
    $('#booking_date_end').datepicker();

    var booking_index_href = '../data/booking_index'
    booking_index_href += '?_=' + Number(new Date());
    var b_table = $('#booking_table').dataTable({
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": booking_index_href,
        "fnServerParams": function ( aoData ) {
            aoData.push(
                { "name": "booking_date_start",
                  "value": $('#booking_date_start').val() } );
            aoData.push(
                { "name": "booking_date_end",
                  "value": $('#booking_date_end').val() } ) ;},
        "aoColumns": [
            { "sTitle": "Name" },
            { "sTitle": "Age" },
            { "sTitle": "SWISID", "bSortable": false },
            { "sTitle": "Race" },
            { "sTitle": "Gender" },
            { "sTitle": "Arrest Date" },
            { "sTitle": "Booking Date" },
            { "sTitle": "Assigned Facility" },
            { "sTitle": "Arresting Agency" },
            { "sTitle": "Current Status" }],
    }).columnFilter({
        "sPlaceHolder": "foot",
        "aoColumns": [
            null, null, null, null, null, null, null,
            null, null, null,
        ]});

    $('#table_filter').submit(function(event) {
        event.preventDefault();
        b_table.fnDraw(); });
    
});    
