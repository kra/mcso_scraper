$(document).ready(function() {

    $.datepicker.regional[""].dateFormat = 'yy-mm-dd';
    $.datepicker.setDefaults($.datepicker.regional['']);

    $('#booking_date_start').datepicker();
    $('#booking_date_end').datepicker();

    var charge_index_href = '../data/charge_index'
    charge_index_href += '?_=' + Number(new Date());
    var b_table = $('#charge_table').dataTable({
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": charge_index_href,
        "fnServerParams": function ( aoData ) {
            aoData.push(
                { "name": "booking_date_start",
                  "value": $('#booking_date_start').val() } );
            aoData.push(
                { "name": "booking_date_end",
                  "value": $('#booking_date_end').val() } ) ;},
        "aoColumns": [
            { "sTitle": "Charge" },
            { "sTitle": "Status" },
            { "sTitle": "Bail"},
            { "sTitle": "Arrest Date" },
            { "sTitle": "Booking Date" }]
    }).columnFilter({
        "sPlaceHolder": "foot",
        "aoColumns": [
            null, null, null, null, null
        ]});

    $('#booking_date').submit(function(event) {
        event.preventDefault();
        b_table.fnDraw(); });
    
});    
