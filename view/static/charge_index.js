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
        "sDom": 'T<"clear">lfrtip',
        "oTableTools": {
            "sSwfPath":
            "/static/TableTools-2.0.3/media/swf/copy_csv_xls_pdf.swf" },
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

    $('#table_filter').submit(function(event) {
        event.preventDefault();
        b_table.fnDraw(); });
    
});    
